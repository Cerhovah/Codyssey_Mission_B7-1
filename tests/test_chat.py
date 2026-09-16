"""Mock 채팅·문맥·사용자별 기록·운영 로그 계약 검증."""

import asyncio
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import logging
import re
from threading import Event

import aiosqlite
import pytest
from fastapi.testclient import TestClient

from app.ai_service import AIResult, AIServiceError, AITimeoutError
from app.auth import create_access_token
from app.config import Settings
from app.logger import app_logger
from app.main import create_app


@pytest.fixture
def chat_client(test_settings: Settings) -> Iterator[TestClient]:
    """등록된 기본 사용자가 있는 Mock 채팅 클라이언트를 제공합니다."""

    with TestClient(create_app(test_settings), raise_server_exceptions=False) as client:
        register = client.post(
            "/api/auth/register",
            json={"username": "chatuser", "password": "pass1234"},
        )
        assert register.status_code == 201
        yield client


def register_and_login(client: TestClient, username: str = "chatuser") -> str:
    """필요하면 사용자를 등록하고 로그인 토큰을 반환합니다."""

    if username != "chatuser":
        response = client.post(
            "/api/auth/register",
            json={"username": username, "password": "pass1234"},
        )
        assert response.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={"username": username, "password": "pass1234"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    """Bearer 인증 헤더를 만듭니다."""

    return {"Authorization": f"Bearer {token}"}


def test_protected_chat_and_history_reject_unauthenticated_before_body(
    chat_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """실제 보호 경로가 인증 실패 시 AI와 DB 쓰기를 호출하지 않습니다."""

    async def forbidden_ai(*_args: object, **_kwargs: object) -> AIResult:
        raise AssertionError("미인증 요청은 AI를 호출하면 안 됩니다.")

    async def forbidden_save(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("미인증 요청은 DB 저장을 호출하면 안 됩니다.")

    monkeypatch.setattr("app.routers.chat_router.generate_ai_response", forbidden_ai)
    monkeypatch.setattr("app.routers.chat_router.save_chat_log", forbidden_save)
    responses = [
        chat_client.post("/api/chat", json={"question": "안녕"}),
        chat_client.post("/api/chat", json={}),
        chat_client.get("/api/me/chats"),
    ]

    for response in responses:
        assert response.status_code == 401
        assert response.json() == {"detail": "인증 토큰이 유효하지 않거나 만료되었습니다."}


def test_authentication_precedes_malformed_json_for_invalid_tokens(
    chat_client: TestClient,
    test_settings: Settings,
) -> None:
    """누락·위조·만료 토큰이 JSON 파싱 실패보다 먼저 401을 반환합니다."""

    valid = register_and_login(chat_client)
    header, payload, signature = valid.split(".")
    changed = ("A" if signature[0] != "A" else "B") + signature[1:]
    tampered = ".".join((header, payload, changed))
    expired = create_access_token(
        "chatuser",
        test_settings,
        now=datetime.now(timezone.utc) - timedelta(days=2),
    )
    headers_to_test = [
        {"Content-Type": "application/json"},
        {**auth_headers(tampered), "Content-Type": "application/json"},
        {**auth_headers(expired), "Content-Type": "application/json"},
    ]

    for headers in headers_to_test:
        chat_response = chat_client.post(
            "/api/chat",
            headers=headers,
            content=b'{"question":',
        )
        history_response = chat_client.get("/api/me/chats", headers=headers)
        assert chat_response.status_code == 401
        assert history_response.status_code == 401
        assert chat_response.json() == {
            "detail": "인증 토큰이 유효하지 않거나 만료되었습니다."
        }
        assert chat_response.headers["WWW-Authenticate"] == "Bearer"


def test_mock_chat_returns_exact_body_and_persists_history(
    chat_client: TestClient,
) -> None:
    """인증→Mock→commit→응답→기록 배열의 첫 수직 연결을 확인합니다."""

    token = register_and_login(chat_client)
    response = chat_client.post(
        "/api/chat",
        headers=auth_headers(token),
        json={"question": "안녕?"},
    )
    history = chat_client.get("/api/me/chats", headers=auth_headers(token))

    assert response.status_code == 200
    assert set(response.json()) == {"answer", "latency_ms"}
    assert response.json()["answer"].startswith("[Mock]")
    assert isinstance(response.json()["latency_ms"], int)
    assert response.json()["latency_ms"] >= 0
    assert response.headers["X-AI-Mode"] == "mock"
    assert response.headers["content-type"] == "application/json; charset=utf-8"
    assert history.status_code == 200
    assert isinstance(history.json(), list)
    assert history.json()[0]["question"] == "안녕?"
    assert history.json()[0]["response"] == response.json()["answer"]
    assert "answer" not in history.json()[0]


@pytest.mark.parametrize(
    ("question", "status_code", "detail"),
    [
        ("", 400, "질문 내용은 공백일 수 없습니다."),
        ("   ", 400, "질문 내용은 공백일 수 없습니다."),
        ("가" * 500, 200, None),
        ("가" * 501, 422, "질문은 최대 500자까지 입력 가능합니다."),
        (" " + "가" * 500 + " ", 422, "질문은 최대 500자까지 입력 가능합니다."),
        ("😀" * 500, 200, None),
    ],
)
def test_question_boundaries_use_raw_unicode_length(
    chat_client: TestClient,
    question: str,
    status_code: int,
    detail: str | None,
) -> None:
    """공백·원문 500자·Unicode code point 경계를 구분합니다."""

    token = register_and_login(chat_client)
    response = chat_client.post(
        "/api/chat",
        headers=auth_headers(token),
        json={"question": question},
    )

    assert response.status_code == status_code
    if detail is not None:
        assert response.json() == {"detail": detail}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message": "구형 키"},
        {"question": None},
        {"question": 123},
        {"question": ["배열"]},
    ],
)
def test_chat_malformed_payload_returns_422_string_detail(
    chat_client: TestClient,
    payload: dict[str, object],
) -> None:
    """누락·구형 키·자료형 오류에서 입력 원문이나 배열형 detail을 숨깁니다."""

    token = register_and_login(chat_client)
    response = chat_client.post(
        "/api/chat",
        headers={**auth_headers(token), "Content-Type": "application/json"},
        json=payload,
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "입력 형식을 확인해 주세요."}


def test_chat_invalid_json_returns_422_string_detail(chat_client: TestClient) -> None:
    """JSON 파싱 실패도 프레임워크 상세를 노출하지 않습니다."""

    token = register_and_login(chat_client)
    response = chat_client.post(
        "/api/chat",
        headers={**auth_headers(token), "Content-Type": "application/json"},
        content=b'{"question":',
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "입력 형식을 확인해 주세요."}


def test_chat_invalid_utf8_respects_auth_then_returns_korean_422(
    chat_client: TestClient,
) -> None:
    """잘못된 UTF-8도 미인증 401, 인증 후 안전한 422 순서를 지킵니다."""

    token = register_and_login(chat_client)
    unauthenticated = chat_client.post(
        "/api/chat",
        headers={"Content-Type": "application/json"},
        content=b"\xff",
    )
    authenticated = chat_client.post(
        "/api/chat",
        headers={**auth_headers(token), "Content-Type": "application/json"},
        content=b"\xff",
    )

    assert unauthenticated.status_code == 401
    assert authenticated.status_code == 422
    assert authenticated.json() == {"detail": "입력 형식을 확인해 주세요."}


@pytest.mark.parametrize(
    "content_type",
    [None, "text/plain", "application/json; charset=latin-1"],
)
def test_chat_rejects_non_json_content_type_without_saving(
    chat_client: TestClient,
    content_type: str | None,
) -> None:
    """유효 JSON 문자열이어도 팀 계약이 아닌 media type은 거부합니다."""

    token = register_and_login(chat_client)
    headers = auth_headers(token)
    if content_type is not None:
        headers["Content-Type"] = content_type
    response = chat_client.post(
        "/api/chat",
        headers=headers,
        content=b'{"question":"content type test"}',
    )
    history = chat_client.get("/api/me/chats", headers=auth_headers(token))

    assert response.status_code == 422
    assert response.json() == {"detail": "입력 형식을 확인해 주세요."}
    assert history.json() == []


def test_chat_accepts_explicit_utf8_json_content_type(chat_client: TestClient) -> None:
    """명시적 UTF-8 JSON media type을 정상 처리합니다."""

    token = register_and_login(chat_client)
    response = chat_client.post(
        "/api/chat",
        headers={
            **auth_headers(token),
            "Content-Type": "application/json; charset=utf-8",
        },
        content='{"question":"UTF-8 검사"}'.encode("utf-8"),
    )

    assert response.status_code == 200


def test_empty_history_is_unwrapped_array(chat_client: TestClient) -> None:
    """기록이 없을 때 wrapper가 아닌 빈 배열을 반환합니다."""

    token = register_and_login(chat_client)
    response = chat_client.get("/api/me/chats", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json() == []


def test_history_is_sorted_and_has_only_contract_fields(chat_client: TestClient) -> None:
    """기록을 id 오름차순과 S07 필드만으로 반환합니다."""

    token = register_and_login(chat_client)
    for question in ("첫 질문", "두 번째 질문"):
        assert (
            chat_client.post(
                "/api/chat",
                headers=auth_headers(token),
                json={"question": question},
            ).status_code
            == 200
        )
    rows = chat_client.get("/api/me/chats", headers=auth_headers(token)).json()

    assert [row["question"] for row in rows] == ["첫 질문", "두 번째 질문"]
    assert [row["id"] for row in rows] == sorted(row["id"] for row in rows)
    assert set(rows[0]) == {"id", "question", "response", "latency_ms", "created_at"}
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", rows[0]["created_at"])


def test_users_cannot_read_or_inject_each_others_data(chat_client: TestClient) -> None:
    """body user_id를 무시하고 JWT 사용자의 기록·문맥만 사용합니다."""

    token_a = register_and_login(chat_client)
    token_b = register_and_login(chat_client, "seconduser")
    response_a = chat_client.post(
        "/api/chat",
        headers=auth_headers(token_a),
        json={"question": "A만의 질문", "user_id": 2},
    )
    response_b = chat_client.post(
        "/api/chat",
        headers=auth_headers(token_b),
        json={"question": "내가 방금 뭘 물어봤지?", "user_id": 1},
    )
    history_a = chat_client.get("/api/me/chats", headers=auth_headers(token_a)).json()
    history_b = chat_client.get("/api/me/chats", headers=auth_headers(token_b)).json()

    assert response_a.status_code == 200
    assert response_b.status_code == 200
    assert [row["question"] for row in history_a] == ["A만의 질문"]
    assert [row["question"] for row in history_b] == ["내가 방금 뭘 물어봤지?"]
    assert "A만의 질문" not in response_b.json()["answer"]


def test_context_contains_only_latest_five_pairs_in_time_order(
    chat_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """6쌍 중 최신 5쌍과 현재 질문의 정확한 message 순서를 검사합니다."""

    token = register_and_login(chat_client)
    for index in range(1, 7):
        response = chat_client.post(
            "/api/chat",
            headers=auth_headers(token),
            json={"question": f"질문 {index}"},
        )
        assert response.status_code == 200

    captured: dict[str, object] = {}

    async def spy_ai(
        messages: list[dict[str, str]],
        *,
        request_id: str,
        settings: Settings,
    ) -> AIResult:
        captured["messages"] = messages
        captured["request_id"] = request_id
        captured["mode"] = settings.resolved_ai_mode
        return AIResult(answer="[Mock] 문맥 검사", latency_ms=3)

    monkeypatch.setattr("app.routers.chat_router.generate_ai_response", spy_ai)
    response = chat_client.post(
        "/api/chat",
        headers=auth_headers(token),
        json={"question": "현재 질문"},
    )
    messages = captured["messages"]

    assert response.status_code == 200
    assert isinstance(messages, list)
    assert len(messages) == 12
    assert messages[0]["role"] == "system"
    assert [item["content"] for item in messages if item["role"] == "user"] == [
        "질문 2",
        "질문 3",
        "질문 4",
        "질문 5",
        "질문 6",
        "현재 질문",
    ]


def test_mock_can_reference_immediately_previous_question(chat_client: TestClient) -> None:
    """두 번째 턴의 Mock이 전달된 직전 사용자 문맥을 사용합니다."""

    token = register_and_login(chat_client)
    first = chat_client.post(
        "/api/chat",
        headers=auth_headers(token),
        json={"question": "배포 방법 알려줘"},
    )
    second = chat_client.post(
        "/api/chat",
        headers=auth_headers(token),
        json={"question": "내가 방금 뭘 물어봤지?"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert "배포 방법 알려줘" in second.json()["answer"]


@pytest.mark.parametrize(
    ("error", "detail"),
    [
        (
            AITimeoutError("timeout"),
            "현재 AI 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.",
        ),
        (
            AIServiceError("upstream"),
            "AI 응답을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ),
    ],
)
def test_ai_failure_returns_504_without_saving(
    chat_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    detail: str,
) -> None:
    """AI 실패를 504로 격리하고 정상 대화 행을 만들지 않습니다."""

    from app.routers import chat_router

    original_ai = chat_router.generate_ai_response
    records: list[logging.LogRecord] = []

    class ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    async def fail_ai(*_args: object, **_kwargs: object) -> AIResult:
        raise error

    monkeypatch.setattr("app.routers.chat_router.generate_ai_response", fail_ai)
    handler = ListHandler()
    app_logger.addHandler(handler)
    token = register_and_login(chat_client)
    try:
        response = chat_client.post(
            "/api/chat",
            headers=auth_headers(token),
            json={"question": "실패 질문"},
        )
    finally:
        app_logger.removeHandler(handler)
    history = chat_client.get("/api/me/chats", headers=auth_headers(token))
    monkeypatch.setattr("app.routers.chat_router.generate_ai_response", original_ai)
    recovery = chat_client.post(
        "/api/chat",
        headers=auth_headers(token),
        json={"question": "복구 질문"},
    )

    assert response.status_code == 504
    assert response.json() == {"detail": detail}
    assert history.json() == []
    assert recovery.status_code == 200
    assert any(record.getMessage().startswith("ai_call_failed request_id=") for record in records)
    if str(error) == "upstream":
        assert all("upstream" not in record.getMessage() for record in records)


@pytest.mark.parametrize(
    "invalid_result",
    [
        AIResult(answer="   ", latency_ms=1),
        AIResult(answer=None, latency_ms=1),
        AIResult(answer=123, latency_ms=1),
        AIResult(answer="잘못된 지연시간", latency_ms=1.5),
        AIResult(answer="잘못된 지연시간", latency_ms=True),
        AIResult(answer="잘못된 지연시간", latency_ms=-1),
    ],
)
def test_invalid_ai_result_returns_504_without_saving(
    chat_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    invalid_result: AIResult,
) -> None:
    """잘못된 답변·지연시간을 성공이나 DB 행으로 취급하지 않습니다."""

    async def empty_ai(*_args: object, **_kwargs: object) -> AIResult:
        return invalid_result

    monkeypatch.setattr("app.routers.chat_router.generate_ai_response", empty_ai)
    token = register_and_login(chat_client)
    response = chat_client.post(
        "/api/chat",
        headers=auth_headers(token),
        json={"question": "빈 답변 검사"},
    )

    assert response.status_code == 504
    assert chat_client.get("/api/me/chats", headers=auth_headers(token)).json() == []


def test_database_save_failure_returns_500_and_logs_failure(
    chat_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DB 실패를 rollback 경로로 보내고 표준 실패 이벤트를 남깁니다."""

    from app.routers import chat_router

    original_save = chat_router.save_chat_log

    async def fail_save(*_args: object, **_kwargs: object) -> None:
        raise aiosqlite.OperationalError("sensitive database detail")

    monkeypatch.setattr("app.routers.chat_router.save_chat_log", fail_save)
    records: list[logging.LogRecord] = []

    class ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = ListHandler()
    app_logger.addHandler(handler)
    try:
        token = register_and_login(chat_client)
        response = chat_client.post(
            "/api/chat",
            headers=auth_headers(token),
            json={"question": "DB 실패 검사"},
        )
    finally:
        app_logger.removeHandler(handler)

    monkeypatch.setattr("app.routers.chat_router.save_chat_log", original_save)
    recovery = chat_client.post(
        "/api/chat",
        headers=auth_headers(token),
        json={"question": "DB 복구 검사"},
    )

    messages = [record.getMessage() for record in records]
    assert response.status_code == 500
    assert response.json() == {
        "detail": "대화 기록을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요."
    }
    assert any(message.startswith("db_save_failed user_id=") for message in messages)
    assert all("sensitive database detail" not in message for message in messages)
    assert recovery.status_code == 200


def test_success_path_emits_required_operational_events(chat_client: TestClient) -> None:
    """요청·AI 시작/성공·DB 성공 네 범주의 이벤트 형식을 확인합니다."""

    records: list[logging.LogRecord] = []

    class ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = ListHandler()
    app_logger.addHandler(handler)
    try:
        token = register_and_login(chat_client)
        response = chat_client.post(
            "/api/chat",
            headers=auth_headers(token),
            json={"question": "로그 검사"},
        )
    finally:
        app_logger.removeHandler(handler)

    messages = [record.getMessage() for record in records]
    assert response.status_code == 200
    assert any(message.startswith("request_received user_id=") for message in messages)
    assert any(message.startswith("ai_call_start user_id=") for message in messages)
    assert any(message.startswith("ai_call_success request_id=") for message in messages)
    assert any(message.startswith("db_save_success user_id=") for message in messages)
    joined = "\n".join(messages)
    assert "pass1234" not in joined
    assert token not in joined
    assert "로그 검사" not in joined


def test_chat_survives_application_restart(
    test_settings: Settings,
) -> None:
    """앱 수명주기를 다시 시작해도 성공 대화가 보존됩니다."""

    with TestClient(create_app(test_settings)) as first_client:
        register = first_client.post(
            "/api/auth/register",
            json={"username": "restartuser", "password": "pass1234"},
        )
        assert register.status_code == 201
        token = first_client.post(
            "/api/auth/login",
            json={"username": "restartuser", "password": "pass1234"},
        ).json()["access_token"]
        assert (
            first_client.post(
                "/api/chat",
                headers=auth_headers(token),
                json={"question": "재시작 전 질문"},
            ).status_code
            == 200
        )

    with TestClient(create_app(test_settings)) as second_client:
        response = second_client.get("/api/me/chats", headers=auth_headers(token))

    assert response.status_code == 200
    assert [row["question"] for row in response.json()] == ["재시작 전 질문"]


def test_same_user_concurrent_turns_are_serialized(
    chat_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """느린 첫 요청보다 두 번째 요청이 먼저 저장되어 문맥이 뒤집히지 않게 합니다."""

    first_ai_started = Event()
    second_ai_started = Event()
    release_first = Event()

    async def controlled_ai(
        messages: list[dict[str, str]],
        *,
        request_id: str,
        settings: Settings,
    ) -> AIResult:
        del request_id, settings
        question = [item["content"] for item in messages if item["role"] == "user"][-1]
        if question == "먼저 도착":
            first_ai_started.set()
            await asyncio.to_thread(release_first.wait)
        else:
            second_ai_started.set()
        return AIResult(answer=f"[Mock] {question}", latency_ms=1)

    monkeypatch.setattr("app.routers.chat_router.generate_ai_response", controlled_ai)
    token = register_and_login(chat_client)

    def send(question: str):
        return chat_client.post(
            "/api/chat",
            headers=auth_headers(token),
            json={"question": question},
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(send, "먼저 도착")
        assert first_ai_started.wait(timeout=2)
        second_future = executor.submit(send, "나중 도착")
        assert not second_ai_started.wait(timeout=0.2)
        release_first.set()
        first_response = first_future.result(timeout=3)
        second_response = second_future.result(timeout=3)

    history = chat_client.get("/api/me/chats", headers=auth_headers(token)).json()
    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_ai_started.is_set()
    assert [row["question"] for row in history] == ["먼저 도착", "나중 도착"]
