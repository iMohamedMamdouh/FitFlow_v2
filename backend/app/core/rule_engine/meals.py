"""توليد الوجبات من الأطعمة المسموحة.

الخوارزمية حتمية بالكامل: لا عشوائية ولا اعتماد على الوقت. نفس المدخلات
تنتج نفس الخطة دائمًا، فيمكن إعادة إنتاج أي خطة قديمة بالضبط عند مراجعة
حالة، ويمكن اختبار المخرجات بقيم مرجعية ثابتة.

الاختيار يدور بين الأصناف المتاحة حسب ترتيب الوجبة، فينتج تنوعًا دون
عشوائية.
"""

from __future__ import annotations

from app.core.enums import Allergen, FoodCategory, MealSlot
from app.core.rule_engine.models import (
    FoodItem,
    Meal,
    MealItem,
    MealPlan,
    NutritionTargets,
    ProfileSnapshot,
)
from app.core.rule_engine.safety import InvalidInputError

# توزيع السعرات على الوجبات. المجموع = 1.0 ويتحقق منه اختبار.
MEAL_DISTRIBUTION: dict[MealSlot, float] = {
    MealSlot.BREAKFAST: 0.25,
    MealSlot.LUNCH: 0.35,
    MealSlot.DINNER: 0.30,
    MealSlot.SNACK: 0.10,
}

PROTEIN_SOURCES = frozenset({FoodCategory.PROTEIN, FoodCategory.DAIRY, FoodCategory.LEGUMES})
CARB_SOURCES = frozenset({FoodCategory.GRAINS, FoodCategory.FRUITS, FoodCategory.VEGETABLES})
FAT_SOURCES = frozenset({FoodCategory.FATS})

MIN_PORTION_G = 15.0
MAX_PORTION_G = 500.0


def exclude_allergens(
    foods: tuple[FoodItem, ...],
    allergens: frozenset[Allergen],
) -> tuple[FoodItem, ...]:
    """يستبعد كل صنف يحتوي مسبّب حساسية للمستخدم.

    الاستبعاد يسبق أي اختيار — لا يُصفّى بعد بناء الوجبة. صنف يدخل الخطة
    ثم يُزال لاحقًا قد ينجو من الإزالة بسبب خطأ في مسار واحد؛ الاستبعاد
    المسبق يجعل الصنف غير موجود أصلًا في مساحة الاختيار.
    """
    if not allergens:
        return foods
    return tuple(food for food in foods if not (food.allergens & allergens))


def _pick(candidates: tuple[FoodItem, ...], rotation: int) -> FoodItem | None:
    """اختيار حتمي يدور بين المتاح — ترتيب ثابت بمعرّف الصنف."""
    if not candidates:
        return None
    ordered = sorted(candidates, key=lambda food: food.food_id)
    return ordered[rotation % len(ordered)]


def _grams_for(food: FoodItem, nutrient_grams: float, per_100g: float) -> float:
    if per_100g <= 0:
        return 0.0
    grams = nutrient_grams / (per_100g / 100)
    return min(max(grams, MIN_PORTION_G), MAX_PORTION_G)


def _to_item(food: FoodItem, grams: float) -> MealItem:
    calories, protein, carbs, fat = food.scaled(grams)
    return MealItem(
        food_id=food.food_id,
        name_ar=food.name_ar,
        grams=round(grams, 1),
        calories=round(calories, 1),
        protein_g=round(protein, 1),
        carbs_g=round(carbs, 1),
        fat_g=round(fat, 1),
    )


def _build_meal(
    slot: MealSlot,
    share: float,
    targets: NutritionTargets,
    foods: tuple[FoodItem, ...],
    rotation: int,
) -> Meal:
    protein_target = targets.protein_g * share
    fat_target = targets.fat_g * share
    carb_target = targets.carbs_g * share

    items: list[MealItem] = []

    protein_food = _pick(
        tuple(f for f in foods if f.category in PROTEIN_SOURCES and f.protein_g > 0), rotation
    )
    if protein_food is not None:
        grams = _grams_for(protein_food, protein_target, protein_food.protein_g)
        items.append(_to_item(protein_food, grams))

    covered_fat = sum(item.fat_g for item in items)
    fat_food = _pick(tuple(f for f in foods if f.category in FAT_SOURCES and f.fat_g > 0), rotation)
    if fat_food is not None and fat_target - covered_fat > 0:
        grams = _grams_for(fat_food, fat_target - covered_fat, fat_food.fat_g)
        items.append(_to_item(fat_food, grams))

    covered_carbs = sum(item.carbs_g for item in items)
    carb_food = _pick(
        tuple(f for f in foods if f.category in CARB_SOURCES and f.carbs_g > 0), rotation
    )
    if carb_food is not None and carb_target - covered_carbs > 0:
        grams = _grams_for(carb_food, carb_target - covered_carbs, carb_food.carbs_g)
        items.append(_to_item(carb_food, grams))

    return Meal(slot=slot, items=tuple(items))


def build_meal_plan(
    profile: ProfileSnapshot,
    targets: NutritionTargets,
    available_foods: tuple[FoodItem, ...],
) -> MealPlan:
    """يبني خطة يوم كامل من الأطعمة المتاحة بعد استبعاد الحساسية."""
    allowed = exclude_allergens(available_foods, profile.allergens)
    if not allowed:
        raise InvalidInputError(
            "لا توجد أطعمة متاحة بعد استبعاد مسبّبات الحساسية — لا يمكن بناء خطة"
        )

    meals = tuple(
        _build_meal(slot, share, targets, allowed, rotation)
        for rotation, (slot, share) in enumerate(MEAL_DISTRIBUTION.items())
    )
    return MealPlan(meals=meals, targets=targets)


__all__ = [
    "MEAL_DISTRIBUTION",
    "build_meal_plan",
    "exclude_allergens",
]
