"""Tests for auth utilities."""

from app.services.auth import (
    create_access_token,
    decode_access_token,
    generate_api_key,
    generate_invite_code,
    hash_api_key,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_token_roundtrip():
    token = create_access_token({"sub": "user-123"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"


def test_invalid_jwt():
    payload = decode_access_token("invalid.token.here")
    assert payload is None


def test_api_key_generation():
    key = generate_api_key()
    assert len(key) == 64  # 32 bytes hex


def test_api_key_hash():
    key = generate_api_key()
    h1 = hash_api_key(key)
    h2 = hash_api_key(key)
    assert h1 == h2
    assert h1 != key


def test_invite_code():
    code = generate_invite_code()
    assert len(code) == 8
