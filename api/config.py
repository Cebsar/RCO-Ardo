from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class SecuritySettings:
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    auth_users: dict[str, str]
    internal_api_keys: set[str]
    cors_allow_origins: list[str]
    cors_allow_credentials: bool
    cors_allow_methods: list[str]
    cors_allow_headers: list[str]

    @classmethod
    def from_env(cls) -> "SecuritySettings":
        users: dict[str, str] = {}
        for item in _split_csv(os.getenv("API_AUTH_USERS")):
            username, separator, password = item.partition(":")
            if separator and username.strip() and password:
                users[username.strip()] = password

        return cls(
            secret_key=os.getenv("API_SECRET_KEY", "development-only-change-me"),
            algorithm=os.getenv("API_JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("API_ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
            auth_users=users,
            internal_api_keys=set(_split_csv(os.getenv("API_INTERNAL_API_KEYS"))),
            cors_allow_origins=_split_csv(os.getenv("API_CORS_ALLOW_ORIGINS")) or ["http://localhost:3000"],
            cors_allow_credentials=os.getenv("API_CORS_ALLOW_CREDENTIALS", "true").lower() == "true",
            cors_allow_methods=_split_csv(os.getenv("API_CORS_ALLOW_METHODS")) or ["GET", "POST", "OPTIONS"],
            cors_allow_headers=_split_csv(os.getenv("API_CORS_ALLOW_HEADERS")) or ["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
        )


@lru_cache(maxsize=1)
def get_security_settings() -> SecuritySettings:
    return SecuritySettings.from_env()
