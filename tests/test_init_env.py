"""R20 로컬 Mock `.env` 최초 생성 도구의 보존·비밀 경계 테스트."""

from concurrent.futures import ThreadPoolExecutor
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

from app.config import PLACEHOLDER_SECRET_KEYS, Settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INIT_ENV_SCRIPT = PROJECT_ROOT / "scripts" / "init_env.py"
SETTING_KEYS = (
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "DATABASE_URL",
    "CODESSEY_API_KEY",
    "CODESSEY_API_BASE",
    "AI_MODEL_NAME",
    "AI_TIMEOUT_SECONDS",
    "APP_ENV",
    "AI_MODE",
    "CONTEXT_TURNS",
)


def load_init_env() -> ModuleType:
    """실제 저장소 `.env`를 만들지 않고 모듈 함수를 불러옵니다."""

    spec = importlib.util.spec_from_file_location("local_init_env", INIT_ENV_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_init_env_creates_valid_mock_settings_without_printing_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """최초 실행은 무작위 키·빈 API 키·분리 DB를 만들고 키를 출력하지 않습니다."""

    module = load_init_env()
    destination = tmp_path / ".env"
    monkeypatch.setattr(module, "ENV_PATH", destination)
    for key in SETTING_KEYS:
        monkeypatch.delenv(key, raising=False)

    result = module.main(["--mode", "mock"])
    captured = capsys.readouterr()
    content = destination.read_text(encoding="utf-8")
    settings = Settings(_env_file=destination)

    assert result == 0
    assert settings.secret_key.lower() not in PLACEHOLDER_SECRET_KEYS
    assert len(settings.secret_key) >= 32
    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 1440
    assert settings.database_url == "sqlite:///./data/chatbot.mock.db"
    assert settings.codessey_api_key == ""
    assert settings.codessey_api_base == "https://api.openai.com/v1"
    assert settings.ai_model_name == "gpt-4o-mini"
    assert settings.ai_timeout_seconds == 8.0
    assert settings.app_env == "development"
    assert settings.ai_mode == "mock"
    assert settings.context_turns == 5
    assert settings.secret_key not in captured.out + captured.err
    assert 'CODESSEY_API_KEY=""' in content
    assert "mode=mock" in captured.out
    assert "database=sqlite:///./data/chatbot.mock.db" in captured.out
    assert captured.err == ""


def test_init_env_refuses_to_overwrite_existing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """두 번째 실행과 기존 수동 설정은 바이트 단위로 보존합니다."""

    module = load_init_env()
    destination = tmp_path / ".env"
    original = b"SECRET_KEY=operator-owned-value\n"
    destination.write_bytes(original)
    monkeypatch.setattr(module, "ENV_PATH", destination)

    result = module.main(["--mode", "mock"])
    captured = capsys.readouterr()

    assert result == 2
    assert destination.read_bytes() == original
    assert captured.out == ""
    assert captured.err == (
        "init_env: ERROR (.env already exists; refusing to overwrite)\n"
    )
    assert "operator-owned-value" not in captured.err


def test_init_env_rejects_real_mode_before_creating_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """실제 키·DB 결정을 자동화하지 않고 미지원 real 초기화를 거부합니다."""

    module = load_init_env()
    destination = tmp_path / ".env"
    monkeypatch.setattr(module, "ENV_PATH", destination)

    with pytest.raises(SystemExit) as raised:
        module.main(["--mode", "real"])

    assert raised.value.code == 2
    assert not destination.exists()


def test_init_env_publishes_only_complete_staged_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """최종 경로는 fsync를 마친 완성 파일을 게시할 때까지 보이지 않습니다."""

    module = load_init_env()
    destination = tmp_path / ".env"
    original_link = module.os.link

    def inspect_then_link(
        source: Path,
        target: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        assert target == destination
        assert follow_symlinks is False
        assert not target.exists()
        settings = Settings(_env_file=source)
        assert settings.ai_mode == "mock"
        assert settings.database_url == "sqlite:///./data/chatbot.mock.db"
        original_link(source, target, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(module.os, "link", inspect_then_link)

    module.create_environment_file(destination)

    assert destination.exists()
    assert list(tmp_path.glob(".env.*.tmp")) == []


def test_init_env_write_failure_preserves_concurrently_created_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """준비 중 실패해도 그 사이 운영자가 만든 최종 파일은 삭제하지 않습니다."""

    module = load_init_env()
    destination = tmp_path / ".env"
    operator_content = b"SECRET_KEY=operator-created-during-staging\n"

    def fail_after_operator_create() -> str:
        destination.write_bytes(operator_content)
        raise OSError("injected staging failure")

    monkeypatch.setattr(module, "build_mock_environment", fail_after_operator_create)

    with pytest.raises(OSError, match="injected staging failure"):
        module.create_environment_file(destination)

    assert destination.read_bytes() == operator_content
    assert list(tmp_path.glob(".env.*.tmp")) == []


def test_init_env_partial_staging_write_never_publishes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """일부만 쓴 뒤 실패하면 최종 파일 없이 소유한 staging만 정리합니다."""

    module = load_init_env()
    destination = tmp_path / ".env"
    original_write = module.os.write
    calls = 0

    def partial_then_fail(descriptor: int, content: memoryview) -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            return original_write(descriptor, content[:10])
        raise OSError("injected partial write failure")

    monkeypatch.setattr(module.os, "write", partial_then_fail)

    with pytest.raises(OSError, match="injected partial write failure"):
        module.create_environment_file(destination)

    assert calls == 2
    assert not destination.exists()
    assert list(tmp_path.glob(".env.*.tmp")) == []


def test_init_env_concurrent_creators_publish_exactly_once(tmp_path: Path) -> None:
    """동시 생성은 완성 파일 하나만 게시하고 나머지는 무덮어쓰기로 실패합니다."""

    module = load_init_env()
    destination = tmp_path / ".env"

    def attempt_create() -> bool:
        try:
            module.create_environment_file(destination)
        except FileExistsError:
            return False
        return True

    with ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(lambda _: attempt_create(), range(16)))

    settings = Settings(_env_file=destination)
    assert outcomes.count(True) == 1
    assert outcomes.count(False) == 15
    assert settings.ai_mode == "mock"
    assert settings.secret_key.lower() not in PLACEHOLDER_SECRET_KEYS
    assert list(tmp_path.glob(".env.*.tmp")) == []
