"""대화 문맥 조립과 Mock·OpenAI 호환 AI 응답을 제공합니다."""

import asyncio
from dataclasses import dataclass
import json
from time import perf_counter
from typing import Literal

import httpx

from app.config import Settings
from app.models import ChatLogRow


SYSTEM_PROMPT = "사용자의 질문에 친절하고 정확한 한국어로 답변하세요."


@dataclass(frozen=True, slots=True)
class AIResult:
    """AI 답변과 측정된 처리 시간을 전달합니다."""

    answer: str
    latency_ms: int


AIErrorCode = Literal[
    "ai_service_error",
    "auth",
    "rate_limit",
    "upstream",
    "network",
    "invalid_json",
    "invalid_response",
]


class AIServiceError(RuntimeError):
    """외부 또는 설정 기반 AI 호출 실패를 나타냅니다."""

    def __init__(
        self,
        message: str = "ai_service_failed",
        *,
        error_code: AIErrorCode = "ai_service_error",
    ) -> None:
        super().__init__(message)
        self.error_code = error_code


class AITimeoutError(AIServiceError):
    """AI 제한 시간을 초과한 경우를 나타냅니다."""


def create_ai_http_client(
    settings: Settings,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> httpx.AsyncClient:
    """TLS 검증과 네 단계 timeout을 켠 수명주기용 HTTP 클라이언트를 만듭니다."""

    return httpx.AsyncClient(
        timeout=httpx.Timeout(settings.ai_timeout_seconds),
        verify=True,
        follow_redirects=False,
        transport=transport,
    )


def build_messages(
    history: list[ChatLogRow],
    question: str,
) -> list[dict[str, str]]:
    """시스템 1개, 최근 대화쌍, 현재 질문 순서로 문맥을 조립합니다."""

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in history:
        messages.append({"role": "user", "content": item.question})
        messages.append({"role": "assistant", "content": item.response})
    messages.append({"role": "user", "content": question})
    return messages


def _mock_answer(messages: list[dict[str, str]]) -> str:
    """외부 호출 없이 결정적인 개발용 답변을 만듭니다."""

    user_messages = [item["content"] for item in messages if item["role"] == "user"]
    current_question = user_messages[-1]
    previous_questions = user_messages[:-1]
    asks_previous = any(word in current_question for word in ("방금", "직전", "이전 질문"))
    if asks_previous and previous_questions:
        return f'[Mock] 직전 질문은 "{previous_questions[-1]}"입니다.'
    return f"[Mock] 질문을 받았습니다: {current_question}"


def _provider_error_code(status_code: int) -> AIErrorCode:
    """공급자 HTTP 상태를 비밀정보 없는 운영 분류명으로 바꿉니다."""

    if status_code in {401, 403}:
        return "auth"
    if status_code == 429:
        return "rate_limit"
    return "upstream"


def _parse_real_answer(response: httpx.Response) -> str:
    """OpenAI 호환 응답에서 비어 있지 않은 첫 답변만 꺼냅니다."""

    if response.status_code != 200:
        raise AIServiceError(error_code=_provider_error_code(response.status_code))

    try:
        payload = response.json()
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AIServiceError(error_code="invalid_json") from exc

    if not isinstance(payload, dict):
        raise AIServiceError(error_code="invalid_response")
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise AIServiceError(error_code="invalid_response")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise AIServiceError(error_code="invalid_response")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise AIServiceError(error_code="invalid_response")
    return content


async def _request_real_answer(
    messages: list[dict[str, str]],
    *,
    settings: Settings,
    http_client: httpx.AsyncClient,
) -> str:
    """설정된 OpenAI 호환 endpoint를 한 번 호출하고 응답을 파싱합니다."""

    response = await http_client.post(
        f"{settings.codessey_api_base.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {settings.codessey_api_key}"},
        json={
            "model": settings.ai_model_name,
            "messages": messages,
            "stream": False,
        },
    )
    return _parse_real_answer(response)


async def generate_ai_response(
    messages: list[dict[str, str]],
    *,
    request_id: str,
    settings: Settings,
    http_client: httpx.AsyncClient,
) -> AIResult:
    """판정된 모드 하나만 실행하며 real 실패를 Mock으로 대체하지 않습니다."""

    del request_id
    started_at = perf_counter()
    if settings.resolved_ai_mode == "mock":
        await asyncio.sleep(0)
        answer = _mock_answer(messages)
    else:
        try:
            answer = await asyncio.wait_for(
                _request_real_answer(
                    messages,
                    settings=settings,
                    http_client=http_client,
                ),
                timeout=settings.ai_timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise AITimeoutError("ai_timeout") from exc
        except httpx.TimeoutException as exc:
            raise AITimeoutError("ai_timeout") from exc
        except httpx.RequestError as exc:
            raise AIServiceError(error_code="network") from exc
    latency_ms = max(0, int((perf_counter() - started_at) * 1000))
    return AIResult(answer=answer, latency_ms=latency_ms)
