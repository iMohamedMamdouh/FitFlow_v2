"""مسارات الأخصائي — مرضاه المسنَدون فقط.

الأخصائي **لا يرى كل المرضى**. الإسناد علاقة صريحة في ``specialist_patients``
يديرها المدير، وكل استعلام هنا يمر بها. أخصائي يرى قائمة المنصة كاملة
تسريب لا يقل عن تسريب سجل بعينه.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access import require_patient_access
from app.core.audit import record_audit
from app.core.db import get_session
from app.core.deps import require_roles
from app.core.enums import PlanStatus
from app.models.audit import AuditAction
from app.models.care_team import SpecialistNote, SpecialistPatient
from app.models.clinical import Injury, PhysiologicalReading
from app.models.plan import Plan
from app.models.user import User, UserRole
from app.schemas.auth import UserPublic
from app.schemas.clinical import InjuryRead, ReadingRead
from app.schemas.plan import PlanSummary

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


@router.get("/patients", response_model=list[UserPublic])
async def list_my_patients(specialist: Specialist, session: Session) -> list[User]:
    patient_ids = await _assigned_patient_ids(session, specialist)

    query = select(User).where(User.role == UserRole.PATIENT, User.deleted_at.is_(None))
    if patient_ids is not None:
        if not patient_ids:
            return []
        query = query.where(User.id.in_(patient_ids))

    return list(await session.scalars(query.order_by(User.created_at.desc())))


@router.get("/patients/{patient_id}/injuries", response_model=list[InjuryRead])
async def read_patient_injuries(
    patient_id: uuid.UUID,
    request: Request,
    specialist: Specialist,
    session: Session,
) -> list[Injury]:
    await require_patient_access(session, specialist, patient_id)

    # الاطلاع على سجل مريض حدث يُسجَّل — المساءلة تشمل القراءة لا التعديل فقط.
    await record_audit(
        session,
        action=AuditAction.PATIENT_RECORD_VIEWED,
        entity_type="user",
        entity_id=patient_id,
        actor_user_id=specialist.id,
        request=request,
    )
    result = await session.scalars(
        select(Injury).where(Injury.user_id == patient_id).order_by(Injury.injury_date.desc())
    )
    await session.commit()
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


@router.post(
    "/patients/{patient_id}/notes",
    status_code=status.HTTP_201_CREATED,
    response_model=None,
)
async def add_patient_note(
    patient_id: uuid.UUID,
    note: str,
    specialist: Specialist,
    session: Session,
    is_internal: bool = False,
) -> dict[str, str]:
    await require_patient_access(session, specialist, patient_id)

    if not note.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="الملاحظة لا يمكن أن تكون فارغة",
        )

    session.add(
        SpecialistNote(
            specialist_id=specialist.id,
            patient_id=patient_id,
            note=note.strip(),
            is_internal=is_internal,
        )
    )
    await session.commit()
    return {"status": "created"}
