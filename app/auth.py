"""비밀번호 해시와 이후 JWT 인증에서 공유할 보안 유틸리티."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Annotated

import aiosqlite
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.hash import bcrypt_sha256

from app.config import Settings
from app.database import get_user_by_username
from app.logger import log_request_received
from app.models import UserRow
from app.schemas import TokenData


DEFAULT_BCRYPT_ROUNDS = 12
DUMMY_PASSWORD_HASH = (
    "$bcrypt-sha256$v=2,t=2b,r=12$l82mD5/A9FII7oJ5Vw0RYO$"
    "fVHN0hfzax1ezlB/vsl3oW.hYhSpDVq"
)
bearer_scheme = HTTPBearer(auto_error=False)


class PasswordHashError(RuntimeError):
    """저장 해시 형식이나 해시 backend 자체의 장애를 나타냅니다."""


def _hash_password_sync(password: str, rounds: int) -> str:
    """스레드 경계 안에서 bcrypt 기반 해시를 계산합니다."""

    return bcrypt_sha256.using(rounds=rounds, version=2).hash(password)


def _verify_password_sync(password: str, hashed_password: str) -> bool:
    """스레드 경계 안에서 비밀번호와 저장 해시를 비교합니다."""

    try:
        return bcrypt_sha256.verify(password, hashed_password)
    except (TypeError, ValueError) as exc:
        raise PasswordHashError("비밀번호 해시를 검증할 수 없습니다.") from exc


async def hash_password(password: str, *, rounds: int = DEFAULT_BCRYPT_ROUNDS) -> str:
    """UTF-8 전체 입력을 자르지 않고 bcrypt_sha256 v2로 해시합니다."""

    return await asyncio.to_thread(_hash_password_sync, password, rounds)


async def verify_password(password: str, hashed_password: str) -> bool:
    """이벤트 루프를 막지 않고 저장된 해시를 검증합니다."""

    return await asyncio.to_thread(_verify_password_sync, password, hashed_password)


def create_access_token(
    username: str,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> str:
    """사용자 아이디와 발급·만료시각을 포함한 HS256 JWT를 만듭니다."""

    issued_at = now or datetime.now(timezone.utc)
    if issued_at.tzinfo is None or issued_at.utcoffset() is None:
        raise ValueError("JWT 발급 시각은 시간대 정보가 있어야 합니다.")
    expires_at = issued_at + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": username,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str, settings: Settings) -> TokenData:
    """서명·알고리즘·필수 claims·시간 범위를 검증합니다."""

    try:
        claims = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            options={"require_sub": True, "require_iat": True, "require_exp": True},
        )
    except (TypeError, ValueError) as exc:
        raise JWTError("JWT claim 형식이 올바르지 않습니다.") from exc
    subject = claims.get("sub")
    issued_at = claims.get("iat")
    expires_at = claims.get("exp")
    current_timestamp = int(datetime.now(timezone.utc).timestamp())

    if not isinstance(subject, str) or not subject.strip():
        raise JWTError("subject claim이 올바르지 않습니다.")
    if isinstance(issued_at, bool) or not isinstance(issued_at, (int, float)):
        raise JWTError("issued-at claim이 올바르지 않습니다.")
    if isinstance(expires_at, bool) or not isinstance(expires_at, (int, float)):
        raise JWTError("expiration claim이 올바르지 않습니다.")
    if (
        issued_at > current_timestamp + 60
        or expires_at <= issued_at
        or expires_at <= current_timestamp
    ):
        raise JWTError("토큰 시간 범위가 올바르지 않습니다.")
    return TokenData(username=subject)


def invalid_token_error() -> HTTPException:
    """보호 API의 모든 인증 실패에 동일한 401 응답을 만듭니다."""

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 토큰이 유효하지 않거나 만료되었습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> UserRow:
    """Bearer 토큰과 실제 DB 사용자 존재를 모두 확인합니다."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        log_request_received("anonymous", request.url.path)
        raise invalid_token_error()

    settings: Settings = request.app.state.settings
    try:
        token_data = decode_access_token(credentials.credentials, settings)
    except JWTError as exc:
        log_request_received("anonymous", request.url.path)
        raise invalid_token_error() from exc

    if token_data.username is None:
        log_request_received("anonymous", request.url.path)
        raise invalid_token_error()
    try:
        user = await get_user_by_username(settings, token_data.username)
    except aiosqlite.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인증 정보를 확인하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc
    if user is None:
        log_request_received("anonymous", request.url.path)
        raise invalid_token_error()
    return user
