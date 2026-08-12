"""ربط التعدادات النقية بأنواع ENUM في Postgres.

القيم نفسها معرَّفة في ``app/core/enums.py`` بلا اعتماديات، ويُعاد تصديرها
هنا حتى تبقى نقاط الاستيراد القائمة كما هي.
"""

from __future__ import annotations

import enum
from typing import TypeVar

from sqlalchemy import Enum as SAEnum

from app.core.enums import (
    ActivityLevel,
    Allergen,
    AttachmentType,
    BodyRegion,
    BodySide,
    ContraindicationSeverity,
    ExerciseCategory,
    ExerciseDifficulty,
    FoodCategory,
    Gender,
    Goal,
    InjuryStatus,
    MealSlot,
    PlanStatus,
    PlanType,
    ReadingSource,
)

_E = TypeVar("_E", bound=enum.Enum)


def pg_enum(enum_cls: type[_E], name: str) -> SAEnum:
    """يبني نوع ENUM في Postgres يخزّن القيم النصية لا أسماء الأعضاء."""
    return SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda cls: [member.value for member in cls],
    )


__all__ = [
    "ActivityLevel",
    "Allergen",
    "AttachmentType",
    "BodyRegion",
    "BodySide",
    "ContraindicationSeverity",
    "ExerciseCategory",
    "ExerciseDifficulty",
    "FoodCategory",
    "Gender",
    "Goal",
    "InjuryStatus",
    "MealSlot",
    "PlanStatus",
    "PlanType",
    "ReadingSource",
    "pg_enum",
]
