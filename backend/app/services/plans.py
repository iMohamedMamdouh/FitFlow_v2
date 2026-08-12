"""الجسر بين قاعدة البيانات ومحرك القواعد.

هذه هي الطبقة الوحيدة التي تعرف الطرفين. المحرك يبقى نقيًا لأن الترجمة
تحدث هنا: نقرأ الحالة من قاعدة البيانات، نبني منها لقطة ثابتة، نستدعي
المحرك، ثم نحفظ قراره.

كل خطة تُنشأ **مسودة** بلا استثناء. لا يوجد مسار في هذا الملف ينتج خطة
معتمدة مباشرة — الاعتماد فعل بشري منفصل (ADR-006).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Allergen, PlanStatus, PlanType
from app.core.rule_engine import (
    FoodItem,
    InjurySnapshot,
    MealPlan,
    ProfileSnapshot,
    build_meal_plan,
    build_nutrition_targets,
    decide_priority,
)
from app.core.rule_engine.priority import PriorityDecision
from app.core.rule_engine.safety import InvalidInputError
from app.models.catalog import Food, FoodAllergenLink
from app.models.clinical import Injury, PhysiologicalReading
from app.models.plan import (
    NutritionPlan,
    Plan,
    PlanMeal,
    PlanMealItem,
    PlanStatusTransition,
)
from app.models.profile import FoodAllergy, UserProfile


class PlanGenerationError(Exception):
    """تعذّر توليد الخطة — الأسباب تُعرض للمستخدم كما هي."""


async def _latest_weight(session: AsyncSession, user_id: uuid.UUID) -> float | None:
    """الوزن الحالي = آخر قياس مسجَّل.

    الوزن لا يُخزَّن في الملف الشخصي عمدًا (المرحلة 2)، فمصدره الوحيد هنا.
    """
    weight = await session.scalar(
        select(PhysiologicalReading.weight_kg)
        .where(
            PhysiologicalReading.user_id == user_id,
            PhysiologicalReading.weight_kg.is_not(None),
        )
        .order_by(PhysiologicalReading.reading_date.desc())
        .limit(1)
    )
    return float(weight) if weight is not None else None


async def build_profile_snapshot(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> ProfileSnapshot:
    """يترجم حالة المستخدم المخزَّنة إلى لقطة يفهمها المحرك."""
    profile = await session.get(UserProfile, user_id)
    if profile is None:
        raise PlanGenerationError("لا يمكن توليد خطة قبل استكمال الملف الشخصي")
    if profile.consent_accepted_at is None:
        raise PlanGenerationError("لم يوافق المستخدم على التنبيه الطبي بعد")

    weight = await _latest_weight(session, user_id)
    if weight is None:
        raise PlanGenerationError("لا يوجد قياس وزن مسجَّل — لا يمكن حساب الاحتياج")

    allergens = await session.scalars(
        select(FoodAllergy.allergen).where(FoodAllergy.user_id == user_id)
    )

    return ProfileSnapshot(
        age_years=profile.age_years,
        gender=profile.gender,
        height_cm=float(profile.height_cm),
        weight_kg=weight,
        activity_level=profile.activity_level,
        goal=profile.goal,
        allergens=frozenset(allergens),
    )


async def load_injury_snapshots(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> tuple[InjurySnapshot, ...]:
    injuries = await session.scalars(select(Injury).where(Injury.user_id == user_id))
    return tuple(
        InjurySnapshot(
            injury_type_slug=str(injury.injury_type_id),
            status=injury.status,
            pain_level=injury.pain_level,
        )
        for injury in injuries
    )


async def load_food_catalogue(session: AsyncSession) -> tuple[FoodItem, ...]:
    """يحمّل الأطعمة المتاحة مع مسبّبات الحساسية المرتبطة بكل صنف."""
    foods = list(await session.scalars(select(Food).where(Food.is_active.is_(True))))
    if not foods:
        raise PlanGenerationError("قاعدة الأغذية فارغة — لا يمكن بناء خطة")

    links = await session.execute(select(FoodAllergenLink.food_id, FoodAllergenLink.allergen))
    by_food: dict[uuid.UUID, set[Allergen]] = {}
    for food_id, allergen in links:
        by_food.setdefault(food_id, set()).add(allergen)

    return tuple(
        FoodItem(
            food_id=str(food.id),
            name_ar=food.name_ar,
            category=food.category,
            calories_per_100g=float(food.calories_per_100g),
            protein_g=float(food.protein_g),
            carbs_g=float(food.carbs_g),
            fat_g=float(food.fat_g),
            allergens=frozenset(by_food.get(food.id, set())),
        )
        for food in foods
    )


async def _persist_meal_plan(session: AsyncSession, plan: Plan, meal_plan: MealPlan) -> None:
    for order, meal in enumerate(meal_plan.meals):
        stored_meal = PlanMeal(plan_id=plan.id, slot=meal.slot, order_index=order)
        session.add(stored_meal)
        await session.flush()

        for item in meal.items:
            session.add(
                PlanMealItem(
                    meal_id=stored_meal.id,
                    food_id=uuid.UUID(item.food_id),
                    grams=round(item.grams, 1),
                )
            )


async def generate_nutrition_plan(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    created_by: uuid.UUID,
) -> tuple[Plan, PriorityDecision]:
    """يولّد خطة غذائية كاملة ويحفظها **كمسودة**."""
    snapshot = await build_profile_snapshot(session, user_id)
    injuries = await load_injury_snapshots(session, user_id)
    decision = decide_priority(snapshot, injuries)

    if not decision.includes_nutrition:
        raise PlanGenerationError(
            "المسار الحالي تأهيل خالص — لا تُولَّد خطة غذائية أثناء المرحلة الحادة"
        )

    try:
        targets = build_nutrition_targets(snapshot, decision.priority)
        meal_plan = build_meal_plan(snapshot, targets, await load_food_catalogue(session))
    except InvalidInputError as exc:
        raise PlanGenerationError(str(exc)) from exc

    plan = Plan(
        user_id=user_id,
        plan_type=PlanType.NUTRITION,
        status=PlanStatus.DRAFT,
        rule_engine_version=targets.engine_version,
    )
    session.add(plan)
    await session.flush()

    session.add(
        NutritionPlan(
            plan_id=plan.id,
            daily_calories=targets.daily_calories,
            protein_g=round(targets.protein_g, 1),
            carbs_g=round(targets.carbs_g, 1),
            fat_g=round(targets.fat_g, 1),
            notes_ar=" • ".join(decision.reasons),
        )
    )
    await _persist_meal_plan(session, plan, meal_plan)

    session.add(
        PlanStatusTransition(
            plan_id=plan.id,
            from_status=None,
            to_status=PlanStatus.DRAFT,
            actor_user_id=created_by,
            reason="توليد آلي من محرك القواعد",
        )
    )
    return plan, decision


async def record_transition(
    session: AsyncSession,
    plan: Plan,
    *,
    to_status: PlanStatus,
    actor_id: uuid.UUID,
    reason: str | None = None,
) -> None:
    """ينقل الخطة ويسجّل الانتقال.

    التحقق من صحة الانتقال ليس هنا — إنه في trigger قاعدة البيانات
    (ADR-006). هذه الدالة تحاول، وقاعدة البيانات ترفض ما لا يجوز.
    """
    session.add(
        PlanStatusTransition(
            plan_id=plan.id,
            from_status=plan.status,
            to_status=to_status,
            actor_user_id=actor_id,
            reason=reason,
        )
    )
    plan.status = to_status
    if to_status is PlanStatus.APPROVED:
        plan.approved_by_specialist_id = actor_id
        plan.approved_at = datetime.now(UTC)


__all__ = [
    "PlanGenerationError",
    "build_profile_snapshot",
    "generate_nutrition_plan",
    "load_food_catalogue",
    "load_injury_snapshots",
    "record_transition",
]
