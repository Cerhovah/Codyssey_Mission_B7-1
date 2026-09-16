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

    assert root.status_code == 200
    assert root.headers["content-type"].startswith("text/html")
    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")


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
