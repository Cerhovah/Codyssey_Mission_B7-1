"""모든 API 오류를 안전한 한국어 detail 문자열로 통일합니다."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger("ai_assistant.errors")


def _validation_message(request: Request, exc: RequestValidationError) -> tuple[int, str]:
    """경로와 필드 경계만 보고 계약상의 상태와 안내를 고릅니다."""

    body: Any = exc.body
    if not isinstance(body, dict):
        body = {}

    path = request.url.path
    username = body.get("username")
    question = body.get("question")

    if path == "/api/auth/register" and isinstance(username, str):
        trimmed_username = username.strip()
        if not trimmed_username:
            return 400, "아이디는 공백일 수 없습니다."
        if len(trimmed_username) < 3:
            return 422, "아이디는 최소 3자 이상이어야 합니다."
    if path == "/api/chat" and isinstance(question, str) and not question.strip():
        return 400, "질문 내용은 공백일 수 없습니다."

    errors = exc.errors()
    for error in errors:
        location = error.get("loc", ())
        field = location[-1] if location else None
        error_type = str(error.get("type", ""))

        if path == "/api/auth/register":
            if field == "username" and "too_short" in error_type:
                return 422, "아이디는 최소 3자 이상이어야 합니다."
            if field == "username" and "too_long" in error_type:
                return 422, "아이디는 최대 50자까지 입력 가능합니다."
            if field == "password" and "too_short" in error_type:
                return 422, "비밀번호는 최소 4자 이상이어야 합니다."
            if field == "password" and "too_long" in error_type:
                return 422, "비밀번호는 최대 100자까지 입력 가능합니다."
            if field == "password" and error_type == "value_error":
                return 422, "비밀번호는 공백일 수 없습니다."

        if path == "/api/auth/login" and field in {"username", "password"}:
            return 422, "아이디와 비밀번호를 확인해 주세요."

        if path == "/api/chat" and field == "question" and "too_long" in error_type:
            return 422, "질문은 최대 500자까지 입력 가능합니다."

    return 422, "입력 형식을 확인해 주세요."


def register_error_handlers(application: FastAPI) -> None:
    """FastAPI와 Starlette 예외를 공통 JSON 구조로 등록합니다."""

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        status_code, message = _validation_message(request, exc)
        return JSONResponse(status_code=status_code, content={"detail": message})

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        _request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "요청을 처리할 수 없습니다."
        if detail == "Not Found":
            detail = "요청한 경로를 찾을 수 없습니다."
        elif detail == "Method Not Allowed":
            detail = "허용되지 않은 요청 방식입니다."
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail},
            headers=exc.headers,
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.error("unexpected_server_error error_type=%s", type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content={"detail": "서버 처리 중 오류가 발생했습니다."},
        )
