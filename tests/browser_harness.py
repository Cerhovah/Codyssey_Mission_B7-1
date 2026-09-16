"""수동 브라우저 회귀에서 느린 AI와 실패를 재현하는 테스트 전용 ASGI 앱."""

import asyncio

from fastapi import Request
import httpx
from starlette.responses import PlainTextResponse

from app.ai_service import AIResult, AITimeoutError, generate_ai_response as real_generate
from app.main import create_app
from app.responses import UTF8JSONResponse
from app.routers import chat_router


async def controlled_generate(
    messages: list[dict[str, str]],
    *,
    request_id: str,
    settings,
    http_client: httpx.AsyncClient,
) -> AIResult:
    """특정 테스트 질문에만 지연·timeout을 주고 나머지는 기존 Mock을 사용합니다."""

    question = messages[-1]["content"]
    if question == "R12 느린 성공":
        await asyncio.sleep(1.5)
        return AIResult(answer="[Test] 느린 응답이 완료되었습니다.", latency_ms=1500)
    if question == "R12 강제 실패":
        await asyncio.sleep(0.4)
        raise AITimeoutError("browser_test_timeout")
    if question == "R13 느린 A 응답":
        await asyncio.sleep(3)
        return AIResult(answer="[Test] 이전 사용자에게만 속한 응답입니다.", latency_ms=3000)
    return await real_generate(
        messages,
        request_id=request_id,
        settings=settings,
        http_client=http_client,
    )


chat_router.generate_ai_response = controlled_generate
app = create_app()


@app.middleware("http")
async def controlled_http_errors(request: Request, call_next):
    """두 테스트 질문에만 JSON 500과 비JSON 500을 반환합니다."""

    if request.method == "POST" and request.url.path == "/api/chat":
        try:
            payload = await request.json()
        except ValueError:
            payload = {}
        question = payload.get("question") if isinstance(payload, dict) else None
        if question == "R12 강제 500":
            return UTF8JSONResponse(
                status_code=500,
                content={"detail": "테스트 서버 오류입니다."},
            )
        if question == "R12 비JSON 실패":
            return PlainTextResponse("untrusted upstream body", status_code=500)
        if question == "R13 늦은 401":
            await asyncio.sleep(2)
            return UTF8JSONResponse(
                status_code=401,
                content={"detail": "테스트용 늦은 인증 오류입니다."},
            )
    return await call_next(request)
