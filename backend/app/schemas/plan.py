"""مخططات الخطط ودورة اعتمادها."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import MealSlot, PlanStatus, PlanType


class PlanGenerateRequest(BaseModel):
    """طلب توليد خطة.

    لا يحتوي حقل ``status``: الخطة المولَّدة تبدأ ``draft`` دائمًا. السماح
    بتحديد الحالة عند الإنشاء يفتح طريقًا لخطة تصل المريض بلا مراجعة.
    """

    plan_type: PlanType = PlanType.NUTRITION


class MealItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    food_id: uuid.UUID
    name_ar: str
    grams: Decimal
    calories: Decimal
    protein_g: Decimal
    carbs_g: Decimal
    fat_g: Decimal


class MealRead(BaseModel):
    slot: MealSlot
    items: list[MealItemRead]
    calories: Decimal
    protein_g: Decimal


class NutritionPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    daily_calories: int
    protein_g: Decimal
    carbs_g: Decimal
    fat_g: Decimal
    notes_ar: str | None


class PlanSummary(BaseModel):
    """تمثيل مختصر — يُستخدم في القوائم."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    plan_type: PlanType
    status: PlanStatus
    rule_engine_version: str
    created_at: datetime
    approved_at: datetime | None


class PlanRead(PlanSummary):
    ai_summary: str | None = None
    review_notes: str | None = None
    approved_by_specialist_id: uuid.UUID | None = None
    nutrition: NutritionPlanRead | None = None
    meals: list[MealRead] = Field(default_factory=list)


class PlanReviewAction(BaseModel):
    """سبب القرار — يُخزَّن في سجل الانتقالات ويظهر للمريض عند الرفض."""

    reason: Annotated[str, Field(min_length=3, max_length=2000)] | None = None


class PlanTransitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: PlanStatus | None
    to_status: PlanStatus
    actor_user_id: uuid.UUID | None
    reason: str | None
    created_at: datetime


__all__ = [
    "MealItemRead",
    "MealRead",
    "NutritionPlanRead",
    "PlanGenerateRequest",
    "PlanRead",
    "PlanReviewAction",
    "PlanSummary",
    "PlanTransitionRead",
]
