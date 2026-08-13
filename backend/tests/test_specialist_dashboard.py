"""اختبارات لوحة الأخصائي (المرحلة 8).

التركيز على شيئين: **صحة المؤشرات** التي يبني عليها الأخصائي ترتيب يومه،
و**بقاء العزل** بعد إضافة أربعة مسارات جديدة تقرأ بيانات مريض.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clinical import DailyLog, Injury
from app.models.user import User, UserRole
from app.schemas.specialist import STALLED_AFTER_DAYS
from tests.conftest import TEST_PASSWORD, SessionFactory, login
from tests.test_attachments import make_injury_type
from tests.test_plan_workflow import assign_specialist, onboard_patient

TODAY = date.today()


async def make_patient(email: str, *, full_name: str = "مريض") -> User:
    async with SessionFactory() as session:
        user = User(
            email=email,
            password_hash=hash_password(TEST_PASSWORD),
            full_name=full_name,
            role=UserRole.PATIENT,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def add_log(user_id: uuid.UUID, *, days_ago: int, adherence: int | None = 80) -> None:
    async with SessionFactory() as session:
        session.add(
            DailyLog(
                user_id=user_id,
                log_date=TODAY - timedelta(days=days_ago),
                diet_adherence_pct=adherence,
            )
        )
        await session.commit()


async def add_injury(user_id: uuid.UUID, *, status: str = "acute") -> None:
    injury_type = await make_injury_type(f"type-{uuid.uuid4().hex[:8]}")
    async with SessionFactory() as session:
        session.add(
            Injury(
                user_id=user_id,
                injury_type_id=injury_type.id,
                injury_date=TODAY - timedelta(days=10),
                pain_level=6,
                status=status,  # type: ignore[arg-type]
            )
        )
        await session.commit()


async def summary_for(client: AsyncClient, headers: dict[str, str], user_id: uuid.UUID) -> dict:
    patients = (await client.get("/api/v1/specialist/patients", headers=headers)).json()
    match = [entry for entry in patients if entry["id"] == str(user_id)]
    assert match, f"المريض {user_id} غير موجود في القائمة"
    return match[0]


# --------------------------------------------------------------- المؤشرات
async def test_a_patient_who_never_started_is_flagged(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    await assign_specialist(session, specialist_user, patient_user)
    headers = await login(client, specialist_user.email)

    summary = await summary_for(client, headers, patient_user.id)

    assert summary["flag"] == "not_started"
    assert summary["profile_complete"] is False
    assert summary["consent_accepted"] is False


async def test_a_plan_awaiting_review_outranks_everything(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    owner = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=owner)).json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/submit", headers=owner)
    # الإصابة الحادة تُسجَّل بعد التوليد: لو سبقته لرفض المحرك توليد خطة
    # غذائية أصلًا (المسار يصبح تأهيلًا خالصًا).
    await add_injury(patient_user.id)

    headers = await login(client, specialist_user.email)
    summary = await summary_for(client, headers, patient_user.id)

    assert summary["flag"] == "needs_review"
    assert summary["plans_awaiting_review"] == 1


async def test_an_acute_injury_is_flagged(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    await add_injury(patient_user.id, status="acute")
    await add_log(patient_user.id, days_ago=0)

    headers = await login(client, specialist_user.email)
    summary = await summary_for(client, headers, patient_user.id)

    assert summary["flag"] == "acute_injury"
    assert summary["has_acute_injury"] is True
    assert summary["active_injuries"] == 1


async def test_silence_beyond_the_window_is_stalled(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    await add_log(patient_user.id, days_ago=STALLED_AFTER_DAYS + 3)

    headers = await login(client, specialist_user.email)
    summary = await summary_for(client, headers, patient_user.id)

    assert summary["flag"] == "stalled"
    assert summary["days_since_last_log"] == STALLED_AFTER_DAYS + 3


async def test_a_patient_who_never_logged_is_stalled_too(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    """الصمت من اليوم الأول صمت أيضًا — لا حالة ثالثة بينهما."""
    await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)

    headers = await login(client, specialist_user.email)
    summary = await summary_for(client, headers, patient_user.id)

    assert summary["flag"] == "stalled"
    assert summary["last_log_date"] is None


async def test_a_recent_log_and_nothing_pending_is_on_track(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    await add_log(patient_user.id, days_ago=1, adherence=90)
    await add_log(patient_user.id, days_ago=2, adherence=70)

    headers = await login(client, specialist_user.email)
    summary = await summary_for(client, headers, patient_user.id)

    assert summary["flag"] == "on_track"
    assert summary["diet_adherence_avg"] == 80


async def test_weight_change_is_measured_from_the_first_reading(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    await client.post(
        "/api/v1/me/readings",
        json={
            "reading_date": (TODAY - timedelta(days=30)).isoformat(),
            "weight_kg": "95.0",
        },
        headers=headers,
    )

    specialist_headers = await login(client, specialist_user.email)
    summary = await summary_for(client, specialist_headers, patient_user.id)

    # onboard_patient يسجّل 92 اليوم، والقياس الأقدم 95 — الفرق 3 كجم نزولًا.
    assert float(summary["latest_weight_kg"]) == 92.0
    assert float(summary["weight_change_kg"]) == -3.0


async def test_the_list_is_ordered_by_urgency(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    """المريض الذي يحتاج تدخّلًا أولًا — لا الأبجدية ولا تاريخ التسجيل."""
    calm = await make_patient("calm@example.com", full_name="مريض منتظم")
    await onboard_patient(client, calm, session)
    await assign_specialist(session, specialist_user, calm)
    await add_log(calm.id, days_ago=0)

    urgent = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=urgent)).json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/submit", headers=urgent)

    headers = await login(client, specialist_user.email)
    patients = (await client.get("/api/v1/specialist/patients", headers=headers)).json()

    assert patients[0]["flag"] == "needs_review"
    assert patients[0]["id"] == str(patient_user.id)
    assert patients[-1]["flag"] == "on_track"


# ------------------------------------------------------------- ملف المريض
async def test_the_specialist_reads_the_full_record(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    owner = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    await client.post(
        "/api/v1/me/logs",
        json={"log_date": TODAY.isoformat(), "pain_level": 3, "diet_adherence_pct": 75},
        headers=owner,
    )
    headers = await login(client, specialist_user.email)

    profile = await client.get(
        f"/api/v1/specialist/patients/{patient_user.id}/profile", headers=headers
    )
    logs = await client.get(f"/api/v1/specialist/patients/{patient_user.id}/logs", headers=headers)

    assert profile.status_code == 200
    assert profile.json()["goal"] == "weight_loss"
    assert logs.status_code == 200
    assert logs.json()[0]["diet_adherence_pct"] == 75


async def test_reading_a_profile_is_written_to_the_audit_log(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    headers = await login(client, specialist_user.email)

    await client.get(f"/api/v1/specialist/patients/{patient_user.id}/profile", headers=headers)
    entries = (
        await client.get(f"/api/v1/specialist/patients/{patient_user.id}/audit", headers=headers)
    ).json()

    views = [entry for entry in entries if entry["action"] == "patient.record_viewed"]
    assert views
    assert views[0]["actor_user_id"] == str(specialist_user.id)
    assert views[0]["actor_name"] == specialist_user.full_name


async def test_the_audit_trail_includes_actions_on_the_patients_plans(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    """اعتماد خطة فاعله أخصائي وهدفه خطة — لا يظهر فيه معرّف المريض."""
    owner = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=owner)).json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/submit", headers=owner)

    headers = await login(client, specialist_user.email)
    await client.post(f"/api/v1/plans/{plan_id}/approve", json={}, headers=headers)

    entries = (
        await client.get(f"/api/v1/specialist/patients/{patient_user.id}/audit", headers=headers)
    ).json()

    assert any(entry["action"] == "plan.approved" for entry in entries)


# ------------------------------------------------------------------ ملاحظات
async def test_notes_are_written_and_read_back(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    headers = await login(client, specialist_user.email)

    created = await client.post(
        f"/api/v1/specialist/patients/{patient_user.id}/notes",
        json={"note": "زيادة البروتين تدريجيًا", "is_internal": True},
        headers=headers,
    )
    listed = await client.get(
        f"/api/v1/specialist/patients/{patient_user.id}/notes", headers=headers
    )

    assert created.status_code == 201
    assert listed.json()[0]["note"] == "زيادة البروتين تدريجيًا"
    assert listed.json()[0]["is_internal"] is True


async def test_an_empty_note_is_rejected(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    headers = await login(client, specialist_user.email)

    response = await client.post(
        f"/api/v1/specialist/patients/{patient_user.id}/notes",
        json={"note": ""},
        headers=headers,
    )

    assert response.status_code == 422


async def test_a_note_cannot_be_attached_to_another_patients_plan(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    owner = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=owner)).json()["id"]

    other = await make_patient("other.note@example.com")
    await assign_specialist(session, specialist_user, other)
    headers = await login(client, specialist_user.email)

    response = await client.post(
        f"/api/v1/specialist/patients/{other.id}/notes",
        json={"note": "ملاحظة", "plan_id": plan_id},
        headers=headers,
    )

    assert response.status_code == 404


# -------------------------------------------------------------------- العزل
async def test_the_new_routes_keep_the_isolation(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    """كل مسار جديد يقرأ بيانات مريض يجب أن يمر بنفس الحاجز."""
    await onboard_patient(client, patient_user, session)
    headers = await login(client, specialist_user.email)  # بلا إسناد

    for path in ("profile", "logs", "notes", "audit"):
        response = await client.get(
            f"/api/v1/specialist/patients/{patient_user.id}/{path}", headers=headers
        )
        assert response.status_code == 404, path

    posted = await client.post(
        f"/api/v1/specialist/patients/{patient_user.id}/notes",
        json={"note": "محاولة"},
        headers=headers,
    )
    assert posted.status_code == 404


async def test_a_patient_cannot_reach_the_specialist_dashboard(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)

    assert (await client.get("/api/v1/specialist/patients", headers=headers)).status_code == 403
    assert (
        await client.get(f"/api/v1/specialist/patients/{patient_user.id}/audit", headers=headers)
    ).status_code == 403


async def test_an_unassigned_patient_is_absent_from_the_list(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    await onboard_patient(client, patient_user, session)
    hidden = await make_patient("hidden@example.com")
    await assign_specialist(session, specialist_user, hidden)
    headers = await login(client, specialist_user.email)

    patients = (await client.get("/api/v1/specialist/patients", headers=headers)).json()

    assert [entry["id"] for entry in patients] == [str(hidden.id)]
