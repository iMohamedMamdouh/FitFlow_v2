"""اختبارات المرفقات الطبية وقاعدة الأنواع (الخطوة 7.5).

رفع الملفات هو المدخل الوحيد في النظام الذي يقبل بايتات عشوائية من
المستخدم ويعيد تقديمها لاحقًا. الاختبارات هنا تغطي الثلاثة التي تهم:
**ماذا يُقبل**، و**من يستطيع القراءة**، و**ما الذي لا يظهر في الرد**.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AttachmentType, BodyRegion
from app.core.security import hash_password
from app.models.catalog import InjuryType
from app.models.clinical import InjuryAttachment
from app.models.user import User, UserRole
from tests.conftest import TEST_PASSWORD, SessionFactory, login

# أصغر ملفات صالحة ممكنة: بادئة التوقيع تكفي لأن الفحص يقرأ البداية فقط.
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 32
PDF = b"%PDF-1.7\n" + b"\x00" * 32


async def make_injury_type(slug: str = "acl-tear") -> InjuryType:
    async with SessionFactory() as session:
        injury_type = InjuryType(
            slug=slug,
            name_ar="قطع الرباط الصليبي الأمامي",
            body_region=BodyRegion.KNEE,
        )
        session.add(injury_type)
        await session.commit()
        await session.refresh(injury_type)
        return injury_type


async def record_injury(client: AsyncClient, headers: dict[str, str]) -> str:
    injury_type = await make_injury_type()
    response = await client.post(
        "/api/v1/me/injuries",
        json={
            "injury_type_id": str(injury_type.id),
            "injury_date": date.today().isoformat(),
            "pain_level": 6,
            "side": "left",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


# ------------------------------------------------------------ قاعدة الأنواع
async def test_injury_types_are_listed_for_the_form(
    client: AsyncClient, patient_user: User
) -> None:
    injury_type = await make_injury_type()
    headers = await login(client, patient_user.email)

    response = await client.get("/api/v1/catalog/injury-types", headers=headers)

    assert response.status_code == 200
    assert [entry["slug"] for entry in response.json()] == [injury_type.slug]


async def test_unreviewed_content_is_flagged_in_the_response(
    client: AsyncClient, patient_user: User
) -> None:
    """المحتوى غير المراجَع لازم يصل للواجهة موسومًا (ADR-003)."""
    await make_injury_type()
    headers = await login(client, patient_user.email)

    entry = (await client.get("/api/v1/catalog/injury-types", headers=headers)).json()[0]

    assert entry["is_clinically_reviewed"] is False


async def test_injury_types_can_be_filtered_by_region(
    client: AsyncClient, patient_user: User
) -> None:
    await make_injury_type()
    headers = await login(client, patient_user.email)

    knee = await client.get("/api/v1/catalog/injury-types?body_region=knee", headers=headers)
    ankle = await client.get("/api/v1/catalog/injury-types?body_region=ankle", headers=headers)

    assert len(knee.json()) == 1
    assert ankle.json() == []


async def test_catalog_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/catalog/injury-types")).status_code == 401


# ------------------------------------------------------------------- الرفع
@pytest.mark.parametrize(
    ("payload", "expected_type"),
    [
        (JPEG, "image/jpeg"),
        (PNG, "image/png"),
        (WEBP, "image/webp"),
        (PDF, "application/pdf"),
    ],
)
async def test_supported_formats_are_accepted(
    client: AsyncClient, patient_user: User, payload: bytes, expected_type: str
) -> None:
    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)

    response = await client.post(
        f"/api/v1/me/injuries/{injury_id}/attachments",
        files={"file": ("scan.bin", payload, "application/octet-stream")},
        headers=headers,
    )

    assert response.status_code == 201, response.text
    assert response.json()["content_type"] == expected_type
    assert response.json()["size_bytes"] == len(payload)


async def test_content_type_comes_from_the_bytes_not_the_header(
    client: AsyncClient, patient_user: User
) -> None:
    """ترويسة الملف قيمة يرسلها العميل — المحتوى هو الحكم."""
    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)

    response = await client.post(
        f"/api/v1/me/injuries/{injury_id}/attachments",
        files={"file": ("x.png", JPEG, "image/png")},
        headers=headers,
    )

    assert response.json()["content_type"] == "image/jpeg"


async def test_a_script_renamed_to_png_is_rejected(client: AsyncClient, patient_user: User) -> None:
    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)

    response = await client.post(
        f"/api/v1/me/injuries/{injury_id}/attachments",
        files={"file": ("evil.png", b"<script>alert(1)</script>", "image/png")},
        headers=headers,
    )

    assert response.status_code == 422
    assert "غير مدعوم" in response.json()["detail"]


async def test_a_riff_file_that_is_not_webp_is_rejected(
    client: AsyncClient, patient_user: User
) -> None:
    """RIFF بادئة مشتركة مع WAV وAVI — البادئة وحدها لا تكفي."""
    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)

    response = await client.post(
        f"/api/v1/me/injuries/{injury_id}/attachments",
        files={"file": ("sound.webp", b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 32, "image/webp")},
        headers=headers,
    )

    assert response.status_code == 422


async def test_an_empty_file_is_rejected(client: AsyncClient, patient_user: User) -> None:
    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)

    response = await client.post(
        f"/api/v1/me/injuries/{injury_id}/attachments",
        files={"file": ("empty.png", b"", "image/png")},
        headers=headers,
    )

    assert response.status_code == 422


async def test_an_oversized_file_is_rejected(client: AsyncClient, patient_user: User) -> None:
    from app.core.config import get_settings

    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)
    oversized = PNG + b"\x00" * (get_settings().max_upload_mb * 1024 * 1024)

    response = await client.post(
        f"/api/v1/me/injuries/{injury_id}/attachments",
        files={"file": ("big.png", oversized, "image/png")},
        headers=headers,
    )

    assert response.status_code == 422
    assert "الحد المسموح" in response.json()["detail"]


async def test_the_file_type_can_be_declared(client: AsyncClient, patient_user: User) -> None:
    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)

    response = await client.post(
        f"/api/v1/me/injuries/{injury_id}/attachments",
        files={"file": ("mri.png", PNG, "image/png")},
        data={"file_type": AttachmentType.MRI.value},
        headers=headers,
    )

    assert response.json()["file_type"] == "mri"


async def test_a_pdf_defaults_to_a_report(client: AsyncClient, patient_user: User) -> None:
    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)

    response = await client.post(
        f"/api/v1/me/injuries/{injury_id}/attachments",
        files={"file": ("report.pdf", PDF, "application/pdf")},
        headers=headers,
    )

    assert response.json()["file_type"] == "report"


async def test_the_storage_key_never_reaches_the_client(
    client: AsyncClient, patient_user: User
) -> None:
    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)

    body = (
        await client.post(
            f"/api/v1/me/injuries/{injury_id}/attachments",
            files={"file": ("scan.png", PNG, "image/png")},
            headers=headers,
        )
    ).json()

    assert "storage_key" not in body


async def test_the_original_filename_is_not_used_in_the_storage_key(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    """اسم الملف مدخل نصي من المستخدم — لا يدخل مسارًا على القرص أبدًا."""
    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)

    await client.post(
        f"/api/v1/me/injuries/{injury_id}/attachments",
        files={"file": ("../../../etc/passwd.png", PNG, "image/png")},
        headers=headers,
    )

    key = await session.scalar(select(InjuryAttachment.storage_key))
    assert key is not None
    assert ".." not in key
    assert key.startswith(f"injuries/{injury_id}/")


# ---------------------------------------------------------------- القراءة
async def test_the_owner_can_download_what_they_uploaded(
    client: AsyncClient, patient_user: User
) -> None:
    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)
    attachment_id = (
        await client.post(
            f"/api/v1/me/injuries/{injury_id}/attachments",
            files={"file": ("scan.png", PNG, "image/png")},
            headers=headers,
        )
    ).json()["id"]

    response = await client.get(
        f"/api/v1/me/injuries/{injury_id}/attachments/{attachment_id}/content",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.content == PNG
    # التنزيل لا العرض: عرض ملف رفعه مستخدم داخل نطاق التطبيق ثغرة XSS مخزَّنة.
    assert response.headers["content-disposition"].startswith("attachment;")
    assert response.headers["x-content-type-options"] == "nosniff"


async def test_attachments_are_listed_for_their_injury(
    client: AsyncClient, patient_user: User
) -> None:
    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)
    for payload in (PNG, JPEG):
        await client.post(
            f"/api/v1/me/injuries/{injury_id}/attachments",
            files={"file": ("scan.bin", payload, "application/octet-stream")},
            headers=headers,
        )

    listed = (
        await client.get(f"/api/v1/me/injuries/{injury_id}/attachments", headers=headers)
    ).json()

    assert len(listed) == 2


# ----------------------------------------------------------------- العزل
async def make_other_patient() -> User:
    async with SessionFactory() as session:
        user = User(
            email="intruder@example.com",
            password_hash=hash_password(TEST_PASSWORD),
            full_name="مريض آخر",
            role=UserRole.PATIENT,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def test_another_patient_cannot_reach_the_attachment(
    client: AsyncClient, patient_user: User
) -> None:
    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)
    attachment_id = (
        await client.post(
            f"/api/v1/me/injuries/{injury_id}/attachments",
            files={"file": ("scan.png", PNG, "image/png")},
            headers=headers,
        )
    ).json()["id"]

    intruder = await make_other_patient()
    intruder_headers = await login(client, intruder.email)

    listing = await client.get(
        f"/api/v1/me/injuries/{injury_id}/attachments", headers=intruder_headers
    )
    download = await client.get(
        f"/api/v1/me/injuries/{injury_id}/attachments/{attachment_id}/content",
        headers=intruder_headers,
    )

    assert listing.status_code == download.status_code == 404


async def test_another_patient_cannot_upload_onto_someone_elses_injury(
    client: AsyncClient, patient_user: User
) -> None:
    headers = await login(client, patient_user.email)
    injury_id = await record_injury(client, headers)

    intruder = await make_other_patient()
    intruder_headers = await login(client, intruder.email)

    response = await client.post(
        f"/api/v1/me/injuries/{injury_id}/attachments",
        files={"file": ("scan.png", PNG, "image/png")},
        headers=intruder_headers,
    )

    assert response.status_code == 404


async def test_an_attachment_of_another_injury_is_not_reachable(
    client: AsyncClient, patient_user: User
) -> None:
    """المعرّفان لازم يتطابقا — إصابة يملكها المستخدم لا تفتح كل المرفقات."""
    headers = await login(client, patient_user.email)
    first = await record_injury(client, headers)
    attachment_id = (
        await client.post(
            f"/api/v1/me/injuries/{first}/attachments",
            files={"file": ("scan.png", PNG, "image/png")},
            headers=headers,
        )
    ).json()["id"]

    injury_type = await make_injury_type("meniscus-tear")
    second = (
        await client.post(
            "/api/v1/me/injuries",
            json={
                "injury_type_id": str(injury_type.id),
                "injury_date": date.today().isoformat(),
                "pain_level": 3,
            },
            headers=headers,
        )
    ).json()["id"]

    response = await client.get(
        f"/api/v1/me/injuries/{second}/attachments/{attachment_id}/content",
        headers=headers,
    )

    assert response.status_code == 404


async def test_an_unknown_injury_returns_not_found(client: AsyncClient, patient_user: User) -> None:
    headers = await login(client, patient_user.email)

    response = await client.get(f"/api/v1/me/injuries/{uuid.uuid4()}/attachments", headers=headers)

    assert response.status_code == 404


async def test_upload_requires_authentication(client: AsyncClient) -> None:
    response = await client.post(
        f"/api/v1/me/injuries/{uuid.uuid4()}/attachments",
        files={"file": ("scan.png", PNG, "image/png")},
    )

    assert response.status_code == 401
