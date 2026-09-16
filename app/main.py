"""FastAPI 앱 기동, 수명주기, 헬스체크와 정적 파일 경계를 구성합니다."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, get_settings
from app.database import initialize_database


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    """설정을 주입할 수 있는 FastAPI 애플리케이션을 만듭니다."""

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        active_settings = settings or get_settings()
        application.state.settings = active_settings
        await initialize_database(active_settings)
        yield

    application = FastAPI(
        title="AI Assistant",
        version="1.0.0",
        lifespan=lifespan,
    )

    @application.get("/", include_in_schema=False)
    async def serve_index() -> Response:
        """프론트가 준비되면 정적 진입 HTML만 제공합니다."""

        index_path = STATIC_DIR / "index.html"
        if not index_path.is_file():
            return JSONResponse(
                status_code=503,
                content={"detail": "프론트엔드가 아직 준비되지 않았습니다."},
            )
        return FileResponse(index_path)

    @application.get("/api/health", response_model=None)
    async def health(request: Request) -> JSONResponse:
        """외부 AI 호출 없이 서버 프로세스의 가용 상태를 알립니다."""

        active_settings: Settings = request.app.state.settings
        return JSONResponse(
            content={"status": "ok"},
            headers={"X-AI-Mode": active_settings.resolved_ai_mode},
        )

    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return application


app = create_app()
