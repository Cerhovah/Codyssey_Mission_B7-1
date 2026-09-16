"""현재 설정의 SQLite에서 한 사용자의 최근 대화를 읽기 전용으로 확인합니다."""

import argparse
import asyncio
import json
from pathlib import Path
import sys

import aiosqlite
from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import Settings  # noqa: E402
from app.database import database_path_from_url  # noqa: E402


SQL_PATH = Path(__file__).with_name("check_logs.sql")


def configure_standard_streams() -> None:
    """Windows에서도 한글 대화가 UTF-8로 손상 없이 출력되게 합니다."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def positive_user_id(value: str) -> int:
    """CLI의 사용자 ID를 양의 정수로 제한합니다."""

    try:
        user_id = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("user-id는 양의 정수여야 합니다.") from exc
    if user_id <= 0:
        raise argparse.ArgumentTypeError("user-id는 양의 정수여야 합니다.")
    return user_id


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="현재 DATABASE_URL의 사용자별 최근 대화를 읽기 전용으로 조회합니다.",
    )
    parser.add_argument("--user-id", required=True, type=positive_user_id)
    return parser.parse_args(argv)


def display_database_path(path: Path) -> str:
    """개인 절대경로를 출력하지 않고 저장소 상대 위치만 표시합니다."""

    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return "<configured-outside-project>"


async def read_user_chats(user_id: int) -> tuple[Path, list[dict[str, object]]]:
    """설정 DB를 생성하지 않는 읽기 전용 연결로 고정 SQL을 실행합니다."""

    if Path.cwd().resolve() != PROJECT_ROOT:
        raise OSError("run from repository root")
    settings = Settings(_env_file=PROJECT_ROOT / ".env")
    database_path = database_path_from_url(settings.database_url)
    if not database_path.is_file():
        raise FileNotFoundError("configured database does not exist")

    sql = SQL_PATH.read_text(encoding="utf-8")
    readonly_uri = f"{database_path.as_uri()}?mode=ro"
    async with aiosqlite.connect(readonly_uri, uri=True) as connection:
        connection.row_factory = aiosqlite.Row
        await connection.execute("PRAGMA query_only = ON")
        rows = await (
            await connection.execute(sql, {"user_id": user_id})
        ).fetchall()
    return database_path, [dict(row) for row in rows]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        database_path, rows = asyncio.run(read_user_chats(args.user_id))
    except (ValidationError, OSError, aiosqlite.Error, ValueError) as exc:
        print(
            f"check_db: ERROR ({type(exc).__name__})",
            file=sys.stderr,
        )
        return 2

    print(
        "check_db: "
        f"database={display_database_path(database_path)} "
        f"user_id={args.user_id} rows={len(rows)}"
    )
    for row in rows:
        print(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    configure_standard_streams()
    raise SystemExit(main())
