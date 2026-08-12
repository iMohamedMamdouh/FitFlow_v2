"""القاعدة العلمية: الأغذية والتمارين وأنواع الإصابات.

محتوى مشترك بين كل المستخدمين، يُدار من لوحة المدير (المرحلة 10) ويملأ في
المرحلة 3. كل صف يحمل ``content_version`` لأن الخطة المولَّدة تُختم بإصدار
المحتوى الذي استُخدم — فلو تغيّر بروتوكول لاحقًا نعرف أي الخطط بُنيت على
النسخة القديمة.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    Allergen,
    BodyRegion,
    ContraindicationSeverity,
    ExerciseCategory,
    ExerciseDifficulty,
    FoodCategory,
    pg_enum,
)


class ReviewedContentMixin:
    """توثيق المراجعة العلمية.

    ADR-003 يشترط مراجعة أخصائي حقيقي لبروتوكولات الإصابات ومكتبة التمارين
    قبل استخدامها في التوليد. الحقول هنا تجعل المراجعة بيانات يمكن الاستعلام
    عنها، لا وعدًا في وثيقة.
    """

    reviewed_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )

    @property
    def is_clinically_reviewed(self) -> bool:
        return self.reviewed_by is not None and self.reviewed_at is not None


# --------------------------------------------------------------------- foods
class Food(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "foods"

    name_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[FoodCategory] = mapped_column(
        pg_enum(FoodCategory, "food_category"), nullable=False
    )

    # كل القيم لكل 100 جرام — توحيد الأساس يمنع أخطاء تحويل صامتة.
    calories_per_100g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    protein_g: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    carbs_g: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    fat_g: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    fiber_g: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False, default=0, server_default=text("0")
    )

    # مصدر البيانات ومعرّفه هناك — يسمح بإعادة الاستيراد وكشف التكرار.
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="manual", server_default=text("'manual'")
    )
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )

    __table_args__ = (
        CheckConstraint("calories_per_100g BETWEEN 0 AND 950", name="calories_within_range"),
        CheckConstraint("protein_g BETWEEN 0 AND 100", name="protein_within_range"),
        CheckConstraint("carbs_g BETWEEN 0 AND 100", name="carbs_within_range"),
        CheckConstraint("fat_g BETWEEN 0 AND 100", name="fat_within_range"),
        CheckConstraint("fiber_g BETWEEN 0 AND 100", name="fiber_within_range"),
        # مجموع الماكروز لا يتجاوز 100 جرام في 100 جرام طعام.
        CheckConstraint("protein_g + carbs_g + fat_g <= 100", name="macros_fit_in_100g"),
        # بحث جزئي في الأسماء العربية. GIN على نص يحتاج فئة معاملات صريحة،
        # ويحتاج امتداد pg_trgm الذي تفعّله الـ migration.
        Index(
            "ix_foods_name_ar_trgm",
            "name_ar",
            postgresql_using="gin",
            postgresql_ops={"name_ar": "gin_trgm_ops"},
        ),
        Index("ix_foods_category_active", "category", "is_active"),
    )


class FoodAllergenLink(Base):
    """مسبّبات الحساسية في طعام معيّن."""

    __tablename__ = "food_allergens"

    food_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("foods.id", ondelete="CASCADE"),
        primary_key=True,
    )
    allergen: Mapped[Allergen] = mapped_column(pg_enum(Allergen, "allergen"), primary_key=True)


# ----------------------------------------------------------------- exercises
class Exercise(Base, UUIDPrimaryKeyMixin, TimestampMixin, ReviewedContentMixin):
    __tablename__ = "exercises"

    name_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    category: Mapped[ExerciseCategory] = mapped_column(
        pg_enum(ExerciseCategory, "exercise_category"), nullable=False
    )
    difficulty: Mapped[ExerciseDifficulty] = mapped_column(
        pg_enum(ExerciseDifficulty, "exercise_difficulty"), nullable=False
    )
    primary_region: Mapped[BodyRegion] = mapped_column(
        pg_enum(BodyRegion, "body_region"), nullable=False
    )

    target_muscles: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    equipment: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    instructions_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )

    __table_args__ = (
        Index("ix_exercises_category_difficulty", "category", "difficulty"),
        Index("ix_exercises_region_active", "primary_region", "is_active"),
    )


class InjuryType(Base, UUIDPrimaryKeyMixin, TimestampMixin, ReviewedContentMixin):
    """نوع إصابة وبروتوكول تأهيله.

    ``phases`` يصف مراحل التأهيل ومعايير الانتقال بينها، بالشكل::

        [{"phase": 1, "name_ar": "...", "goals": [...],
          "criteria_to_advance": [...], "typical_duration_days": 14}, ...]
    """

    __tablename__ = "injury_types"

    name_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    body_region: Mapped[BodyRegion] = mapped_column(
        pg_enum(BodyRegion, "body_region"), nullable=False
    )
    description_ar: Mapped[str | None] = mapped_column(Text, nullable=True)

    phases: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )

    __table_args__ = (
        CheckConstraint("jsonb_typeof(phases) = 'array'", name="phases_is_array"),
        Index("ix_injury_types_region_active", "body_region", "is_active"),
    )


class ExerciseContraindication(Base):
    """منع تمرين مع نوع إصابة.

    **أخطر علاقة في النظام كله.** لولا المفتاحان الأجنبيان هنا لكانت
    الموانع مصفوفة معرّفات داخل JSON، وخطأ حرف واحد فيها يعني تمرينًا
    ممنوعًا يمر إلى مريض مصاب دون أي رسالة خطأ.
    """

    __tablename__ = "exercise_contraindications"

    exercise_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
    )
    injury_type_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("injury_types.id", ondelete="CASCADE"),
        primary_key=True,
    )
    severity: Mapped[ContraindicationSeverity] = mapped_column(
        pg_enum(ContraindicationSeverity, "contraindication_severity"),
        nullable=False,
        default=ContraindicationSeverity.ABSOLUTE,
    )
    rationale_ar: Mapped[str | None] = mapped_column(Text, nullable=True)


__all__ = [
    "Exercise",
    "ExerciseContraindication",
    "Food",
    "FoodAllergenLink",
    "InjuryType",
    "ReviewedContentMixin",
]
