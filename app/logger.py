"""과제 표준 운영 이벤트를 중복 없이 기록합니다."""

import logging
from pathlib import Path
import sys


app_logger = logging.getLogger("ai_assistant")
_HANDLER_MARKER = "ai_assistant_managed"


def configure_logging(log_path: Path) -> None:
    """stdout과 파일 handler를 프로세스당 한 번만 구성합니다."""

    if any(getattr(handler, _HANDLER_MARKER, False) for handler in app_logger.handlers):
        return

    log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    setattr(stream_handler, _HANDLER_MARKER, True)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    setattr(file_handler, _HANDLER_MARKER, True)

    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False
    app_logger.addHandler(stream_handler)
    app_logger.addHandler(file_handler)


def log_request_received(user_id: int | str, path: str) -> None:
    """인증 결과가 확인된 요청 수신 이벤트를 기록합니다."""

    app_logger.info("request_received user_id=%s path=%s", user_id, path)


def log_ai_call_start(user_id: int, request_id: str, ai_mode: str) -> None:
    """AI 호출 시작 이벤트를 기록합니다."""

    app_logger.info(
        "ai_call_start user_id=%s request_id=%s mode=%s",
        user_id,
        request_id,
        ai_mode,
    )


def log_ai_call_success(request_id: str, latency_ms: int, ai_mode: str) -> None:
    """AI 응답 성공 이벤트를 기록합니다."""

    app_logger.info(
        "ai_call_success request_id=%s latency_ms=%s mode=%s",
        request_id,
        latency_ms,
        ai_mode,
    )


def log_ai_call_failed(request_id: str, error_detail: str) -> None:
    """비밀값 없는 분류명으로 AI 실패 이벤트를 기록합니다."""

    app_logger.error("ai_call_failed request_id=%s error=%s", request_id, error_detail)


def log_db_save_success(user_id: int, chat_id: int) -> None:
    """대화 DB commit 성공 이벤트를 기록합니다."""

    app_logger.info("db_save_success user_id=%s chat_id=%s", user_id, chat_id)


def log_db_save_failed(user_id: int, error_detail: str) -> None:
    """비밀값 없는 분류명으로 DB 저장 실패 이벤트를 기록합니다."""

    app_logger.error("db_save_failed user_id=%s error=%s", user_id, error_detail)
