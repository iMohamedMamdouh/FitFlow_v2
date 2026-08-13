"""مخططات إدارة القاعدة العلمية (الخطوة 10.2).

ثلاثة كيانات بثلاثة مخططات لا مخطط واحد بحقول اختيارية: الطعام قيم غذائية
لكل 100 جرام، والتمرين موانع وحركة، ونوع الإصابة بروتوكول مراحل. دمجها
يعني نموذجًا نصفه معطَّل دائمًا، وتحققًا لا يستطيع أن يشترط شيئًا.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import (
    Allergen,
    BodyRegion,
    ExerciseCategory,
    ExerciseDifficulty,
    FoodCategory,
)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class ReviewState(BaseModel):
    """حالة المراجعة العلمية (ADR-003).

    ``is_reviewed`` محسوب لا مُخزَّن: التخزين يسمح بأن يقول الصف "مراجَع"
    بلا مراجع ولا تاريخ.
    """

    reviewed_by: str | None
    reviewed_at: datetime | None
    source_reference: str | None
    content_version: int
    is_reviewed: bool


class ReviewRequest(BaseModel):
    """توثيق مراجعة مختص.

    الاسم والمرجع إلزاميان: "مراجَع" بلا من ولا مرجع ليس مراجعة، وهو
    بالضبط ما يمنعه ADR-003.
    """

    reviewed_by: str = Field(min_length=2, max_length=200)
    source_reference: str = Field(min_length=3)

    @field_validator("reviewed_by", "source_reference")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


# ----------------------------------------------------------------- الأغذية
class FoodUpsert(BaseModel):
    name_ar: str = Field(min_length=2, max_length=200)
    name_en: str | None = Field(default=None, max_length=200)
    category: FoodCategory
    calories_per_100g: Decimal = Field(ge=0, le=950)
    protein_g: Decimal = Field(ge=0, le=100)
    carbs_g: Decimal = Field(ge=0, le=100)
    fat_g: Decimal = Field(ge=0, le=100)
    fiber_g: Decimal = Field(default=Decimal(0), ge=0, le=100)
    allergens: list[Allergen] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("name_ar")
    @classmethod
    def _strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("name_en")
    @classmethod
    def _strip_optional(cls, value: str | None) -> str | None:
        return _clean(value)


class FoodRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name_ar: str
    name_en: str | None
    category: FoodCategory
    calories_per_100g: Decimal
    protein_g: Decimal
    carbs_g: Decimal
    fat_g: Decimal
    fiber_g: Decimal
    allergens: list[Allergen]
    source: str
    is_active: bool


# ---------------------------------------------------------------- التمارين
class ExerciseUpsert(BaseModel):
    name_ar: str = Field(min_length=2, max_length=200)
    name_en: str | None = Field(default=None, max_length=200)
    slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9-]+$")
    category: ExerciseCategory
    difficulty: ExerciseDifficulty
    primary_region: BodyRegion
    target_muscles: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    instructions_ar: str | None = None
    video_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True

    @field_validator("name_ar", "slug")
    @classmethod
    def _strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("name_en", "instructions_ar", "video_url")
    @classmethod
    def _strip_optional(cls, value: str | None) -> str | None:
        return _clean(value)

    @field_validator("target_muscles", "equipment")
    @classmethod
    def _clean_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class ExerciseRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name_ar: str
    name_en: str | None
    slug: str
    category: ExerciseCategory
    difficulty: ExerciseDifficulty
    primary_region: BodyRegion
    target_muscles: list[str]
    equipment: list[str]
    instructions_ar: str | None
    video_url: str | None
    is_active: bool
    review: ReviewState


# ----------------------------------------------------------- أنواع الإصابات
class InjuryTypeUpsert(BaseModel):
    name_ar: str = Field(min_length=2, max_length=200)
    name_en: str | None = Field(default=None, max_length=200)
    slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9-]+$")
    body_region: BodyRegion
    description_ar: str | None = None
    phases: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("name_ar", "slug")
    @classmethod
    def _strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("name_en", "description_ar")
    @classmethod
    def _strip_optional(cls, value: str | None) -> str | None:
        return _clean(value)


class InjuryTypeRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name_ar: str
    name_en: str | None
    slug: str
    body_region: BodyRegion
    description_ar: str | None
    phases: list[dict[str, Any]]
    is_active: bool
    review: ReviewState


__all__ = [
    "ExerciseRow",
    "ExerciseUpsert",
    "FoodRow",
    "FoodUpsert",
    "InjuryTypeRow",
    "InjuryTypeUpsert",
    "ReviewRequest",
    "ReviewState",
]
