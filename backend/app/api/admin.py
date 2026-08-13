"""مسارات المدير (المرحلة 10).

كل مسار هنا محمي بـ ``require_roles(UserRole.ADMIN)``. الشيء الوحيد الذي
كان يُفعل بـ SQL يدوي حتى الآن — إسناد المريض إلى أخصائي — صار مسارًا
مدقَّقًا هنا.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.db import get_session
from app.core.deps import require_roles
from app.core.security import hash_password
from app.models.audit import AuditAction
from app.models.care_team import SpecialistPatient
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminUserRow,
    AssignmentRequest,
    PlatformStats,
    UserUpdateRequest,
)
from app.schemas.auth import CreateStaffRequest, UserPublic
from app.services.admin import (
    build_platform_stats,
    build_user_rows,
    has_active_patients,
    users_query,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)

Session = Annotated[AsyncSession, Depends(get_session)]
Admin = Annotated[User, Depends(require_roles(UserRole.ADMIN))]


async def _load_user(session: AsyncSession, user_id: uuid.UUID) -> User:
    user = await session.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المستخدم غير موجود")
    return user


# ------------------------------------------------------------- المستخدمون
@router.get("/users", response_model=list[AdminUserRow])
async def list_users(
    session: Session,
    role: Annotated[UserRole | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
    is_active: Annotated[bool | None, Query()] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[AdminUserRow]:
    limit = min(max(limit, 1), 200)
    result = await session.scalars(
        users_query(role=role, search=search, is_active=is_active).limit(limit).offset(offset)
    )
    return await build_user_rows(session, list(result))


@router.post("/users", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_staff_user(
    payload: CreateStaffRequest,
    request: Request,
    session: Session,
    admin: Admin,
) -> User:
    existing = await session.scalar(select(User.id).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="هذا البريد الإلكتروني مسجّل بالفعل",
        )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=payload.role,
    )
    session.add(user)
    await session.flush()

    await record_audit(
        session,
        action=AuditAction.USER_CREATED_BY_ADMIN,
        entity_type="user",
        entity_id=user.id,
        actor_user_id=admin.id,
        after={"email": user.email, "role": user.role.value},
        request=request,
    )
    await session.commit()
    await session.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=AdminUserRow)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdateRequest,
    request: Request,
    session: Session,
    admin: Admin,
) -> AdminUserRow:
    """تعديل اسم مستخدم أو دوره أو حالته.

    حارسان لا يمكن تجاوزهما:

    1. **المدير لا يعطّل نفسه ولا يخفّض دوره.** آخر مدير يفعل ذلك يُغلق
       اللوحة على الجميع، ولا يوجد مسار عام لاستعادتها.
    2. **الأخصائي ذو المرضى لا يُخفَّض دوره.** قاعدة البيانات ترفضه أصلًا
       (مفتاح أجنبي مركّب على ``users(id, role)``)، لكنها ترفضه بخطأ سلامة
       غامض؛ هنا يتحول إلى رسالة تقول ما يجب فعله: انقل مرضاه أولًا.

    التعطيل ليس ضمن الحارس الثاني عمدًا: تعطيل حساب مخترَق فعل عاجل، وعدد
    مرضاه ظاهر في نفس الشاشة فالقرار مبنيّ على معلومة لا على مفاجأة.
    """
    user = await _load_user(session, user_id)

    if user.id == admin.id and (
        payload.is_active is False or payload.role not in (None, user.role)
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="لا يمكنك تعطيل حسابك أو تغيير دورك بنفسك",
        )

    demoting = (
        payload.role is not None
        and payload.role is not UserRole.SPECIALIST
        and user.role is UserRole.SPECIALIST
    )
    if demoting and await has_active_patients(session, user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="لهذا الأخصائي مرضى مسنَدون — انقلهم إلى أخصائي آخر قبل تغيير دوره",
        )

    before = {"full_name": user.full_name, "role": user.role.value, "is_active": user.is_active}

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    after = {"full_name": user.full_name, "role": user.role.value, "is_active": user.is_active}
    if after == before:
        # لا تغيير فعلي: لا سطر في سجل التدقيق. سجلّ مليء بتعديلات فارغة
        # يخفي التعديلات الحقيقية.
        rows = await build_user_rows(session, [user])
        return rows[0]

    await record_audit(
        session,
        action=AuditAction.USER_UPDATED_BY_ADMIN,
        entity_type="user",
        entity_id=user.id,
        actor_user_id=admin.id,
        before=before,
        after=after,
        request=request,
    )
    await session.commit()
    await session.refresh(user)

    rows = await build_user_rows(session, [user])
    return rows[0]


# --------------------------------------------------------------- الإسناد
@router.post("/assignments", status_code=status.HTTP_204_NO_CONTENT)
async def assign_patient(
    payload: AssignmentRequest,
    request: Request,
    session: Session,
    admin: Admin,
) -> None:
    """إسناد مريض إلى أخصائي.

    الإسناد المنتهي يُعاد تفعيله بدل إنشاء صف ثانٍ: المفتاح الأساسي مركّب
    من الطرفين، وصفّ ثانٍ مستحيل أصلًا — لكن الأهم أن عودة مريض إلى
    أخصائيه السابق حدث شائع، ومعالجتها كخطأ تجعل الشاشة تكذب.
    """
    specialist = await _load_user(session, payload.specialist_id)
    patient = await _load_user(session, payload.patient_id)

    if specialist.role is not UserRole.SPECIALIST or not specialist.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="الإسناد يكون إلى أخصائي مفعَّل فقط",
        )
    if patient.role is not UserRole.PATIENT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="الطرف الثاني ليس مريضًا")

    link = await session.scalar(
        select(SpecialistPatient).where(
            SpecialistPatient.specialist_id == specialist.id,
            SpecialistPatient.patient_id == patient.id,
        )
    )

    if link is not None and link.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="المريض مسنَد إلى هذا الأخصائي بالفعل",
        )

    if link is None:
        session.add(
            SpecialistPatient(
                specialist_id=specialist.id,
                patient_id=patient.id,
                assigned_by=admin.id,
                is_active=True,
            )
        )
    else:
        link.is_active = True
        link.ended_at = None
        link.assigned_by = admin.id

    await record_audit(
        session,
        action=AuditAction.PATIENT_ASSIGNED,
        entity_type="specialist_patient",
        entity_id=patient.id,
        actor_user_id=admin.id,
        after={"specialist_id": str(specialist.id), "patient_id": str(patient.id)},
        request=request,
    )
    await session.commit()


@router.delete(
    "/assignments/{specialist_id}/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unassign_patient(
    specialist_id: uuid.UUID,
    patient_id: uuid.UUID,
    request: Request,
    session: Session,
    admin: Admin,
) -> None:
    """إنهاء الإسناد.

    الصف يبقى بـ ``is_active=false`` وتاريخ انتهاء: من كان يتابع هذا
    المريض ومتى سؤال سريري يُسأل لاحقًا، وحذف الصف يمحو إجابته.
    """
    link = await session.scalar(
        select(SpecialistPatient).where(
            SpecialistPatient.specialist_id == specialist_id,
            SpecialistPatient.patient_id == patient_id,
            SpecialistPatient.is_active.is_(True),
        )
    )
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="لا يوجد إسناد نشط")

    link.is_active = False
    link.ended_at = datetime.now(UTC)

    await record_audit(
        session,
        action=AuditAction.PATIENT_UNASSIGNED,
        entity_type="specialist_patient",
        entity_id=patient_id,
        actor_user_id=admin.id,
        before={"specialist_id": str(specialist_id), "patient_id": str(patient_id)},
        request=request,
    )
    await session.commit()


# -------------------------------------------------------------- الإحصاءات
@router.get("/stats", response_model=PlatformStats)
async def platform_stats(session: Session) -> PlatformStats:
    return await build_platform_stats(session)
