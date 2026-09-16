"""R19 배포 템플릿과 무변경 렌더러의 안전 경계 테스트."""

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RENDER_SCRIPT = PROJECT_ROOT / "deploy" / "render_config.py"
SERVICE_TEMPLATE = PROJECT_ROOT / "deploy" / "chatbot.service.template"
NGINX_TEMPLATE = PROJECT_ROOT / "deploy" / "nginx.conf.template"
DEPLOYMENT_GUIDE = PROJECT_ROOT / "docs" / "DEPLOYMENT.md"


def load_renderer() -> ModuleType:
    """CLI 부작용 없이 고정 경로 렌더 함수를 불러옵니다."""

    spec = importlib.util.spec_from_file_location("deployment_renderer", RENDER_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def renderer_arguments(*, force: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        app_user="ai-assistant",
        app_group="ai-assistant",
        app_dir="/srv/ai-assistant",
        env_file="/etc/ai-assistant/ai-assistant.env",
        data_dir="/var/lib/ai-assistant",
        server_name="chat.example.test",
        force=force,
    )


def test_templates_keep_private_single_worker_proxy_boundary() -> None:
    """systemd는 비root·내부 8000, Nginx는 80→127.0.0.1만 선언합니다."""

    service = SERVICE_TEMPLATE.read_text(encoding="utf-8")
    nginx = NGINX_TEMPLATE.read_text(encoding="utf-8")

    assert "/home/" not in service + nginx
    assert "SECRET_KEY" not in service + nginx
    assert "CODESSEY_API_KEY" not in service + nginx
    assert "User={{APP_USER}}" in service
    assert "Group={{APP_GROUP}}" in service
    assert "EnvironmentFile={{ENV_FILE}}" in service
    assert "--host 127.0.0.1 --port 8000 --workers 1" in service
    assert "--reload" not in service
    assert "Restart=on-failure" in service
    assert "NoNewPrivileges=true" in service
    assert "ProtectSystem=strict" in service
    assert "ReadWritePaths={{DATA_DIR}} {{APP_DIR}}/logs" in service
    assert "listen 80 default_server;" in nginx
    assert "proxy_pass http://127.0.0.1:8000;" in nginx
    assert "0.0.0.0:8000" not in service + nginx
    assert "proxy_read_timeout 15s;" in nginx
    assert "proxy_send_timeout 15s;" in nginx


def test_generated_deployment_files_are_git_ignored() -> None:
    """머신별 렌더 결과가 실수로 Git 후보가 되지 않습니다."""

    completed = subprocess.run(
        [
            "git",
            "check-ignore",
            "deploy/generated/ai-assistant.service",
            "deploy/generated/ai-assistant.nginx.conf",
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=30,
    )
    assert completed.returncode == 0
    assert set(completed.stdout.splitlines()) == {
        "deploy/generated/ai-assistant.service",
        "deploy/generated/ai-assistant.nginx.conf",
    }


def test_renderer_writes_only_reviewable_generated_files(tmp_path: Path) -> None:
    """정상 입력은 임시 출력 두 개만 만들고 placeholder를 모두 제거합니다."""

    renderer = load_renderer()
    output_dir = tmp_path / "generated"
    service_path, nginx_path = renderer.render_configs(
        renderer_arguments(),
        output_dir_for_test=output_dir,
    )

    assert service_path == output_dir / "ai-assistant.service"
    assert nginx_path == output_dir / "ai-assistant.nginx.conf"
    assert sorted(path.name for path in output_dir.iterdir()) == [
        "ai-assistant.nginx.conf",
        "ai-assistant.service",
    ]
    service = (output_dir / "ai-assistant.service").read_text(encoding="utf-8")
    nginx = (output_dir / "ai-assistant.nginx.conf").read_text(encoding="utf-8")
    assert "{{" not in service + nginx
    assert "User=ai-assistant" in service
    assert "WorkingDirectory=/srv/ai-assistant" in service
    assert "EnvironmentFile=/etc/ai-assistant/ai-assistant.env" in service
    assert "ReadWritePaths=/var/lib/ai-assistant /srv/ai-assistant/logs" in service
    assert "server_name chat.example.test;" in nginx

    preserved_service = service
    with pytest.raises(renderer.RenderError, match="output already exists"):
        renderer.render_configs(
            renderer_arguments(),
            output_dir_for_test=output_dir,
        )
    assert (output_dir / "ai-assistant.service").read_text(
        encoding="utf-8"
    ) == preserved_service

    renderer.render_configs(
        renderer_arguments(force=True),
        output_dir_for_test=output_dir,
    )
    assert (output_dir / "ai-assistant.service").read_text(
        encoding="utf-8"
    ) == preserved_service


@pytest.mark.parametrize(
    ("option", "value", "expected_error"),
    [
        ("--app-user", "root;id", "invalid app-user"),
        ("--app-user", "root", "invalid app-user"),
        ("--app-group", "UPPER", "invalid app-group"),
        ("--app-dir", "relative/app", "invalid app-dir"),
        ("--env-file", "/etc/../secret", "invalid env-file"),
        ("--data-dir", "/", "invalid data-dir"),
        ("--server-name", "example.test; return 200", "invalid server-name"),
    ],
)
def test_renderer_rejects_injection_and_ambiguous_paths(
    tmp_path: Path,
    option: str,
    value: str,
    expected_error: str,
) -> None:
    """systemd/Nginx 문법에 주입될 값과 상대·루트 경로를 거부합니다."""

    renderer = load_renderer()
    option_to_attribute = {
        "--app-user": "app_user",
        "--app-group": "app_group",
        "--app-dir": "app_dir",
        "--env-file": "env_file",
        "--data-dir": "data_dir",
        "--server-name": "server_name",
    }
    arguments = renderer_arguments()
    setattr(arguments, option_to_attribute[option], value)

    with pytest.raises(renderer.RenderError, match=expected_error):
        renderer.render_configs(
            arguments,
            output_dir_for_test=tmp_path / "rejected",
        )
    assert not (tmp_path / "rejected").exists()


def test_renderer_cli_has_no_arbitrary_output_directory_option() -> None:
    """CLI 결과 위치는 gitignored deploy/generated로 고정합니다."""

    completed = subprocess.run(
        [sys.executable, str(RENDER_SCRIPT), "--help"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=30,
    )
    assert completed.returncode == 0
    assert "--output-dir" not in completed.stdout


def test_renderer_rejects_nonregular_and_symlink_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """force를 사용해도 디렉터리·심볼릭 링크를 설정 파일처럼 덮지 않습니다."""

    renderer = load_renderer()
    output_dir = tmp_path / "generated"
    output_dir.mkdir()
    (output_dir / "ai-assistant.service").mkdir()

    with pytest.raises(renderer.RenderError, match="regular file"):
        renderer.render_configs(
            renderer_arguments(force=True),
            output_dir_for_test=output_dir,
        )

    symlink_output = tmp_path / "symlink-output"
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda path: path == symlink_output or original_is_symlink(path),
    )

    with pytest.raises(renderer.RenderError, match="must not be a symlink"):
        renderer.render_configs(
            renderer_arguments(force=True),
            output_dir_for_test=symlink_output,
        )


def test_deployment_guide_keeps_external_actions_blocked() -> None:
    """가이드는 비용·TLS·포트·swap·외부 검증의 승인 경계를 숨기지 않습니다."""

    guide = DEPLOYMENT_GUIDE.read_text(encoding="utf-8")

    for required_text in (
        "Ubuntu 22.04",
        "t2.micro",
        "2GB swap",
        "127.0.0.1:8000",
        "22/tcp",
        "8000/tcp",
        "HTTP 80",
        "HTTPS 443",
        "swapon --show --bytes",
        "nginx -t",
        "systemd-analyze verify",
        "default.disabled-ai-assistant",
        "기존 /swapfile fstab 항목을 검토하세요",
        "PUBLIC_URL=BLOCKED_EXTERNAL",
        "REAL_AI=BLOCKED_EXTERNAL",
    ):
        assert required_text in guide
    assert "무료를 가정하지 않습니다" in guide
    assert "OOM을 완전히 예방" in guide
    assert "실행하지 않았습니다" in guide
