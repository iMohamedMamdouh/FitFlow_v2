"""تقويم التطبيق.

**اليوم عند المستخدم لا عند الخادم.** الواجهة تحسب "اليوم" بتوقيت المنصة
(``Africa/Cairo``)، وكان الخادم يقارنه بتاريخه المحلي — وهو UTC في
الحاويات وفي التكامل المستمر. النتيجة: بين الساعة 21:00 و24:00 بتوقيت UTC
يكون التاريخ عند المستخدم قد دخل الغد بالفعل، فيُرفض كل تسجيل يومي وكل
قياس وزن برسالة "التاريخ في المستقبل" — ثلاث ساعات كل ليلة، ولمستخدمين
لم يخطئوا في شيء.

اللحظات (``datetime``) تبقى UTC كما هي: الختم الزمني حقيقة مطلقة، أما
**اليوم** فمفهوم محلي — والتفريق بينهما هو كل ما في هذا الملف.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def app_timezone() -> ZoneInfo:
    return ZoneInfo(get_settings().timezone)


def today() -> date:
    """تاريخ اليوم بتوقيت المنصة — المرجع الوحيد لكل مقارنة تاريخ."""
    return datetime.now(app_timezone()).date()


__all__ = ["app_timezone", "today"]
