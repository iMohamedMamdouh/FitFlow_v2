"""مخططات لوحة الأخصائي (المرحلة 8)."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PatientFlag(enum.StrEnum):
    """مؤشر حالة المريض في قائمة الأخصائي.

    القائمة المرتّبة أبجديًا عديمة الفائدة لأخصائي عنده ثلاثون مريضًا؛ ما
    يحتاجه هو **من يستدعي تدخّلًا اليوم**. لذلك المؤشرات مرتَّبة بالأولوية
    ويُختار أعلاها لكل مريض:

    ``NEEDS_REVIEW``  خطة تنتظر توقيعه — الوحيد الذي يعطّله شخص آخر
    ``ACUTE_INJURY``  إصابة حادة مسجَّلة، وهي تُقدَّم على أي هدف
    ``STALLED``       لا تسجيل يومي منذ أسبوع — المتابعة انقطعت
    ``NOT_STARTED``   لم يستكمل ملفه أو لم يوافق على التنبيه بعد
    ``ON_TRACK``      لا شيء يستدعي تدخّلًا
    """

    NEEDS_REVIEW = "needs_review"
    ACUTE_INJURY = "acute_injury"
    STALLED = "stalled"
    NOT_STARTED = "not_started"
    ON_TRACK = "on_track"


# عدد الأيام بلا تسجيل يومي قبل اعتبار المتابعة متعثّرة.
STALLED_AFTER_DAYS = 7


class PatientSummary(BaseModel):
    """سطر واحد في قائمة مرضى الأخصائي.

    كل ما يحتاجه القرار "أفتح هذا الملف الآن أم لا" مجمَّع هنا في استعلام
    واحد. البديل — جلب القائمة ثم نداء لكل مريض — يعني عشرات النداءات
    لعرض شاشة واحدة.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    flag: PatientFlag
    plans_awaiting_review: int
    has_active_plan: bool
    active_injuries: int
    has_acute_injury: bool
    profile_complete: bool
    consent_accepted: bool

    latest_weight_kg: Decimal | None
    weight_change_kg: Decimal | None
    last_log_date: date | None
    days_since_last_log: int | None
    diet_adherence_avg: int | None


class SpecialistNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    specialist_id: uuid.UUID | None
    plan_id: uuid.UUID | None
    note: str
    is_internal: bool
    created_at: datetime


class SpecialistNoteCreate(BaseModel):
    """ملاحظة على مريض.

    الحقول في الجسم لا في الـ query string: ملاحظة سريرية قد تكون فقرة
    كاملة، ووضعها في الرابط يعني ظهورها في سجلات الخادم وفي تاريخ
    المتصفح — وهي بيانات مريض.
    """

    note: str = Field(min_length=1, max_length=4000)
    plan_id: uuid.UUID | None = None
    # ملاحظة داخلية لا يراها المريض — مساحة الأخصائي للتفكير السريري.
    is_internal: bool = False


class AuditEntryRead(BaseModel):
    """سطر من سجل التدقيق كما يُعرض للأخصائي (الخطوة 8.5)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    action: str
    entity_type: str
    entity_id: str | None
    actor_user_id: uuid.UUID | None
    actor_name: str | None = None
    created_at: datetime


__all__ = [
    "STALLED_AFTER_DAYS",
    "AuditEntryRead",
    "PatientFlag",
    "PatientSummary",
    "SpecialistNoteCreate",
    "SpecialistNoteRead",
]
