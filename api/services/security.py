from __future__ import annotations

from fastapi import HTTPException, status

from api.config import get_security_settings
from api.schemas.security import TokenResponse
from api.security import create_access_token, verify_password


class SecurityService:
    def issue_token(self, username: str, password: str) -> TokenResponse:
        settings = get_security_settings()
        if not verify_password(username, password, settings):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return TokenResponse(
            access_token=create_access_token(username, settings),
            expires_in=settings.access_token_expire_minutes * 60,
        )
