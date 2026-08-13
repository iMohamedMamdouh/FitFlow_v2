"""لوحة المدير (المرحلة 10): المستخدمون، الإسناد، الإحصاءات.

الإسناد كان يُنفَّذ بـ SQL يدوي حتى هذه المرحلة، فاختباراته تركّز على ما
لا يستطيع SQL اليدوي حمايته: من يُسمح بإسناده إلى من، وماذا يحدث لسجل
التدقيق، وأي تعديل على الأدوار يترك اللوحة بلا مدير أو مريضًا بلا متابِع.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditAction, AuditLog
from app.models.care_team import SpecialistPatient
from app.models.clinical import DailyLog
from app.models.user import User, UserRole
from tests.conftest import login

pytestmark = pytest.mark.asyncio

ADMIN = "/api/v1/admin"


async def _assign(client: AsyncClient, headers: dict[str, str], specialist: User, patient: User):
    return await client.post(
        f"{ADMIN}/assignments",
        headers=headers,
        json={"specialist_id": str(specialist.id), "patient_id": str(patient.id)},
    )


# ---------------------------------------------------------------- القائمة
async def test_user_list_filters_by_role_and_search(
    client: AsyncClient,
    admin_user: User,
    specialist_user: User,
    patient_user: User,
) -> None:
    headers = await login(client, admin_user.email)

    everyone = await client.get(f"{ADMIN}/users", headers=headers)
    assert everyone.status_code == 200
    assert len(everyone.json()) == 3

    specialists = await client.get(f"{ADMIN}/users?role=specialist", headers=headers)
    assert [row["email"] for row in specialists.json()] == [specialist_user.email]

    # البحث يشمل البريد والاسم معًا — من يبحث عن مستخدم يكتب ما يتذكّره.
    by_email = await client.get(f"{ADMIN}/users?search=PATIENT@", headers=headers)
    assert [row["email"] for row in by_email.json()] == [patient_user.email]

    by_name = await client.get(f"{ADMIN}/users?search=اختبار", headers=headers)
    assert len(by_name.json()) == 3


async def test_user_list_shows_assignment_counts(
    client: AsyncClient,
    admin_user: User,
    specialist_user: User,
    patient_user: User,
) -> None:
    headers = await login(client, admin_user.email)
    assert (await _assign(client, headers, specialist_user, patient_user)).status_code == 204

    rows = {
        row["email"]: row for row in (await client.get(f"{ADMIN}/users", headers=headers)).json()
    }
    assert rows[specialist_user.email]["assigned_patients"] == 1
    assert rows[patient_user.email]["specialists"] == [
        {"id": str(specialist_user.id), "full_name": specialist_user.full_name}
    ]
    # المريض ليس أخصائيًا: العدّاد صفر لا القيمة نفسها معكوسة.
    assert rows[patient_user.email]["assigned_patients"] == 0


async def test_only_admins_reach_the_dashboard(
    client: AsyncClient,
    specialist_user: User,
    patient_user: User,
) -> None:
    for user in (specialist_user, patient_user):
        headers = await login(client, user.email)
        assert (await client.get(f"{ADMIN}/users", headers=headers)).status_code == 403
        assert (await client.get(f"{ADMIN}/stats", headers=headers)).status_code == 403
        assert (await _assign(client, headers, specialist_user, patient_user)).status_code == 403


# ---------------------------------------------------------------- التعديل
async def test_admin_cannot_lock_themselves_out(client: AsyncClient, admin_user: User) -> None:
    headers = await login(client, admin_user.email)

    disabled = await client.patch(
        f"{ADMIN}/users/{admin_user.id}", headers=headers, json={"is_active": False}
    )
    assert disabled.status_code == 409

    demoted = await client.patch(
        f"{ADMIN}/users/{admin_user.id}", headers=headers, json={"role": "patient"}
    )
    assert demoted.status_code == 409

    # تعديل اسمه هو نفسه مسموح — الحارس على الصلاحية لا على السطر كله.
    renamed = await client.patch(
        f"{ADMIN}/users/{admin_user.id}", headers=headers, json={"full_name": "مدير المنصة"}
    )
    assert renamed.status_code == 200
    assert renamed.json()["full_name"] == "مدير المنصة"


async def test_specialist_with_patients_cannot_be_demoted(
    client: AsyncClient,
    admin_user: User,
    specialist_user: User,
    patient_user: User,
) -> None:
    headers = await login(client, admin_user.email)
    await _assign(client, headers, specialist_user, patient_user)

    refused = await client.patch(
        f"{ADMIN}/users/{specialist_user.id}", headers=headers, json={"role": "patient"}
    )
    assert refused.status_code == 409
    assert "مرضى" in refused.json()["detail"]

    # التعطيل مسموح — فعل عاجل لا يجوز أن يمنعه عدد المرضى.
    disabled = await client.patch(
        f"{ADMIN}/users/{specialist_user.id}", headers=headers, json={"is_active": False}
    )
    assert disabled.status_code == 200
    assert disabled.json()["is_active"] is False


async def test_disabled_user_cannot_log_in(
    client: AsyncClient, admin_user: User, patient_user: User
) -> None:
    headers = await login(client, admin_user.email)
    await client.patch(
        f"{ADMIN}/users/{patient_user.id}", headers=headers, json={"is_active": False}
    )

    refused = await client.post(
        "/api/v1/auth/login",
        json={"email": patient_user.email, "password": "TestPassword123!"},
    )
    assert refused.status_code == 401


async def test_update_is_audited_but_a_no_op_is_not(
    client: AsyncClient,
    session: AsyncSession,
    admin_user: User,
    patient_user: User,
) -> None:
    headers = await login(client, admin_user.email)

    await client.patch(
        f"{ADMIN}/users/{patient_user.id}", headers=headers, json={"full_name": "اسم جديد"}
    )
    # نفس القيمة مرة ثانية: لا يُفترض أن يُكتب سطر ثانٍ.
    await client.patch(
        f"{ADMIN}/users/{patient_user.id}", headers=headers, json={"full_name": "اسم جديد"}
    )

    entries = list(
        await session.scalars(
            select(AuditLog).where(AuditLog.action == AuditAction.USER_UPDATED_BY_ADMIN.value)
        )
    )
    assert len(entries) == 1
    assert entries[0].before is not None
    assert entries[0].before["full_name"] == "مستخدم اختبار"
    assert entries[0].after is not None
    assert entries[0].after["full_name"] == "اسم جديد"


async def test_updating_a_missing_user_is_404(client: AsyncClient, admin_user: User) -> None:
    headers = await login(client, admin_user.email)
    response = await client.patch(
        f"{ADMIN}/users/{uuid.uuid4()}", headers=headers, json={"is_active": False}
    )
    assert response.status_code == 404


# ---------------------------------------------------------------- الإسناد
async def test_assignment_reaches_the_specialist_dashboard(
    client: AsyncClient,
    admin_user: User,
    specialist_user: User,
    patient_user: User,
) -> None:
    admin_headers = await login(client, admin_user.email)
    specialist_headers = await login(client, specialist_user.email)

    before = await client.get("/api/v1/specialist/patients", headers=specialist_headers)
    assert before.json() == []

    assert (await _assign(client, admin_headers, specialist_user, patient_user)).status_code == 204

    after = await client.get("/api/v1/specialist/patients", headers=specialist_headers)
    assert [row["id"] for row in after.json()] == [str(patient_user.id)]


async def test_assignment_rejects_wrong_roles(
    client: AsyncClient,
    admin_user: User,
    specialist_user: User,
    patient_user: User,
) -> None:
    headers = await login(client, admin_user.email)

    # مريض في موضع الأخصائي
    swapped = await client.post(
        f"{ADMIN}/assignments",
        headers=headers,
        json={"specialist_id": str(patient_user.id), "patient_id": str(specialist_user.id)},
    )
    assert swapped.status_code == 409

    missing = await client.post(
        f"{ADMIN}/assignments",
        headers=headers,
        json={"specialist_id": str(specialist_user.id), "patient_id": str(uuid.uuid4())},
    )
    assert missing.status_code == 404


async def test_assignment_to_a_disabled_specialist_is_refused(
    client: AsyncClient,
    admin_user: User,
    specialist_user: User,
    patient_user: User,
) -> None:
    headers = await login(client, admin_user.email)
    await client.patch(
        f"{ADMIN}/users/{specialist_user.id}", headers=headers, json={"is_active": False}
    )

    refused = await _assign(client, headers, specialist_user, patient_user)
    assert refused.status_code == 409


async def test_duplicate_assignment_is_refused(
    client: AsyncClient,
    admin_user: User,
    specialist_user: User,
    patient_user: User,
) -> None:
    headers = await login(client, admin_user.email)
    assert (await _assign(client, headers, specialist_user, patient_user)).status_code == 204
    assert (await _assign(client, headers, specialist_user, patient_user)).status_code == 409


async def test_unassign_keeps_the_row_and_reassign_revives_it(
    client: AsyncClient,
    session: AsyncSession,
    admin_user: User,
    specialist_user: User,
    patient_user: User,
) -> None:
    headers = await login(client, admin_user.email)
    await _assign(client, headers, specialist_user, patient_user)

    ended = await client.delete(
        f"{ADMIN}/assignments/{specialist_user.id}/{patient_user.id}", headers=headers
    )
    assert ended.status_code == 204

    link = await session.scalar(
        select(SpecialistPatient).where(SpecialistPatient.patient_id == patient_user.id)
    )
    # الصف باقٍ: "من كان يتابع هذا المريض ومتى" سؤال سريري يُسأل لاحقًا.
    assert link is not None
    assert link.is_active is False
    assert link.ended_at is not None

    specialist_headers = await login(client, specialist_user.email)
    listed = await client.get("/api/v1/specialist/patients", headers=specialist_headers)
    assert listed.json() == []

    # المريض لم يعد مرئيًا للأخصائي أصلًا — لا من القائمة ولا بالمعرّف.
    record = await client.get(
        f"/api/v1/specialist/patients/{patient_user.id}/profile", headers=specialist_headers
    )
    assert record.status_code == 404

    assert (await _assign(client, headers, specialist_user, patient_user)).status_code == 204
    revived = await client.get("/api/v1/specialist/patients", headers=specialist_headers)
    assert [row["id"] for row in revived.json()] == [str(patient_user.id)]


async def test_unassigning_what_is_not_assigned_is_404(
    client: AsyncClient,
    admin_user: User,
    specialist_user: User,
    patient_user: User,
) -> None:
    headers = await login(client, admin_user.email)
    response = await client.delete(
        f"{ADMIN}/assignments/{specialist_user.id}/{patient_user.id}", headers=headers
    )
    assert response.status_code == 404


async def test_assignment_is_audited(
    client: AsyncClient,
    session: AsyncSession,
    admin_user: User,
    specialist_user: User,
    patient_user: User,
) -> None:
    headers = await login(client, admin_user.email)
    await _assign(client, headers, specialist_user, patient_user)
    await client.delete(
        f"{ADMIN}/assignments/{specialist_user.id}/{patient_user.id}", headers=headers
    )

    actions = list(
        await session.scalars(
            select(AuditLog.action).where(AuditLog.entity_type == "specialist_patient")
        )
    )
    assert AuditAction.PATIENT_ASSIGNED.value in actions
    assert AuditAction.PATIENT_UNASSIGNED.value in actions


# -------------------------------------------------------------- الإحصاءات
async def test_stats_count_users_plans_and_activity(
    client: AsyncClient,
    session: AsyncSession,
    admin_user: User,
    specialist_user: User,
    patient_user: User,
) -> None:
    headers = await login(client, admin_user.email)

    session.add(DailyLog(user_id=patient_user.id, log_date=date.today(), weight_kg=80))
    await session.commit()

    stats = (await client.get(f"{ADMIN}/stats", headers=headers)).json()

    by_role = {row["role"]: row for row in stats["users"]}
    assert by_role["patient"]["total"] == 1
    assert by_role["specialist"]["active"] == 1
    # الأدوار الثلاثة حاضرة دائمًا — صفر معروض أوضح من صف غائب.
    assert set(by_role) == {role.value for role in UserRole}

    assert stats["patients_without_specialist"] == 1
    assert stats["logs_last_7_days"] == 1
    assert stats["plans_awaiting_review"] == 0

    await _assign(client, headers, specialist_user, patient_user)
    after = (await client.get(f"{ADMIN}/stats", headers=headers)).json()
    assert after["patients_without_specialist"] == 0
