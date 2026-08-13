"""إدارة القاعدة العلمية من لوحة المدير (الخطوة 10.2).

ثلاث قواعد تحكم كل المسارات هنا:

1. **لا حذف.** التعطيل (`is_active=false`) فقط. الخطط المولَّدة تشير إلى
   هذا المحتوى، وحذف صنف غذائي يترك خطة مريض تشير إلى لا شيء.
2. **إصدار المحتوى يزيد مع المضمون لا مع العرض.** تصحيح اسم لا يرفع
   الإصدار، وتغيير بروتوكول مراحل يرفعه — لأن الخطة تُختم بالإصدار،
   والختم الذي يتغيّر مع كل تعديل إملائي لا يدل على شيء.
3. **المراجعة توثيق لا مربّع اختيار.** تسجيلها يشترط اسم المراجِع ومرجعه
   (ADR-003)، ولا يوجد مسار يجعل المحتوى "مراجَعًا" بلا الاثنين.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.audit import record_audit
from app.core.db import get_session
from app.core.deps import require_roles
from app.core.enums import BodyRegion, ExerciseCategory, FoodCategory
from app.models.audit import AuditAction
from app.models.catalog import Exercise, Food, FoodAllergenLink, InjuryType
from app.models.user import User, UserRole
from app.schemas.admin_catalog import (
    ExerciseRow,
    ExerciseUpsert,
    FoodRow,
    FoodUpsert,
    InjuryTypeRow,
    InjuryTypeUpsert,
    ReviewRequest,
)
from app.services.admin_catalog import (
    apply_exercise,
    apply_injury_type,
    exercise_row,
    food_row,
    injury_type_row,
)

router = APIRouter(
    prefix="/admin/catalog",
    tags=["admin-catalog"],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)

Session = Annotated[AsyncSession, Depends(get_session)]
Admin = Annotated[User, Depends(require_roles(UserRole.ADMIN))]

_DUPLICATE_SLUG = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="المعرّف النصي (slug) مستخدَم بالفعل",
)


_Entity = TypeVar("_Entity", Food, Exercise, InjuryType)


def _search_filter(
    model: type[Food] | type[Exercise] | type[InjuryType], search: str | None
) -> ColumnElement[bool] | None:
    if not search:
        return None
    pattern = f"%{search.strip().lower()}%"
    return or_(func.lower(model.name_ar).like(pattern), func.lower(model.name_en).like(pattern))


async def _load(session: AsyncSession, model: type[_Entity], entity_id: uuid.UUID) -> _Entity:
    entity = await session.get(model, entity_id)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="العنصر غير موجود")
    return entity


# ----------------------------------------------------------------- الأغذية
async def _allergens_of(
    session: AsyncSession, food_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[FoodAllergenLink]]:
    if not food_ids:
        return {}
    rows = await session.scalars(
        select(FoodAllergenLink).where(FoodAllergenLink.food_id.in_(food_ids))
    )
    grouped: dict[uuid.UUID, list[FoodAllergenLink]] = {}
    for link in rows:
        grouped.setdefault(link.food_id, []).append(link)
    return grouped


@router.get("/foods", response_model=list[FoodRow])
async def list_foods(
    session: Session,
    search: Annotated[str | None, Query(max_length=200)] = None,
    category: Annotated[FoodCategory | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[FoodRow]:
    statement = select(Food)
    condition = _search_filter(Food, search)
    if condition is not None:
        statement = statement.where(condition)
    if category is not None:
        statement = statement.where(Food.category == category)
    if is_active is not None:
        statement = statement.where(Food.is_active.is_(is_active))

    foods = list(
        await session.scalars(
            statement.order_by(Food.name_ar).limit(min(max(limit, 1), 300)).offset(offset)
        )
    )
    allergens = await _allergens_of(session, [food.id for food in foods])
    return [food_row(food, allergens.get(food.id, [])) for food in foods]


async def _write_allergens(session: AsyncSession, food: Food, payload: FoodUpsert) -> None:
    await session.execute(delete(FoodAllergenLink).where(FoodAllergenLink.food_id == food.id))
    for allergen in dict.fromkeys(payload.allergens):
        session.add(FoodAllergenLink(food_id=food.id, allergen=allergen))


@router.post("/foods", response_model=FoodRow, status_code=status.HTTP_201_CREATED)
async def create_food(
    payload: FoodUpsert, request: Request, session: Session, admin: Admin
) -> FoodRow:
    food = Food(**payload.model_dump(exclude={"allergens"}), source="admin")
    session.add(food)
    await session.flush()
    await _write_allergens(session, food, payload)

    await record_audit(
        session,
        action=AuditAction.CATALOG_CREATED,
        entity_type="food",
        entity_id=food.id,
        actor_user_id=admin.id,
        after={"name_ar": food.name_ar, "category": food.category.value},
        request=request,
    )
    await session.commit()
    await session.refresh(food)
    allergens = await _allergens_of(session, [food.id])
    return food_row(food, allergens.get(food.id, []))


@router.patch("/foods/{food_id}", response_model=FoodRow)
async def update_food(
    food_id: uuid.UUID,
    payload: FoodUpsert,
    request: Request,
    session: Session,
    admin: Admin,
) -> FoodRow:
    food: Food = await _load(session, Food, food_id)
    before = {"name_ar": food.name_ar, "is_active": food.is_active}

    for field, value in payload.model_dump(exclude={"allergens"}).items():
        setattr(food, field, value)
    await _write_allergens(session, food, payload)

    await record_audit(
        session,
        action=AuditAction.CATALOG_UPDATED,
        entity_type="food",
        entity_id=food.id,
        actor_user_id=admin.id,
        before=before,
        after={"name_ar": food.name_ar, "is_active": food.is_active},
        request=request,
    )
    await session.commit()
    await session.refresh(food)
    allergens = await _allergens_of(session, [food.id])
    return food_row(food, allergens.get(food.id, []))


# ---------------------------------------------------------------- التمارين
@router.get("/exercises", response_model=list[ExerciseRow])
async def list_exercises(
    session: Session,
    search: Annotated[str | None, Query(max_length=200)] = None,
    category: Annotated[ExerciseCategory | None, Query()] = None,
    region: Annotated[BodyRegion | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    unreviewed: Annotated[bool | None, Query()] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ExerciseRow]:
    statement = select(Exercise)
    condition = _search_filter(Exercise, search)
    if condition is not None:
        statement = statement.where(condition)
    if category is not None:
        statement = statement.where(Exercise.category == category)
    if region is not None:
        statement = statement.where(Exercise.primary_region == region)
    if is_active is not None:
        statement = statement.where(Exercise.is_active.is_(is_active))
    if unreviewed:
        statement = statement.where(Exercise.reviewed_at.is_(None))

    rows = await session.scalars(
        statement.order_by(Exercise.name_ar).limit(min(max(limit, 1), 300)).offset(offset)
    )
    return [exercise_row(exercise) for exercise in rows]


@router.post("/exercises", response_model=ExerciseRow, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    payload: ExerciseUpsert, request: Request, session: Session, admin: Admin
) -> ExerciseRow:
    exercise = Exercise(**payload.model_dump())
    session.add(exercise)
    try:
        await session.flush()
    except IntegrityError as error:
        await session.rollback()
        raise _DUPLICATE_SLUG from error

    await record_audit(
        session,
        action=AuditAction.CATALOG_CREATED,
        entity_type="exercise",
        entity_id=exercise.id,
        actor_user_id=admin.id,
        after={"slug": payload.slug, "name_ar": payload.name_ar},
        request=request,
    )
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise _DUPLICATE_SLUG from error

    await session.refresh(exercise)
    return exercise_row(exercise)


@router.patch("/exercises/{exercise_id}", response_model=ExerciseRow)
async def update_exercise(
    exercise_id: uuid.UUID,
    payload: ExerciseUpsert,
    request: Request,
    session: Session,
    admin: Admin,
) -> ExerciseRow:
    exercise: Exercise = await _load(session, Exercise, exercise_id)
    before = {"content_version": exercise.content_version, "is_active": exercise.is_active}

    bumped = apply_exercise(exercise, payload)

    await record_audit(
        session,
        action=AuditAction.CATALOG_UPDATED,
        entity_type="exercise",
        entity_id=exercise.id,
        actor_user_id=admin.id,
        before=before,
        after={
            "content_version": exercise.content_version,
            "is_active": exercise.is_active,
            "scientific_change": bumped,
        },
        request=request,
    )
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise _DUPLICATE_SLUG from error

    await session.refresh(exercise)
    return exercise_row(exercise)


# ----------------------------------------------------------- أنواع الإصابات
@router.get("/injury-types", response_model=list[InjuryTypeRow])
async def list_injury_types(
    session: Session,
    search: Annotated[str | None, Query(max_length=200)] = None,
    region: Annotated[BodyRegion | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    unreviewed: Annotated[bool | None, Query()] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[InjuryTypeRow]:
    statement = select(InjuryType)
    condition = _search_filter(InjuryType, search)
    if condition is not None:
        statement = statement.where(condition)
    if region is not None:
        statement = statement.where(InjuryType.body_region == region)
    if is_active is not None:
        statement = statement.where(InjuryType.is_active.is_(is_active))
    if unreviewed:
        statement = statement.where(InjuryType.reviewed_at.is_(None))

    rows = await session.scalars(
        statement.order_by(InjuryType.name_ar).limit(min(max(limit, 1), 300)).offset(offset)
    )
    return [injury_type_row(injury_type) for injury_type in rows]


@router.post("/injury-types", response_model=InjuryTypeRow, status_code=status.HTTP_201_CREATED)
async def create_injury_type(
    payload: InjuryTypeUpsert, request: Request, session: Session, admin: Admin
) -> InjuryTypeRow:
    injury_type = InjuryType(**payload.model_dump())
    session.add(injury_type)
    try:
        await session.flush()
    except IntegrityError as error:
        await session.rollback()
        raise _DUPLICATE_SLUG from error

    await record_audit(
        session,
        action=AuditAction.CATALOG_CREATED,
        entity_type="injury_type",
        entity_id=injury_type.id,
        actor_user_id=admin.id,
        after={"slug": payload.slug, "name_ar": payload.name_ar},
        request=request,
    )
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise _DUPLICATE_SLUG from error

    await session.refresh(injury_type)
    return injury_type_row(injury_type)


@router.patch("/injury-types/{injury_type_id}", response_model=InjuryTypeRow)
async def update_injury_type(
    injury_type_id: uuid.UUID,
    payload: InjuryTypeUpsert,
    request: Request,
    session: Session,
    admin: Admin,
) -> InjuryTypeRow:
    injury_type: InjuryType = await _load(session, InjuryType, injury_type_id)
    before = {"content_version": injury_type.content_version, "is_active": injury_type.is_active}

    bumped = apply_injury_type(injury_type, payload)

    await record_audit(
        session,
        action=AuditAction.CATALOG_UPDATED,
        entity_type="injury_type",
        entity_id=injury_type.id,
        actor_user_id=admin.id,
        before=before,
        after={
            "content_version": injury_type.content_version,
            "is_active": injury_type.is_active,
            "scientific_change": bumped,
        },
        request=request,
    )
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise _DUPLICATE_SLUG from error

    await session.refresh(injury_type)
    return injury_type_row(injury_type)


# ---------------------------------------------------------------- المراجعة
@router.post("/exercises/{exercise_id}/review", response_model=ExerciseRow)
async def review_exercise(
    exercise_id: uuid.UUID,
    payload: ReviewRequest,
    request: Request,
    session: Session,
    admin: Admin,
) -> ExerciseRow:
    exercise: Exercise = await _load(session, Exercise, exercise_id)
    exercise.reviewed_by = payload.reviewed_by
    exercise.source_reference = payload.source_reference
    exercise.reviewed_at = datetime.now(UTC)

    await record_audit(
        session,
        action=AuditAction.CATALOG_REVIEWED,
        entity_type="exercise",
        entity_id=exercise.id,
        actor_user_id=admin.id,
        after={"reviewed_by": payload.reviewed_by, "content_version": exercise.content_version},
        request=request,
    )
    await session.commit()
    await session.refresh(exercise)
    return exercise_row(exercise)


@router.post("/injury-types/{injury_type_id}/review", response_model=InjuryTypeRow)
async def review_injury_type(
    injury_type_id: uuid.UUID,
    payload: ReviewRequest,
    request: Request,
    session: Session,
    admin: Admin,
) -> InjuryTypeRow:
    injury_type: InjuryType = await _load(session, InjuryType, injury_type_id)
    injury_type.reviewed_by = payload.reviewed_by
    injury_type.source_reference = payload.source_reference
    injury_type.reviewed_at = datetime.now(UTC)

    await record_audit(
        session,
        action=AuditAction.CATALOG_REVIEWED,
        entity_type="injury_type",
        entity_id=injury_type.id,
        actor_user_id=admin.id,
        after={"reviewed_by": payload.reviewed_by, "content_version": injury_type.content_version},
        request=request,
    )
    await session.commit()
    await session.refresh(injury_type)
    return injury_type_row(injury_type)
