"""مخططات الملف الشخصي والبيانات السريرية (Contract-First)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.clock import today
from app.core.enums import (
    ActivityLevel,
    Allergen,
    AttachmentType,
    BodySide,
    Gender,
    Goal,
    InjuryStatus,
    ReadingSource,
)

Height = Annotated[Decimal, Field(ge=50, le=260, decimal_places=1)]
Weight = Annotated[Decimal, Field(ge=20, le=500, decimal_places=2)]
PainLevel = Annotated[int, Field(ge=0, le=10)]
Percentage = Annotated[int, Field(ge=0, le=100)]


def _reject_future(value: date, label: str) -> date:
    # تاريخ اليوم بتوقيت المنصة لا بتوقيت الخادم — انظر ``app.core.clock``.
    if value > today():
        raise ValueError(f"{label} لا يمكن أن يكون في المستقبل")
    return value


# ------------------------------------------------------------ الملف الشخصي
class ProfileUpsert(BaseModel):
    """إنشاء أو تحديث الملف الشخصي.

    ``birth_date`` لا ``age``: العمر المخزَّن يتقادم بصمت، وإعادة التحليل
    اليومية ستحسب السعرات بعمر قديم دون أن يشتكي أحد.
    """

    birth_date: date
    gender: Gender
    height_cm: Height
    activity_level: ActivityLevel = ActivityLevel.SEDENTARY
    goal: Goal
    medical_history: list[Any] = Field(default_factory=list)
    chronic_diseases: list[Any] = Field(default_factory=list)
    medications: list[Any] = Field(default_factory=list)
    allergens: list[Allergen] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("birth_date")
    @classmethod
    def _birth_date_is_plausible(cls, value: date) -> date:
        _reject_future(value, "تاريخ الميلاد")
        if value.year < today().year - 120:
            raise ValueError("تاريخ الميلاد غير منطقي")
        return value

    @field_validator("allergens")
    @classmethod
    def _deduplicate(cls, value: list[Allergen]) -> list[Allergen]:
        return sorted(set(value))


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    birth_date: date
    age_years: int
    gender: Gender
    height_cm: Decimal
    activity_level: ActivityLevel
    goal: Goal
    medical_history: list[Any]
    chronic_diseases: list[Any]
    medications: list[Any]
    notes: str | None
    consent_accepted_at: datetime | None
    allergens: list[Allergen] = Field(default_factory=list)


# ----------------------------------------------------------------- الإصابات
class InjuryCreate(BaseModel):
    injury_type_id: uuid.UUID
    injury_date: date
    pain_level: PainLevel
    status: InjuryStatus = InjuryStatus.ACUTE
    side: BodySide = BodySide.NOT_APPLICABLE
    range_of_motion: dict[str, Any] = Field(default_factory=dict)
    had_surgery: bool = False
    surgery_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("injury_date")
    @classmethod
    def _injury_date_is_past(cls, value: date) -> date:
        return _reject_future(value, "تاريخ الإصابة")

    @model_validator(mode="after")
    def _surgery_fields_agree(self) -> InjuryCreate:
        """نفس القيد الموجود في قاعدة البيانات، مطبَّقًا مبكرًا برسالة مفهومة."""
        if self.had_surgery and self.surgery_date is None:
            raise ValueError("تاريخ الجراحة مطلوب عند تسجيل إجراء جراحي")
        if not self.had_surgery and self.surgery_date is not None:
            raise ValueError("تاريخ جراحة مسجَّل بدون إثبات إجراء الجراحة")
        if self.surgery_date is not None and self.surgery_date < self.injury_date:
            raise ValueError("تاريخ الجراحة لا يسبق تاريخ الإصابة")
        return self


class AttachmentRead(BaseModel):
    """وصف مرفق طبي — بلا ``storage_key``.

    مفتاح التخزين تفصيلة داخلية؛ تسريبه للواجهة يحوّل أي خطأ لاحق في
    التحقق من الصلاحية إلى وصول مباشر للملف.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    injury_id: uuid.UUID
    file_type: AttachmentType
    content_type: str
    size_bytes: int
    created_at: datetime


class InjuryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    injury_type_id: uuid.UUID
    injury_date: date
    pain_level: int
    status: InjuryStatus
    side: BodySide
    current_phase: int
    had_surgery: bool
    surgery_date: date | None
    notes: str | None
    created_at: datetime


# ---------------------------------------------------------------- القياسات
class ReadingCreate(BaseModel):
    reading_date: date
    weight_kg: Weight | None = None
    body_fat_pct: Annotated[Decimal, Field(ge=1, le=70)] | None = None
    muscle_mass_kg: Annotated[Decimal, Field(ge=5, le=150)] | None = None
    resting_hr: Annotated[int, Field(ge=25, le=250)] | None = None
    source: ReadingSource = ReadingSource.MANUAL

    @field_validator("reading_date")
    @classmethod
    def _reading_date_is_past(cls, value: date) -> date:
        return _reject_future(value, "تاريخ القياس")

    @model_validator(mode="after")
    def _has_at_least_one_measurement(self) -> ReadingCreate:
        """قياس فارغ يملأ السلسلة الزمنية بصفوف لا تحمل معلومة."""
        if all(
            value is None
            for value in (self.weight_kg, self.body_fat_pct, self.muscle_mass_kg, self.resting_hr)
        ):
            raise ValueError("القياس يحتاج قيمة واحدة على الأقل")
        return self


class ReadingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reading_date: date
    weight_kg: Decimal | None
    body_fat_pct: Decimal | None
    muscle_mass_kg: Decimal | None
    resting_hr: int | None
    source: ReadingSource


class DailyLogCreate(BaseModel):
    log_date: date
    weight_kg: Weight | None = None
    pain_level: PainLevel | None = None
    diet_adherence_pct: Percentage | None = None
    exercise_adherence_pct: Percentage | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("log_date")
    @classmethod
    def _log_date_is_past(cls, value: date) -> date:
        return _reject_future(value, "تاريخ التسجيل")


class DailyLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    log_date: date
    weight_kg: Decimal | None
    pain_level: int | None
    diet_adherence_pct: int | None
    exercise_adherence_pct: int | None
    notes: str | None


__all__ = [
    "AttachmentRead",
    "DailyLogCreate",
    "DailyLogRead",
    "InjuryCreate",
    "InjuryRead",
    "ProfileRead",
    "ProfileUpsert",
    "ReadingCreate",
    "ReadingRead",
]
