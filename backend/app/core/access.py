"""فرض العزل بين المرضى.

أخطر ثغرة في نظام صحي ليست كسر كلمة سر، بل **تسريب أفقي**: مستخدم مصادَق
عليه يقرأ سجل مريض آخر بتغيير معرّف في الرابط (IDOR). كل مسار يقرأ بيانات
مريض يمر من هنا.

القاعدة:

- المريض: بياناته فقط
- الأخصائي: مرضاه المسنَدون فقط — لا كل المرضى
- المدير: الجميع (وكل وصول يُسجَّل في سجل التدقيق)
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.care_team import SpecialistPatient
from app.models.user import User, UserRole

# 404 لا 403 عند غياب الصلاحية على سجل مريض بعينه: الرد بـ 403 يؤكد أن
# المعرّف موجود، فيتحول المسار إلى أداة لاستكشاف من هو مسجَّل في المنصة.
_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="المورد غير موجود",
)


async def is_assigned_specialist(
    session: AsyncSession,
    specialist_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> bool:
    assignment = await session.scalar(
        select(SpecialistPatient.patient_id).where(
            SpecialistPatient.specialist_id == specialist_id,
            SpecialistPatient.patient_id == patient_id,
            SpecialistPatient.is_active.is_(True),
        )
    )
    return assignment is not None


async def can_access_patient(
    session: AsyncSession,
    actor: User,
    patient_id: uuid.UUID,
) -> bool:
    if actor.id == patient_id:
        return True
    if actor.role is UserRole.ADMIN:
        return True
    if actor.role is UserRole.SPECIALIST:
        return await is_assigned_specialist(session, actor.id, patient_id)
    return False


async def require_patient_access(
    session: AsyncSession,
    actor: User,
    patient_id: uuid.UUID,
) -> None:
    """يرفع 404 إذا لم يكن للمستخدم حق الوصول لبيانات هذا المريض."""
    if not await can_access_patient(session, actor, patient_id):
        raise _NOT_FOUND


__all__ = [
    "can_access_patient",
    "is_assigned_specialist",
    "require_patient_access",
]
