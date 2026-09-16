"""aiosqlite 연결, 스키마 생성, 트랜잭션 기반을 제공합니다."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3

import aiosqlite

from app.config import Settings
from app.models import UserRow


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    latency_ms INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_logs_user_id_id
ON chat_logs(user_id, id);
"""


class DuplicateUsernameError(Exception):
    """동일한 아이디의 등록 경쟁을 안전하게 구분합니다."""


def database_path_from_url(database_url: str) -> Path:
    """SQLite URL에서 현재 작업 폴더 기준 파일 경로를 계산합니다."""

    raw_path = database_url.removeprefix("sqlite:///")
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


async def open_database(settings: Settings) -> aiosqlite.Connection:
    """공통 PRAGMA를 적용한 새 데이터베이스 연결을 엽니다."""

    path = database_path_from_url(settings.database_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = await aiosqlite.connect(path)
    connection.row_factory = aiosqlite.Row
    await connection.execute("PRAGMA foreign_keys = ON")
    await connection.execute("PRAGMA busy_timeout = 3000")
    return connection


@asynccontextmanager
async def database_connection(settings: Settings) -> AsyncIterator[aiosqlite.Connection]:
    """연결을 항상 닫는 비동기 컨텍스트 관리자를 제공합니다."""

    connection = await open_database(settings)
    try:
        yield connection
    finally:
        await connection.close()


async def initialize_database(settings: Settings) -> None:
    """기존 데이터를 지우지 않고 WAL과 필수 스키마를 준비합니다."""

    async with database_connection(settings) as connection:
        await connection.execute("PRAGMA journal_mode = WAL")
        await connection.executescript(SCHEMA_SQL)
        await connection.commit()


async def create_user(
    settings: Settings,
    username: str,
    hashed_password: str,
) -> UserRow:
    """사용자를 저장하고 UNIQUE 충돌과 일반 DB 오류를 구분합니다."""

    async with database_connection(settings) as connection:
        try:
            cursor = await connection.execute(
                "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
                (username, hashed_password),
            )
            row = await (
                await connection.execute(
                    """
                    SELECT id, username, hashed_password, created_at
                    FROM users
                    WHERE id = ?
                    """,
                    (cursor.lastrowid,),
                )
            ).fetchone()
            if row is None:
                raise aiosqlite.DatabaseError("저장된 사용자 행을 다시 찾을 수 없습니다.")
            await connection.commit()
        except aiosqlite.IntegrityError as exc:
            await connection.rollback()
            if getattr(exc, "sqlite_errorcode", None) == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
                raise DuplicateUsernameError from exc
            raise
        except aiosqlite.Error:
            await connection.rollback()
            raise

    return UserRow(**dict(row))


async def get_user_by_username(settings: Settings, username: str) -> UserRow | None:
    """정확한 대소문자의 아이디로 사용자 한 명을 조회합니다."""

    async with database_connection(settings) as connection:
        row = await (
            await connection.execute(
                """
                SELECT id, username, hashed_password, created_at
                FROM users
                WHERE username = ?
                """,
                (username,),
            )
        ).fetchone()
    return UserRow(**dict(row)) if row is not None else None
