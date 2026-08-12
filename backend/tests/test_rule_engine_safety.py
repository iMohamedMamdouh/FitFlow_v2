"""اختبارات الحدود الآمنة (ADR-007) ورفض المدخلات.

المبدأ المُختبَر هنا: المحرك **يرفض بصوت عالٍ** ولا يصحّح بصمت. معادلة
Mifflin-St Jeor صحيحة إحصائيًا لكنها تنتج قيمًا خطرة عند أطراف المدخلات،
وحدود هذا الملف هي ما يحوّل الخطأ من "توصية ضارة" إلى "رفض واضح".
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.core.enums import ActivityLevel, Gender, Goal
from app.core.rule_engine import (
    AdjustmentKind,
    InsufficientDataError,
    InvalidInputError,
    Priority,
    ProfileSnapshot,
    WeightPoint,
    basal_metabolic_rate,
    build_nutrition_targets,
    calculate_energy,
    distribute_macros,
    evaluate_adjustment,
    protein_reference_weight,
    summarize_trend,
)
from app.core.rule_engine.safety import MAX_DEFICIT_RATIO

BASE_DATE = date(2026, 1, 1)


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


# ----------------------------------------------------------- رفض المدخلات
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("age_years", 5),
        ("age_years", 130),
        ("height_cm", 40.0),
        ("height_cm", 260.0),
        ("weight_kg", 10.0),
        ("weight_kg", 500.0),
    ],
)
def test_out_of_range_input_is_rejected_not_clamped(field: str, value: float) -> None:
    profile = make_profile(**{field: value})

    with pytest.raises(InvalidInputError, match="خارج النطاق"):
        basal_metabolic_rate(profile)


def test_the_error_names_the_offending_field() -> None:
    """رسالة الخطأ تُعرض للأخصائي — لازم تقول أي حقل بالضبط."""
    with pytest.raises(InvalidInputError, match="الوزن"):
        basal_metabolic_rate(make_profile(weight_kg=800.0))


@pytest.mark.parametrize("age", [14, 100])
def test_boundary_ages_are_accepted(age: int) -> None:
    assert basal_metabolic_rate(make_profile(age_years=age)) > 0


# --------------------------------------------------------- أرضية السعرات
def test_floor_protects_a_very_small_woman() -> None:
    profile = make_profile(
        gender=Gender.FEMALE,
        height_cm=150.0,
        weight_kg=42.0,
        age_years=28,
        activity_level=ActivityLevel.SEDENTARY,
        goal=Goal.WEIGHT_LOSS,
    )

    targets = build_nutrition_targets(profile, Priority.WEIGHT_LOSS)

    assert targets.daily_calories == 1200
    assert targets.energy.safety_floor_applied is True


def test_floor_differs_by_gender() -> None:
    shared = {
        "height_cm": 160.0,
        "weight_kg": 48.0,
        "age_years": 30,
        "activity_level": ActivityLevel.SEDENTARY,
        "goal": Goal.WEIGHT_LOSS,
    }

    woman = build_nutrition_targets(make_profile(gender=Gender.FEMALE, **shared))
    man = build_nutrition_targets(make_profile(gender=Gender.MALE, **shared))

    assert woman.daily_calories >= 1200
    assert man.daily_calories >= 1500


def test_deficit_never_exceeds_the_cap() -> None:
    """المريض الصغير الحجم: عجز 500 ثابت يتجاوز ربع احتياجه."""
    profile = make_profile(
        gender=Gender.FEMALE,
        height_cm=152.0,
        weight_kg=52.0,
        age_years=35,
        activity_level=ActivityLevel.SEDENTARY,
        goal=Goal.WEIGHT_LOSS,
    )

    energy = calculate_energy(profile, Priority.WEIGHT_LOSS)

    assert energy.deficit_capped is True
    assert abs(energy.goal_adjustment) <= energy.tdee * MAX_DEFICIT_RATIO + 0.01


def test_large_patient_gets_the_standard_deficit() -> None:
    """السقف نسبي: لا يقيّد من احتياجه كبير."""
    profile = make_profile(weight_kg=120.0, activity_level=ActivityLevel.ACTIVE)

    energy = calculate_energy(profile, Priority.WEIGHT_LOSS)

    assert energy.deficit_capped is False
    assert energy.goal_adjustment == pytest.approx(-500.0)


def test_rehabilitation_never_gets_a_deficit() -> None:
    """ADR-007: الالتئام يحتاج طاقة كاملة مهما كان الوزن."""
    obese_and_injured = make_profile(weight_kg=115.0, goal=Goal.WEIGHT_LOSS)

    energy = calculate_energy(obese_and_injured, Priority.REHAB_ONLY)

    assert energy.goal_adjustment == pytest.approx(0.0)


def test_rehabilitation_goal_alone_also_blocks_the_deficit() -> None:
    profile = make_profile(goal=Goal.REHABILITATION, weight_kg=110.0)

    energy = calculate_energy(profile, Priority.WEIGHT_LOSS)

    assert energy.goal_adjustment == pytest.approx(0.0)


# --------------------------------------------------------------- الماكروز
def test_macros_never_go_negative_at_the_floor() -> None:
    """أخطر ناتج ممكن: كربوهيدرات سالبة تصل للمريض كخطة مستحيلة."""
    profile = make_profile(gender=Gender.FEMALE, weight_kg=120.0, height_cm=155.0)

    protein_g, carbs_g, fat_g = distribute_macros(profile, 1200)

    assert protein_g > 0
    assert carbs_g >= 0
    assert fat_g > 0


def test_macro_calories_stay_close_to_the_target() -> None:
    profile = make_profile()
    targets = build_nutrition_targets(profile)

    assert targets.macro_calories == pytest.approx(targets.daily_calories, rel=0.02)


def test_obesity_uses_adjusted_weight_for_protein() -> None:
    """1.8 جم/كجم على وزن 140 كجم كمية غير مبررة تزاحم باقي الماكروز."""
    obese = make_profile(weight_kg=140.0, height_cm=175.0)

    reference = protein_reference_weight(obese)

    assert reference < obese.weight_kg
    assert reference > 68.9  # لا ينزل تحت الوزن المثالي


def test_normal_weight_uses_actual_weight_for_protein() -> None:
    normal = make_profile(weight_kg=75.0, height_cm=178.0)

    assert protein_reference_weight(normal) == pytest.approx(75.0)


def test_rehabilitation_raises_protein() -> None:
    """التئام الأنسجة يرفع احتياج البروتين فوق حالة الثبات."""
    body = {"weight_kg": 80.0, "height_cm": 178.0}
    maintenance = build_nutrition_targets(make_profile(goal=Goal.MAINTENANCE, **body))
    rehab = build_nutrition_targets(make_profile(goal=Goal.REHABILITATION, **body))

    assert rehab.protein_g > maintenance.protein_g


# ------------------------------------------------------- بيانات غير كافية
def test_single_reading_cannot_produce_a_trend() -> None:
    with pytest.raises(InsufficientDataError):
        summarize_trend((WeightPoint(on=BASE_DATE, weight_kg=90.0),))


def test_readings_too_close_together_are_refused() -> None:
    """تذبذب الماء اليومي يشبه الثبات — قرار على 3 أيام قرار على ضجيج."""
    readings = (
        WeightPoint(on=BASE_DATE, weight_kg=90.0),
        WeightPoint(on=BASE_DATE + timedelta(days=3), weight_kg=90.0),
    )

    with pytest.raises(InsufficientDataError, match="الاتجاه"):
        summarize_trend(readings)


def test_readings_outside_the_window_are_ignored() -> None:
    readings = (
        WeightPoint(on=BASE_DATE, weight_kg=99.0),
        WeightPoint(on=BASE_DATE + timedelta(days=60), weight_kg=90.0),
        WeightPoint(on=BASE_DATE + timedelta(days=72), weight_kg=89.5),
    )

    trend = summarize_trend(readings)

    assert trend.start.weight_kg == 90.0
    assert trend.days == 12


def test_unordered_readings_are_sorted_first() -> None:
    readings = (
        WeightPoint(on=BASE_DATE + timedelta(days=14), weight_kg=89.0),
        WeightPoint(on=BASE_DATE, weight_kg=90.0),
    )

    trend = summarize_trend(readings)

    assert trend.change_kg == pytest.approx(-1.0)


# ------------------------------------------------------------- التعديلات
def test_maintenance_plan_is_never_reduced_for_a_plateau() -> None:
    """الثبات هو الهدف في خطة الثبات، لا مشكلة تُعالَج."""
    profile = make_profile(goal=Goal.MAINTENANCE)
    readings = (
        WeightPoint(on=BASE_DATE, weight_kg=82.0),
        WeightPoint(on=BASE_DATE + timedelta(days=14), weight_kg=82.0),
    )

    adjustment = evaluate_adjustment(profile, 2400, readings, is_weight_loss_plan=False)

    assert adjustment.kind is AdjustmentKind.NONE
    assert adjustment.delta == 0


def test_every_adjustment_requires_specialist_review() -> None:
    """ADR-006: لا تعديل يصل المريض دون اعتماد."""
    profile = make_profile()
    readings = (
        WeightPoint(on=BASE_DATE, weight_kg=82.0),
        WeightPoint(on=BASE_DATE + timedelta(days=14), weight_kg=82.0),
    )

    adjustment = evaluate_adjustment(profile, 2400, readings)

    assert adjustment.kind is AdjustmentKind.PLATEAU
    assert adjustment.requires_specialist_review is True
    assert adjustment.reasons, "التعديل بلا سبب لا يمكن للأخصائي مراجعته"


def test_adjustment_carries_the_engine_version() -> None:
    profile = make_profile()
    readings = (
        WeightPoint(on=BASE_DATE, weight_kg=82.0),
        WeightPoint(on=BASE_DATE + timedelta(days=14), weight_kg=81.0),
    )

    adjustment = evaluate_adjustment(profile, 2400, readings)

    assert adjustment.engine_version.count(".") == 2
