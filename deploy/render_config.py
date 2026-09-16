"""승인된 Linux 배포값으로 Nginx와 systemd 템플릿을 로컬 렌더링합니다."""

import argparse
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = PROJECT_ROOT / "deploy"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "deploy" / "generated"
ACCOUNT_PATTERN = re.compile(r"[a-z_][a-z0-9_-]{0,31}")
SERVER_LABEL = r"(?:[A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9-]{0,61}[A-Za-z0-9])"
SERVER_NAME_PATTERN = re.compile(
    rf"_|{SERVER_LABEL}(?:\.{SERVER_LABEL})*"
)
SAFE_PATH_PATTERN = re.compile(r"/[A-Za-z0-9._/-]+")


class RenderError(RuntimeError):
    """시스템 파일을 건드리기 전에 안전하지 않은 렌더 입력을 거부합니다."""


def configure_standard_streams() -> None:
    """Windows에서도 CLI 결과를 UTF-8로 출력합니다."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Nginx/systemd 설정을 로컬 디렉터리에만 렌더링합니다. "
            "설치·sudo·서비스 재시작은 수행하지 않습니다."
        )
    )
    parser.add_argument("--app-user", required=True)
    parser.add_argument("--app-group", required=True)
    parser.add_argument("--app-dir", required=True)
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--server-name", required=True)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def validate_account(value: str, label: str) -> str:
    if value == "root" or ACCOUNT_PATTERN.fullmatch(value) is None:
        raise RenderError(f"invalid {label}")
    return value


def validate_server_name(value: str) -> str:
    if len(value) > 253 or SERVER_NAME_PATTERN.fullmatch(value) is None:
        raise RenderError("invalid server-name")
    return value


def validate_posix_path(value: str, label: str) -> str:
    path = PurePosixPath(value)
    if (
        not path.is_absolute()
        or value == "/"
        or SAFE_PATH_PATTERN.fullmatch(value) is None
        or ".." in path.parts
        or "//" in value
    ):
        raise RenderError(f"invalid {label}")
    return value.rstrip("/")


def render_template(template_name: str, replacements: dict[str, str]) -> str:
    """알려진 placeholder를 모두 치환하고 미치환 값을 거부합니다."""

    rendered = (TEMPLATE_DIR / template_name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    if "{{" in rendered or "}}" in rendered:
        raise RenderError("unresolved template placeholder")
    return rendered


def write_atomic(path: Path, content: str) -> None:
    """같은 디렉터리의 임시 파일을 교체해 부분 파일을 남기지 않습니다."""

    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def render_configs(
    args: argparse.Namespace,
    *,
    output_dir_for_test: Path | None = None,
) -> tuple[Path, Path]:
    """고정된 두 파일만 만들며 기존 결과는 명시적 force 없이는 보존합니다."""

    replacements = {
        "APP_USER": validate_account(args.app_user, "app-user"),
        "APP_GROUP": validate_account(args.app_group, "app-group"),
        "APP_DIR": validate_posix_path(args.app_dir, "app-dir"),
        "ENV_FILE": validate_posix_path(args.env_file, "env-file"),
        "DATA_DIR": validate_posix_path(args.data_dir, "data-dir"),
        "SERVER_NAME": validate_server_name(args.server_name),
    }
    requested_output_dir = output_dir_for_test or DEFAULT_OUTPUT_DIR
    if requested_output_dir.is_symlink():
        raise RenderError("output directory must not be a symlink")
    output_dir = requested_output_dir.resolve()
    service_path = output_dir / "ai-assistant.service"
    nginx_path = output_dir / "ai-assistant.nginx.conf"
    for path in (service_path, nginx_path):
        if path.is_symlink():
            raise RenderError("output target must not be a symlink")
        if path.exists() and not path.is_file():
            raise RenderError("output target must be a regular file")
    existing = [path.name for path in (service_path, nginx_path) if path.exists()]
    if existing and not args.force:
        raise RenderError("output already exists; use --force after review")

    service = render_template("chatbot.service.template", replacements)
    nginx = render_template("nginx.conf.template", replacements)
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_dir.is_symlink():
        raise RenderError("output directory must not be a symlink")
    write_atomic(service_path, service)
    write_atomic(nginx_path, nginx)
    return service_path, nginx_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        service_path, nginx_path = render_configs(args)
    except (OSError, RenderError) as exc:
        print(f"render_deploy_config: ERROR ({exc})", file=sys.stderr)
        return 2
    print(f"render_deploy_config: service={service_path}")
    print(f"render_deploy_config: nginx={nginx_path}")
    print("render_deploy_config: no sudo, service, or network actions performed")
    return 0


if __name__ == "__main__":
    configure_standard_streams()
    raise SystemExit(main())
