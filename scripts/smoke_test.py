"""외부 호출과 영구 DB 없이 최소 API 왕복을 실행합니다."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import httpx
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


class SmokeFailure(RuntimeError):
    """민감한 응답 본문 없이 smoke 단계 실패를 표시합니다."""


def configure_standard_streams() -> None:
    """CLI 결과가 운영체제 코드 페이지와 무관하게 UTF-8이 되게 합니다."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def require(condition: bool, stage: str) -> None:
    if not condition:
        raise SmokeFailure(f"{stage} 계약 실패")


def run_smoke() -> None:
    """health부터 사용자별 기록까지 Mock 모드의 실제 API를 왕복합니다."""

    transport_calls = 0

    async def forbidden_transport(_request: httpx.Request) -> httpx.Response:
        nonlocal transport_calls
        transport_calls += 1
        return httpx.Response(500, json={"detail": "blocked"})

    temporary_root: Path
    with TemporaryDirectory(prefix="ai-assistant-smoke-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        database_path = temporary_root / "smoke.db"
        settings = Settings(
            _env_file=None,
            secret_key="smoke-only-secret-key-that-is-long-enough",
            algorithm="HS256",
            access_token_expire_minutes=1440,
            database_url=f"sqlite:///{database_path.as_posix()}",
            codessey_api_key="",
            codessey_api_base="https://provider.invalid/v1",
            ai_model_name="smoke-model",
            ai_timeout_seconds=8.0,
            app_env="test",
            ai_mode="mock",
            context_turns=5,
        )
        application = create_app(
            settings,
            ai_transport=httpx.MockTransport(forbidden_transport),
            log_path=None,
        )

        with TestClient(application, raise_server_exceptions=False) as client:
            health = client.get("/api/health")
            require(health.status_code == 200, "health")
            require(health.json() == {"status": "ok"}, "health body")

            register = client.post(
                "/api/auth/register",
                json={"username": "smoke_user", "password": "smoke-pass-1234"},
            )
            require(register.status_code == 201, "register")

            login = client.post(
                "/api/auth/login",
                json={"username": "smoke_user", "password": "smoke-pass-1234"},
            )
            require(login.status_code == 200, "login")
            token = login.json().get("access_token")
            require(isinstance(token, str) and bool(token), "login token")
            headers = {"Authorization": f"Bearer {token}"}

            chat = client.post(
                "/api/chat",
                headers=headers,
                json={"question": "smoke round trip"},
            )
            require(chat.status_code == 200, "chat")
            require(chat.json().get("answer", "").startswith("[Mock]"), "chat mode")

            history = client.get("/api/me/chats", headers=headers)
            require(history.status_code == 200, "history")
            require(isinstance(history.json(), list), "history body")
            require(len(history.json()) == 1, "history rows")

        require(transport_calls == 0, "external transport count")

    require(not temporary_root.exists(), "temporary directory cleanup")


def main() -> int:
    try:
        run_smoke()
    except SmokeFailure as exc:
        print(f"smoke_test: FAIL ({exc})", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"smoke_test: FAIL ({type(exc).__name__})", file=sys.stderr)
        return 1
    print(
        "smoke_test: PASS "
        "health=200 register=201 login=200 chat=200 history_rows=1 "
        "mode=mock external_calls=0"
    )
    return 0


if __name__ == "__main__":
    configure_standard_streams()
    raise SystemExit(main())
