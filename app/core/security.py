"""Security utilities for password hashing and JWT token handling"""

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from app.core.config import settings

# PBKDF2 parameters
PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 100_000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using PBKDF2-HMAC-SHA256 with a random salt.

    Returns:
        Formatted string: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_bytes(SALT_BYTES)
    key = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a stored PBKDF2-HMAC-SHA256 hash.

    Args:
        plain_password: The plaintext candidate password
        hashed_password: Stored hash string in format pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>

    Returns:
        True if password matches, False otherwise
    """
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False

        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_key = bytes.fromhex(parts[3])

        computed_key = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            plain_password.encode("utf-8"),
            salt,
            iterations
        )
        return hmac.compare_digest(computed_key, expected_key)
    except Exception:
        return False


def _b64url_encode(data: bytes) -> str:
    """Base64 URL encode without padding"""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    """Base64 URL decode with padding restoration"""
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("ascii"))


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token (HS256).

    Args:
        data: Dictionary of claims to encode in payload
        expires_delta: Optional expiration delta. Defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string: <header>.<payload>.<signature>
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    })

    header = {"alg": "HS256", "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_json = json.dumps(to_encode, separators=(",", ":")).encode("utf-8")

    header_b64 = _b64url_encode(header_json)
    payload_b64 = _b64url_encode(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    secret_key = settings.JWT_SECRET_KEY.encode("utf-8")
    signature = hmac.new(secret_key, signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a signed JWT access token (HS256).

    Args:
        token: Encoded JWT string

    Returns:
        Payload dictionary if valid

    Raises:
        ValueError: If token is malformed, signature is invalid, or token has expired
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    header_b64, payload_b64, sig_b64 = parts

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    secret_key = settings.JWT_SECRET_KEY.encode("utf-8")
    expected_sig = hmac.new(secret_key, signing_input, hashlib.sha256).digest()

    try:
        actual_sig = _b64url_decode(sig_b64)
    except Exception:
        raise ValueError("Invalid signature encoding")

    if not hmac.compare_digest(actual_sig, expected_sig):
        raise ValueError("Invalid token signature")

    try:
        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        raise ValueError("Invalid token payload")

    exp = payload.get("exp")
    if exp is not None:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        if now_ts > exp:
            raise ValueError("Token has expired")

    return payload
