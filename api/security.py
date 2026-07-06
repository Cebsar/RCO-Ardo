from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from api.config import SecuritySettings, get_security_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    auth_type: str


def _b64encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _b64decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding)


def _sign(message: str, secret_key: str) -> str:
    digest = hmac.new(secret_key.encode("utf-8"), message.encode("ascii"), hashlib.sha256).digest()
    return _b64encode(digest)


def create_access_token(subject: str, settings: SecuritySettings | None = None) -> str:
    resolved = settings or get_security_settings()
    if resolved.algorithm != "HS256":
        raise ValueError("Only HS256 is supported by the API security foundation")

    now = datetime.now(UTC)
    header = {"alg": resolved.algorithm, "typ": "JWT"}
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=resolved.access_token_expire_minutes)).timestamp()),
        "type": "access",
    }
    signing_input = ".".join(
        [
            _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    return f"{signing_input}.{_sign(signing_input, resolved.secret_key)}"


def decode_access_token(token: str, settings: SecuritySettings | None = None) -> dict[str, Any]:
    resolved = settings or get_security_settings()
    try:
        header_b64, payload_b64, signature = token.split(".", maxsplit=2)
        signing_input = f"{header_b64}.{payload_b64}"
        expected_signature = _sign(signing_input, resolved.secret_key)
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token signature")
        header = json.loads(_b64decode(header_b64))
        payload = json.loads(_b64decode(payload_b64))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token") from exc

    if header.get("alg") != resolved.algorithm or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")
    if int(payload.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token expired")
    return payload


def verify_password(username: str, password: str, settings: SecuritySettings | None = None) -> bool:
    resolved = settings or get_security_settings()
    expected = resolved.auth_users.get(username)
    if not expected:
        return False
    if expected.startswith("sha256$"):
        digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(expected.removeprefix("sha256$"), digest)
    return hmac.compare_digest(expected, password)


def require_principal(
    bearer_token: str | None = Security(oauth2_scheme),
    api_key: str | None = Security(api_key_header),
) -> Principal:
    settings = get_security_settings()
    if api_key and api_key in settings.internal_api_keys:
        return Principal(subject="internal-service", auth_type="api_key")
    if bearer_token:
        payload = decode_access_token(bearer_token, settings)
        subject = str(payload.get("sub") or "")
        if subject:
            return Principal(subject=subject, auth_type="jwt")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
