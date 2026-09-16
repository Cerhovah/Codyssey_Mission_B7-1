"""R18 로컬 DB·smoke·Git 기여 감사 도구의 실제 실행 회귀 테스트."""

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECK_DB_SCRIPT = PROJECT_ROOT / "scripts" / "check_db.py"
SMOKE_SCRIPT = PROJECT_ROOT / "scripts" / "smoke_test.py"
AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "audit_contributions.py"
CONFIG_ENV_KEYS = {
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
}


def script_environment(**overrides: str) -> dict[str, str]:
    """개발자 머신의 실제 앱 설정을 자식 검증 프로세스에서 제거합니다."""

    environment = os.environ.copy()
    for key in CONFIG_ENV_KEYS:
        environment.pop(key, None)
    environment.update(overrides)
    return environment


def run_python_script(
    script: Path,
    *arguments: str,
    environment: dict[str, str] | None = None,
    working_directory: Path = PROJECT_ROOT,
) -> subprocess.CompletedProcess[str]:
    """현재 가상환경 Python으로 CLI를 UTF-8 캡처해 실행합니다."""

    return subprocess.run(
        [sys.executable, str(script), *arguments],
        cwd=working_directory,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=30,
    )


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_check_logs_sql_keeps_bound_user_query_contract() -> None:
    """SQL 파일이 사용자 바인딩·최신 20행 계약과 정확히 일치합니다."""

    sql = (PROJECT_ROOT / "scripts" / "check_logs.sql").read_text(
        encoding="utf-8"
    )

    assert sql == (
        "SELECT id, user_id, question, response, latency_ms, created_at\n"
        "FROM chat_logs\n"
        "WHERE user_id = :user_id\n"
        "ORDER BY id DESC\n"
        "LIMIT 20;\n"
    )


def test_check_db_reads_only_selected_users_latest_twenty(tmp_path: Path) -> None:
    """현재 설정 DB에서 다른 사용자를 섞지 않고 최신 20행만 읽습니다."""

    database_path = tmp_path / "verification.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                response TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        for sequence in range(1, 26):
            connection.execute(
                """
                INSERT INTO chat_logs
                    (user_id, question, response, latency_ms, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    1,
                    f"선택사용자-질문-{sequence}{'🙂' if sequence == 25 else ''}",
                    f"선택사용자-답변-{sequence}",
                    sequence,
                    f"2026-01-01T00:00:{sequence:02d}",
                ),
            )
        connection.execute(
            """
            INSERT INTO chat_logs
                (user_id, question, response, latency_ms, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (2, "다른사용자-비공개-질문", "다른사용자-비공개-답변", 999, "later"),
        )
        connection.commit()

    bytes_before = database_path.read_bytes()
    environment = script_environment(
        SECRET_KEY="check-db-test-secret-key-that-is-long-enough",
        DATABASE_URL=sqlite_url(database_path),
        CODESSEY_API_KEY="",
        CODESSEY_API_BASE="https://provider.invalid/v1",
        AI_MODEL_NAME="test-model",
        APP_ENV="test",
        AI_MODE="mock",
    )

    completed = run_python_script(
        CHECK_DB_SCRIPT,
        "--user-id",
        "1",
        environment=environment,
    )

    assert completed.returncode == 0, completed.stderr
    lines = completed.stdout.splitlines()
    assert lines[0] == (
        "check_db: database=<configured-outside-project> user_id=1 rows=20"
    )
    rows = [json.loads(line) for line in lines[1:]]
    assert [row["id"] for row in rows] == list(range(25, 5, -1))
    assert {row["user_id"] for row in rows} == {1}
    assert all("선택사용자" in row["question"] for row in rows)
    assert rows[0]["question"].endswith("🙂")
    assert "다른사용자-비공개" not in completed.stdout
    assert str(tmp_path) not in completed.stdout + completed.stderr
    assert database_path.read_bytes() == bytes_before

    injection = run_python_script(
        CHECK_DB_SCRIPT,
        "--user-id",
        "1 OR 1=1",
        environment=environment,
    )
    assert injection.returncode == 2
    assert "rows=" not in injection.stdout
    assert database_path.read_bytes() == bytes_before


def test_check_db_does_not_create_a_missing_database(tmp_path: Path) -> None:
    """설정 DB가 없을 때 빈 SQLite 파일을 만드는 대신 안전하게 실패합니다."""

    missing_database = tmp_path / "missing.db"
    environment = script_environment(
        SECRET_KEY="check-db-test-secret-key-that-is-long-enough",
        DATABASE_URL=sqlite_url(missing_database),
        CODESSEY_API_KEY="",
        CODESSEY_API_BASE="https://provider.invalid/v1",
        AI_MODEL_NAME="test-model",
        APP_ENV="test",
        AI_MODE="mock",
    )

    completed = run_python_script(
        CHECK_DB_SCRIPT,
        "--user-id",
        "1",
        environment=environment,
    )

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "check_db: ERROR (FileNotFoundError)" in completed.stderr
    assert str(tmp_path) not in completed.stderr
    assert not missing_database.exists()


def test_smoke_ignores_hostile_real_configuration_and_leaves_no_state(
    tmp_path: Path,
) -> None:
    """host 환경이 real이어도 smoke는 외부 호출·운영 DB·로그를 건드리지 않습니다."""

    hostile_database = tmp_path / "must-not-open.db"
    hostile_database.write_bytes(b"must remain byte-for-byte unchanged")
    bytes_before = hostile_database.read_bytes()
    log_path = PROJECT_ROOT / "logs" / "app.log"
    log_before = (
        (log_path.stat().st_size, log_path.stat().st_mtime_ns)
        if log_path.exists()
        else None
    )
    sentinel_api_key = "SENTINEL_REAL_API_KEY_MUST_NOT_APPEAR"
    sentinel_secret = "sentinel-host-secret-that-is-long-enough"
    environment = script_environment(
        SECRET_KEY=sentinel_secret,
        DATABASE_URL=sqlite_url(hostile_database),
        CODESSEY_API_KEY=sentinel_api_key,
        CODESSEY_API_BASE="https://example.invalid/v1",
        AI_MODEL_NAME="hostile-real-model",
        ALGORITHM="none",
        ACCESS_TOKEN_EXPIRE_MINUTES="0",
        AI_TIMEOUT_SECONDS="-1",
        APP_ENV="production",
        AI_MODE="real",
        CONTEXT_TURNS="999",
    )

    completed = run_python_script(SMOKE_SCRIPT, environment=environment)

    combined_output = completed.stdout + completed.stderr
    assert completed.returncode == 0, combined_output
    assert (
        "smoke_test: PASS health=200 register=201 login=200 chat=200 "
        "history_rows=1 mode=mock external_calls=0"
    ) in completed.stdout
    for sensitive_value in (
        sentinel_api_key,
        sentinel_secret,
        "smoke-pass-1234",
        "smoke round trip",
        "access_token",
    ):
        assert sensitive_value not in combined_output
    assert hostile_database.read_bytes() == bytes_before
    log_after = (
        (log_path.stat().st_size, log_path.stat().st_mtime_ns)
        if log_path.exists()
        else None
    )
    assert log_after == log_before


def run_git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """테스트 저장소에서만 로컬 Git 명령을 실행합니다."""

    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    return completed


def commit_file(
    repository: Path,
    filename: str,
    content: str,
    subject: str,
    email: str,
) -> str:
    """지정한 primary author 한 명으로 파일 커밋을 만듭니다."""

    (repository / filename).write_text(content, encoding="utf-8")
    run_git(repository, "add", "--", filename)
    run_git(
        repository,
        "-c",
        "user.name=Test Author",
        "-c",
        f"user.email={email}",
        "commit",
        "-m",
        subject,
    )
    return run_git(repository, "rev-parse", "HEAD").stdout.strip()


def test_audit_uses_exact_range_author_and_nonempty_nonmerge_candidates(
    tmp_path: Path,
) -> None:
    """다른 ref·이메일·merge·빈 커밋을 유효 후보로 잘못 세지 않습니다."""

    repository = tmp_path / "audit-repository"
    repository.mkdir()
    run_git(repository, "init", "--initial-branch=main")
    run_git(repository, "config", "user.name", "Test Author")
    run_git(repository, "config", "user.email", "target@example.com")

    base_sha = commit_file(
        repository,
        "base.txt",
        "base",
        "base commit",
        "base@example.com",
    )
    run_git(repository, "switch", "-c", "side-only")
    side_sha = commit_file(
        repository,
        "side.txt",
        "side",
        "side branch only",
        "target@example.com",
    )
    run_git(repository, "switch", "main")

    first_sha = commit_file(
        repository,
        "first.txt",
        "first",
        "기능 한글 제목",
        "target@example.com",
    )
    alias_sha = commit_file(
        repository,
        "alias.txt",
        "alias",
        "same name different email",
        "alias@example.com",
    )
    run_git(
        repository,
        "-c",
        "user.name=Test Author",
        "-c",
        "user.email=target@example.com",
        "commit",
        "--allow-empty",
        "-m",
        "empty candidate",
    )
    empty_sha = run_git(repository, "rev-parse", "HEAD").stdout.strip()

    run_git(repository, "switch", "-c", "merge-source")
    merged_change_sha = commit_file(
        repository,
        "merged.txt",
        "merged change",
        "merged branch change",
        "target@example.com",
    )
    run_git(repository, "switch", "main")
    run_git(
        repository,
        "-c",
        "user.name=Test Author",
        "-c",
        "user.email=target@example.com",
        "merge",
        "--no-ff",
        "merge-source",
        "-m",
        "merge commit must be excluded",
    )
    merge_sha = run_git(repository, "rev-parse", "HEAD").stdout.strip()
    escape_sha = commit_file(
        repository,
        "escape.txt",
        "terminal safety",
        "escape\x1b[2Jsubject🙂",
        "target@example.com",
    )
    run_git(
        repository,
        "remote",
        "add",
        "origin",
        "ssh://token:secret@example.com/private/repository.git",
    )

    completed = run_python_script(
        AUDIT_SCRIPT,
        "--repository",
        str(repository),
        "--ref",
        "main",
        "--base",
        base_sha,
        "--author-email",
        "target@example.com",
        "--minimum",
        "3",
    )

    assert completed.returncode == 0, completed.stderr
    output = completed.stdout
    assert "repository: ssh://example.com/private/repository.git" in output
    assert "token" not in output
    assert "secret" not in output
    assert f"ref: main -> {escape_sha}" in output
    assert f"base: {base_sha} -> {base_sha}" in output
    assert "Test Author <target@example.com>: 4" in output
    assert "Test Author <alias@example.com>: 1" in output
    assert f"{first_sha} 기능 한글 제목" in output
    assert f"{merged_change_sha} merged branch change" in output
    assert f"{empty_sha} empty candidate" in output
    assert f"{escape_sha} escape�[2Jsubject🙂" in output
    assert "\x1b" not in output
    assert "files: <no changed files>" in output
    assert "candidate_count: 3" in output
    assert "under_minimum: NO" in output
    assert "empty_diff_candidates: 1" in output
    assert "content_review: NEEDS_HUMAN_REVIEW" in output
    assert "pr_evidence: NOT_RUN" in output
    assert "remote_fetch: NOT_RUN" in output
    assert side_sha not in output
    assert alias_sha not in output
    assert merge_sha not in output.split("candidate_commits:", 1)[1]

    under_minimum = run_python_script(
        AUDIT_SCRIPT,
        "--repository",
        str(repository),
        "--ref",
        "main",
        "--base",
        base_sha,
        "--author-email",
        "target@example.com",
        "--minimum",
        "4",
    )
    assert under_minimum.returncode == 1
    assert "candidate_count: 3" in under_minimum.stdout
    assert "under_minimum: YES" in under_minimum.stdout

    invalid_ref = run_python_script(
        AUDIT_SCRIPT,
        "--repository",
        str(repository),
        "--ref=-malicious",
        "--base",
        base_sha,
        "--author-email",
        "target@example.com",
    )
    assert invalid_ref.returncode == 2
    assert invalid_ref.stdout == ""
    assert "audit_contributions: NOT_RUN (invalid ref)" in invalid_ref.stderr

    non_ancestor = run_python_script(
        AUDIT_SCRIPT,
        "--repository",
        str(repository),
        "--ref",
        "side-only",
        "--base",
        first_sha,
        "--author-email",
        "target@example.com",
    )
    assert non_ancestor.returncode == 2
    assert "NOT_RUN (base is not an ancestor of ref)" in non_ancestor.stderr

    invalid_email = run_python_script(
        AUDIT_SCRIPT,
        "--repository",
        str(repository),
        "--ref",
        "main",
        "--base",
        base_sha,
        "--author-email=target@example.com\x1b[2J",
    )
    assert invalid_email.returncode == 2
    assert invalid_email.stdout == ""
    assert invalid_email.stderr == (
        "audit_contributions: NOT_RUN (invalid author-email)\n"
    )

    verified_shape_only = run_python_script(
        AUDIT_SCRIPT,
        "--repository",
        str(repository),
        "--ref",
        "main",
        "--base",
        base_sha,
        "--author-email",
        "target@example.com",
        "--minimum",
        "3",
        "--pr-url",
        "https://github.com/example/repository/pull/1?token=PRIVATE#fragment",
    )
    assert verified_shape_only.returncode == 0
    assert "pr_evidence: PROVIDED_UNVERIFIED" in verified_shape_only.stdout
    assert "https://github.com/example/repository/pull/1" in verified_shape_only.stdout
    assert "PRIVATE" not in verified_shape_only.stdout
    assert "fragment" not in verified_shape_only.stdout

    malformed_pr = run_python_script(
        AUDIT_SCRIPT,
        "--repository",
        str(repository),
        "--ref",
        "main",
        "--base",
        base_sha,
        "--author-email",
        "target@example.com",
        "--pr-url",
        "https://example.com:bad/pull/1",
    )
    assert malformed_pr.returncode == 2
    assert malformed_pr.stderr == "audit_contributions: NOT_RUN (invalid pr-url)\n"

    run_git(
        repository,
        "remote",
        "set-url",
        "origin",
        "https://example.com:bad/private-token",
    )
    malformed_origin = run_python_script(
        AUDIT_SCRIPT,
        "--repository",
        str(repository),
        "--ref",
        "main",
        "--base",
        base_sha,
        "--author-email",
        "target@example.com",
        "--minimum",
        "3",
    )
    assert malformed_origin.returncode == 0
    assert "repository: <opaque-remote>" in malformed_origin.stdout
    assert "private-token" not in malformed_origin.stdout
