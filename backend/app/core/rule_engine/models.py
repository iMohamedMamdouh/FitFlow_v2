"""مدخلات ومخرجات محرك القواعد — dataclasses نقية.

لا ORM ولا Pydantic ولا أي إطار. المحرك يأخذ لقطة ثابتة من البيانات
ويُرجع قرارًا ثابتًا: نفس المدخلات تنتج نفس المخرجات دائمًا، فيمكن اختباره
بالكامل بلا قاعدة بيانات، ويمكن إعادة إنتاج أي خطة قديمة بالضبط.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.core.enums import (
    ActivityLevel,
    Allergen,
    FoodCategory,
    Gender,
    Goal,
    InjuryStatus,
    MealSlot,
)
from app.core.rule_engine.version import RULE_ENGINE_VERSION


@dataclass(frozen=True, slots=True)
class ProfileSnapshot:
    """حالة المستخدم لحظة التوليد.

    العمر يُمرَّر محسوبًا لا كتاريخ ميلاد: المحرك دالة نقية، ولو قرأ تاريخ
    اليوم بنفسه لأصبح ناتجه متغيرًا بمرور الوقت وتعذّر اختباره.
    """

    age_years: int
    gender: Gender
    height_cm: float
    weight_kg: float
    activity_level: ActivityLevel
    goal: Goal
    allergens: frozenset[Allergen] = field(default_factory=frozenset)

    @property
    def bmi(self) -> float:
        height_m = self.height_cm / 100
        return self.weight_kg / (height_m * height_m)


@dataclass(frozen=True, slots=True)
class InjurySnapshot:
    injury_type_slug: str
    status: InjuryStatus
    pain_level: int

    @property
    def is_active(self) -> bool:
        return self.status is not InjuryStatus.RECOVERED

    @property
    def is_acute(self) -> bool:
        return self.status is InjuryStatus.ACUTE


@dataclass(frozen=True, slots=True)
class WeightPoint:
    on: date
    weight_kg: float


@dataclass(frozen=True, slots=True)
class FoodItem:
    """صنف غذائي بقيمه لكل 100 جرام."""

    food_id: str
    name_ar: str
    category: FoodCategory
    calories_per_100g: float
    protein_g: float
    carbs_g: float
    fat_g: float
    allergens: frozenset[Allergen] = field(default_factory=frozenset)

    def scaled(self, grams: float) -> tuple[float, float, float, float]:
        """(سعرات، بروتين، كربوهيدرات، دهون) لكمية معيّنة."""
        factor = grams / 100
        return (
            self.calories_per_100g * factor,
            self.protein_g * factor,
            self.carbs_g * factor,
            self.fat_g * factor,
        )


@dataclass(frozen=True, slots=True)
class EnergyBreakdown:
    """تفصيل حساب الطاقة — يُعرض للأخصائي ليراجع كل خطوة لا النتيجة فقط."""

    bmr: float
    tdee: float
    goal_adjustment: float
    safety_floor_applied: bool
    deficit_capped: bool


@dataclass(frozen=True, slots=True)
class NutritionTargets:
    daily_calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    energy: EnergyBreakdown
    engine_version: str = RULE_ENGINE_VERSION

    @property
    def macro_calories(self) -> float:
        return self.protein_g * 4 + self.carbs_g * 4 + self.fat_g * 9


@dataclass(frozen=True, slots=True)
class MealItem:
    food_id: str
    name_ar: str
    grams: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


@dataclass(frozen=True, slots=True)
class Meal:
    slot: MealSlot
    items: tuple[MealItem, ...]

    @property
    def calories(self) -> float:
        return sum(item.calories for item in self.items)

    @property
    def protein_g(self) -> float:
        return sum(item.protein_g for item in self.items)

    @property
    def carbs_g(self) -> float:
        return sum(item.carbs_g for item in self.items)

    @property
    def fat_g(self) -> float:
        return sum(item.fat_g for item in self.items)


@dataclass(frozen=True, slots=True)
class MealPlan:
    meals: tuple[Meal, ...]
    targets: NutritionTargets
    engine_version: str = RULE_ENGINE_VERSION

    @property
    def calories(self) -> float:
        return sum(meal.calories for meal in self.meals)

    @property
    def protein_g(self) -> float:
        return sum(meal.protein_g for meal in self.meals)

    @property
    def carbs_g(self) -> float:
        return sum(meal.carbs_g for meal in self.meals)

    @property
    def fat_g(self) -> float:
        return sum(meal.fat_g for meal in self.meals)

    @property
    def calorie_deviation_pct(self) -> float:
        """انحراف المجموع الفعلي عن الهدف — يقيس جودة التوزيع."""
        target = self.targets.daily_calories
        return abs(self.calories - target) / target * 100


__all__ = [
    "EnergyBreakdown",
    "FoodItem",
    "InjurySnapshot",
    "Meal",
    "MealItem",
    "MealPlan",
    "NutritionTargets",
    "ProfileSnapshot",
    "WeightPoint",
]
