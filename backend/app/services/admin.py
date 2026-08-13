"""استعلامات لوحة المدير.

كل دالة هنا تعمل على **دفعة** لا على صفّ في كل نداء: قائمة المستخدمين
تحتاج عدد المرضى لكل أخصائي وأسماء الأخصائيين لكل مريض، وجلبها بنداء
لكل سطر يعني عشرات الاستعلامات لعرض صفحة واحدة.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.clock import today
from app.core.enums import InjuryStatus, PlanStatus
from app.models.care_team import SpecialistPatient
from app.models.catalog import Exercise, Food, InjuryType
from app.models.clinical import DailyLog, Injury
from app.models.plan import Plan
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminUserRow,
    AssignedSpecialist,
    PlanStatusCount,
    PlatformStats,
    RoleCount,
)

# نافذة نشاط التسجيل اليومي في لوحة المدير — أسبوع يكفي للحكم على
# "هل المنصة مستخدَمة الآن" دون أن يبتلعه تاريخ قديم.
ACTIVITY_WINDOW_DAYS = 7


def users_query(
    *,
    role: UserRole | None,
    search: str | None,
    is_active: bool | None,
) -> Select[tuple[User]]:
    """استعلام القائمة قبل الترقيم.

    المحذوفون مستبعدون دائمًا: الحذف هنا ناعم، وإظهار حساب محذوف في قائمة
    قابلة للتعديل يعني إعادة تفعيله بالخطأ.
    """
    statement = select(User).where(User.deleted_at.is_(None))

    if role is not None:
        statement = statement.where(User.role == role)
    if is_active is not None:
        statement = statement.where(User.is_active.is_(is_active))
    if search:
        pattern = f"%{search.strip().lower()}%"
        statement = statement.where(
            or_(func.lower(User.full_name).like(pattern), User.email.like(pattern))
        )

    return statement.order_by(User.created_at.desc())


async def _assignment_counts(
    session: AsyncSession, specialist_ids: list[uuid.UUID]
) -> dict[uuid.UUID, int]:
    if not specialist_ids:
        return {}
    rows = await session.execute(
        select(SpecialistPatient.specialist_id, func.count())
        .where(
            SpecialistPatient.specialist_id.in_(specialist_ids),
            SpecialistPatient.is_active.is_(True),
        )
        .group_by(SpecialistPatient.specialist_id)
    )
    return dict(rows.all())  # type: ignore[arg-type]


async def _assigned_specialists(
    session: AsyncSession, patient_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[AssignedSpecialist]]:
    if not patient_ids:
        return {}
    specialist = aliased(User)
    rows = await session.execute(
        select(SpecialistPatient.patient_id, specialist.id, specialist.full_name)
        .join(specialist, specialist.id == SpecialistPatient.specialist_id)
        .where(
            SpecialistPatient.patient_id.in_(patient_ids),
            SpecialistPatient.is_active.is_(True),
        )
        .order_by(specialist.full_name)
    )
    assigned: dict[uuid.UUID, list[AssignedSpecialist]] = {}
    for patient_id, specialist_id, full_name in rows:
        assigned.setdefault(patient_id, []).append(
            AssignedSpecialist(id=specialist_id, full_name=full_name)
        )
    return assigned


async def build_user_rows(session: AsyncSession, users: list[User]) -> list[AdminUserRow]:
    """يضيف أعداد الإسناد إلى صفحة واحدة من المستخدمين — باستعلامين لا بنداء لكل سطر."""
    specialist_ids = [user.id for user in users if user.role is UserRole.SPECIALIST]
    patient_ids = [user.id for user in users if user.role is UserRole.PATIENT]

    counts = await _assignment_counts(session, specialist_ids)
    assigned = await _assigned_specialists(session, patient_ids)

    return [
        AdminUserRow(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            assigned_patients=counts.get(user.id, 0),
            specialists=assigned.get(user.id, []),
        )
        for user in users
    ]


async def has_active_patients(session: AsyncSession, specialist_id: uuid.UUID) -> bool:
    """هل لهذا الأخصائي مرضى نشطون؟

    تُسأل قبل تخفيض الدور أو التعطيل: قاعدة البيانات نفسها ترفض تخفيض
    أخصائي له إسنادات (مفتاح أجنبي مركّب على ``users(id, role)``)، لكن
    الرفض يصل كخطأ سلامة غامض. السؤال هنا يحوّله إلى رسالة مفهومة.
    """
    found = await session.scalar(
        select(SpecialistPatient.patient_id)
        .where(
            SpecialistPatient.specialist_id == specialist_id,
            SpecialistPatient.is_active.is_(True),
        )
        .limit(1)
    )
    return found is not None


async def build_platform_stats(session: AsyncSession) -> PlatformStats:
    """أرقام المنصة في تسعة استعلامات مجمَّعة."""
    role_rows = await session.execute(
        select(User.role, func.count(), func.count().filter(User.is_active.is_(True)))
        .where(User.deleted_at.is_(None))
        .group_by(User.role)
    )
    counts = {role: (total, active) for role, total, active in role_rows}
    users = [
        RoleCount(role=role, total=counts.get(role, (0, 0))[0], active=counts.get(role, (0, 0))[1])
        for role in UserRole
    ]

    plan_rows = await session.execute(select(Plan.status, func.count()).group_by(Plan.status))
    plans = [PlanStatusCount(status=status, total=total) for status, total in plan_rows]
    awaiting = next((row.total for row in plans if row.status is PlanStatus.PENDING_REVIEW), 0)

    assigned = select(SpecialistPatient.patient_id).where(SpecialistPatient.is_active.is_(True))
    unassigned = await session.scalar(
        select(func.count())
        .select_from(User)
        .where(
            User.role == UserRole.PATIENT,
            User.deleted_at.is_(None),
            User.id.not_in(assigned),
        )
    )

    injury_rows = await session.execute(
        select(Injury.status, func.count())
        .where(Injury.status != InjuryStatus.RECOVERED)
        .group_by(Injury.status)
    )
    injury_counts: dict[InjuryStatus, int] = dict(injury_rows.all())  # type: ignore[arg-type]

    since = today() - timedelta(days=ACTIVITY_WINDOW_DAYS)
    logs = await session.scalar(
        select(func.count()).select_from(DailyLog).where(DailyLog.log_date >= since)
    )

    foods = await session.scalar(
        select(func.count()).select_from(Food).where(Food.is_active.is_(True))
    )
    exercises = await session.scalar(
        select(func.count()).select_from(Exercise).where(Exercise.is_active.is_(True))
    )
    injury_types = await session.scalar(
        select(func.count()).select_from(InjuryType).where(InjuryType.is_active.is_(True))
    )
    # المحتوى غير المراجَع (ADR-003) رقم إداري لا تفصيلة: كل تمرين أو
    # بروتوكول بلا مراجع معروف هو دَين علمي على المنصة.
    unreviewed_exercises = await session.scalar(
        select(func.count())
        .select_from(Exercise)
        .where(Exercise.is_active.is_(True), Exercise.reviewed_at.is_(None))
    )
    unreviewed_injuries = await session.scalar(
        select(func.count())
        .select_from(InjuryType)
        .where(InjuryType.is_active.is_(True), InjuryType.reviewed_at.is_(None))
    )

    return PlatformStats(
        users=users,
        plans=plans,
        plans_awaiting_review=awaiting,
        patients_without_specialist=unassigned or 0,
        active_injuries=sum(injury_counts.values()),
        acute_injuries=injury_counts.get(InjuryStatus.ACUTE, 0),
        logs_last_7_days=logs or 0,
        catalog_foods=foods or 0,
        catalog_exercises=exercises or 0,
        catalog_injury_types=injury_types or 0,
        catalog_unreviewed=(unreviewed_exercises or 0) + (unreviewed_injuries or 0),
    )


__all__ = [
    "ACTIVITY_WINDOW_DAYS",
    "build_platform_stats",
    "build_user_rows",
    "has_active_patients",
    "users_query",
]
