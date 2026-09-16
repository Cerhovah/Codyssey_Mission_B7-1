"""테스트 전용 설정과 임시 데이터베이스 fixture."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from app.config import Settings


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """운영 파일과 분리된 테스트 설정을 반환합니다."""

    return Settings(
        _env_file=None,
        secret_key="test-only-secret-key-that-is-long-enough",
        database_url=f"sqlite:///{(tmp_path / 'chatbot.test.db').as_posix()}",
        app_env="test",
        ai_mode="mock",
    )


@pytest.fixture(autouse=True)
def clear_settings_cache() -> Iterator[None]:
    """각 테스트가 이전 환경 설정 캐시에 영향받지 않게 합니다."""

    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
