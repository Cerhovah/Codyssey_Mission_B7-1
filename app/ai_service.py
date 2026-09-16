"""대화 문맥 조립과 개발용 Mock AI 응답을 제공합니다."""

import asyncio
from dataclasses import dataclass
from time import perf_counter

from app.config import Settings
from app.models import ChatLogRow


SYSTEM_PROMPT = "사용자의 질문에 친절하고 정확한 한국어로 답변하세요."


@dataclass(frozen=True, slots=True)
class AIResult:
    """AI 답변과 측정된 처리 시간을 전달합니다."""

    answer: str
    latency_ms: int


class AIServiceError(RuntimeError):
    """외부 또는 설정 기반 AI 호출 실패를 나타냅니다."""


class AITimeoutError(AIServiceError):
    """AI 제한 시간을 초과한 경우를 나타냅니다."""


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


async def generate_ai_response(
    messages: list[dict[str, str]],
    *,
    request_id: str,
    settings: Settings,
) -> AIResult:
    """현재 단계에서는 명시적 Mock만 실행하고 실모드 fallback은 거부합니다."""

    del request_id
    if settings.resolved_ai_mode != "mock":
        raise AIServiceError("real_adapter_not_ready")

    started_at = perf_counter()
    await asyncio.sleep(0)
    answer = _mock_answer(messages)
    latency_ms = max(0, int((perf_counter() - started_at) * 1000))
    return AIResult(answer=answer, latency_ms=latency_ms)
