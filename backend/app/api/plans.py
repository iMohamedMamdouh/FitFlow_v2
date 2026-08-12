"""توليد الخطط ودورة اعتمادها.

الترتيب هنا يعكس ADR-006 حرفيًا: التوليد ينتج **مسودة** فقط، والانتقال بين
الحالات فعل منفصل لكل خطوة، والاعتماد حكر على الأخصائي.

قاعدة البيانات هي الحكم النهائي على صحة الانتقال (trigger). هذه المسارات
تحاول، وقاعدة البيانات ترفض ما لا يجوز — فلا يكفي تجاوز هذه الطبقة.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access import require_patient_access
from app.core.audit import record_audit
from app.core.db import get_session
from app.core.deps import CurrentUser, require_roles
from app.core.enums import PlanStatus
from app.models.audit import AuditAction
from app.models.catalog import Food
from app.models.plan import (
    NutritionPlan,
    Plan,
    PlanMeal,
    PlanMealItem,
    PlanStatusTransition,
)
from app.models.user import User, UserRole
from app.schemas.plan import (
    MealItemRead,
    MealRead,
    NutritionPlanRead,
    PlanGenerateRequest,
    PlanRead,
    PlanReviewAction,
    PlanSummary,
    PlanTransitionRead,
)
from app.services.plans import PlanGenerationError, generate_nutrition_plan, record_transition

router = APIRouter(prefix="/plans", tags=["plans"])

Session = Annotated[AsyncSession, Depends(get_session)]
Reviewer = Annotated[User, Depends(require_roles(UserRole.SPECIALIST, UserRole.ADMIN))]

_PLAN_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="الخطة غير موجودة",
)


async def _load_plan(session: AsyncSession, plan_id: uuid.UUID) -> Plan:
    plan = await session.get(Plan, plan_id)
    if plan is None:
        raise _PLAN_NOT_FOUND
    return plan


async def _serialize(session: AsyncSession, plan: Plan) -> PlanRead:
    nutrition = await session.get(NutritionPlan, plan.id)

    meals_result = await session.scalars(
        select(PlanMeal).where(PlanMeal.plan_id == plan.id).order_by(PlanMeal.order_index)
    )
    meals: list[MealRead] = []
    for meal in meals_result:
        rows = await session.execute(
            select(PlanMealItem, Food)
            .join(Food, Food.id == PlanMealItem.food_id)
            .where(PlanMealItem.meal_id == meal.id)
        )
        items = []
        for item, food in rows:
            # الحساب بـ Decimal طوال الطريق: خلط Decimal بـ float يرفع
            # TypeError، وتحويلها إلى float يُدخل خطأ تقريب في قيم غذائية.
            factor = item.grams / Decimal(100)
            items.append(
                MealItemRead(
                    food_id=food.id,
                    name_ar=food.name_ar,
                    grams=item.grams,
                    calories=round(food.calories_per_100g * factor, 1),
                    protein_g=round(food.protein_g * factor, 1),
                    carbs_g=round(food.carbs_g * factor, 1),
                    fat_g=round(food.fat_g * factor, 1),
                )
            )
        meals.append(
            MealRead(
                slot=meal.slot,
                items=items,
                calories=round(sum((i.calories for i in items), Decimal(0)), 1),
                protein_g=round(sum((i.protein_g for i in items), Decimal(0)), 1),
            )
        )

    return PlanRead(
        id=plan.id,
        user_id=plan.user_id,
        plan_type=plan.plan_type,
        status=plan.status,
        rule_engine_version=plan.rule_engine_version,
        created_at=plan.created_at,
        approved_at=plan.approved_at,
        approved_by_specialist_id=plan.approved_by_specialist_id,
        ai_summary=plan.ai_summary,
        review_notes=plan.review_notes,
        nutrition=NutritionPlanRead.model_validate(nutrition) if nutrition else None,
        meals=meals,
    )


async def _transition(
    session: AsyncSession,
    plan: Plan,
    *,
    to_status: PlanStatus,
    actor: User,
    action: AuditAction,
    request: Request,
    reason: str | None = None,
) -> Plan:
    """ينفّذ الانتقال ويترجم رفض قاعدة البيانات إلى رسالة مفهومة."""
    await record_transition(session, plan, to_status=to_status, actor_id=actor.id, reason=reason)
    await record_audit(
        session,
        action=action,
        entity_type="plan",
        entity_id=plan.id,
        actor_user_id=actor.id,
        after={"status": to_status.value},
        request=request,
    )
    try:
        await session.commit()
    except DBAPIError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"انتقال غير مسموح إلى الحالة {to_status.value}",
        ) from exc

    await session.refresh(plan)
    return plan


# ------------------------------------------------------------------ التوليد
@router.post("/generate", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
async def generate_plan(
    payload: PlanGenerateRequest,
    request: Request,
    user: CurrentUser,
    session: Session,
    patient_id: uuid.UUID | None = None,
) -> PlanRead:
    """يولّد خطة **مسودة**.

    المريض يولّد لنفسه، والأخصائي يولّد لمرضاه. الناتج في الحالتين مسودة
    لا يراها المريض قبل الاعتماد.
    """
    target_id = patient_id or user.id
    await require_patient_access(session, user, target_id)

    try:
        plan, decision = await generate_nutrition_plan(
            session, user_id=target_id, created_by=user.id
        )
    except PlanGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    await record_audit(
        session,
        action=AuditAction.PLAN_GENERATED,
        entity_type="plan",
        entity_id=plan.id,
        actor_user_id=user.id,
        after={"priority": decision.priority.value, "plan_type": payload.plan_type.value},
        request=request,
    )
    await session.commit()
    await session.refresh(plan)
    return await _serialize(session, plan)


# ------------------------------------------------------------------ القراءة
@router.get("/{plan_id}", response_model=PlanRead)
async def read_plan(
    plan_id: uuid.UUID,
    user: CurrentUser,
    session: Session,
) -> PlanRead:
    plan = await _load_plan(session, plan_id)
    await require_patient_access(session, user, plan.user_id)

    # المريض لا يرى خطته قبل اعتمادها، حتى وهي خطته.
    is_own_patient_view = user.id == plan.user_id and user.role is UserRole.PATIENT
    if is_own_patient_view and not plan.status.is_visible_to_patient:
        raise _PLAN_NOT_FOUND

    return await _serialize(session, plan)


@router.get("/{plan_id}/history", response_model=list[PlanTransitionRead])
async def read_plan_history(
    plan_id: uuid.UUID,
    reviewer: Reviewer,
    session: Session,
) -> list[PlanStatusTransition]:
    plan = await _load_plan(session, plan_id)
    await require_patient_access(session, reviewer, plan.user_id)

    result = await session.scalars(
        select(PlanStatusTransition)
        .where(PlanStatusTransition.plan_id == plan_id)
        .order_by(PlanStatusTransition.created_at)
    )
    return list(result)


# -------------------------------------------------------------- دورة الاعتماد
@router.post("/{plan_id}/submit", response_model=PlanSummary)
async def submit_for_review(
    plan_id: uuid.UUID,
    request: Request,
    user: CurrentUser,
    session: Session,
) -> Plan:
    plan = await _load_plan(session, plan_id)
    await require_patient_access(session, user, plan.user_id)

    return await _transition(
        session,
        plan,
        to_status=PlanStatus.PENDING_REVIEW,
        actor=user,
        action=AuditAction.PLAN_SUBMITTED_FOR_REVIEW,
        request=request,
    )


@router.post("/{plan_id}/approve", response_model=PlanSummary)
async def approve_plan(
    plan_id: uuid.UUID,
    payload: PlanReviewAction,
    request: Request,
    reviewer: Reviewer,
    session: Session,
) -> Plan:
    """اعتماد الخطة — حكر على الأخصائي والمدير."""
    plan = await _load_plan(session, plan_id)
    await require_patient_access(session, reviewer, plan.user_id)

    return await _transition(
        session,
        plan,
        to_status=PlanStatus.APPROVED,
        actor=reviewer,
        action=AuditAction.PLAN_APPROVED,
        request=request,
        reason=payload.reason,
    )


@router.post("/{plan_id}/request-changes", response_model=PlanSummary)
async def request_changes(
    plan_id: uuid.UUID,
    payload: PlanReviewAction,
    request: Request,
    reviewer: Reviewer,
    session: Session,
) -> Plan:
    plan = await _load_plan(session, plan_id)
    await require_patient_access(session, reviewer, plan.user_id)

    if not payload.reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="طلب التعديل يحتاج سببًا يوضّح المطلوب",
        )

    plan.review_notes = payload.reason
    return await _transition(
        session,
        plan,
        to_status=PlanStatus.CHANGES_REQUESTED,
        actor=reviewer,
        action=AuditAction.PLAN_CHANGES_REQUESTED,
        request=request,
        reason=payload.reason,
    )


@router.post("/{plan_id}/activate", response_model=PlanSummary)
async def activate_plan(
    plan_id: uuid.UUID,
    request: Request,
    reviewer: Reviewer,
    session: Session,
) -> Plan:
    """التفعيل — الخطوة الوحيدة التي تجعل الخطة مرئية للمريض."""
    plan = await _load_plan(session, plan_id)
    await require_patient_access(session, reviewer, plan.user_id)

    # الخطة المفعّلة القائمة من نفس النوع تُؤرشف أولًا: الفهرس الفريد
    # الجزئي يسمح بواحدة فقط، والأرشفة هنا تجعل السلوك مقصودًا لا خطأ.
    current = await session.scalar(
        select(Plan).where(
            Plan.user_id == plan.user_id,
            Plan.plan_type == plan.plan_type,
            Plan.status == PlanStatus.ACTIVE,
            Plan.id != plan.id,
        )
    )
    if current is not None:
        await record_transition(
            session,
            current,
            to_status=PlanStatus.ARCHIVED,
            actor_id=reviewer.id,
            reason="حلّت محلها خطة أحدث",
        )
        await session.flush()

    return await _transition(
        session,
        plan,
        to_status=PlanStatus.ACTIVE,
        actor=reviewer,
        action=AuditAction.PLAN_ACTIVATED,
        request=request,
    )
