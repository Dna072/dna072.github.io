from __future__ import annotations

import jwt
import pytest
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("supersecret1")
    assert hashed != "supersecret1"
    assert verify_password("supersecret1", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_encodes_subject_and_type():
    token = create_access_token("user-123")
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_refresh_token_type_enforced():
    token = create_refresh_token("user-123")
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, expected_type="access")


def test_tampered_token_rejected():
    token = create_access_token("user-123")
    with pytest.raises(jwt.PyJWTError):
        decode_token(token + "tamper", expected_type="access")
