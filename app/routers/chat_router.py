"""인증·문맥·AI·DB를 연결하는 채팅 및 내 기록 API."""

import asyncio
from collections.abc import AsyncIterator
import json
from typing import Annotated
from uuid import uuid4

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.ai_service import (
    AIServiceError,
    AITimeoutError,
    build_messages,
    generate_ai_response,
)
from app.auth import get_current_user
from app.config import Settings
from app.database import get_recent_chat_logs, list_chat_logs, save_chat_log
from app.logger import (
    log_ai_call_failed,
    log_ai_call_start,
    log_ai_call_success,
    log_db_save_failed,
    log_db_save_success,
    log_request_received,
)
from app.models import UserRow
from app.schemas import ChatLogItem, ChatRequest, ChatResponse, ErrorDetailResponse


router = APIRouter(tags=["채팅"])
CHAT_REQUEST_SCHEMA = ChatRequest.model_json_schema()


async def serialize_chat_user(
    request: Request,
    current_user: Annotated[UserRow, Depends(get_current_user)],
) -> AsyncIterator[UserRow]:
    """단일 프로세스에서 같은 사용자의 대화 turn 순서를 직렬화합니다."""

    guard: asyncio.Lock = request.app.state.chat_turn_locks_guard
    async with guard:
        user_lock = request.app.state.chat_turn_locks.setdefault(
            current_user.id,
            asyncio.Lock(),
        )
    async with user_lock:
        yield current_user


@router.post(
    "/api/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorDetailResponse},
        401: {"model": ErrorDetailResponse},
        422: {"model": ErrorDetailResponse},
        500: {"model": ErrorDetailResponse},
        504: {"model": ErrorDetailResponse},
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": CHAT_REQUEST_SCHEMA}},
        }
    },
)
async def chat(
    request: Request,
    response: Response,
    current_user: Annotated[UserRow, Depends(serialize_chat_user)],
) -> ChatResponse:
    """최근 문맥으로 AI 답변을 만든 뒤 commit 성공 후 반환합니다."""

    settings: Settings = request.app.state.settings
    request_id = uuid4().hex
    log_request_received(current_user.id, request.url.path)

    content_type_parts = [
        part.strip().lower()
        for part in request.headers.get("content-type", "").split(";")
    ]
    media_type = content_type_parts[0]
    charset_values = [
        part.split("=", 1)[1].strip('"')
        for part in content_type_parts[1:]
        if part.startswith("charset=")
    ]
    if media_type != "application/json" or any(
        charset not in {"utf-8", "utf8"} for charset in charset_values
    ):
        raise HTTPException(
            status_code=422,
            detail="입력 형식을 확인해 주세요.",
        )
    try:
        raw_payload = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=422,
            detail="입력 형식을 확인해 주세요.",
        ) from exc
    try:
        payload = ChatRequest.model_validate(raw_payload)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors(), body=raw_payload) from exc

    try:
        history = await get_recent_chat_logs(
            settings,
            current_user.id,
            settings.context_turns,
        )
    except aiosqlite.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 기록을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc

    messages = build_messages(history, payload.question)
    ai_mode = settings.resolved_ai_mode
    log_ai_call_start(current_user.id, request_id, ai_mode)
    try:
        result = await generate_ai_response(
            messages,
            request_id=request_id,
            settings=settings,
            http_client=request.app.state.ai_http_client,
        )
    except (AITimeoutError, asyncio.TimeoutError) as exc:
        log_ai_call_failed(request_id, "timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="현재 AI 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc
    except AIServiceError as exc:
        log_ai_call_failed(request_id, exc.error_code)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI 응답을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc

    if (
        not isinstance(result.answer, str)
        or not result.answer.strip()
        or isinstance(result.latency_ms, bool)
        or not isinstance(result.latency_ms, int)
        or result.latency_ms < 0
    ):
        log_ai_call_failed(request_id, "invalid_response")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI 응답을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.",
        )
    log_ai_call_success(request_id, result.latency_ms, ai_mode)

    try:
        saved = await save_chat_log(
            settings,
            current_user.id,
            payload.question,
            result.answer,
            result.latency_ms,
        )
    except aiosqlite.Error as exc:
        log_db_save_failed(current_user.id, "database_error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 기록을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc

    log_db_save_success(current_user.id, saved.id)
    response.headers["X-AI-Mode"] = ai_mode
    return ChatResponse(answer=result.answer, latency_ms=result.latency_ms)


@router.get(
    "/api/me/chats",
    response_model=list[ChatLogItem],
    responses={
        401: {"model": ErrorDetailResponse},
        500: {"model": ErrorDetailResponse},
    },
)
async def get_my_chats(
    request: Request,
    current_user: Annotated[UserRow, Depends(get_current_user)],
) -> list[ChatLogItem]:
    """검증된 현재 사용자의 기록만 배열로 반환합니다."""

    settings: Settings = request.app.state.settings
    log_request_received(current_user.id, request.url.path)
    try:
        rows = await list_chat_logs(settings, current_user.id)
    except aiosqlite.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 기록을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc
    return [ChatLogItem.model_validate(row) for row in rows]
