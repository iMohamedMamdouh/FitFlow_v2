"""الخطط ودورة اعتمادها.

الجدول ``plans`` هو الرأس المشترك، وكل نوع خطة له جدول تفاصيل يشاركه المفتاح
الأساسي. حالة الخطة آلة حالات مفروضة **في قاعدة البيانات** لا في التطبيق وحده
(ADR-006): وصول خطة غير معتمدة إلى مريض هو أخطر عطل ممكن هنا، فيُغلق على
مستويين — CHECK وTrigger — لا على مستوى واحد يمكن لأي مسار جديد أن يتجاوزه.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import MealSlot, PlanStatus, PlanType, pg_enum

# مصدر الحقيقة الوحيد للانتقالات المسموحة. الـ trigger في الـ migration
# يطبّق نفس الجدول حرفيًا، وهناك اختبار يقارن الاثنين حتى لا يتباعدا.
ALLOWED_STATUS_TRANSITIONS: dict[PlanStatus, frozenset[PlanStatus]] = {
    PlanStatus.DRAFT: frozenset({PlanStatus.PENDING_REVIEW, PlanStatus.ARCHIVED}),
    PlanStatus.PENDING_REVIEW: frozenset(
        {PlanStatus.APPROVED, PlanStatus.CHANGES_REQUESTED, PlanStatus.ARCHIVED}
    ),
    PlanStatus.CHANGES_REQUESTED: frozenset({PlanStatus.DRAFT, PlanStatus.ARCHIVED}),
    PlanStatus.APPROVED: frozenset({PlanStatus.ACTIVE, PlanStatus.ARCHIVED}),
    PlanStatus.ACTIVE: frozenset({PlanStatus.ARCHIVED}),
    PlanStatus.ARCHIVED: frozenset(),
}


class Plan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    plan_type: Mapped[PlanType] = mapped_column(pg_enum(PlanType, "plan_type"), nullable=False)
    status: Mapped[PlanStatus] = mapped_column(
        pg_enum(PlanStatus, "plan_status"),
        nullable=False,
        default=PlanStatus.DRAFT,
        index=True,
    )

    # ختم الإصدارات: يخبرنا أي منطق وأي محتوى علمي أنتج هذه الخطة تحديدًا.
    # بدونه، تغيير قاعدة في المحرك يترك خططًا قديمة لا نعرف كيف بُنيت.
    rule_engine_version: Mapped[str] = mapped_column(String(20), nullable=False)
    content_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )

    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    approved_by_specialist_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    active_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    active_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    __table_args__ = (
        # خطة معتمدة أو مفعّلة بلا معتمِد = خطة وصلت لمريض دون مراجعة.
        CheckConstraint(
            "status NOT IN ('approved', 'active')"
            " OR (approved_by_specialist_id IS NOT NULL AND approved_at IS NOT NULL)",
            name="approved_plan_has_approver",
        ),
        # والعكس: مسودة تحمل بيانات اعتماد تعني اعتمادًا مزيّفًا.
        CheckConstraint(
            "status NOT IN ('draft', 'pending_review')"
            " OR (approved_by_specialist_id IS NULL AND approved_at IS NULL)",
            name="unapproved_plan_has_no_approver",
        ),
        CheckConstraint(
            "active_to IS NULL OR active_from IS NULL OR active_to >= active_from",
            name="active_period_is_ordered",
        ),
        Index("ix_plans_user_status", "user_id", "status"),
        # خطة مفعّلة واحدة لكل مستخدم لكل نوع — يُفرض بفهرس فريد جزئي في
        # الـ migration، لأن القيد المشروط لا يُعبَّر عنه بـ UniqueConstraint.
    )

    @property
    def is_visible_to_patient(self) -> bool:
        return self.status.is_visible_to_patient


class PlanStatusTransition(Base, UUIDPrimaryKeyMixin):
    """سجل انتقالات حالة الخطة — من غيّر الحالة، من ماذا إلى ماذا، ومتى."""

    __tablename__ = "plan_status_transitions"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[PlanStatus | None] = mapped_column(
        pg_enum(PlanStatus, "plan_status"), nullable=True
    )
    to_status: Mapped[PlanStatus] = mapped_column(
        pg_enum(PlanStatus, "plan_status"), nullable=False
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )


class NutritionPlan(Base, TimestampMixin):
    __tablename__ = "nutrition_plans"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        primary_key=True,
    )
    daily_calories: Mapped[int] = mapped_column(Integer, nullable=False)
    protein_g: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)
    carbs_g: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)
    fat_g: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)
    notes_ar: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        # الحد الأدنى المطلق من ADR-007. المحرك يطبّق الحد الأدق حسب الجنس
        # (1200 للإناث و1500 للذكور)؛ هذا القيد هو الحاجز الأخير الذي يمنع
        # أي مسار — سكربت أو استيراد أو خطأ برمجي — من كتابة خطة تجويع.
        CheckConstraint("daily_calories >= 1200", name="calories_above_safety_floor"),
        CheckConstraint("daily_calories <= 6000", name="calories_below_upper_bound"),
        CheckConstraint("protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0", name="macros_positive"),
    )


class PlanMeal(Base, UUIDPrimaryKeyMixin):
    """وجبة داخل خطة غذائية، وما فيها من أطعمة بكمياتها."""

    __tablename__ = "plan_meals"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slot: Mapped[MealSlot] = mapped_column(pg_enum(MealSlot, "meal_slot"), nullable=False)
    order_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )

    __table_args__ = (UniqueConstraint("plan_id", "slot", "order_index", name="unique_meal_slot"),)


class PlanMealItem(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "plan_meal_items"

    meal_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("plan_meals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # RESTRICT: لا يُحذف طعام من القاعدة العلمية وهو مستخدم في خطة قائمة.
    food_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("foods.id", ondelete="RESTRICT"),
        nullable=False,
    )
    grams: Mapped[Decimal] = mapped_column(Numeric(7, 1), nullable=False)

    __table_args__ = (CheckConstraint("grams > 0 AND grams <= 5000", name="grams_within_range"),)


class RehabPlan(Base, TimestampMixin):
    __tablename__ = "rehab_plans"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        primary_key=True,
    )
    injury_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("injuries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    phase: Mapped[int] = mapped_column(Integer, nullable=False)
    goals: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    __table_args__ = (CheckConstraint("phase BETWEEN 1 AND 10", name="phase_within_range"),)


class TrainingPlan(Base, TimestampMixin):
    __tablename__ = "training_plans"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sessions_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    notes_ar: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("sessions_per_week BETWEEN 1 AND 14", name="sessions_within_range"),
    )


class PlanExercise(Base, UUIDPrimaryKeyMixin):
    """تمرين موصوف داخل خطة تأهيل أو تدريب.

    جدول واحد للنوعين لأن الوصف واحد. والمفتاح الأجنبي على ``exercises``
    هو ما يجعل فحص الموانع ممكنًا: يمكن الاستعلام مباشرة عمّا إذا كانت خطة
    تحتوي تمرينًا ممنوعًا مع إصابة صاحبها.
    """

    __tablename__ = "plan_exercises"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("exercises.id", ondelete="RESTRICT"),
        nullable=False,
    )
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )

    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    intensity_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes_ar: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("sets BETWEEN 1 AND 20", name="sets_within_range"),
        CheckConstraint("reps IS NULL OR reps BETWEEN 1 AND 200", name="reps_within_range"),
        CheckConstraint(
            "day_of_week IS NULL OR day_of_week BETWEEN 0 AND 6", name="day_of_week_valid"
        ),
        CheckConstraint(
            "intensity_pct IS NULL OR intensity_pct BETWEEN 1 AND 100",
            name="intensity_within_range",
        ),
        # تمرين بلا تكرارات ولا مدة لا يمكن تنفيذه — أحدهما مطلوب.
        CheckConstraint(
            "reps IS NOT NULL OR duration_seconds IS NOT NULL",
            name="has_reps_or_duration",
        ),
    )


__all__ = [
    "ALLOWED_STATUS_TRANSITIONS",
    "NutritionPlan",
    "Plan",
    "PlanExercise",
    "PlanMeal",
    "PlanMealItem",
    "PlanStatusTransition",
    "RehabPlan",
    "TrainingPlan",
]
