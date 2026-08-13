"""بناء ملخّصات المرضى للوحة الأخصائي.

كل دالة هنا تعمل على **قائمة مرضى دفعة واحدة** لا على مريض في كل نداء.
لوحة أخصائي عنده ثلاثون مريضًا تحتاج ستة استعلامات مجمَّعة، لا مائة
وثمانين استعلامًا فرديًا — والفرق يظهر كزمن تحميل لا كسطر في سجل.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import today
from app.core.enums import InjuryStatus, PlanStatus
from app.models.clinical import DailyLog, Injury, PhysiologicalReading
from app.models.plan import Plan
from app.models.profile import UserProfile
from app.models.user import User
from app.schemas.specialist import STALLED_AFTER_DAYS, PatientFlag, PatientSummary

# نافذة حساب متوسط الالتزام — أسبوعان يكفيان لإظهار اتجاه دون أن يبتلعه
# تاريخ قديم لم يعد يمثّل الحالة.
ADHERENCE_WINDOW_DAYS = 14


async def _plan_counts(
    session: AsyncSession, patient_ids: list[uuid.UUID]
) -> tuple[dict[uuid.UUID, int], set[uuid.UUID]]:
    rows = await session.execute(
        select(Plan.user_id, Plan.status, func.count())
        .where(Plan.user_id.in_(patient_ids))
        .group_by(Plan.user_id, Plan.status)
    )
    awaiting: dict[uuid.UUID, int] = {}
    active: set[uuid.UUID] = set()
    for user_id, status, count in rows:
        if status is PlanStatus.PENDING_REVIEW:
            awaiting[user_id] = count
        elif status is PlanStatus.ACTIVE:
            active.add(user_id)
    return awaiting, active


async def _injury_counts(
    session: AsyncSession, patient_ids: list[uuid.UUID]
) -> tuple[dict[uuid.UUID, int], set[uuid.UUID]]:
    rows = await session.execute(
        select(Injury.user_id, Injury.status, func.count())
        .where(Injury.user_id.in_(patient_ids))
        .group_by(Injury.user_id, Injury.status)
    )
    active: dict[uuid.UUID, int] = {}
    acute: set[uuid.UUID] = set()
    for user_id, status, count in rows:
        if status is InjuryStatus.RECOVERED:
            continue
        active[user_id] = active.get(user_id, 0) + count
        if status is InjuryStatus.ACUTE:
            acute.add(user_id)
    return active, acute


async def _weights(
    session: AsyncSession, patient_ids: list[uuid.UUID]
) -> tuple[dict[uuid.UUID, Decimal], dict[uuid.UUID, Decimal]]:
    """أحدث وزن وأول وزن لكل مريض — بـ ``DISTINCT ON`` لا باستعلام لكل مريض."""
    base = select(PhysiologicalReading.user_id, PhysiologicalReading.weight_kg).where(
        PhysiologicalReading.user_id.in_(patient_ids),
        PhysiologicalReading.weight_kg.is_not(None),
    )

    latest_rows = await session.execute(
        base.distinct(PhysiologicalReading.user_id).order_by(
            PhysiologicalReading.user_id, PhysiologicalReading.reading_date.desc()
        )
    )
    first_rows = await session.execute(
        base.distinct(PhysiologicalReading.user_id).order_by(
            PhysiologicalReading.user_id, PhysiologicalReading.reading_date.asc()
        )
    )
    return (
        {user_id: weight for user_id, weight in latest_rows if weight is not None},
        {user_id: weight for user_id, weight in first_rows if weight is not None},
    )


async def _log_signals(
    session: AsyncSession, patient_ids: list[uuid.UUID]
) -> tuple[dict[uuid.UUID, date], dict[uuid.UUID, int]]:
    last_rows = await session.execute(
        select(DailyLog.user_id, func.max(DailyLog.log_date))
        .where(DailyLog.user_id.in_(patient_ids))
        .group_by(DailyLog.user_id)
    )
    since = today() - timedelta(days=ADHERENCE_WINDOW_DAYS)
    adherence_rows = await session.execute(
        select(DailyLog.user_id, func.avg(DailyLog.diet_adherence_pct))
        .where(
            DailyLog.user_id.in_(patient_ids),
            DailyLog.log_date >= since,
            DailyLog.diet_adherence_pct.is_not(None),
        )
        .group_by(DailyLog.user_id)
    )
    return (
        {user_id: last for user_id, last in last_rows if last is not None},
        {user_id: round(float(avg)) for user_id, avg in adherence_rows if avg is not None},
    )


async def _profiles(
    session: AsyncSession, patient_ids: list[uuid.UUID]
) -> tuple[set[uuid.UUID], set[uuid.UUID]]:
    rows = await session.execute(
        select(UserProfile.user_id, UserProfile.consent_accepted_at).where(
            UserProfile.user_id.in_(patient_ids)
        )
    )
    complete: set[uuid.UUID] = set()
    consented: set[uuid.UUID] = set()
    for user_id, accepted_at in rows:
        complete.add(user_id)
        if accepted_at is not None:
            consented.add(user_id)
    return complete, consented


def _decide_flag(
    *,
    awaiting_review: int,
    has_acute_injury: bool,
    profile_complete: bool,
    consent_accepted: bool,
    days_since_last_log: int | None,
) -> PatientFlag:
    """أعلى مؤشر ينطبق — الترتيب هنا هو ترتيب الإلحاح لا ترتيب الفحص."""
    if awaiting_review > 0:
        return PatientFlag.NEEDS_REVIEW
    if has_acute_injury:
        return PatientFlag.ACUTE_INJURY
    if not profile_complete or not consent_accepted:
        return PatientFlag.NOT_STARTED
    # المريض الذي لم يسجّل يومًا واحدًا أصلًا متعثّر مثل من توقّف.
    if days_since_last_log is None or days_since_last_log > STALLED_AFTER_DAYS:
        return PatientFlag.STALLED
    return PatientFlag.ON_TRACK


async def build_patient_summaries(
    session: AsyncSession,
    patients: list[User],
) -> list[PatientSummary]:
    """يبني ملخّصًا لكل مريض، مرتّبًا بالإلحاح ثم بالاسم."""
    if not patients:
        return []

    patient_ids = [patient.id for patient in patients]
    awaiting, active_plans = await _plan_counts(session, patient_ids)
    active_injuries, acute = await _injury_counts(session, patient_ids)
    latest_weight, first_weight = await _weights(session, patient_ids)
    last_log, adherence = await _log_signals(session, patient_ids)
    complete, consented = await _profiles(session, patient_ids)

    now = today()
    summaries: list[PatientSummary] = []
    for patient in patients:
        last = last_log.get(patient.id)
        days_since = (now - last).days if last is not None else None
        latest = latest_weight.get(patient.id)
        first = first_weight.get(patient.id)

        summaries.append(
            PatientSummary(
                id=patient.id,
                email=patient.email,
                full_name=patient.full_name,
                is_active=patient.is_active,
                created_at=patient.created_at,
                flag=_decide_flag(
                    awaiting_review=awaiting.get(patient.id, 0),
                    has_acute_injury=patient.id in acute,
                    profile_complete=patient.id in complete,
                    consent_accepted=patient.id in consented,
                    days_since_last_log=days_since,
                ),
                plans_awaiting_review=awaiting.get(patient.id, 0),
                has_active_plan=patient.id in active_plans,
                active_injuries=active_injuries.get(patient.id, 0),
                has_acute_injury=patient.id in acute,
                profile_complete=patient.id in complete,
                consent_accepted=patient.id in consented,
                latest_weight_kg=latest,
                weight_change_kg=(
                    latest - first if latest is not None and first is not None else None
                ),
                last_log_date=last,
                days_since_last_log=days_since,
                diet_adherence_avg=adherence.get(patient.id),
            )
        )

    order = list(PatientFlag)
    summaries.sort(key=lambda summary: (order.index(summary.flag), summary.full_name))
    return summaries


__all__ = ["ADHERENCE_WINDOW_DAYS", "build_patient_summaries"]
