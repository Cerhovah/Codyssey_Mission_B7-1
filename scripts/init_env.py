"""기존 파일을 덮지 않고 로컬 Mock 개발용 `.env`를 한 번 생성합니다."""

import argparse
import os
from pathlib import Path
import secrets
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
MOCK_DATABASE_URL = "sqlite:///./data/chatbot.mock.db"


def configure_standard_streams() -> None:
    """Windows에서도 결과를 UTF-8로 표시합니다."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="비밀값을 출력하지 않고 개발용 Mock `.env`를 최초 한 번 만듭니다.",
    )
    parser.add_argument("--mode", required=True, choices=("mock",))
    return parser.parse_args(argv)


def build_mock_environment() -> str:
    """팀 키 이름을 유지하고 실 API 키가 빈 Mock 설정을 만듭니다."""

    secret_key = secrets.token_urlsafe(32)
    return (
        "# scripts/init_env.py가 만든 로컬 Mock 개발 설정\n"
        f'SECRET_KEY="{secret_key}"\n'
        'ALGORITHM="HS256"\n'
        "ACCESS_TOKEN_EXPIRE_MINUTES=1440\n"
        f'DATABASE_URL="{MOCK_DATABASE_URL}"\n'
        'CODESSEY_API_KEY=""\n'
        'CODESSEY_API_BASE="https://api.openai.com/v1"\n'
        'AI_MODEL_NAME="gpt-4o-mini"\n'
        "AI_TIMEOUT_SECONDS=8.0\n"
        "APP_ENV=development\n"
        "AI_MODE=mock\n"
        "CONTEXT_TURNS=5\n"
    )


def create_environment_file(destination: Path | None = None) -> None:
    """완성한 임시 파일을 hard link로 원자적·무덮어쓰기 게시합니다."""

    target = destination or ENV_PATH
    payload = build_mock_environment().encode("utf-8")
    descriptor, staging_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    staging_path = Path(staging_name)
    owner_stat = os.fstat(descriptor)
    try:
        remaining = memoryview(payload)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("short write while staging .env")
            remaining = remaining[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1

        # os.link는 대상이 이미 있으면 원자적으로 실패하므로, 완성 전 파일 노출과
        # 동시 실행의 덮어쓰기를 모두 피합니다. 실패 시 target은 절대 삭제하지 않습니다.
        os.link(staging_path, target, follow_symlinks=False)
    finally:
        try:
            if descriptor >= 0:
                os.close(descriptor)
        except OSError:
            pass

        # 무작위 staging 경로가 외부에서 교체됐다면 그 파일도 삭제하지 않습니다.
        try:
            current_stat = staging_path.lstat()
        except FileNotFoundError:
            pass
        else:
            if os.path.samestat(owner_stat, current_stat):
                staging_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        create_environment_file()
    except FileExistsError:
        print(
            "init_env: ERROR (.env already exists; refusing to overwrite)",
            file=sys.stderr,
        )
        return 2
    except OSError as exc:
        print(f"init_env: ERROR ({type(exc).__name__})", file=sys.stderr)
        return 2

    print(f"init_env: created .env mode={args.mode} database={MOCK_DATABASE_URL}")
    print("init_env: secret and API key values were not printed")
    return 0


if __name__ == "__main__":
    configure_standard_streams()
    raise SystemExit(main())
