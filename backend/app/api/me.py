"""مسارات المستخدم الحالي — بياناته هو فقط.

كل مسار هنا يعمل على ``current_user.id`` ولا يقبل معرّف مستخدم من الطلب.
غياب المعرّف من الواجهة يجعل تسريب البيانات الأفقي (IDOR) غير ممكن هنا
بحكم التصميم، لا بحكم فحص يمكن نسيانه.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.db import get_session
from app.core.deps import CurrentUser
from app.core.enums import Allergen, PlanStatus
from app.models.audit import AuditAction
from app.models.catalog import InjuryType
from app.models.clinical import DailyLog, Injury, PhysiologicalReading
from app.models.plan import Plan
from app.models.profile import FoodAllergy, UserProfile
from app.schemas.clinical import (
    DailyLogCreate,
    DailyLogRead,
    InjuryCreate,
    InjuryRead,
    ProfileRead,
    ProfileUpsert,
    ReadingCreate,
    ReadingRead,
)
from app.schemas.plan import PlanSummary

router = APIRouter(prefix="/me", tags=["me"])

Session = Annotated[AsyncSession, Depends(get_session)]


async def _load_allergens(session: AsyncSession, user_id: uuid.UUID) -> list[Allergen]:
    result = await session.scalars(
        select(FoodAllergy.allergen).where(FoodAllergy.user_id == user_id)
    )
    return sorted(result)


def _to_profile_read(profile: UserProfile, allergens: list[Allergen]) -> ProfileRead:
    return ProfileRead(
        user_id=profile.user_id,
        birth_date=profile.birth_date,
        age_years=profile.age_years,
        gender=profile.gender,
        height_cm=profile.height_cm,
        activity_level=profile.activity_level,
        goal=profile.goal,
        medical_history=profile.medical_history,
        chronic_diseases=profile.chronic_diseases,
        medications=profile.medications,
        notes=profile.notes,
        consent_accepted_at=profile.consent_accepted_at,
        allergens=allergens,
    )


# ------------------------------------------------------------ الملف الشخصي
@router.get("/profile", response_model=ProfileRead)
async def read_my_profile(user: CurrentUser, session: Session) -> ProfileRead:
    profile = await session.get(UserProfile, user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لم يُستكمل الملف الشخصي بعد",
        )
    return _to_profile_read(profile, await _load_allergens(session, user.id))


@router.put("/profile", response_model=ProfileRead)
async def upsert_my_profile(
    payload: ProfileUpsert,
    request: Request,
    user: CurrentUser,
    session: Session,
) -> ProfileRead:
    profile = await session.get(UserProfile, user.id)
    before = (
        {"goal": profile.goal.value, "activity_level": profile.activity_level.value}
        if profile
        else None
    )

    if profile is None:
        profile = UserProfile(user_id=user.id, birth_date=payload.birth_date, gender=payload.gender)
        session.add(profile)

    profile.birth_date = payload.birth_date
    profile.gender = payload.gender
    profile.height_cm = payload.height_cm
    profile.activity_level = payload.activity_level
    profile.goal = payload.goal
    profile.medical_history = payload.medical_history
    profile.chronic_diseases = payload.chronic_diseases
    profile.medications = payload.medications
    profile.notes = payload.notes

    # الحساسية تُستبدل بالكامل: الدمج التراكمي يُبقي حساسية أزالها المستخدم،
    # وهو خطأ في الاتجاه الخطر — يستبعد طعامًا آمنًا بدل أن يسمح بضار.
    await session.execute(delete(FoodAllergy).where(FoodAllergy.user_id == user.id))
    for allergen in payload.allergens:
        session.add(FoodAllergy(user_id=user.id, allergen=allergen))

    await record_audit(
        session,
        action=AuditAction.PROFILE_UPDATED,
        entity_type="user_profile",
        entity_id=user.id,
        actor_user_id=user.id,
        before=before,
        after={"goal": profile.goal.value, "activity_level": profile.activity_level.value},
        request=request,
    )
    await session.commit()
    await session.refresh(profile)
    return _to_profile_read(profile, await _load_allergens(session, user.id))


@router.post("/profile/consent", response_model=ProfileRead)
async def accept_medical_disclaimer(
    request: Request,
    user: CurrentUser,
    session: Session,
) -> ProfileRead:
    """الموافقة على التنبيه الطبي — شرط قانوني قبل توليد أي خطة."""
    from datetime import UTC, datetime

    profile = await session.get(UserProfile, user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لم يُستكمل الملف الشخصي بعد",
        )

    profile.consent_accepted_at = datetime.now(UTC)
    await record_audit(
        session,
        action=AuditAction.CONSENT_ACCEPTED,
        entity_type="user_profile",
        entity_id=user.id,
        actor_user_id=user.id,
        request=request,
    )
    await session.commit()
    await session.refresh(profile)
    return _to_profile_read(profile, await _load_allergens(session, user.id))


# ----------------------------------------------------------------- الإصابات
@router.get("/injuries", response_model=list[InjuryRead])
async def list_my_injuries(user: CurrentUser, session: Session) -> list[Injury]:
    result = await session.scalars(
        select(Injury).where(Injury.user_id == user.id).order_by(Injury.injury_date.desc())
    )
    return list(result)


@router.post("/injuries", response_model=InjuryRead, status_code=status.HTTP_201_CREATED)
async def record_my_injury(
    payload: InjuryCreate,
    request: Request,
    user: CurrentUser,
    session: Session,
) -> Injury:
    injury_type = await session.get(InjuryType, payload.injury_type_id)
    if injury_type is None or not injury_type.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="نوع الإصابة غير معروف",
        )

    injury = Injury(user_id=user.id, **payload.model_dump())
    session.add(injury)
    await session.flush()

    await record_audit(
        session,
        action=AuditAction.INJURY_RECORDED,
        entity_type="injury",
        entity_id=injury.id,
        actor_user_id=user.id,
        after={"status": injury.status.value, "pain_level": injury.pain_level},
        request=request,
    )
    await session.commit()
    await session.refresh(injury)
    return injury


# ---------------------------------------------------------------- القياسات
@router.get("/readings", response_model=list[ReadingRead])
async def list_my_readings(
    user: CurrentUser,
    session: Session,
    limit: int = 90,
) -> list[PhysiologicalReading]:
    result = await session.scalars(
        select(PhysiologicalReading)
        .where(PhysiologicalReading.user_id == user.id)
        .order_by(PhysiologicalReading.reading_date.desc())
        .limit(min(max(limit, 1), 365))
    )
    return list(result)


@router.post("/readings", response_model=ReadingRead, status_code=status.HTTP_201_CREATED)
async def record_my_reading(
    payload: ReadingCreate,
    user: CurrentUser,
    session: Session,
) -> PhysiologicalReading:
    existing = await session.scalar(
        select(PhysiologicalReading).where(
            PhysiologicalReading.user_id == user.id,
            PhysiologicalReading.reading_date == payload.reading_date,
            PhysiologicalReading.source == payload.source,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="يوجد قياس مسجَّل بالفعل في هذا اليوم من نفس المصدر",
        )

    reading = PhysiologicalReading(user_id=user.id, **payload.model_dump())
    session.add(reading)
    await session.commit()
    await session.refresh(reading)
    return reading


# ------------------------------------------------------------ التسجيل اليومي
@router.post("/logs", response_model=DailyLogRead, status_code=status.HTTP_201_CREATED)
async def record_my_daily_log(
    payload: DailyLogCreate,
    user: CurrentUser,
    session: Session,
) -> DailyLog:
    existing = await session.scalar(
        select(DailyLog).where(DailyLog.user_id == user.id, DailyLog.log_date == payload.log_date)
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="يوجد تسجيل لهذا اليوم بالفعل",
        )

    log = DailyLog(user_id=user.id, **payload.model_dump())
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


# -------------------------------------------------------------------- الخطط
@router.get("/plans", response_model=list[PlanSummary])
async def list_my_plans(user: CurrentUser, session: Session) -> list[Plan]:
    """الخطط المرئية للمريض فقط.

    الفلترة على مستوى الاستعلام لا بعد جلب الصفوف: خطة غير معتمدة لا
    تُحمَّل أصلًا، فلا يمكن لخطأ في التسلسل أن يسرّبها.
    """
    visible = [status_ for status_ in PlanStatus if status_.is_visible_to_patient]
    result = await session.scalars(
        select(Plan)
        .where(Plan.user_id == user.id, Plan.status.in_(visible))
        .order_by(Plan.created_at.desc())
    )
    return list(result)
