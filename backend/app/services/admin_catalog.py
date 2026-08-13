"""تحويلات القاعدة العلمية بين النماذج والمخططات.

الملف يجيب سؤالين متكرّرين: **متى يزيد إصدار المحتوى**، و**ماذا يُعرض عن
حالة المراجعة**. تركهما في مسارات الـ API يعني ثلاث نسخ من الجواب —
واحدة لكل كيان — تتباعد مع أول تعديل.
"""

from __future__ import annotations

from typing import Any

from app.models.catalog import Exercise, Food, FoodAllergenLink, InjuryType
from app.schemas.admin_catalog import (
    ExerciseRow,
    ExerciseUpsert,
    FoodRow,
    InjuryTypeRow,
    InjuryTypeUpsert,
    ReviewState,
)

# الحقول التي يغيّر تعديلها **المضمون العلمي** لا العرض. الخطة المولَّدة
# تُختم بـ `content_version`، فزيادته على تصحيح خطأ إملائي في الاسم تجعل
# الختم بلا معنى، وإهمالها عند تغيير بروتوكول يجعله كذبة.
SCIENTIFIC_EXERCISE_FIELDS = frozenset(
    {"category", "difficulty", "primary_region", "target_muscles", "equipment", "instructions_ar"}
)
SCIENTIFIC_INJURY_FIELDS = frozenset({"body_region", "phases"})


def review_state(entity: Exercise | InjuryType) -> ReviewState:
    return ReviewState(
        reviewed_by=entity.reviewed_by,
        reviewed_at=entity.reviewed_at,
        source_reference=entity.source_reference,
        content_version=entity.content_version,
        is_reviewed=entity.is_clinically_reviewed,
    )


def food_row(food: Food, allergens: list[FoodAllergenLink]) -> FoodRow:
    return FoodRow(
        id=food.id,
        name_ar=food.name_ar,
        name_en=food.name_en,
        category=food.category,
        calories_per_100g=food.calories_per_100g,
        protein_g=food.protein_g,
        carbs_g=food.carbs_g,
        fat_g=food.fat_g,
        fiber_g=food.fiber_g,
        allergens=[link.allergen for link in allergens],
        source=food.source,
        is_active=food.is_active,
    )


def exercise_row(exercise: Exercise) -> ExerciseRow:
    return ExerciseRow(
        id=exercise.id,
        name_ar=exercise.name_ar,
        name_en=exercise.name_en,
        slug=exercise.slug,
        category=exercise.category,
        difficulty=exercise.difficulty,
        primary_region=exercise.primary_region,
        target_muscles=[str(muscle) for muscle in exercise.target_muscles],
        equipment=[str(item) for item in exercise.equipment],
        instructions_ar=exercise.instructions_ar,
        video_url=exercise.video_url,
        is_active=exercise.is_active,
        review=review_state(exercise),
    )


def injury_type_row(injury_type: InjuryType) -> InjuryTypeRow:
    return InjuryTypeRow(
        id=injury_type.id,
        name_ar=injury_type.name_ar,
        name_en=injury_type.name_en,
        slug=injury_type.slug,
        body_region=injury_type.body_region,
        description_ar=injury_type.description_ar,
        phases=[dict(phase) for phase in injury_type.phases],
        is_active=injury_type.is_active,
        review=review_state(injury_type),
    )


def _changed_fields(entity: object, payload: dict[str, Any]) -> set[str]:
    return {field for field, value in payload.items() if getattr(entity, field) != value}


def apply_exercise(exercise: Exercise, payload: ExerciseUpsert) -> bool:
    """يطبّق التعديل ويرجّع ما إذا زاد إصدار المحتوى."""
    values = payload.model_dump()
    scientific = _changed_fields(exercise, values) & SCIENTIFIC_EXERCISE_FIELDS

    for field, value in values.items():
        setattr(exercise, field, value)

    if scientific:
        exercise.content_version += 1
    return bool(scientific)


def apply_injury_type(injury_type: InjuryType, payload: InjuryTypeUpsert) -> bool:
    values = payload.model_dump()
    scientific = _changed_fields(injury_type, values) & SCIENTIFIC_INJURY_FIELDS

    for field, value in values.items():
        setattr(injury_type, field, value)

    if scientific:
        injury_type.content_version += 1
    return bool(scientific)


__all__ = [
    "SCIENTIFIC_EXERCISE_FIELDS",
    "SCIENTIFIC_INJURY_FIELDS",
    "apply_exercise",
    "apply_injury_type",
    "exercise_row",
    "food_row",
    "injury_type_row",
    "review_state",
]
