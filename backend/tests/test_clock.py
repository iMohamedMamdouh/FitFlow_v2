"""تقويم التطبيق: "اليوم" عند المستخدم لا عند الخادم.

الخلل الذي تحرسه هذه الاختبارات ظهر في التشغيل الحقيقي: الواجهة تحسب
تاريخ اليوم بتوقيت المنصة، وكان الخادم يقارنه بتاريخه المحلي (UTC في
الحاويات). بين 21:00 و24:00 بتوقيت UTC يكون اليوم في القاهرة قد بدأ
بالفعل، فيُرفض كل تسجيل يومي وكل قياس وزن برسالة "التاريخ في المستقبل".

الاختبارات مستقلة عن ساعة التشغيل: تختار منطقة زمنية يختلف تاريخها **الآن**
عن تاريخ UTC، فتمرّ في أي وقت من اليوم.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient

from app.core import clock
from app.core.config import get_settings
from app.models.user import User
from tests.conftest import login

# الوسم على الدوال غير المتزامنة وحدها: وسم الملف كله يُنبّه على كل
# اختبار متزامن فيه.
asyncio_test = pytest.mark.asyncio

# طرفا العالم: أحدهما دائمًا في تاريخ مختلف عن UTC مهما كانت الساعة.
_AHEAD = "Pacific/Kiritimati"  # ‎+14
_BEHIND = "Pacific/Midway"  # ‎-11


def _zone_with_a_different_date() -> str:
    utc_today = datetime.now(UTC).date()
    for zone in (_AHEAD, _BEHIND):
        if datetime.now(ZoneInfo(zone)).date() != utc_today:
            return zone
    raise AssertionError("لا يمكن أن تتطابق المنطقتان مع UTC في اللحظة نفسها")


@pytest.fixture
def shifted_timezone(monkeypatch: pytest.MonkeyPatch) -> str:
    zone = _zone_with_a_different_date()
    monkeypatch.setattr(clock, "app_timezone", lambda: ZoneInfo(zone))
    return zone


def test_today_reads_the_configured_timezone(shifted_timezone: str) -> None:
    assert clock.today() == datetime.now(ZoneInfo(shifted_timezone)).date()
    assert clock.today() != datetime.now(UTC).date()


def test_default_timezone_is_the_market_not_the_server() -> None:
    # الافتراضي يتبع السوق المستهدَف: خادم UTC لا يغيّر يوم المستخدم.
    assert get_settings().timezone == "Africa/Cairo"


@asyncio_test
async def test_a_reading_dated_today_is_accepted_across_the_date_line(
    client: AsyncClient, patient_user: User, shifted_timezone: str
) -> None:
    """قياس مؤرَّخ بـ"اليوم" عند المستخدم يُقبل ولو كان غدًا بتوقيت الخادم."""
    headers = await login(client, patient_user.email)
    local_today = datetime.now(ZoneInfo(shifted_timezone)).date()

    response = await client.post(
        "/api/v1/me/readings",
        headers=headers,
        json={"reading_date": local_today.isoformat(), "weight_kg": "80.5", "source": "manual"},
    )
    assert response.status_code == 201, response.text


@asyncio_test
async def test_tomorrow_is_still_refused(
    client: AsyncClient, patient_user: User, shifted_timezone: str
) -> None:
    """الحارس لم يُلغَ: الغد بتوقيت المنصة نفسها ما زال مرفوضًا."""
    headers = await login(client, patient_user.email)
    tomorrow = datetime.now(ZoneInfo(shifted_timezone)).date() + timedelta(days=1)

    response = await client.post(
        "/api/v1/me/readings",
        headers=headers,
        json={"reading_date": tomorrow.isoformat(), "weight_kg": "80.5", "source": "manual"},
    )
    assert response.status_code == 422
    assert "المستقبل" in response.text
