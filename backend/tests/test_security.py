"""اختبارات وحدات الأمان: التجزئة والرموز."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    ALGORITHM,
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    password_needs_rehash,
    verify_password,
)
from app.models.user import UserRole

PASSWORD = "CorrectHorseBattery1!"


# ------------------------------------------------------------------ passwords
def test_hash_uses_argon2() -> None:
    assert hash_password(PASSWORD).startswith("$argon2")


def test_same_password_hashes_differently_each_time() -> None:
    """الملح العشوائي يمنع كشف تطابق كلمات السر بين حسابين."""
    assert hash_password(PASSWORD) != hash_password(PASSWORD)


def test_correct_password_verifies() -> None:
    assert verify_password(PASSWORD, hash_password(PASSWORD)) is True


def test_wrong_password_does_not_verify() -> None:
    assert verify_password("WrongPassword1!", hash_password(PASSWORD)) is False


def test_malformed_hash_is_rejected_without_raising() -> None:
    assert verify_password(PASSWORD, "not-a-valid-hash") is False


def test_needs_rehash_is_false_for_current_parameters() -> None:
    assert password_needs_rehash(hash_password(PASSWORD)) is False


def test_needs_rehash_is_true_for_unreadable_hash() -> None:
    assert password_needs_rehash("garbage") is True


# --------------------------------------------------------------------- tokens
def test_access_token_round_trip() -> None:
    user_id = uuid.uuid4()

    token, expires_at = create_access_token(user_id, UserRole.SPECIALIST)
    payload = decode_token(token, expected_type="access")

    assert payload.user_id == user_id
    assert payload.role is UserRole.SPECIALIST
    assert payload.token_type == "access"
    assert expires_at > datetime.now(UTC)


def test_refresh_token_carries_the_supplied_jti() -> None:
    jti = uuid.uuid4()

    token, _ = create_refresh_token(uuid.uuid4(), UserRole.PATIENT, jti)

    assert decode_token(token, expected_type="refresh").jti == jti


def test_token_type_mismatch_is_rejected() -> None:
    token, _ = create_access_token(uuid.uuid4(), UserRole.PATIENT)

    with pytest.raises(InvalidTokenError):
        decode_token(token, expected_type="refresh")


def test_token_signed_with_another_key_is_rejected() -> None:
    forged = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "role": "admin",
            "type": "access",
            "jti": str(uuid.uuid4()),
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
        },
        "an_attacker_supplied_key_that_is_long_enough",
        algorithm=ALGORITHM,
    )

    with pytest.raises(InvalidTokenError):
        decode_token(forged, expected_type="access")


def test_expired_token_is_rejected() -> None:
    settings = get_settings()
    past = datetime.now(UTC) - timedelta(hours=2)
    expired = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "role": "patient",
            "type": "access",
            "jti": str(uuid.uuid4()),
            "iat": int(past.timestamp()),
            "exp": int((past + timedelta(minutes=1)).timestamp()),
        },
        settings.secret_key.get_secret_value(),
        algorithm=ALGORITHM,
    )

    with pytest.raises(InvalidTokenError):
        decode_token(expired, expected_type="access")


def test_token_missing_required_claims_is_rejected() -> None:
    settings = get_settings()
    incomplete = jwt.encode(
        {"sub": str(uuid.uuid4()), "type": "access"},
        settings.secret_key.get_secret_value(),
        algorithm=ALGORITHM,
    )

    with pytest.raises(InvalidTokenError):
        decode_token(incomplete, expected_type="access")


def test_token_with_unknown_role_is_rejected() -> None:
    settings = get_settings()
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "role": "superuser",
            "type": "access",
            "jti": str(uuid.uuid4()),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        },
        settings.secret_key.get_secret_value(),
        algorithm=ALGORITHM,
    )

    with pytest.raises(InvalidTokenError):
        decode_token(token, expected_type="access")
