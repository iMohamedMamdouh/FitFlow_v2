"""محاكاة دور الأخصائي — **للتطوير المحلي فقط**.

    python -m app.cli.demo_review patient@example.com

المشكلة التي يحلها: عرض الخطة لا يظهر للمريض قبل اعتماد أخصائي (ADR-006)،
ولوحة الأخصائي هي المرحلة 8. فلتجربة الواجهة من طرف إلى طرف اليوم يحتاج
المطوّر أن ينوب عن الأخصائي يدويًا — وهذا ما يفعله هذا السكربت.

**يرفض العمل خارج بيئة ``local``.** أداة تعتمد الخطط آليًا هي بالضبط ما
تمنعه ADR-006؛ وجودها مقبول فقط لأنها لا تعمل إلا على جهاز مطوّر، والحاجز
هنا صريح لا اتفاق ضمني.
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import SessionFactory, engine
from app.core.enums import PlanStatus
from app.core.security import hash_password
from app.models.care_team import SpecialistPatient
from app.models.plan import Plan
from app.models.user import User, UserRole
from app.services.plans import record_transition

DEMO_SPECIALIST_EMAIL = "specialist@example.com"
DEMO_SPECIALIST_PASSWORD = "SpecialistPass123!"

# الانتقالات المسموحة نحو التفعيل، بالترتيب الذي تفرضه قاعدة البيانات.
_ROUTE_TO_ACTIVE = {
    PlanStatus.DRAFT: (PlanStatus.PENDING_REVIEW, PlanStatus.APPROVED, PlanStatus.ACTIVE),
    PlanStatus.PENDING_REVIEW: (PlanStatus.APPROVED, PlanStatus.ACTIVE),
    PlanStatus.CHANGES_REQUESTED: (
        PlanStatus.DRAFT,
        PlanStatus.PENDING_REVIEW,
        PlanStatus.APPROVED,
        PlanStatus.ACTIVE,
    ),
    PlanStatus.APPROVED: (PlanStatus.ACTIVE,),
}


async def review_latest_plan(patient_email: str) -> int:
    settings = get_settings()
    if settings.environment != "local":
        print(
            "✗ رُفض التنفيذ: هذه الأداة للتطوير المحلي فقط."
            " الاعتماد في أي بيئة أخرى فعل بشري (ADR-006).",
            file=sys.stderr,
        )
        return 1

    async with SessionFactory() as session:
        patient = await session.scalar(
            select(User).where(User.email == patient_email.strip().lower())
        )
        if patient is None:
            print(f"✗ لا يوجد مستخدم بالبريد {patient_email}", file=sys.stderr)
            return 1
        if patient.role is not UserRole.PATIENT:
            print("✗ الحساب المطلوب ليس حساب مريض", file=sys.stderr)
            return 1

        specialist = await session.scalar(select(User).where(User.email == DEMO_SPECIALIST_EMAIL))
        if specialist is None:
            specialist = User(
                email=DEMO_SPECIALIST_EMAIL,
                password_hash=hash_password(DEMO_SPECIALIST_PASSWORD),
                full_name="د. أخصائي التجربة",
                role=UserRole.SPECIALIST,
            )
            session.add(specialist)
            await session.flush()
            print(f"✓ أُنشئ أخصائي تجريبي: {DEMO_SPECIALIST_EMAIL} / {DEMO_SPECIALIST_PASSWORD}")

        assignment = await session.get(SpecialistPatient, (specialist.id, patient.id))
        if assignment is None:
            session.add(SpecialistPatient(specialist_id=specialist.id, patient_id=patient.id))
            print("✓ أُسنِد المريض إلى الأخصائي")
        elif not assignment.is_active:
            assignment.is_active = True
            print("✓ أُعيد تفعيل الإسناد")

        plan = await session.scalar(
            select(Plan).where(Plan.user_id == patient.id).order_by(Plan.created_at.desc()).limit(1)
        )
        if plan is None:
            print("✗ لا توجد خطة لهذا المريض — ولّد خطة من الواجهة أولًا", file=sys.stderr)
            return 1
        if plan.status is PlanStatus.ACTIVE:
            print("• الخطة مفعّلة بالفعل — لا حاجة لشيء.")
            await session.commit()
            return 0

        route = _ROUTE_TO_ACTIVE.get(plan.status)
        if route is None:
            print(f"✗ لا يمكن تفعيل خطة حالتها {plan.status.value}", file=sys.stderr)
            return 1

        for target in route:
            await record_transition(
                session,
                plan,
                to_status=target,
                actor_id=specialist.id,
                reason="محاكاة مراجعة أخصائي (تطوير محلي)",
            )
            await session.flush()
            print(f"  → {target.value}")

        await session.commit()

    print("✓ الخطة مفعّلة — حدّث صفحة /plan في المتصفح.")
    return 0


async def _main() -> int:
    if len(sys.argv) != 2:
        print("الاستخدام: python -m app.cli.demo_review <بريد المريض>", file=sys.stderr)
        return 2
    try:
        return await review_latest_plan(sys.argv[1])
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
