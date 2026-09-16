"""R02 서버 기동·설정·SQLite 초기화 회귀 테스트."""

from pathlib import Path

import aiosqlite
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.database import database_connection, database_path_from_url, initialize_database
from app.main import create_app


def test_settings_reject_placeholder_secret() -> None:
    """예시 JWT 키로 서버가 기동하지 않는지 확인합니다."""

    with pytest.raises(ValidationError):
        Settings(_env_file=None, secret_key="your_super_secret_jwt_key_here")


@pytest.mark.parametrize(
    ("app_env", "ai_mode", "api_key"),
    [
        ("test", "real", ""),
        ("production", "mock", "real-looking-key"),
        ("production", "auto", "your_codessey_api_key"),
    ],
)
def test_settings_reject_unsafe_ai_mode(
    app_env: str,
    ai_mode: str,
    api_key: str,
) -> None:
    """실모드와 운영모드의 조용한 Mock 전환을 거부합니다."""

    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            secret_key="test-only-secret-key-that-is-long-enough",
            app_env=app_env,
            ai_mode=ai_mode,
            codessey_api_key=api_key,
        )


async def test_database_initialization_enables_wal_fk_and_index(
    test_settings: Settings,
) -> None:
    """스키마·인덱스와 연결별 안전 PRAGMA를 검사합니다."""

    await initialize_database(test_settings)
    async with database_connection(test_settings) as connection:
        journal_row = await (await connection.execute("PRAGMA journal_mode")).fetchone()
        foreign_key_row = await (await connection.execute("PRAGMA foreign_keys")).fetchone()
        tables = await (
            await connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            )
        ).fetchall()
        indexes = await (
            await connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' ORDER BY name"
            )
        ).fetchall()

    assert journal_row[0].lower() == "wal"
    assert foreign_key_row[0] == 1
    assert {row[0] for row in tables} >= {"users", "chat_logs"}
    assert "idx_chat_logs_user_id_id" in {row[0] for row in indexes}


async def test_reinitialization_preserves_existing_user(test_settings: Settings) -> None:
    """재기동 초기화가 저장된 행을 삭제하지 않는지 확인합니다."""

    await initialize_database(test_settings)
    async with database_connection(test_settings) as connection:
        await connection.execute(
            "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
            ("preserved", "not-a-real-hash"),
        )
        await connection.commit()

    await initialize_database(test_settings)
    async with database_connection(test_settings) as connection:
        row = await (
            await connection.execute(
                "SELECT username FROM users WHERE username = ?",
                ("preserved",),
            )
        ).fetchone()

    assert row[0] == "preserved"


def test_health_contract_and_static_boundary(test_settings: Settings) -> None:
    """헬스 body와 저장소 비공개 경계를 HTTP 수준에서 확인합니다."""

    with TestClient(create_app(test_settings)) as client:
        health = client.get("/api/health")
        root = client.get("/")
        env_file = client.get("/.env")
        database_file = client.get("/data/chatbot.db")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert health.headers["X-AI-Mode"] == "mock"
    assert root.status_code == 503
    assert root.json() == {"detail": "프론트엔드가 아직 준비되지 않았습니다."}
    assert env_file.status_code == 404
    assert database_file.status_code == 404


def test_database_url_resolves_to_configured_file(test_settings: Settings) -> None:
    """설정 URL이 의도한 임시 파일 하나를 가리키는지 확인합니다."""

    path = database_path_from_url(test_settings.database_url)
    assert path.name == "chatbot.test.db"
    assert path.parent.exists() or path.parent.parent.exists()
