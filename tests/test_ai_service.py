"""R16 실제 AI adapter·timeout·모드 판정의 가짜 transport 검증."""

import asyncio
import json
import logging
from pathlib import Path
from threading import Event

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.ai_service import (
    AIServiceError,
    AITimeoutError,
    create_ai_http_client,
    generate_ai_response,
)
from app.config import Settings
from app.logger import app_logger
from app.main import create_app


PROVIDER_KEY = "test-provider-key"
SECRET_KEY = "test-only-secret-key-that-is-long-enough"
TIMEOUT_DETAIL = "현재 AI 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요."
GENERIC_AI_DETAIL = "AI 응답을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요."
MESSAGES = [
    {"role": "system", "content": "테스트 시스템"},
    {"role": "user", "content": "테스트 질문"},
]


class ListHandler(logging.Handler):
    """전파를 끈 앱 로거의 레코드를 테스트 안에서 수집합니다."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def make_settings(
    tmp_path: Path,
    name: str,
    *,
    app_env: str = "test",
    ai_mode: str = "real",
    api_key: str = PROVIDER_KEY,
    api_base: str = "https://provider.test/v1",
    timeout: float = 0.2,
) -> Settings:
    """외부 네트워크와 운영 DB에서 분리된 AI 테스트 설정을 만듭니다."""

    return Settings(
        _env_file=None,
        secret_key=SECRET_KEY,
        database_url=f"sqlite:///{(tmp_path / f'{name}.db').as_posix()}",
        codessey_api_key=api_key,
        codessey_api_base=api_base,
        ai_model_name="test-model",
        ai_timeout_seconds=timeout,
        app_env=app_env,
        ai_mode=ai_mode,
    )


def register_and_login(client: TestClient, username: str = "realuser") -> str:
    """실제 라우터 통합 테스트용 Bearer 토큰을 발급합니다."""

    register = client.post(
        "/api/auth/register",
        json={"username": username, "password": "pass1234"},
    )
    assert register.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={"username": username, "password": "pass1234"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_http_client_enables_tls_and_all_timeout_phases(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """수명주기 클라이언트가 TLS·4단계 timeout·redirect 차단을 명시합니다."""

    captured: dict[str, object] = {}
    sentinel = object()

    def fake_async_client(**kwargs: object) -> object:
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(httpx, "AsyncClient", fake_async_client)

    assert create_ai_http_client(test_settings) is sentinel
    timeout = captured["timeout"]
    assert isinstance(timeout, httpx.Timeout)
    assert timeout.connect == test_settings.ai_timeout_seconds
    assert timeout.read == test_settings.ai_timeout_seconds
    assert timeout.write == test_settings.ai_timeout_seconds
    assert timeout.pool == test_settings.ai_timeout_seconds
    assert captured["verify"] is True
    assert captured["follow_redirects"] is False
    assert captured["transport"] is None


@pytest.mark.parametrize(
    "api_base",
    ["https://provider.test/v1", "https://provider.test/v1/"],
)
async def test_real_adapter_posts_exact_contract_and_parses_answer(
    tmp_path: Path,
    api_base: str,
) -> None:
    """URL·Bearer·body·응답 파싱을 실제 HTTPX 전송 경계에서 고정합니다."""

    settings = make_settings(tmp_path, "adapter", api_base=api_base, timeout=1.25)
    requests: list[httpx.Request] = []

    async def provider(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "가짜 실제 답변"}}]},
        )

    client = create_ai_http_client(
        settings,
        transport=httpx.MockTransport(provider),
    )
    original_messages = [dict(item) for item in MESSAGES]
    async with client:
        result = await generate_ai_response(
            original_messages,
            request_id="test-request-id",
            settings=settings,
            http_client=client,
        )

    assert len(requests) == 1
    request = requests[0]
    assert request.method == "POST"
    assert str(request.url) == "https://provider.test/v1/chat/completions"
    assert request.headers["Authorization"] == f"Bearer {PROVIDER_KEY}"
    assert json.loads(request.content) == {
        "model": "test-model",
        "messages": MESSAGES,
        "stream": False,
    }
    assert PROVIDER_KEY not in str(request.url)
    assert PROVIDER_KEY not in request.content.decode("utf-8")
    assert request.extensions["timeout"] == {
        "connect": 1.25,
        "read": 1.25,
        "write": 1.25,
        "pool": 1.25,
    }
    assert original_messages == MESSAGES
    assert result.answer == "가짜 실제 답변"
    assert isinstance(result.latency_ms, int)
    assert not isinstance(result.latency_ms, bool)
    assert result.latency_ms >= 0
    assert client.is_closed is True


@pytest.mark.parametrize(
    ("app_env", "ai_mode", "api_key", "expected"),
    [
        ("development", "auto", "", "mock"),
        ("test", "auto", "your_codessey_api_key", "mock"),
        ("development", "auto", PROVIDER_KEY, "real"),
        ("test", "mock", PROVIDER_KEY, "mock"),
        ("test", "real", PROVIDER_KEY, "real"),
        ("production", "auto", PROVIDER_KEY, "real"),
        ("production", "real", PROVIDER_KEY, "real"),
    ],
)
def test_ai_mode_positive_matrix(
    tmp_path: Path,
    app_env: str,
    ai_mode: str,
    api_key: str,
    expected: str,
) -> None:
    """환경·명시 모드·키 상태의 허용 조합을 고정합니다."""

    settings = make_settings(
        tmp_path,
        f"mode-{app_env}-{ai_mode}",
        app_env=app_env,
        ai_mode=ai_mode,
        api_key=api_key,
    )
    assert settings.resolved_ai_mode == expected


@pytest.mark.parametrize(
    ("app_env", "ai_mode", "api_key"),
    [
        ("test", "real", ""),
        ("development", "real", "your_codessey_api_key"),
        ("production", "mock", PROVIDER_KEY),
        ("production", "auto", ""),
        ("production", "real", "your_codessey_api_key"),
    ],
)
def test_ai_mode_rejects_unsafe_matrix(
    tmp_path: Path,
    app_env: str,
    ai_mode: str,
    api_key: str,
) -> None:
    """real 무키와 운영 Mock 전환을 서버 기동 전에 거부합니다."""

    with pytest.raises(ValidationError):
        make_settings(
            tmp_path,
            f"invalid-{app_env}-{ai_mode}",
            app_env=app_env,
            ai_mode=ai_mode,
            api_key=api_key,
        )


@pytest.mark.parametrize(
    "api_base",
    [
        "",
        "/v1",
        "http://provider.test/v1",
        "https://user:password@provider.test/v1",
        "https://provider.test/v1?api_key=secret",
        "https://provider.test/v1#fragment",
    ],
)
def test_ai_base_rejects_insecure_or_loggable_urls(
    tmp_path: Path,
    api_base: str,
) -> None:
    """키·대화가 평문 또는 URL 메타데이터로 새는 공급자 주소를 거부합니다."""

    with pytest.raises(ValidationError):
        make_settings(
            tmp_path,
            "invalid-provider-url",
            api_base=api_base,
        )


def test_ai_base_validation_error_does_not_echo_rejected_secret_value(
    tmp_path: Path,
) -> None:
    """기동 오류가 URL 사용자정보나 query의 합성 비밀값을 반사하지 않습니다."""

    unsafe_base = (
        "https://URL_USER_SECRET:URL_PASSWORD_SECRET@provider.test/v1"
        "?api_key=QUERY_SECRET"
    )
    with pytest.raises(ValidationError) as captured:
        make_settings(
            tmp_path,
            "secret-provider-url",
            api_base=unsafe_base,
        )

    error_text = str(captured.value)
    for marker in (
        "URL_USER_SECRET",
        "URL_PASSWORD_SECRET",
        "QUERY_SECRET",
        unsafe_base,
    ):
        assert marker not in error_text


@pytest.mark.parametrize(
    ("app_env", "ai_mode", "api_key"),
    [
        ("development", "auto", ""),
        ("test", "auto", "your_codessey_api_key"),
        ("test", "mock", PROVIDER_KEY),
    ],
)
def test_mock_modes_use_no_transport_and_lifespan_closes_client(
    tmp_path: Path,
    app_env: str,
    ai_mode: str,
    api_key: str,
) -> None:
    """모든 유효 Mock 선택에서 외부 전송 0회와 client 종료를 확인합니다."""

    settings = make_settings(
        tmp_path,
        f"mock-route-{app_env}-{ai_mode}",
        app_env=app_env,
        ai_mode=ai_mode,
        api_key=api_key,
    )
    calls = 0

    async def forbidden_provider(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise AssertionError("Mock 모드는 외부 transport를 호출하면 안 됩니다.")

    application = create_app(
        settings,
        ai_transport=httpx.MockTransport(forbidden_provider),
    )
    with TestClient(application, raise_server_exceptions=False) as client:
        ai_client = application.state.ai_http_client
        assert ai_client.is_closed is False
        token = register_and_login(client)
        response = client.post(
            "/api/chat",
            headers=auth_headers(token),
            json={"question": "Mock 경로 검사"},
        )
        health = client.get("/api/health")

        assert response.status_code == 200
        assert response.json()["answer"].startswith("[Mock]")
        assert response.headers["X-AI-Mode"] == "mock"
        assert health.headers["X-AI-Mode"] == "mock"
        assert application.state.ai_http_client is ai_client
        assert calls == 0

    assert ai_client.is_closed is True


def test_httpx_timeout_returns_504_then_same_real_client_recovers(
    tmp_path: Path,
) -> None:
    """HTTPX timeout 뒤 같은 앱·client·transport의 다음 real 요청이 성공합니다."""

    settings = make_settings(tmp_path, "httpx-timeout", timeout=0.2)
    calls = 0

    async def provider(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ReadTimeout("SECRET_NETWORK_DETAIL", request=request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "복구된 실제 경로"}}]},
        )

    application = create_app(settings, ai_transport=httpx.MockTransport(provider))
    log_handler = ListHandler()
    app_logger.addHandler(log_handler)
    try:
        with TestClient(application, raise_server_exceptions=False) as client:
            ai_client = application.state.ai_http_client
            token = register_and_login(client)
            failed = client.post(
                "/api/chat",
                headers=auth_headers(token),
                json={"question": "timeout 질문"},
            )
            empty_history = client.get("/api/me/chats", headers=auth_headers(token))
            recovered = client.post(
                "/api/chat",
                headers=auth_headers(token),
                json={"question": "복구 질문"},
            )
            history = client.get("/api/me/chats", headers=auth_headers(token))

            assert application.state.ai_http_client is ai_client
            assert ai_client.is_closed is False
    finally:
        app_logger.removeHandler(log_handler)

    messages = [record.getMessage() for record in log_handler.records]
    assert failed.status_code == 504
    assert failed.json() == {"detail": TIMEOUT_DETAIL}
    assert empty_history.json() == []
    assert recovered.status_code == 200
    assert recovered.json()["answer"] == "복구된 실제 경로"
    assert recovered.headers["X-AI-Mode"] == "real"
    assert [row["question"] for row in history.json()] == ["복구 질문"]
    assert calls == 2
    assert any(message.endswith("error=timeout") for message in messages)
    assert "SECRET_NETWORK_DETAIL" not in "\n".join(messages)
    assert ai_client.is_closed is True


def test_overall_timeout_cancels_handler_then_same_real_client_recovers(
    tmp_path: Path,
) -> None:
    """wait_for 전체 제한이 느린 전송을 취소하고 다음 요청을 막지 않습니다."""

    settings = make_settings(tmp_path, "overall-timeout", timeout=0.02)
    calls = 0
    cancelled = Event()

    async def provider(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            try:
                await asyncio.sleep(1)
            finally:
                cancelled.set()
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "전체 제한 뒤 복구"}}]},
        )

    application = create_app(settings, ai_transport=httpx.MockTransport(provider))
    log_handler = ListHandler()
    app_logger.addHandler(log_handler)
    try:
        with TestClient(application, raise_server_exceptions=False) as client:
            ai_client = application.state.ai_http_client
            token = register_and_login(client)
            failed = client.post(
                "/api/chat",
                headers=auth_headers(token),
                json={"question": "전체 제한 질문"},
            )
            empty_history = client.get("/api/me/chats", headers=auth_headers(token))
            recovered = client.post(
                "/api/chat",
                headers=auth_headers(token),
                json={"question": "전체 제한 복구"},
            )
            history = client.get("/api/me/chats", headers=auth_headers(token))
    finally:
        app_logger.removeHandler(log_handler)

    messages = [record.getMessage() for record in log_handler.records]
    assert failed.status_code == 504
    assert failed.json() == {"detail": TIMEOUT_DETAIL}
    assert empty_history.json() == []
    assert cancelled.is_set()
    assert recovered.status_code == 200
    assert recovered.json()["answer"] == "전체 제한 뒤 복구"
    assert [row["question"] for row in history.json()] == ["전체 제한 복구"]
    assert calls == 2
    assert any(message.endswith("error=timeout") for message in messages)
    assert ai_client.is_closed is True


async def test_caller_cancellation_is_not_translated_to_service_error(
    tmp_path: Path,
) -> None:
    """상위 작업 취소는 504용 예외로 바꾸지 않고 그대로 전파합니다."""

    settings = make_settings(tmp_path, "caller-cancel", timeout=2)
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def provider(_request: httpx.Request) -> httpx.Response:
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()
        raise AssertionError("취소 뒤에는 도달할 수 없습니다.")

    client = create_ai_http_client(
        settings,
        transport=httpx.MockTransport(provider),
    )
    async with client:
        task = asyncio.create_task(
            generate_ai_response(
                MESSAGES,
                request_id="caller-cancel",
                settings=settings,
                http_client=client,
            )
        )
        await asyncio.wait_for(started.wait(), timeout=0.2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    assert cancelled.is_set()


def test_real_failure_matrix_is_safe_unretried_and_never_falls_back(
    tmp_path: Path,
) -> None:
    """공급자·네트워크·응답 장애를 분류된 504로만 노출합니다."""

    settings = make_settings(
        tmp_path,
        "failure-matrix",
        ai_mode="auto",
        api_key=PROVIDER_KEY,
        timeout=0.2,
    )
    cases = [
        ("status-401", "auth"),
        ("status-403", "auth"),
        ("status-429", "rate_limit"),
        ("status-500", "upstream"),
        ("connect-error", "network"),
        ("read-error", "network"),
        ("invalid-json", "invalid_json"),
        ("blank-content", "invalid_response"),
    ]
    requests: list[httpx.Request] = []

    async def provider(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        call_number = len(requests)
        if call_number > len(cases):
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "장애 뒤 정상 답변"}}]},
            )

        kind, _expected_code = cases[call_number - 1]
        if kind.startswith("status-"):
            return httpx.Response(
                int(kind.removeprefix("status-")),
                json={"error": "provider-secret-body"},
            )
        if kind == "connect-error":
            raise httpx.ConnectError(
                f"network detail containing {PROVIDER_KEY}",
                request=request,
            )
        if kind == "read-error":
            raise httpx.ReadError("provider-secret-body", request=request)
        if kind == "invalid-json":
            return httpx.Response(200, content=b"provider-secret-body")
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "   "}}]},
        )

    application = create_app(settings, ai_transport=httpx.MockTransport(provider))
    log_handler = ListHandler()
    app_logger.addHandler(log_handler)
    try:
        with TestClient(application, raise_server_exceptions=False) as client:
            token = register_and_login(client)
            for index, (_kind, _expected_code) in enumerate(cases, start=1):
                response = client.post(
                    "/api/chat",
                    headers=auth_headers(token),
                    json={"question": f"비밀 질문 {index}"},
                )
                assert response.status_code == 504
                assert response.json() == {"detail": GENERIC_AI_DETAIL}
                assert "WWW-Authenticate" not in response.headers
                assert len(requests) == index
                assert client.get(
                    "/api/me/chats",
                    headers=auth_headers(token),
                ).json() == []

            recovered = client.post(
                "/api/chat",
                headers=auth_headers(token),
                json={"question": "장애 뒤 복구"},
            )
            history = client.get("/api/me/chats", headers=auth_headers(token))
    finally:
        app_logger.removeHandler(log_handler)

    failure_messages = [
        record.getMessage()
        for record in log_handler.records
        if record.getMessage().startswith("ai_call_failed request_id=")
    ]
    assert [message.rsplit("error=", 1)[1] for message in failure_messages] == [
        expected_code for _kind, expected_code in cases
    ]
    assert recovered.status_code == 200
    assert recovered.json()["answer"] == "장애 뒤 정상 답변"
    assert recovered.headers["X-AI-Mode"] == "real"
    assert [row["question"] for row in history.json()] == ["장애 뒤 복구"]
    assert len(requests) == len(cases) + 1
    joined_logs = "\n".join(record.getMessage() for record in log_handler.records)
    ai_starts = [
        record.getMessage()
        for record in log_handler.records
        if record.getMessage().startswith("ai_call_start user_id=")
    ]
    ai_successes = [
        record.getMessage()
        for record in log_handler.records
        if record.getMessage().startswith("ai_call_success request_id=")
    ]
    assert len(ai_starts) == len(cases) + 1
    assert all(message.endswith(" mode=real") for message in ai_starts)
    assert len(ai_successes) == 1
    assert ai_successes[0].endswith(" mode=real")
    assert "provider-secret-body" not in joined_logs
    assert PROVIDER_KEY not in joined_logs
    assert "Bearer " not in joined_logs
    assert "비밀 질문" not in joined_logs
    assert all("[Mock]" not in request.content.decode("utf-8") for request in requests)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        "text",
        {},
        {"choices": []},
        {"choices": [1]},
        {"choices": [{}]},
        {"choices": [{"message": []}]},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": None}}]},
        {"choices": [{"message": {"content": 1}}]},
        {"choices": [{"message": {"content": "   "}}]},
    ],
)
async def test_real_adapter_rejects_every_invalid_response_shape(
    tmp_path: Path,
    payload: object,
) -> None:
    """JSON 최상위부터 content까지 구조 불일치를 모두 실패로 처리합니다."""

    settings = make_settings(tmp_path, "invalid-shape")
    calls = 0

    async def provider(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if payload is None:
            return httpx.Response(
                200,
                content=b"null",
                headers={"Content-Type": "application/json"},
            )
        return httpx.Response(200, json=payload)

    client = create_ai_http_client(
        settings,
        transport=httpx.MockTransport(provider),
    )
    async with client:
        with pytest.raises(AIServiceError) as captured:
            await generate_ai_response(
                MESSAGES,
                request_id="invalid-shape",
                settings=settings,
                http_client=client,
            )

    assert captured.value.error_code == "invalid_response"
    assert calls == 1


async def test_real_adapter_classifies_non_json_without_exposing_body(
    tmp_path: Path,
) -> None:
    """비JSON 본문은 원문을 예외 문자열로 노출하지 않고 분류합니다."""

    settings = make_settings(tmp_path, "invalid-json")

    async def provider(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"provider-secret-body")

    client = create_ai_http_client(
        settings,
        transport=httpx.MockTransport(provider),
    )
    async with client:
        with pytest.raises(AIServiceError) as captured:
            await generate_ai_response(
                MESSAGES,
                request_id="invalid-json",
                settings=settings,
                http_client=client,
            )

    assert captured.value.error_code == "invalid_json"
    assert "provider-secret-body" not in str(captured.value)


async def test_httpx_read_timeout_maps_to_timeout_error_once(
    tmp_path: Path,
) -> None:
    """직접 adapter 호출에서도 HTTPX timeout을 전용 예외로 한 번만 변환합니다."""

    settings = make_settings(tmp_path, "direct-httpx-timeout")
    calls = 0

    async def provider(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("provider-secret-body", request=request)

    client = create_ai_http_client(
        settings,
        transport=httpx.MockTransport(provider),
    )
    async with client:
        with pytest.raises(AITimeoutError):
            await generate_ai_response(
                MESSAGES,
                request_id="direct-timeout",
                settings=settings,
                http_client=client,
            )

    assert calls == 1
