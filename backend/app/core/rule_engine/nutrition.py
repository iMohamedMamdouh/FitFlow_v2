"""حسابات الطاقة وتوزيع الماكروز.

المعادلة المعتمدة: **Mifflin-St Jeor** — الأدق للسكان العامين مقارنة
بـ Harris-Benedict، والأوسع اعتمادًا في المراجع السريرية.

ترتيب الحساب مقصود، وكل خطوة تُسجَّل في ``EnergyBreakdown`` ليراجع الأخصائي
الطريق لا النتيجة::

    BMR → TDEE → تعديل الهدف → سقف العجز (25%) → أرضية السعرات الآمنة
"""

from __future__ import annotations

from app.core.enums import Gender, Goal
from app.core.rule_engine.models import EnergyBreakdown, NutritionTargets, ProfileSnapshot
from app.core.rule_engine.priority import OBESITY_BMI_THRESHOLD, Priority
from app.core.rule_engine.safety import (
    ACTIVITY_MULTIPLIERS,
    FAT_CALORIE_SHARE,
    MAX_AGE_YEARS,
    MAX_DAILY_CALORIES,
    MAX_DEFICIT_RATIO,
    MAX_HEIGHT_CM,
    MAX_PROTEIN_G_PER_KG,
    MAX_WEIGHT_KG,
    MIN_AGE_YEARS,
    MIN_FAT_G_PER_KG,
    MIN_HEIGHT_CM,
    MIN_PROTEIN_G_PER_KG,
    MIN_WEIGHT_KG,
    TARGET_DEFICIT_KCAL,
    TARGET_SURPLUS_KCAL,
    calorie_floor,
    require_range,
)

# بروتين بالجرام لكل كيلوجرام من الوزن المرجعي.
PROTEIN_G_PER_KG_BY_GOAL: dict[Goal, float] = {
    Goal.WEIGHT_LOSS: 1.8,  # يحافظ على الكتلة العضلية أثناء العجز
    Goal.MUSCLE_GAIN: 1.8,
    Goal.MAINTENANCE: 1.4,
    Goal.REHABILITATION: 2.0,  # التئام الأنسجة يرفع الاحتياج
}

# مؤشر كتلة مرجعي لحساب "الوزن المثالي" عند تعديل وزن السمنة.
REFERENCE_BMI = 22.5
ADJUSTED_WEIGHT_FACTOR = 0.25


def validate_profile(profile: ProfileSnapshot) -> None:
    """يرفض أي مدخل خارج النطاق البشري المعقول قبل أي حساب."""
    require_range(profile.age_years, MIN_AGE_YEARS, MAX_AGE_YEARS, field="العمر", unit="سنة")
    require_range(profile.height_cm, MIN_HEIGHT_CM, MAX_HEIGHT_CM, field="الطول", unit="سم")
    require_range(profile.weight_kg, MIN_WEIGHT_KG, MAX_WEIGHT_KG, field="الوزن", unit="كجم")


def basal_metabolic_rate(profile: ProfileSnapshot) -> float:
    """معدل الأيض الأساسي (Mifflin-St Jeor)."""
    validate_profile(profile)
    base = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age_years
    return base + 5 if profile.gender is Gender.MALE else base - 161


def total_daily_energy_expenditure(profile: ProfileSnapshot) -> float:
    """الاحتياج اليومي الكلي: الأيض الأساسي مضروبًا في معامل النشاط."""
    return basal_metabolic_rate(profile) * ACTIVITY_MULTIPLIERS[profile.activity_level]


def protein_reference_weight(profile: ProfileSnapshot) -> float:
    """الوزن المستخدم في حساب البروتين.

    عند السمنة نستخدم **الوزن المعدَّل** لا الفعلي. الأنسجة الدهنية لا
    تستهلك بروتينًا كالعضل، فحساب 1.8 جم/كجم على وزن 140 كجم ينتج كمية
    غير مبررة تزاحم باقي الماكروز وتُثقل الكلى دون فائدة.
    """
    if profile.bmi < OBESITY_BMI_THRESHOLD:
        return profile.weight_kg

    height_m = profile.height_cm / 100
    ideal_weight = REFERENCE_BMI * height_m * height_m
    return ideal_weight + ADJUSTED_WEIGHT_FACTOR * (profile.weight_kg - ideal_weight)


def _goal_adjustment(profile: ProfileSnapshot, tdee: float, priority: Priority) -> float:
    """تعديل السعرات حسب الهدف — سالب للعجز وموجب للفائض."""
    # التأهيل الخالص لا عجز فيه مهما كان الوزن: الالتئام يحتاج طاقة كاملة.
    if priority is Priority.REHAB_ONLY or profile.goal is Goal.REHABILITATION:
        return 0.0
    if profile.goal is Goal.MUSCLE_GAIN:
        return float(TARGET_SURPLUS_KCAL)
    if profile.goal is Goal.WEIGHT_LOSS or priority in {
        Priority.WEIGHT_LOSS,
        Priority.REHAB_PLUS_DIET,
    }:
        return -float(TARGET_DEFICIT_KCAL)
    return 0.0


def calculate_energy(
    profile: ProfileSnapshot,
    priority: Priority = Priority.FITNESS,
) -> EnergyBreakdown:
    """يحسب الطاقة اليومية مع تطبيق كل حدود الأمان، ويوثّق ما طُبِّق منها."""
    bmr = basal_metabolic_rate(profile)
    tdee = bmr * ACTIVITY_MULTIPLIERS[profile.activity_level]

    adjustment = _goal_adjustment(profile, tdee, priority)

    # سقف العجز: لا يتجاوز نسبة من الاحتياج مهما كان الهدف.
    max_deficit = tdee * MAX_DEFICIT_RATIO
    deficit_capped = adjustment < 0 and abs(adjustment) > max_deficit
    if deficit_capped:
        adjustment = -max_deficit

    target = tdee + adjustment

    # الأرضية الآمنة — آخر حاجز، يُطبَّق بعد كل شيء.
    floor = calorie_floor(profile.gender)
    floor_applied = target < floor
    if floor_applied:
        target = float(floor)

    target = min(target, float(MAX_DAILY_CALORIES))

    return EnergyBreakdown(
        bmr=bmr,
        tdee=tdee,
        goal_adjustment=target - tdee,
        safety_floor_applied=floor_applied,
        deficit_capped=deficit_capped,
    )


def distribute_macros(
    profile: ProfileSnapshot,
    daily_calories: int,
) -> tuple[float, float, float]:
    """يوزّع السعرات على (بروتين، كربوهيدرات، دهون) بالجرام.

    الترتيب: البروتين أولًا (احتياج مرتبط بالوزن لا بالسعرات)، ثم الدهون
    (حصة من السعرات مع حد أدنى هرموني)، والكربوهيدرات هي الباقي.
    """
    reference_weight = protein_reference_weight(profile)
    protein_per_kg = PROTEIN_G_PER_KG_BY_GOAL[profile.goal]
    protein_per_kg = min(max(protein_per_kg, MIN_PROTEIN_G_PER_KG), MAX_PROTEIN_G_PER_KG)
    protein_g = protein_per_kg * reference_weight

    fat_g = max(daily_calories * FAT_CALORIE_SHARE / 9, MIN_FAT_G_PER_KG * reference_weight)

    remaining = daily_calories - (protein_g * 4 + fat_g * 9)

    # عند سعرات منخفضة قد يلتهم البروتين والدهون كل الميزانية. نخفّض
    # البروتين تدريجيًا حتى حده الأدنى بدل إخراج كربوهيدرات سالبة —
    # قيمة سالبة هنا تعني خطة مستحيلة تصل للمريض بلا أي تحذير.
    if remaining < 0:
        min_protein_g = MIN_PROTEIN_G_PER_KG * reference_weight
        available_for_protein = daily_calories - fat_g * 9
        protein_g = max(min_protein_g, available_for_protein / 4)
        remaining = daily_calories - (protein_g * 4 + fat_g * 9)

    carbs_g = max(remaining / 4, 0.0)
    return round(protein_g, 1), round(carbs_g, 1), round(fat_g, 1)


def build_nutrition_targets(
    profile: ProfileSnapshot,
    priority: Priority = Priority.FITNESS,
) -> NutritionTargets:
    """المدخل الرئيسي: من لقطة المستخدم إلى أهداف غذائية كاملة."""
    energy = calculate_energy(profile, priority)
    daily_calories = round(energy.tdee + energy.goal_adjustment)
    protein_g, carbs_g, fat_g = distribute_macros(profile, daily_calories)

    return NutritionTargets(
        daily_calories=daily_calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        energy=energy,
    )


__all__ = [
    "PROTEIN_G_PER_KG_BY_GOAL",
    "basal_metabolic_rate",
    "build_nutrition_targets",
    "calculate_energy",
    "distribute_macros",
    "protein_reference_weight",
    "total_daily_energy_expenditure",
    "validate_profile",
]
