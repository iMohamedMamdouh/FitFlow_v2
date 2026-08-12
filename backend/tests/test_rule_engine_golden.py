"""حزمة الحالات المرجعية (Golden Tests) — خطوة 4.9.

القيم في ملفات YAML **محسوبة من المعادلات مباشرة** بسكربت مستقل عن كود
المحرك، لا مسجَّلة من ناتج تشغيله. الفرق جوهري: اختبار يسجّل ناتج الكود
الحالي يوثّق السلوك أيًا كان، بينما الحساب المستقل يكشف الخطأ.

أي فشل هنا يعني أن قرارًا سريريًا تغيّر — ويحتاج مراجعة أخصائي وزيادة
``RULE_ENGINE_VERSION``، لا تعديل القيمة المتوقعة لتوافق الكود.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml

from app.core.enums import ActivityLevel, Gender, Goal, InjuryStatus
from app.core.rule_engine import (
    AdjustmentKind,
    InjurySnapshot,
    Priority,
    ProfileSnapshot,
    WeightPoint,
    build_nutrition_targets,
    decide_priority,
    evaluate_adjustment,
)

GOLDEN_DIR = Path(__file__).parent / "golden"
BASE_DATE = date(2026, 1, 1)


def _load(filename: str) -> list[dict[str, Any]]:
    with (GOLDEN_DIR / filename).open(encoding="utf-8") as handle:
        return list(yaml.safe_load(handle)["cases"])


NUTRITION_CASES = _load("nutrition_cases.yaml")
PRIORITY_CASES = _load("priority_cases.yaml")
ADJUSTMENT_CASES = _load("adjustment_cases.yaml")


def _case_id(case: dict[str, Any]) -> str:
    return str(case["name"])


# ------------------------------------------------------------------ التغذية
@pytest.mark.parametrize("case", NUTRITION_CASES, ids=_case_id)
def test_nutrition_matches_the_reference_calculation(case: dict[str, Any]) -> None:
    data = case["input"]
    expected = case["expected"]

    profile = ProfileSnapshot(
        age_years=data["age_years"],
        gender=Gender(data["gender"]),
        height_cm=float(data["height_cm"]),
        weight_kg=float(data["weight_kg"]),
        activity_level=ActivityLevel(data["activity_level"]),
        goal=Goal(data["goal"]),
    )
    targets = build_nutrition_targets(profile, decide_priority(profile).priority)

    assert profile.bmi == pytest.approx(expected["bmi"], abs=0.01)
    assert targets.energy.bmr == pytest.approx(expected["bmr"], abs=0.01)
    assert targets.energy.tdee == pytest.approx(expected["tdee"], abs=0.01)
    assert targets.daily_calories == expected["daily_calories"]
    assert targets.protein_g == pytest.approx(expected["protein_g"], abs=0.1)
    assert targets.carbs_g == pytest.approx(expected["carbs_g"], abs=0.1)
    assert targets.fat_g == pytest.approx(expected["fat_g"], abs=0.1)
    assert targets.energy.safety_floor_applied is expected["safety_floor_applied"]
    assert targets.energy.deficit_capped is expected["deficit_capped"]


@pytest.mark.parametrize("case", NUTRITION_CASES, ids=_case_id)
def test_every_reference_case_respects_the_safety_floor(case: dict[str, Any]) -> None:
    """لا حالة واحدة تنزل تحت الأرضية — الفحص الشامل لـ ADR-007."""
    data = case["input"]
    profile = ProfileSnapshot(
        age_years=data["age_years"],
        gender=Gender(data["gender"]),
        height_cm=float(data["height_cm"]),
        weight_kg=float(data["weight_kg"]),
        activity_level=ActivityLevel(data["activity_level"]),
        goal=Goal(data["goal"]),
    )
    targets = build_nutrition_targets(profile, decide_priority(profile).priority)

    floor = 1500 if profile.gender is Gender.MALE else 1200
    assert targets.daily_calories >= floor
    assert targets.daily_calories <= 6000
    assert targets.protein_g > 0
    assert targets.carbs_g >= 0
    assert targets.fat_g > 0


# ----------------------------------------------------------------- الأولوية
@pytest.mark.parametrize("case", PRIORITY_CASES, ids=_case_id)
def test_priority_matches_the_reference_decision(case: dict[str, Any]) -> None:
    body = case["bmi_profile"]
    profile = ProfileSnapshot(
        age_years=35,
        gender=Gender.MALE,
        height_cm=float(body["height_cm"]),
        weight_kg=float(body["weight_kg"]),
        activity_level=ActivityLevel.MODERATE,
        goal=Goal(case["goal"]),
    )
    injuries = tuple(
        InjurySnapshot(
            injury_type_slug=item["slug"],
            status=InjuryStatus(item["status"]),
            pain_level=item["pain"],
        )
        for item in case["injuries"]
    )

    decision = decide_priority(profile, injuries)

    assert decision.priority is Priority(case["expected"])
    assert decision.reasons, "كل قرار لازم يحمل سببًا يُعرض للأخصائي"


@pytest.mark.parametrize("case", PRIORITY_CASES, ids=_case_id)
def test_acute_injury_never_gets_a_calorie_deficit(case: dict[str, Any]) -> None:
    """ADR-007: لا عجز حراري أثناء المرحلة الحادة، مهما كان الوزن."""
    if case["expected"] != Priority.REHAB_ONLY.value:
        pytest.skip("الحالة ليست تأهيلًا خالصًا")

    body = case["bmi_profile"]
    profile = ProfileSnapshot(
        age_years=35,
        gender=Gender.MALE,
        height_cm=float(body["height_cm"]),
        weight_kg=float(body["weight_kg"]),
        activity_level=ActivityLevel.MODERATE,
        goal=Goal(case["goal"]),
    )
    targets = build_nutrition_targets(profile, Priority.REHAB_ONLY)

    assert targets.daily_calories >= round(targets.energy.tdee)


# ------------------------------------------------------------------ التعديل
@pytest.mark.parametrize("case", ADJUSTMENT_CASES, ids=_case_id)
def test_adjustment_matches_the_reference_decision(case: dict[str, Any]) -> None:
    profile = ProfileSnapshot(
        age_years=35,
        gender=Gender(case["gender"]),
        height_cm=175.0,
        weight_kg=float(case["weight_kg"]),
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.WEIGHT_LOSS,
    )
    readings = tuple(
        WeightPoint(on=BASE_DATE + timedelta(days=offset), weight_kg=float(weight))
        for offset, weight in case["readings"]
    )

    adjustment = evaluate_adjustment(profile, case["current_calories"], readings)

    assert adjustment.kind is AdjustmentKind(case["expected_kind"])
    assert adjustment.suggested_calories == case["expected_calories"]


@pytest.mark.parametrize("case", ADJUSTMENT_CASES, ids=_case_id)
def test_no_adjustment_ever_goes_below_the_floor(case: dict[str, Any]) -> None:
    profile = ProfileSnapshot(
        age_years=35,
        gender=Gender(case["gender"]),
        height_cm=175.0,
        weight_kg=float(case["weight_kg"]),
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.WEIGHT_LOSS,
    )
    readings = tuple(
        WeightPoint(on=BASE_DATE + timedelta(days=offset), weight_kg=float(weight))
        for offset, weight in case["readings"]
    )

    adjustment = evaluate_adjustment(profile, case["current_calories"], readings)

    floor = 1500 if profile.gender is Gender.MALE else 1200
    assert adjustment.suggested_calories >= floor


def test_the_suite_covers_at_least_forty_reference_cases() -> None:
    """معيار الإنجاز المعلن للخطوة 4.9."""
    total = len(NUTRITION_CASES) + len(PRIORITY_CASES) + len(ADJUSTMENT_CASES)
    assert total >= 40, f"عدد الحالات المرجعية {total} أقل من الحد المطلوب"
