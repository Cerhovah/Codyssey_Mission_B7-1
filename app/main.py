"""FastAPI 앱 기동, 수명주기, 헬스체크와 정적 파일 경계를 구성합니다."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx

from app.ai_service import create_ai_http_client
from app.config import Settings, get_settings
from app.database import initialize_database
from app.errors import register_error_handlers
from app.logger import configure_logging
from app.routers.auth_router import router as auth_router
from app.routers.chat_router import router as chat_router
from app.responses import UTF8JSONResponse
from app.schemas import HealthResponse


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
LOG_PATH = PROJECT_ROOT / "logs" / "app.log"


def create_app(
    settings: Settings | None = None,
    *,
    ai_transport: httpx.AsyncBaseTransport | None = None,
    log_path: Path | None = LOG_PATH,
) -> FastAPI:
    """설정을 주입할 수 있는 FastAPI 애플리케이션을 만듭니다."""

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        active_settings = settings or get_settings()
        application.state.settings = active_settings
        application.state.chat_turn_locks = {}
        application.state.chat_turn_locks_guard = asyncio.Lock()
        if log_path is not None:
            configure_logging(log_path)
        await initialize_database(active_settings)
        async with create_ai_http_client(
            active_settings,
            transport=ai_transport,
        ) as ai_http_client:
            application.state.ai_http_client = ai_http_client
            yield

    application = FastAPI(
        title="AI Assistant",
        version="1.0.0",
        lifespan=lifespan,
        default_response_class=UTF8JSONResponse,
    )
    register_error_handlers(application)
    application.include_router(auth_router)
    application.include_router(chat_router)

    @application.get("/", include_in_schema=False)
    async def serve_index() -> Response:
        """프론트가 준비되면 정적 진입 HTML만 제공합니다."""

        index_path = STATIC_DIR / "index.html"
        if not index_path.is_file():
            return UTF8JSONResponse(
                status_code=503,
                content={"detail": "프론트엔드가 아직 준비되지 않았습니다."},
            )
        return FileResponse(index_path)

    @application.get("/api/health", response_model=HealthResponse)
    async def health(request: Request) -> UTF8JSONResponse:
        """외부 AI 호출 없이 서버 프로세스의 가용 상태를 알립니다."""

        active_settings: Settings = request.app.state.settings
        return UTF8JSONResponse(
            content={"status": "ok"},
            headers={"X-AI-Mode": active_settings.resolved_ai_mode},
        )

    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return application


app = create_app()
