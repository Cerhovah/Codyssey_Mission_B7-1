"""정적 프론트 경계와 서버 제공 조건 회귀 테스트."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_ROOT = PROJECT_ROOT / "static"


@pytest.fixture
def frontend_client(test_settings: Settings) -> Iterator[TestClient]:
    """정적 화면을 제공하는 테스트 클라이언트를 만듭니다."""

    with TestClient(create_app(test_settings)) as client:
        yield client


def test_root_and_stylesheet_are_served_by_fastapi(frontend_client: TestClient) -> None:
    """HTML 직접 열기 대신 서버의 `/`와 `/static/` 경로를 사용합니다."""

    root = frontend_client.get("/")
    stylesheet = frontend_client.get("/static/css/style.css")
    api_script = frontend_client.get("/static/js/api.js")
    auth_script = frontend_client.get("/static/js/auth.js")
    app_script = frontend_client.get("/static/js/app.js")

    assert root.status_code == 200
    assert root.headers["content-type"].startswith("text/html")
    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")
    assert api_script.status_code == 200
    assert auth_script.status_code == 200
    assert app_script.status_code == 200
    assert "javascript" in api_script.headers["content-type"]


def test_html_has_minimum_chat_and_auth_state_regions() -> None:
    """로그인·대화·입력·오류 표시를 위한 기본 DOM을 고정합니다."""

    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")
    required_ids = {
        "session-status",
        "open-login-button",
        "logout-button",
        "connection-status",
        "message-list",
        "empty-state",
        "loading-indicator",
        "chat-form",
        "question-input",
        "send-button",
        "auth-modal",
        "auth-content",
        "toast-region",
    }

    for element_id in required_ids:
        assert f'id="{element_id}"' in html


def test_frontend_is_static_and_self_contained() -> None:
    """Python 템플릿·환경 변수·외부 CDN에 직접 의존하지 않습니다."""

    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")

    assert "{{" not in html
    assert "{%" not in html
    assert ".env" not in html
    assert "localhost" not in html
    assert "127.0.0.1" not in html
    assert "http://" not in html
    assert "https://" not in html
    assert 'href="/static/css/style.css"' in html
    assert 'src="/static/js/auth.js"' in html
    assert 'src="/static/js/app.js"' in html


def test_api_calls_are_centralized_in_api_module() -> None:
    """endpoint·fetch가 DOM/인증 모듈로 새지 않게 합니다."""

    api_source = (STATIC_ROOT / "js" / "api.js").read_text(encoding="utf-8")
    auth_source = (STATIC_ROOT / "js" / "auth.js").read_text(encoding="utf-8")
    app_source = (STATIC_ROOT / "js" / "app.js").read_text(encoding="utf-8")

    assert "fetch(" in api_source
    assert 'const API_BASE = "/api"' in api_source
    assert 'request("/auth/login"' in api_source
    assert 'request("/auth/register"' in api_source
    assert 'request("/health"' in api_source
    assert 'request("/chat"' in api_source
    assert 'request("/me/chats"' in api_source
    assert "fetch(" not in auth_source
    assert "fetch(" not in app_source
    assert '"/api' not in auth_source
    assert '"/api' not in app_source


def test_chat_uses_exact_question_answer_and_latency_contract() -> None:
    """채팅 요청·응답은 최신 팀 API 필드만 사용합니다."""

    api_source = (STATIC_ROOT / "js" / "api.js").read_text(encoding="utf-8")
    app_source = (STATIC_ROOT / "js" / "app.js").read_text(encoding="utf-8")

    assert "body: { question }" in api_source
    assert "const { answer, latency_ms: latencyMs }" in api_source
    assert "result.status !== 200" in api_source
    chat_contract = api_source.split("export async function sendChat", 1)[1]
    assert "|| !answer" not in chat_contract
    assert "result.answer" in app_source
    assert "result.latencyMs" in app_source
    for legacy_field in ("reply", "message", "chat_id"):
        assert f"result.{legacy_field}" not in app_source


def test_messages_are_rendered_as_text_without_html_injection() -> None:
    """사용자 질문과 AI 답변은 DOM textContent로만 표시합니다."""

    scripts = "\n".join(
        path.read_text(encoding="utf-8") for path in (STATIC_ROOT / "js").glob("*.js")
    )

    assert "content.textContent = text" in scripts
    assert "innerHTML" not in scripts
    assert "insertAdjacentHTML" not in scripts


def test_question_validation_uses_raw_unicode_code_points() -> None:
    """공백 여부와 원문 500자 상한을 서버 기준에 맞춰 검사합니다."""

    app_source = (STATIC_ROOT / "js" / "app.js").read_text(encoding="utf-8")

    assert "Array.from(value).length" in app_source
    assert "if (!question.trim())" in app_source
    assert "questionLength(question) > MAX_QUESTION_LENGTH" in app_source
    assert "sendChat(question, token, controller.signal)" in app_source


def test_chat_response_is_guarded_by_current_session() -> None:
    """로그아웃·사용자 전환 뒤 도착한 응답은 현재 화면에 그리지 않습니다."""

    app_source = (STATIC_ROOT / "js" / "app.js").read_text(encoding="utf-8")
    chat_block = app_source.split("async function handleChatSubmit", 1)[1]
    chat_block = chat_block.split("async function loadChatHistory", 1)[0]

    assert "requestGeneration !== sessionGeneration" in chat_block
    assert chat_block.count("token !== getAccessToken()") == 2
    assert "activeChatController?.abort()" in chat_block


def test_history_uses_unwrapped_array_and_response_field() -> None:
    """내 기록은 래퍼 없이 배열로 받고 각 항목의 response를 렌더링합니다."""

    api_source = (STATIC_ROOT / "js" / "api.js").read_text(encoding="utf-8")
    app_source = (STATIC_ROOT / "js" / "app.js").read_text(encoding="utf-8")

    assert 'request("/me/chats"' in api_source
    assert "result.status !== 200" in api_source
    assert "!Array.isArray(result.data)" in api_source
    assert "chats: result.data" in api_source
    assert "for (const item of result.chats)" in app_source
    assert 'appendMessage("assistant", item.response, item.latency_ms)' in app_source
    assert "item.answer" not in app_source


def test_history_contract_validates_exact_item_types() -> None:
    """기록 id·질문·응답·지연·생성시각의 타입을 화면 반영 전에 확인합니다."""

    api_source = (STATIC_ROOT / "js" / "api.js").read_text(encoding="utf-8")

    assert "Number.isInteger(item.id)" in api_source
    assert 'typeof item.question === "string"' in api_source
    assert 'typeof item.response === "string"' in api_source
    assert "Number.isInteger(item.latency_ms)" in api_source
    assert 'typeof item.created_at === "string"' in api_source


def test_history_loading_blocks_chat_and_ignores_stale_sessions() -> None:
    """기록 로딩 중 전송을 막고 사용자 전환 뒤 늦은 배열을 버립니다."""

    app_source = (STATIC_ROOT / "js" / "app.js").read_text(encoding="utf-8")

    assert "const busy = sending || loadingHistory" in app_source
    assert "if (sending || loadingHistory)" in app_source
    assert "getChatHistory(token, controller.signal)" in app_source
    history_block = app_source.split("async function loadChatHistory", 1)[1]
    history_block = history_block.split("function handleAuthChange", 1)[0]
    assert "requestGeneration !== sessionGeneration" in history_block
    assert history_block.count("token !== getAccessToken()") == 2
    assert "activeHistoryController?.abort()" in app_source
    assert 'title: "대화 기록을 불러오지 못했습니다."' in history_block


def test_only_protected_api_unauthorized_clears_the_session() -> None:
    """chat/history 401만 세션을 지우고 로그인 401은 모달 오류로 남깁니다."""

    app_source = (STATIC_ROOT / "js" / "app.js").read_text(encoding="utf-8")
    auth_source = (STATIC_ROOT / "js" / "auth.js").read_text(encoding="utf-8")
    login_block = auth_source.split("async function handleLoginSubmit", 1)[1]
    login_block = login_block.split("async function handleRegisterSubmit", 1)[0]

    assert "error.status !== 401" in app_source
    assert "clearSession()" in app_source
    assert 'openLoginModal("로그인이 만료되었습니다. 다시 로그인해 주세요.")' in app_source
    assert "clearSession()" not in login_block
    assert "showLoginError(message)" in login_block
    assert 'elements.authNotice.textContent = ""' in login_block

    chat_catch = app_source.split("async function handleChatSubmit", 1)[1]
    chat_catch = chat_catch.split("async function loadChatHistory", 1)[0]
    assert chat_catch.index("token !== getAccessToken()") < chat_catch.index(
        "handleProtectedUnauthorized(error)"
    )


def test_chat_loading_blocks_duplicate_submit_and_recovers_in_finally() -> None:
    """느린 요청 중 모든 제출 경로를 막고 성공·실패 뒤 폼을 복구합니다."""

    app_source = (STATIC_ROOT / "js" / "app.js").read_text(encoding="utf-8")
    submit_block = app_source.split("async function handleChatSubmit", 1)[1]
    submit_block = submit_block.split("async function loadChatHistory", 1)[0]

    assert "if (sending || loadingHistory)" in submit_block
    assert "setSending(true)" in submit_block
    assert "} finally {" in submit_block
    assert "setSending(false)" in submit_block
    assert 'elements.chatForm.setAttribute("aria-busy", String(busy))' in app_source
    assert 'elements.messageList.setAttribute("aria-busy", String(busy))' in app_source
    assert 'elements.sendButton.textContent = sending' in app_source
    assert "elements.questionInput.disabled = !authenticated || busy" in app_source


def test_failed_chat_keeps_question_for_manual_retry() -> None:
    """실패 시 입력을 보존하고 성공한 현재 요청에서만 비웁니다."""

    app_source = (STATIC_ROOT / "js" / "app.js").read_text(encoding="utf-8")
    submit_block = app_source.split("async function handleChatSubmit", 1)[1]
    submit_block = submit_block.split("async function loadChatHistory", 1)[0]
    success_block, catch_block = submit_block.split("} catch (error)", 1)

    assert 'elements.questionInput.value = ""' in success_block
    assert 'elements.questionInput.value = ""' not in catch_block


def test_login_stores_only_access_token_and_password_stays_ephemeral() -> None:
    """비밀번호·사용자 입력을 브라우저 저장소에 기록하지 않습니다."""

    auth_source = (STATIC_ROOT / "js" / "auth.js").read_text(encoding="utf-8")

    assert 'const TOKEN_KEY = "access_token"' in auth_source
    assert "localStorage.setItem(TOKEN_KEY, token)" in auth_source
    assert "localStorage.setItem" in auth_source
    assert auth_source.count("localStorage.setItem") == 1
    assert "localStorage.setItem(\"password\"" not in auth_source
    assert 'elements.loginPassword.value = ""' in auth_source


def test_auth_event_does_not_broadcast_bearer_token() -> None:
    """다른 프론트 모듈에는 인증 여부만 알리고 토큰 원문은 전달하지 않습니다."""

    auth_source = (STATIC_ROOT / "js" / "auth.js").read_text(encoding="utf-8")

    assert "detail: { authenticated }" in auth_source
    assert "detail: { authenticated, token }" not in auth_source
    assert "detail: { authenticated: Boolean(token), token }" not in auth_source


def test_login_success_restores_focus_to_a_visible_control() -> None:
    """로그인 버튼이 숨겨진 뒤에도 포커스가 숨은 요소에 남지 않습니다."""

    auth_source = (STATIC_ROOT / "js" / "auth.js").read_text(encoding="utf-8")

    success_block = auth_source.split(
        "const result = await login(credentials, controller.signal);",
        1,
    )[1]
    success_block = success_block.split("} catch (error)", 1)[0]
    assert "hideAuthModal({ restoreFocus: false })" in success_block
    assert "elements.logoutButton.focus()" in success_block


def test_closing_login_cancels_stale_request_and_clears_password() -> None:
    """닫힌 모달의 늦은 응답이 세션을 바꾸거나 비밀번호를 남기지 않습니다."""

    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")
    auth_source = (STATIC_ROOT / "js" / "auth.js").read_text(encoding="utf-8")

    assert '<form id="login-form" class="auth-form" method="post">' in html
    assert "activeLoginController?.abort()" in auth_source
    assert "login(credentials, controller.signal)" in auth_source
    assert "activeLoginController !== controller || controller.signal.aborted" in auth_source
    cancel_block = auth_source.split("function cancelLoginAttempt()", 1)[1]
    cancel_block = cancel_block.split("function showLoginError", 1)[0]
    assert 'elements.loginPassword.value = ""' in cancel_block
    assert 'addEventListener("click", cancelLoginAttempt)' in auth_source


def test_register_uses_exact_contract_and_returns_to_login() -> None:
    """가입은 201과 username/password·message/username 계약만 사용합니다."""

    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")
    api_source = (STATIC_ROOT / "js" / "api.js").read_text(encoding="utf-8")
    auth_source = (STATIC_ROOT / "js" / "auth.js").read_text(encoding="utf-8")

    assert '<form id="register-form" class="auth-form" method="post" hidden>' in html
    assert 'autocomplete="new-password"' in html
    assert 'request("/auth/register"' in api_source
    assert "result.status !== 201" in api_source
    assert "username: credentials.username" in api_source
    assert "password: credentials.password" in api_source
    assert "const { message, username } = result.data || {}" in api_source
    assert "showLoginView({ notice: result.message })" in auth_source
    assert "elements.loginUsername.value = result.username" in auth_source


def test_register_errors_stay_local_and_password_is_ephemeral() -> None:
    """400·422 detail은 가입 폼에 표시하고 비밀번호는 저장하거나 전파하지 않습니다."""

    auth_source = (STATIC_ROOT / "js" / "auth.js").read_text(encoding="utf-8")

    register_block = auth_source.split("async function handleRegisterSubmit", 1)[1]
    register_block = register_block.split("function renderAiMode", 1)[0]
    assert "error instanceof ApiError ? error.message" in register_block
    assert "showRegisterError(message)" in register_block
    assert 'elements.registerPassword.value = ""' in register_block
    assert "localStorage" not in register_block
    assert auth_source.count("localStorage.setItem") == 1


def test_register_request_is_cancelled_when_auth_view_changes() -> None:
    """가입 모달 전환·닫기 뒤의 늦은 응답은 UI를 변경하지 않습니다."""

    auth_source = (STATIC_ROOT / "js" / "auth.js").read_text(encoding="utf-8")

    assert "activeRegisterController?.abort()" in auth_source
    assert "register(credentials, controller.signal)" in auth_source
    assert "activeRegisterController !== controller || controller.signal.aborted" in auth_source
    assert "cancelRegisterAttempt()" in auth_source


def test_stale_auth_errors_cannot_change_the_current_form() -> None:
    """취소된 로그인·가입 오류도 현재 폼의 상태나 입력을 변경하지 않습니다."""

    auth_source = (STATIC_ROOT / "js" / "auth.js").read_text(encoding="utf-8")
    login_block = auth_source.split("async function handleLoginSubmit", 1)[1]
    login_block = login_block.split("async function handleRegisterSubmit", 1)[0]
    register_block = auth_source.split("async function handleRegisterSubmit", 1)[1]
    register_block = register_block.split("function renderAiMode", 1)[0]

    assert "activeLoginController !== controller" in login_block.split("} catch (error)", 1)[1]
    assert "controller.signal.aborted" in login_block.split("} catch (error)", 1)[1]
    assert "activeRegisterController !== controller" in register_block.split(
        "} catch (error)",
        1,
    )[1]
    assert "controller.signal.aborted" in register_block.split("} catch (error)", 1)[1]


def test_optional_ai_mode_header_is_not_required_for_success() -> None:
    """선택 헤더 부재를 null로 처리하고 로그인 성공 조건에 포함하지 않습니다."""

    api_source = (STATIC_ROOT / "js" / "api.js").read_text(encoding="utf-8")
    auth_source = (STATIC_ROOT / "js" / "auth.js").read_text(encoding="utf-8")

    assert 'response.headers.get("X-AI-Mode") || null' in api_source
    assert "if (!aiMode)" in auth_source
    assert "result.aiMode" not in auth_source.split("setToken(result.accessToken)", 1)[0]


@pytest.mark.parametrize(
    "path",
    ["/.env", "/.git/config", "/data/chatbot.db", "/logs/app.log", "/README.md"],
)
def test_repository_files_are_not_exposed(
    frontend_client: TestClient,
    path: str,
) -> None:
    """정적 mount가 저장소 루트나 민감 산출물을 노출하지 않습니다."""

    assert frontend_client.get(path).status_code == 404
