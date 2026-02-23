"""Authentication helpers: password hashing, JWT tokens, API key hashing."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings

_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a random 32-byte hex API key."""
    return secrets.token_hex(32)


def hash_api_key(key: str) -> str:
    """SHA-256 hash of an API key (for storage)."""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_invite_code() -> str:
    """Generate an 8-character alphanumeric invite code."""
    return secrets.token_urlsafe(6)[:8]
