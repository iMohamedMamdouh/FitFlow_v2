"""اختبارات آلة حالات الخطة (ADR-006).

هذه أهم اختبارات المرحلة 2. الحالة المفروضة هنا هي ما يمنع أخطر عطل في
المنصة: وصول خطة تأهيل غير معتمدة إلى مريض.

الاختبارات تعدّل الحالة بـ SQL مباشر لا عبر الـ ORM — لأن ما نختبره هو
حاجز قاعدة البيانات نفسه، لا أي منطق في التطبيق فوقه.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PlanStatus, PlanType
from app.models.plan import ALLOWED_STATUS_TRANSITIONS
from app.models.user import User

# الحالات التي تشترط وجود معتمِد، والحالات التي تمنعه.
REQUIRES_APPROVER = {PlanStatus.APPROVED, PlanStatus.ACTIVE}
FORBIDS_APPROVER = {PlanStatus.DRAFT, PlanStatus.PENDING_REVIEW}

# التحويل الصريح للأنواع مطلوب: المعامل يظهر في موضع لا يستطيع الخادم
# استنتاج نوعه منه، فيفشل التحضير بـ AmbiguousParameterError.
_INSERT_PLAN = text("""
    INSERT INTO plans (
        id, user_id, plan_type, status, rule_engine_version,
        approved_by_specialist_id, approved_at, created_at, updated_at
    )
    VALUES (
        CAST(:id AS uuid), CAST(:user_id AS uuid),
        CAST(:plan_type AS plan_type), CAST(:status AS plan_status), '0.1.0',
        CAST(:approver AS uuid), CAST(:approved_at AS timestamptz), now(), now()
    )
    """)


async def _insert_plan(
    session: AsyncSession,
    *,
    user: User,
    status: PlanStatus,
    approver_id: uuid.UUID | None,
    plan_type: PlanType = PlanType.NUTRITION,
) -> uuid.UUID:
    plan_id = uuid.uuid4()
    approver = approver_id if status in REQUIRES_APPROVER else None
    await session.execute(
        _INSERT_PLAN,
        {
            "id": plan_id,
            "user_id": user.id,
            "plan_type": plan_type.value,
            "status": status.value,
            "approver": approver,
            "approved_at": datetime.now(UTC) if approver is not None else None,
        },
    )
    await session.commit()
    return plan_id


async def _change_status(
    session: AsyncSession,
    plan_id: uuid.UUID,
    to_status: PlanStatus,
    approver_id: uuid.UUID,
) -> None:
    if to_status in REQUIRES_APPROVER:
        approver_sql = "approved_by_specialist_id = CAST(:approver AS uuid), approved_at = now()"
    elif to_status in FORBIDS_APPROVER:
        approver_sql = "approved_by_specialist_id = NULL, approved_at = NULL"
    else:
        approver_sql = "approved_by_specialist_id = approved_by_specialist_id"

    await session.execute(
        text(
            f"UPDATE plans SET status = CAST(:status AS plan_status), {approver_sql}"
            " WHERE id = CAST(:id AS uuid)"
        ),
        {"status": to_status.value, "id": plan_id, "approver": approver_id},
    )
    await session.commit()


# ------------------------------------------------------- المصفوفة الكاملة
@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [(source, target) for source in PlanStatus for target in PlanStatus if source is not target],
)
async def test_every_status_pair_matches_the_declared_transition_table(
    session: AsyncSession,
    patient_user: User,
    specialist_user: User,
    from_status: PlanStatus,
    to_status: PlanStatus,
) -> None:
    """كل زوج حالات (30 حالة) يُقارن بالجدول المعلن في الكود.

    هذا الاختبار هو ما يمنع تباعد جدول الانتقالات في ``app/models/plan.py``
    عن الـ trigger في الـ migration. أي تعديل في أحدهما دون الآخر يُسقط
    اختبارًا هنا بالتحديد.
    """
    plan_id = await _insert_plan(
        session, user=patient_user, status=from_status, approver_id=specialist_user.id
    )
    is_allowed = to_status in ALLOWED_STATUS_TRANSITIONS[from_status]

    if is_allowed:
        await _change_status(session, plan_id, to_status, specialist_user.id)
        stored = await session.scalar(
            text("SELECT status FROM plans WHERE id = CAST(:id AS uuid)"), {"id": plan_id}
        )
        assert stored == to_status.value
    else:
        with pytest.raises(DBAPIError):
            await _change_status(session, plan_id, to_status, specialist_user.id)
        await session.rollback()


async def test_archived_plan_is_terminal(
    session: AsyncSession, patient_user: User, specialist_user: User
) -> None:
    """لا خروج من الأرشيف — الخطة المؤرشفة سجل تاريخي لا يُعاد تفعيله."""
    assert ALLOWED_STATUS_TRANSITIONS[PlanStatus.ARCHIVED] == frozenset()

    plan_id = await _insert_plan(
        session, user=patient_user, status=PlanStatus.ARCHIVED, approver_id=None
    )

    with pytest.raises(DBAPIError):
        await _change_status(session, plan_id, PlanStatus.ACTIVE, specialist_user.id)
    await session.rollback()


async def test_draft_cannot_jump_straight_to_active(
    session: AsyncSession, patient_user: User, specialist_user: User
) -> None:
    """القفز فوق المراجعة هو بالضبط ما تمنعه هذه الآلة."""
    plan_id = await _insert_plan(
        session, user=patient_user, status=PlanStatus.DRAFT, approver_id=None
    )

    with pytest.raises(DBAPIError):
        await _change_status(session, plan_id, PlanStatus.ACTIVE, specialist_user.id)
    await session.rollback()


async def test_full_happy_path_reaches_active(
    session: AsyncSession, patient_user: User, specialist_user: User
) -> None:
    plan_id = await _insert_plan(
        session, user=patient_user, status=PlanStatus.DRAFT, approver_id=None
    )

    for step in (PlanStatus.PENDING_REVIEW, PlanStatus.APPROVED, PlanStatus.ACTIVE):
        await _change_status(session, plan_id, step, specialist_user.id)

    stored = await session.scalar(
        text("SELECT status FROM plans WHERE id = CAST(:id AS uuid)"), {"id": plan_id}
    )
    assert stored == PlanStatus.ACTIVE.value


async def test_rejection_loop_returns_the_plan_to_draft(
    session: AsyncSession, patient_user: User, specialist_user: User
) -> None:
    plan_id = await _insert_plan(
        session, user=patient_user, status=PlanStatus.PENDING_REVIEW, approver_id=None
    )

    await _change_status(session, plan_id, PlanStatus.CHANGES_REQUESTED, specialist_user.id)
    await _change_status(session, plan_id, PlanStatus.DRAFT, specialist_user.id)

    stored = await session.scalar(
        text("SELECT status FROM plans WHERE id = CAST(:id AS uuid)"), {"id": plan_id}
    )
    assert stored == PlanStatus.DRAFT.value


# --------------------------------------------------------- قيود الاعتماد
async def test_active_plan_without_approver_is_rejected(
    session: AsyncSession, patient_user: User
) -> None:
    """الحاجز الثاني: حتى الإدخال المباشر لا يُنشئ خطة مفعّلة بلا معتمِد."""
    with pytest.raises(IntegrityError):
        await session.execute(
            _INSERT_PLAN,
            {
                "id": uuid.uuid4(),
                "user_id": patient_user.id,
                "plan_type": PlanType.NUTRITION.value,
                "status": PlanStatus.ACTIVE.value,
                "approver": None,
                "approved_at": None,
            },
        )
        await session.commit()
    await session.rollback()


async def test_draft_carrying_approval_data_is_rejected(
    session: AsyncSession, patient_user: User, specialist_user: User
) -> None:
    """اعتماد مزيّف: مسودة تحمل اسم معتمِد وتاريخ اعتماد."""
    with pytest.raises(IntegrityError):
        await session.execute(
            text("""
                INSERT INTO plans (
                    id, user_id, plan_type, status, rule_engine_version,
                    approved_by_specialist_id, approved_at, created_at, updated_at
                )
                VALUES (CAST(:id AS uuid), CAST(:user_id AS uuid), 'nutrition', 'draft',
                        '0.1.0', CAST(:approver AS uuid), now(), now(), now())
                """),
            {
                "id": uuid.uuid4(),
                "user_id": patient_user.id,
                "approver": specialist_user.id,
            },
        )
        await session.commit()
    await session.rollback()


# ------------------------------------------------- خطة مفعّلة واحدة فقط
async def test_only_one_active_plan_per_user_and_type(
    session: AsyncSession, patient_user: User, specialist_user: User
) -> None:
    """خطتان غذائيتان مفعّلتان لنفس المريض = تعليمات متناقضة تصله معًا."""
    await _insert_plan(
        session, user=patient_user, status=PlanStatus.ACTIVE, approver_id=specialist_user.id
    )

    with pytest.raises(IntegrityError):
        await _insert_plan(
            session, user=patient_user, status=PlanStatus.ACTIVE, approver_id=specialist_user.id
        )
    await session.rollback()


async def test_active_plans_of_different_types_coexist(
    session: AsyncSession, patient_user: User, specialist_user: User
) -> None:
    """القيد على النوع لا على المستخدم: خطة غذاء وخطة تأهيل معًا مسموحتان."""
    await _insert_plan(
        session,
        user=patient_user,
        status=PlanStatus.ACTIVE,
        approver_id=specialist_user.id,
        plan_type=PlanType.NUTRITION,
    )
    await _insert_plan(
        session,
        user=patient_user,
        status=PlanStatus.ACTIVE,
        approver_id=specialist_user.id,
        plan_type=PlanType.REHAB,
    )

    count = await session.scalar(
        text("SELECT count(*) FROM plans WHERE user_id = CAST(:uid AS uuid) AND status = 'active'"),
        {"uid": patient_user.id},
    )
    assert count == 2


async def test_many_archived_plans_are_allowed(session: AsyncSession, patient_user: User) -> None:
    """الفهرس الفريد جزئي — الأرشيف غير محدود."""
    for _ in range(3):
        await _insert_plan(session, user=patient_user, status=PlanStatus.ARCHIVED, approver_id=None)

    count = await session.scalar(
        text(
            "SELECT count(*) FROM plans WHERE user_id = CAST(:uid AS uuid) AND status = 'archived'"
        ),
        {"uid": patient_user.id},
    )
    assert count == 3
