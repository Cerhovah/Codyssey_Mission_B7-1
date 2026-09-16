"""비밀번호 해시와 이후 JWT 인증에서 공유할 보안 유틸리티."""

import asyncio

from passlib.hash import bcrypt_sha256


DEFAULT_BCRYPT_ROUNDS = 12


def _hash_password_sync(password: str, rounds: int) -> str:
    """스레드 경계 안에서 bcrypt 기반 해시를 계산합니다."""

    return bcrypt_sha256.using(rounds=rounds, version=2).hash(password)


def _verify_password_sync(password: str, hashed_password: str) -> bool:
    """스레드 경계 안에서 비밀번호와 저장 해시를 비교합니다."""

    try:
        return bcrypt_sha256.verify(password, hashed_password)
    except (TypeError, ValueError):
        return False


async def hash_password(password: str, *, rounds: int = DEFAULT_BCRYPT_ROUNDS) -> str:
    """UTF-8 전체 입력을 자르지 않고 bcrypt_sha256 v2로 해시합니다."""

    return await asyncio.to_thread(_hash_password_sync, password, rounds)


async def verify_password(password: str, hashed_password: str) -> bool:
    """이벤트 루프를 막지 않고 저장된 해시를 검증합니다."""

    return await asyncio.to_thread(_verify_password_sync, password, hashed_password)
