"""مسارات الأخصائي — مرضاه المسنَدون فقط.

الأخصائي **لا يرى كل المرضى**. الإسناد علاقة صريحة في ``specialist_patients``
يديرها المدير، وكل استعلام هنا يمر بها. أخصائي يرى قائمة المنصة كاملة
تسريب لا يقل عن تسريب سجل بعينه.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.access import require_patient_access
from app.core.audit import record_audit
from app.core.db import get_session
from app.core.deps import require_roles
from app.core.enums import Allergen, PlanStatus
from app.models.audit import AuditAction, AuditLog
from app.models.care_team import SpecialistNote, SpecialistPatient
from app.models.clinical import DailyLog, Injury, PhysiologicalReading
from app.models.plan import Plan
from app.models.profile import FoodAllergy, UserProfile
from app.models.user import User, UserRole
from app.schemas.clinical import DailyLogRead, InjuryRead, ProfileRead, ReadingRead
from app.schemas.plan import PlanSummary
from app.schemas.specialist import (
    AuditEntryRead,
    PatientSummary,
    SpecialistNoteCreate,
    SpecialistNoteRead,
)
from app.services.care_team import build_patient_summaries

router = APIRouter(prefix="/specialist", tags=["specialist"])

Session = Annotated[AsyncSession, Depends(get_session)]
Specialist = Annotated[User, Depends(require_roles(UserRole.SPECIALIST, UserRole.ADMIN))]


async def _assigned_patient_ids(
    session: AsyncSession,
    specialist: User,
) -> list[uuid.UUID] | None:
    """معرّفات المرضى المسنَدين — أو ``None`` للمدير الذي يرى الجميع."""
    if specialist.role is UserRole.ADMIN:
        return None
    result = await session.scalars(
        select(SpecialistPatient.patient_id).where(
            SpecialistPatient.specialist_id == specialist.id,
            SpecialistPatient.is_active.is_(True),
        )
    )
    return list(result)


async def _load_patients(session: AsyncSession, specialist: User) -> list[User]:
    patient_ids = await _assigned_patient_ids(session, specialist)

    query = select(User).where(User.role == UserRole.PATIENT, User.deleted_at.is_(None))
    if patient_ids is not None:
        if not patient_ids:
            return []
        query = query.where(User.id.in_(patient_ids))

    return list(await session.scalars(query.order_by(User.created_at.desc())))


@router.get("/patients", response_model=list[PatientSummary])
async def list_my_patients(specialist: Specialist, session: Session) -> list[PatientSummary]:
    """قائمة المرضى مع مؤشرات الحالة (الخطوة 8.1)."""
    return await build_patient_summaries(session, await _load_patients(session, specialist))


@router.get("/patients/{patient_id}/profile", response_model=ProfileRead)
async def read_patient_profile(
    patient_id: uuid.UUID,
    request: Request,
    specialist: Specialist,
    session: Session,
) -> ProfileRead:
    await require_patient_access(session, specialist, patient_id)

    profile = await session.get(UserProfile, patient_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لم يُستكمل الملف الشخصي بعد",
        )

    # الاطلاع على سجل مريض حدث يُسجَّل — المساءلة تشمل القراءة لا التعديل فقط.
    await record_audit(
        session,
        action=AuditAction.PATIENT_RECORD_VIEWED,
        entity_type="user",
        entity_id=patient_id,
        actor_user_id=specialist.id,
        request=request,
    )
    allergens = sorted(
        await session.scalars(select(FoodAllergy.allergen).where(FoodAllergy.user_id == patient_id))
    )
    await session.commit()

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
        allergens=list[Allergen](allergens),
    )


@router.get("/patients/{patient_id}/injuries", response_model=list[InjuryRead])
async def read_patient_injuries(
    patient_id: uuid.UUID,
    specialist: Specialist,
    session: Session,
) -> list[Injury]:
    await require_patient_access(session, specialist, patient_id)

    result = await session.scalars(
        select(Injury).where(Injury.user_id == patient_id).order_by(Injury.injury_date.desc())
    )
    return list(result)


@router.get("/patients/{patient_id}/readings", response_model=list[ReadingRead])
async def read_patient_readings(
    patient_id: uuid.UUID,
    specialist: Specialist,
    session: Session,
    limit: int = 90,
) -> list[PhysiologicalReading]:
    await require_patient_access(session, specialist, patient_id)

    result = await session.scalars(
        select(PhysiologicalReading)
        .where(PhysiologicalReading.user_id == patient_id)
        .order_by(PhysiologicalReading.reading_date.desc())
        .limit(min(max(limit, 1), 365))
    )
    return list(result)


@router.get("/patients/{patient_id}/logs", response_model=list[DailyLogRead])
async def read_patient_logs(
    patient_id: uuid.UUID,
    specialist: Specialist,
    session: Session,
    limit: int = 90,
) -> list[DailyLog]:
    """التسجيل اليومي — مصدر قراءة الالتزام والألم على المدى."""
    await require_patient_access(session, specialist, patient_id)

    result = await session.scalars(
        select(DailyLog)
        .where(DailyLog.user_id == patient_id)
        .order_by(DailyLog.log_date.desc())
        .limit(min(max(limit, 1), 365))
    )
    return list(result)


@router.get("/patients/{patient_id}/plans", response_model=list[PlanSummary])
async def read_patient_plans(
    patient_id: uuid.UUID,
    specialist: Specialist,
    session: Session,
) -> list[Plan]:
    """كل خطط المريض — بما فيها المسودات، فهي مادة المراجعة."""
    await require_patient_access(session, specialist, patient_id)

    result = await session.scalars(
        select(Plan).where(Plan.user_id == patient_id).order_by(Plan.created_at.desc())
    )
    return list(result)


@router.get("/review-queue", response_model=list[PlanSummary])
async def read_review_queue(specialist: Specialist, session: Session) -> list[Plan]:
    """الخطط المنتظرة مراجعة هذا الأخصائي — شاشة عمله اليومية."""
    patient_ids = await _assigned_patient_ids(session, specialist)

    query = select(Plan).where(Plan.status == PlanStatus.PENDING_REVIEW)
    if patient_ids is not None:
        if not patient_ids:
            return []
        query = query.where(Plan.user_id.in_(patient_ids))

    return list(await session.scalars(query.order_by(Plan.created_at)))


# ------------------------------------------------------------------ الملاحظات
@router.get("/patients/{patient_id}/notes", response_model=list[SpecialistNoteRead])
async def read_patient_notes(
    patient_id: uuid.UUID,
    specialist: Specialist,
    session: Session,
) -> list[SpecialistNote]:
    await require_patient_access(session, specialist, patient_id)

    result = await session.scalars(
        select(SpecialistNote)
        .where(SpecialistNote.patient_id == patient_id)
        .order_by(SpecialistNote.created_at.desc())
    )
    return list(result)


@router.post(
    "/patients/{patient_id}/notes",
    response_model=SpecialistNoteRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_patient_note(
    patient_id: uuid.UUID,
    payload: SpecialistNoteCreate,
    specialist: Specialist,
    session: Session,
) -> SpecialistNote:
    await require_patient_access(session, specialist, patient_id)

    if payload.plan_id is not None:
        # الملاحظة المرتبطة بخطة يجب أن تكون خطة هذا المريض، وإلا صارت
        # الملاحظات طريقًا جانبيًا للربط بسجلات مرضى آخرين.
        owner = await session.scalar(select(Plan.user_id).where(Plan.id == payload.plan_id))
        if owner != patient_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="الخطة غير موجودة لهذا المريض",
            )

    note = SpecialistNote(
        specialist_id=specialist.id,
        patient_id=patient_id,
        plan_id=payload.plan_id,
        note=payload.note.strip(),
        is_internal=payload.is_internal,
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return note


# ------------------------------------------------------------- سجل التدقيق
@router.get("/patients/{patient_id}/audit", response_model=list[AuditEntryRead])
async def read_patient_audit(
    patient_id: uuid.UUID,
    specialist: Specialist,
    session: Session,
    limit: int = 100,
) -> list[AuditEntryRead]:
    """سجل التدقيق الخاص بمريض (الخطوة 8.5).

    القيد يخص المريض إن كان **فاعله** (سجّل إصابة، وافق على التنبيه)، أو
    **هدفه** (اطّلع أخصائي على سجله)، أو كان على **خطة من خططه** (اعتماد،
    طلب تعديل، تفعيل). الحالة الثالثة هي أهمّ ما يريده الأخصائي وأكثر ما
    يسهل نسيانه: فاعلها أخصائي وهدفها خطة، فلا يظهر فيها معرّف المريض
    إطلاقًا.
    """
    await require_patient_access(session, specialist, patient_id)

    plan_ids = select(func.cast(Plan.id, Text)).where(Plan.user_id == patient_id)

    actor = aliased(User)
    rows = await session.execute(
        select(AuditLog, actor.full_name)
        .outerjoin(actor, AuditLog.actor_user_id == actor.id)
        .where(
            (AuditLog.actor_user_id == patient_id)
            | (AuditLog.entity_id == str(patient_id))
            | (AuditLog.entity_id.in_(plan_ids)),
        )
        .order_by(AuditLog.created_at.desc())
        .limit(min(max(limit, 1), 500))
    )

    return [
        AuditEntryRead(
            id=entry.id,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            actor_user_id=entry.actor_user_id,
            actor_name=actor_name,
            created_at=entry.created_at,
        )
        for entry, actor_name in rows
    ]
