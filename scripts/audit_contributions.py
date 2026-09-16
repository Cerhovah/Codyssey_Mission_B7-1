"""명시한 Git 범위와 작성자 이메일의 non-merge 기여 후보를 읽기 전용 감사합니다."""

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys
import unicodedata
from urllib.parse import urlsplit, urlunsplit


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AuditError(RuntimeError):
    """원격 변경 없이 로컬 Git 감사를 중단해야 하는 입력 오류입니다."""


def configure_standard_streams() -> None:
    """커밋 제목을 Windows에서도 UTF-8로 그대로 표시합니다."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


@dataclass(frozen=True, slots=True)
class Commit:
    sha: str
    author_name: str
    author_email: str
    subject: str
    files: tuple[str, ...]


def positive_integer(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("minimum은 양의 정수여야 합니다.") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("minimum은 양의 정수여야 합니다.")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="정확한 base..ref 범위의 작성자별 로컬 Git 기여 후보를 감사합니다.",
    )
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--author-email", required=True)
    parser.add_argument("--minimum", type=positive_integer, default=10)
    parser.add_argument("--pr-url", action="append", default=[])
    return parser.parse_args(argv)


def run_git(
    repository: Path,
    *arguments: str,
    allowed_returncodes: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[str]:
    """shell 해석과 네트워크 작업 없이 로컬 Git 명령만 실행합니다."""

    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode not in allowed_returncodes:
        raise AuditError(f"git command failed: {arguments[0]}")
    return completed


def validate_revision_input(value: str, label: str) -> None:
    if (
        not value
        or value.startswith("-")
        or any(
            unicodedata.category(character) in {"Cc", "Cf", "Cs"}
            for character in value
        )
    ):
        raise AuditError(f"invalid {label}")


def resolve_revision(repository: Path, value: str, label: str) -> str:
    validate_revision_input(value, label)
    return run_git(
        repository,
        "rev-parse",
        "--verify",
        "--end-of-options",
        f"{value}^{{commit}}",
    ).stdout.strip()


def one_line(value: str) -> str:
    """커밋 메타데이터의 제어문자가 터미널 구조를 바꾸지 않게 합니다."""

    sanitized = "".join(
        " "
        if character.isspace()
        else "�"
        if unicodedata.category(character) in {"Cc", "Cf", "Cs"}
        else character
        for character in value
    )
    return " ".join(sanitized.split())


def validate_author_email(value: str) -> None:
    """정확 비교와 안전한 출력을 해치는 이메일 입력을 거부합니다."""

    if (
        not value
        or value.count("@") != 1
        or any(
            character.isspace()
            or unicodedata.category(character) in {"Cc", "Cf", "Cs"}
            for character in value
        )
    ):
        raise AuditError("invalid author-email")


def changed_files(repository: Path, sha: str) -> tuple[str, ...]:
    output = run_git(
        repository,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        "-z",
        sha,
    ).stdout
    return tuple(one_line(path) for path in output.split("\0") if path)


def read_non_merge_commits(repository: Path, base_sha: str, ref_sha: str) -> list[Commit]:
    output = run_git(
        repository,
        "log",
        "--no-merges",
        "-z",
        "--format=format:%H%x00%an%x00%ae%x00%s",
        f"{base_sha}..{ref_sha}",
    ).stdout
    fields = output.split("\0") if output else []
    if len(fields) % 4 != 0:
        raise AuditError("unexpected git log format")
    commits: list[Commit] = []
    for offset in range(0, len(fields), 4):
        sha, name, email, subject = fields[offset : offset + 4]
        commits.append(
            Commit(
                sha=sha,
                author_name=one_line(name),
                author_email=one_line(email),
                subject=one_line(subject),
                files=changed_files(repository, sha),
            )
        )
    return commits


def safe_repository_label(repository: Path) -> str:
    """origin의 자격정보·query를 제거하고 저장소 식별자만 표시합니다."""

    completed = run_git(
        repository,
        "remote",
        "get-url",
        "origin",
        allowed_returncodes=(0, 2),
    )
    if completed.returncode != 0:
        return f"{repository.name} (local)"
    remote = completed.stdout.strip()
    if Path(remote).is_absolute() or PureWindowsPath(remote).is_absolute():
        return "<local-file-remote>"
    try:
        parsed = urlsplit(remote)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return "<opaque-remote>"
    if parsed.scheme in {"http", "https", "ssh"} and hostname:
        host = f"[{hostname}]" if ":" in hostname else hostname
        if port is not None:
            host = f"{host}:{port}"
        return one_line(urlunsplit((parsed.scheme, host, parsed.path, "", "")))
    if parsed.scheme == "file":
        return "<local-file-remote>"
    scp_match = re.fullmatch(
        r"(?:[^@\s]+@)?([A-Za-z0-9.-]+):([^\r\n]+)",
        remote,
    )
    if scp_match:
        return one_line(f"{scp_match.group(1)}:{scp_match.group(2)}")
    return "<opaque-remote>"


def validate_pr_urls(urls: list[str]) -> list[str]:
    safe_urls: list[str] = []
    for url in urls:
        if any(
            unicodedata.category(character) in {"Cc", "Cf", "Cs"}
            for character in url
        ):
            raise AuditError("invalid pr-url")
        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            port = parsed.port
        except ValueError as exc:
            raise AuditError("invalid pr-url") from exc
        if (
            parsed.scheme != "https"
            or not hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise AuditError("invalid pr-url")
        host = f"[{hostname}]" if ":" in hostname else hostname
        if port is not None:
            host = f"{host}:{port}"
        safe_urls.append(one_line(urlunsplit(("https", host, parsed.path, "", ""))))
    return safe_urls


def audit(args: argparse.Namespace) -> int:
    repository = args.repository.resolve()
    if not repository.is_dir():
        raise AuditError("repository directory does not exist")
    inside = run_git(repository, "rev-parse", "--is-inside-work-tree").stdout.strip()
    if inside != "true":
        raise AuditError("repository is not a Git work tree")

    validate_author_email(args.author_email)
    base_sha = resolve_revision(repository, args.base, "base")
    ref_sha = resolve_revision(repository, args.ref, "ref")
    ancestry = run_git(
        repository,
        "merge-base",
        "--is-ancestor",
        base_sha,
        ref_sha,
        allowed_returncodes=(0, 1),
    )
    if ancestry.returncode != 0:
        raise AuditError("base is not an ancestor of ref")

    commits = read_non_merge_commits(repository, base_sha, ref_sha)
    author_counts = Counter(
        (commit.author_name, commit.author_email) for commit in commits
    )
    authored_commits = [
        commit for commit in commits if commit.author_email == args.author_email
    ]
    empty_candidates = [commit for commit in authored_commits if not commit.files]
    candidates = [commit for commit in authored_commits if commit.files]
    pr_urls = validate_pr_urls(args.pr_url)

    print(f"repository: {safe_repository_label(repository)}")
    print(f"ref: {args.ref} -> {ref_sha}")
    print(f"base: {args.base} -> {base_sha}")
    print(f"range: {base_sha}..{ref_sha}")
    print("actual_authors:")
    for (name, email), count in sorted(
        author_counts.items(),
        key=lambda item: (item[0][1], item[0][0]),
    ):
        print(f"  - {name} <{email}>: {count}")

    print(f"candidate_email: {args.author_email}")
    print("candidate_commits:")
    if not authored_commits:
        print("  - <none>")
    for commit in authored_commits:
        files = ", ".join(commit.files) if commit.files else "<no changed files>"
        print(f"  - {commit.sha} {commit.subject}")
        print(f"    files: {files}")

    under_minimum = len(candidates) < args.minimum
    print(f"candidate_count: {len(candidates)}")
    print(f"minimum_required: {args.minimum}")
    print(f"under_minimum: {'YES' if under_minimum else 'NO'}")
    print(f"empty_diff_candidates: {len(empty_candidates)}")
    print("content_review: NEEDS_HUMAN_REVIEW")
    if pr_urls:
        print("pr_evidence: PROVIDED_UNVERIFIED")
        for url in pr_urls:
            print(f"  - {url}")
    else:
        print("pr_evidence: NOT_RUN")
    print("remote_fetch: NOT_RUN")
    return 1 if under_minimum else 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return audit(args)
    except AuditError as exc:
        print(f"audit_contributions: NOT_RUN ({exc})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    configure_standard_streams()
    raise SystemExit(main())
