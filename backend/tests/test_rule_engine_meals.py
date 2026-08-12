"""اختبارات مولّد الوجبات — أهمها فلترة الحساسية.

طعام يحتوي مسبّب حساسية يمر إلى خطة مريض هو أخطر خطأ يمكن لهذه الوحدة
إنتاجه، وقد يكون أثره فوريًا ومهددًا للحياة.
"""

from __future__ import annotations

import pytest

from app.core.enums import ActivityLevel, Allergen, FoodCategory, Gender, Goal, MealSlot
from app.core.rule_engine import (
    FoodItem,
    InvalidInputError,
    ProfileSnapshot,
    build_meal_plan,
    build_nutrition_targets,
    exclude_allergens,
)
from app.core.rule_engine.meals import MEAL_DISTRIBUTION

CHICKEN = FoodItem(
    food_id="chicken",
    name_ar="صدور دجاج",
    category=FoodCategory.PROTEIN,
    calories_per_100g=165,
    protein_g=31,
    carbs_g=0,
    fat_g=3.6,
)
YOGHURT = FoodItem(
    food_id="yoghurt",
    name_ar="زبادي",
    category=FoodCategory.DAIRY,
    calories_per_100g=61,
    protein_g=3.5,
    carbs_g=4.7,
    fat_g=3.3,
    allergens=frozenset({Allergen.DAIRY}),
)
RICE = FoodItem(
    food_id="rice",
    name_ar="أرز أبيض",
    category=FoodCategory.GRAINS,
    calories_per_100g=130,
    protein_g=2.7,
    carbs_g=28,
    fat_g=0.3,
)
BREAD = FoodItem(
    food_id="bread",
    name_ar="عيش بلدي",
    category=FoodCategory.GRAINS,
    calories_per_100g=250,
    protein_g=8,
    carbs_g=50,
    fat_g=1.5,
    allergens=frozenset({Allergen.GLUTEN}),
)
OLIVE_OIL = FoodItem(
    food_id="olive-oil",
    name_ar="زيت زيتون",
    category=FoodCategory.FATS,
    calories_per_100g=884,
    protein_g=0,
    carbs_g=0,
    fat_g=100,
)
PEANUT_BUTTER = FoodItem(
    food_id="peanut-butter",
    name_ar="زبدة فول سوداني",
    category=FoodCategory.FATS,
    calories_per_100g=588,
    protein_g=25,
    carbs_g=20,
    fat_g=50,
    allergens=frozenset({Allergen.PEANUTS}),
)

PANTRY = (CHICKEN, YOGHURT, RICE, BREAD, OLIVE_OIL, PEANUT_BUTTER)


def make_profile(**overrides: object) -> ProfileSnapshot:
    defaults: dict[str, object] = {
        "age_years": 30,
        "gender": Gender.MALE,
        "height_cm": 178.0,
        "weight_kg": 82.0,
        "activity_level": ActivityLevel.MODERATE,
        "goal": Goal.WEIGHT_LOSS,
    }
    return ProfileSnapshot(**(defaults | overrides))  # type: ignore[arg-type]


# --------------------------------------------------------- فلترة الحساسية
def test_allergenic_foods_are_removed() -> None:
    allowed = exclude_allergens(PANTRY, frozenset({Allergen.PEANUTS}))

    assert PEANUT_BUTTER not in allowed
    assert CHICKEN in allowed


def test_multiple_allergens_are_all_honoured() -> None:
    allowed = exclude_allergens(PANTRY, frozenset({Allergen.GLUTEN, Allergen.DAIRY}))

    assert {food.food_id for food in allowed} == {"chicken", "rice", "olive-oil", "peanut-butter"}


def test_no_allergens_leaves_the_pantry_untouched() -> None:
    assert exclude_allergens(PANTRY, frozenset()) == PANTRY


def test_generated_plan_never_contains_an_allergen() -> None:
    """الاختبار الأهم في الملف."""
    allergens = frozenset({Allergen.GLUTEN, Allergen.PEANUTS})
    profile = make_profile(allergens=allergens)
    targets = build_nutrition_targets(profile)

    plan = build_meal_plan(profile, targets, PANTRY)

    served = {item.food_id for meal in plan.meals for item in meal.items}
    assert "bread" not in served
    assert "peanut-butter" not in served


def test_plan_fails_loudly_when_everything_is_excluded() -> None:
    """الامتناع الصريح أفضل من خطة فارغة تبدو صالحة."""
    profile = make_profile(allergens=frozenset({Allergen.GLUTEN, Allergen.DAIRY}))
    targets = build_nutrition_targets(profile)

    with pytest.raises(InvalidInputError, match="الحساسية"):
        build_meal_plan(profile, targets, (BREAD, YOGHURT))


# ------------------------------------------------------------ بنية الخطة
def test_meal_shares_sum_to_one() -> None:
    assert sum(MEAL_DISTRIBUTION.values()) == pytest.approx(1.0)


def test_plan_contains_every_meal_slot() -> None:
    profile = make_profile()
    plan = build_meal_plan(profile, build_nutrition_targets(profile), PANTRY)

    assert {meal.slot for meal in plan.meals} == set(MealSlot)


def test_plan_totals_land_near_the_target() -> None:
    profile = make_profile()
    targets = build_nutrition_targets(profile)

    plan = build_meal_plan(profile, targets, PANTRY)

    assert plan.calorie_deviation_pct < 20
    assert plan.protein_g == pytest.approx(targets.protein_g, rel=0.25)


def test_plan_generation_is_deterministic() -> None:
    """العشوائية ممنوعة: خطة قديمة يجب أن تُعاد إنتاجها بالضبط عند المراجعة."""
    profile = make_profile()
    targets = build_nutrition_targets(profile)

    first = build_meal_plan(profile, targets, PANTRY)
    second = build_meal_plan(profile, targets, PANTRY)

    assert first == second


def test_food_order_does_not_change_the_plan() -> None:
    """الترتيب يُحسم بمعرّف الصنف، فترتيب الإدخال لا يؤثر."""
    profile = make_profile()
    targets = build_nutrition_targets(profile)

    forward = build_meal_plan(profile, targets, PANTRY)
    backward = build_meal_plan(profile, targets, tuple(reversed(PANTRY)))

    assert forward == backward


def test_portions_stay_within_practical_limits() -> None:
    profile = make_profile()
    plan = build_meal_plan(profile, build_nutrition_targets(profile), PANTRY)

    for meal in plan.meals:
        for item in meal.items:
            assert 15 <= item.grams <= 500, f"كمية غير عملية: {item.name_ar} {item.grams} جم"


def test_every_item_reports_its_own_nutrition() -> None:
    profile = make_profile()
    plan = build_meal_plan(profile, build_nutrition_targets(profile), PANTRY)

    for meal in plan.meals:
        for item in meal.items:
            expected_calories, expected_protein, _, _ = next(
                food for food in PANTRY if food.food_id == item.food_id
            ).scaled(item.grams)
            assert item.calories == pytest.approx(expected_calories, abs=0.1)
            assert item.protein_g == pytest.approx(expected_protein, abs=0.1)


def test_plan_carries_the_engine_version() -> None:
    """كل مخرج يحمل إصداره — بدونه لا نعرف بأي منطق أُنتجت خطة قديمة."""
    profile = make_profile()
    plan = build_meal_plan(profile, build_nutrition_targets(profile), PANTRY)

    assert plan.engine_version == plan.targets.engine_version
    assert plan.engine_version.count(".") == 2
