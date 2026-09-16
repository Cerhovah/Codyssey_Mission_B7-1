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

    assert root.status_code == 200
    assert root.headers["content-type"].startswith("text/html")
    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")
    assert api_script.status_code == 200
    assert auth_script.status_code == 200
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


def test_api_calls_are_centralized_in_api_module() -> None:
    """endpoint·fetch가 DOM/인증 모듈로 새지 않게 합니다."""

    api_source = (STATIC_ROOT / "js" / "api.js").read_text(encoding="utf-8")
    auth_source = (STATIC_ROOT / "js" / "auth.js").read_text(encoding="utf-8")

    assert "fetch(" in api_source
    assert 'const API_BASE = "/api"' in api_source
    assert 'request("/auth/login"' in api_source
    assert 'request("/health"' in api_source
    assert "fetch(" not in auth_source
    assert '"/api' not in auth_source


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
