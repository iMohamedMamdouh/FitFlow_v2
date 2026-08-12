"""الملف الشخصي والطبي للمستخدم."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import ActivityLevel, Allergen, Gender, Goal, pg_enum


class UserProfile(Base, TimestampMixin):
    """بيانات المستخدم الثابتة نسبيًا.

    قراران يختلفان عن المخطط الأولي، وكلاهما لتفادي بيانات تتعفّن بصمت:

    1. نخزّن **تاريخ الميلاد** لا العمر. العمر المخزَّن يصبح خاطئًا بعد سنة،
       وإعادة التحليل اليومية (المرحلة 9) ستعيد حساب السعرات بعمر قديم دون
       أن يشتكي أحد.
    2. **الوزن ليس هنا** — مكانه ``physiological_readings`` لأنه سلسلة زمنية.
       تخزينه في مكانين ينتج نسختين تتباعدان، ولا أحد يعرف أيهما الصحيحة.
    """

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender] = mapped_column(pg_enum(Gender, "gender"), nullable=False)
    height_cm: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)

    activity_level: Mapped[ActivityLevel] = mapped_column(
        pg_enum(ActivityLevel, "activity_level"),
        nullable=False,
        default=ActivityLevel.SEDENTARY,
    )
    goal: Mapped[Goal] = mapped_column(pg_enum(Goal, "goal"), nullable=False)

    # حقول طبية حرة الشكل — تُملأ من نماذج المرحلة 5 ويقرأها الأخصائي.
    medical_history: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    chronic_diseases: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    medications: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # الموافقة على التنبيه الطبي — شرط قانوني قبل توليد أي خطة (خطة §9).
    consent_accepted_at: Mapped[date | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("height_cm BETWEEN 50 AND 260", name="height_within_human_range"),
        CheckConstraint("birth_date <= CURRENT_DATE", name="birth_date_not_in_future"),
        CheckConstraint(
            "birth_date >= CURRENT_DATE - INTERVAL '120 years'",
            name="birth_date_within_120_years",
        ),
    )

    @property
    def age_years(self) -> int:
        """العمر محسوبًا لحظة القراءة — لا يتقادم."""
        today = date.today()
        had_birthday = (today.month, today.day) >= (self.birth_date.month, self.birth_date.day)
        return today.year - self.birth_date.year - (0 if had_birthday else 1)

    @property
    def has_accepted_disclaimer(self) -> bool:
        return self.consent_accepted_at is not None


class FoodAllergy(Base, TimestampMixin):
    """حساسية غذائية مسجَّلة على مستخدم.

    جدول منفصل بنوع محدود بدل مصفوفة نصوص داخل الملف الشخصي: مطابقة
    الحساسية بالأطعمة تتم بمفتاح أجنبي، فيستحيل أن يمر طعام بسبب اختلاف
    كتابة اسم المسبّب.
    """

    __tablename__ = "user_food_allergies"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    allergen: Mapped[Allergen] = mapped_column(pg_enum(Allergen, "allergen"), primary_key=True)
    severity_note: Mapped[str | None] = mapped_column(Text, nullable=True)


__all__ = ["FoodAllergy", "UserProfile"]
