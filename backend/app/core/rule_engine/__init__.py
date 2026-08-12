"""محرك القواعد — قلب المنصة.

**وحدة نقية**: ممنوع أن تستورد FastAPI أو SQLAlchemy أو أي إطار. يُفرض ذلك
باختبار معماري، لا بالاتفاق. القيمة في أن كل قرار سريري هنا قابل للاختبار
بلا قاعدة بيانات ولا خادم، ومحسوب بالكامل من مدخلات صريحة.

المبدأ الحاكم (ADR-001): المحرك **يقرر**، والذكاء الاصطناعي **يشرح**،
والأخصائي **يعتمد**.
"""

from app.core.rule_engine.adjustments import (
    AdjustmentKind,
    PlanAdjustment,
    WeightTrend,
    evaluate_adjustment,
    summarize_trend,
)
from app.core.rule_engine.meals import MEAL_DISTRIBUTION, build_meal_plan, exclude_allergens
from app.core.rule_engine.models import (
    EnergyBreakdown,
    FoodItem,
    InjurySnapshot,
    Meal,
    MealItem,
    MealPlan,
    NutritionTargets,
    ProfileSnapshot,
    WeightPoint,
)
from app.core.rule_engine.nutrition import (
    basal_metabolic_rate,
    build_nutrition_targets,
    calculate_energy,
    distribute_macros,
    protein_reference_weight,
    total_daily_energy_expenditure,
)
from app.core.rule_engine.priority import Priority, PriorityDecision, decide_priority
from app.core.rule_engine.safety import (
    InsufficientDataError,
    InvalidInputError,
    RuleEngineError,
)
from app.core.rule_engine.version import RULE_ENGINE_VERSION

__all__ = [
    "MEAL_DISTRIBUTION",
    "RULE_ENGINE_VERSION",
    "AdjustmentKind",
    "EnergyBreakdown",
    "FoodItem",
    "InjurySnapshot",
    "InsufficientDataError",
    "InvalidInputError",
    "Meal",
    "MealItem",
    "MealPlan",
    "NutritionTargets",
    "PlanAdjustment",
    "Priority",
    "PriorityDecision",
    "ProfileSnapshot",
    "RuleEngineError",
    "WeightPoint",
    "WeightTrend",
    "basal_metabolic_rate",
    "build_meal_plan",
    "build_nutrition_targets",
    "calculate_energy",
    "decide_priority",
    "distribute_macros",
    "evaluate_adjustment",
    "exclude_allergens",
    "protein_reference_weight",
    "summarize_trend",
    "total_daily_energy_expenditure",
]
