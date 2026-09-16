"""R17 실제 SQLite INSERT·COMMIT 실패와 rollback·복구 검증."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import logging

import aiosqlite
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.logger import app_logger
from app.main import create_app


DB_FAILURE_DETAIL = "대화 기록을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요."
INSERT_TRIGGER = "test_fail_chat_log_insert"


class ListHandler(logging.Handler):
    """전파를 끈 앱 로거의 레코드를 테스트 안에서 수집합니다."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@dataclass
class TransactionProbe:
    """실제 연결의 INSERT·COMMIT·rollback 관찰값을 보관합니다."""

    failure_kind: str
    failed_question: str
    insert_attempts: int = 0
    insert_failure_was_in_transaction: bool = False
    commit_failure_injected: bool = False
    uncommitted_row_visible: bool = False
    commit_was_in_transaction: bool = False
    rollback_calls: int = 0
    rollback_before: list[bool] = field(default_factory=list)
    rollback_after: list[bool] = field(default_factory=list)


class ProbedConnection:
    """실제 aiosqlite 연결을 위임하며 commit 한 지점만 선택적으로 실패시킵니다."""

    def __init__(
        self,
        connection: aiosqlite.Connection,
        probe: TransactionProbe,
    ) -> None:
        self._connection = connection
        self._probe = probe
        self._saw_chat_insert = False

    async def execute(self, statement: str, *args: object) -> aiosqlite.Cursor:
        is_chat_insert = "INSERT INTO chat_logs" in statement
        if is_chat_insert:
            self._saw_chat_insert = True
            self._probe.insert_attempts += 1
        try:
            return await self._connection.execute(statement, *args)
        except aiosqlite.Error:
            if is_chat_insert and self._probe.failure_kind == "insert":
                self._probe.insert_failure_was_in_transaction = (
                    self._connection.in_transaction
                )
                row = await (
                    await self._connection.execute(
                        "SELECT 1 FROM chat_logs WHERE question = ?",
                        (self._probe.failed_question,),
                    )
                ).fetchone()
                self._probe.uncommitted_row_visible = row is not None
            raise

    async def commit(self) -> None:
        if (
            self._probe.failure_kind == "commit"
            and self._saw_chat_insert
            and not self._probe.commit_failure_injected
        ):
            self._probe.commit_failure_injected = True
            self._probe.commit_was_in_transaction = self._connection.in_transaction
            row = await (
                await self._connection.execute(
                    "SELECT 1 FROM chat_logs WHERE question = ?",
                    (self._probe.failed_question,),
                )
            ).fetchone()
            self._probe.uncommitted_row_visible = row is not None
            raise aiosqlite.OperationalError("SENSITIVE_COMMIT_FAILURE")
        await self._connection.commit()

    async def rollback(self) -> None:
        self._probe.rollback_calls += 1
        self._probe.rollback_before.append(self._connection.in_transaction)
        await self._connection.rollback()
        self._probe.rollback_after.append(self._connection.in_transaction)

    def __getattr__(self, name: str) -> object:
        return getattr(self._connection, name)


def register_and_login(client: TestClient) -> str:
    register = client.post(
        "/api/auth/register",
        json={"username": "dbfailureuser", "password": "pass1234"},
    )
    assert register.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={"username": "dbfailureuser", "password": "pass1234"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_insert_failure_trigger(
    settings: Settings,
    original_database_connection,
) -> None:
    """임시 테스트 DB의 실제 INSERT가 SQLite에서 실패하도록 합니다."""

    async with original_database_connection(settings) as connection:
        await connection.execute(
            f"""
            CREATE TRIGGER {INSERT_TRIGGER}
            AFTER INSERT ON chat_logs
            BEGIN
                SELECT RAISE(FAIL, 'SENSITIVE_INSERT_FAILURE');
            END
            """
        )
        await connection.commit()


async def drop_insert_failure_trigger(
    settings: Settings,
    original_database_connection,
) -> None:
    """같은 앱의 후속 정상 요청을 위해 테스트 trigger만 제거합니다."""

    async with original_database_connection(settings) as connection:
        await connection.execute(f"DROP TRIGGER {INSERT_TRIGGER}")
        await connection.commit()


async def read_persisted_questions(
    settings: Settings,
    original_database_connection,
) -> list[str]:
    """라우터 응답과 별개로 실제 SQLite의 저장 결과를 확인합니다."""

    async with original_database_connection(settings) as connection:
        rows = await (
            await connection.execute("SELECT question FROM chat_logs ORDER BY id")
        ).fetchall()
    return [row[0] for row in rows]


@pytest.mark.parametrize("failure_kind", ["insert", "commit"])
def test_actual_database_failure_rolls_back_logs_and_recovers(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    failure_kind: str,
) -> None:
    """실제 INSERT/미커밋 행을 실패시켜 500·rollback·0행·복구를 검증합니다."""

    from app import database as database_module

    failed_question = f"DB_SECRET_QUESTION_{failure_kind}"
    recovery_question = f"DB 복구 질문 {failure_kind}"
    probe = TransactionProbe(
        failure_kind=failure_kind,
        failed_question=failed_question,
    )
    original_database_connection = database_module.database_connection
    application = create_app(test_settings)

    with TestClient(application, raise_server_exceptions=False) as client:
        token = register_and_login(client)
        if failure_kind == "insert":
            asyncio.run(
                create_insert_failure_trigger(
                    test_settings,
                    original_database_connection,
                )
            )

        @asynccontextmanager
        async def probed_database_connection(
            settings: Settings,
        ) -> AsyncIterator[ProbedConnection]:
            async with original_database_connection(settings) as connection:
                yield ProbedConnection(connection, probe)

        monkeypatch.setattr(
            database_module,
            "database_connection",
            probed_database_connection,
        )
        log_handler = ListHandler()
        app_logger.addHandler(log_handler)
        try:
            try:
                failed = client.post(
                    "/api/chat",
                    headers=auth_headers(token),
                    json={"question": failed_question},
                )
                empty_history = client.get(
                    "/api/me/chats",
                    headers=auth_headers(token),
                )
            finally:
                if failure_kind == "insert":
                    asyncio.run(
                        drop_insert_failure_trigger(
                            test_settings,
                            original_database_connection,
                        )
                    )
            recovered = client.post(
                "/api/chat",
                headers=auth_headers(token),
                json={"question": recovery_question},
            )
            history = client.get(
                "/api/me/chats",
                headers=auth_headers(token),
            )
        finally:
            app_logger.removeHandler(log_handler)

    persisted_questions = asyncio.run(
        read_persisted_questions(
            test_settings,
            original_database_connection,
        )
    )
    messages = [record.getMessage() for record in log_handler.records]

    assert failed.status_code == 500
    assert failed.json() == {"detail": DB_FAILURE_DETAIL}
    assert empty_history.status_code == 200
    assert empty_history.json() == []
    assert recovered.status_code == 200
    assert recovered.json()["answer"].startswith("[Mock]")
    assert [row["question"] for row in history.json()] == [recovery_question]
    assert persisted_questions == [recovery_question]

    assert probe.insert_attempts == 2
    assert probe.rollback_calls == 1
    assert probe.rollback_after == [False]
    if failure_kind == "commit":
        assert probe.commit_failure_injected is True
        assert probe.commit_was_in_transaction is True
        assert probe.uncommitted_row_visible is True
        assert probe.rollback_before == [True]
    else:
        assert probe.commit_failure_injected is False
        assert probe.insert_failure_was_in_transaction is True
        assert probe.uncommitted_row_visible is True
        assert probe.rollback_before == [True]

    db_failures = [
        message for message in messages if message.startswith("db_save_failed user_id=")
    ]
    db_successes = [
        message for message in messages if message.startswith("db_save_success user_id=")
    ]
    ai_successes = [
        message for message in messages if message.startswith("ai_call_success request_id=")
    ]
    assert len(db_failures) == 1
    assert db_failures[0].endswith("error=database_error")
    assert len(db_successes) == 1
    assert len(ai_successes) == 2

    joined_logs = "\n".join(messages)
    for secret in (
        "SENSITIVE_INSERT_FAILURE",
        "SENSITIVE_COMMIT_FAILURE",
        failed_question,
        token,
        "pass1234",
    ):
        assert secret not in joined_logs
