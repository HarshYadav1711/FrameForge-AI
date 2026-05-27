from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import health, jobs
from app.config import get_settings
from app.core.exceptions import FrameForgeError
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    setup_logging(settings.debug)
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    settings.jobs_path.mkdir(parents=True, exist_ok=True)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="FrameForge AI",
        description="AI-powered narrated video automation API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(FrameForgeError)
    async def frameforge_error_handler(
        _request: Request,
        exc: FrameForgeError,
    ) -> JSONResponse:
        status = 404 if exc.code == "job_not_found" else 500
        return JSONResponse(
            status_code=status,
            content={"error": exc.code, "message": exc.message},
        )

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(jobs.router, prefix="/api/v1")

    return app


app = create_app()
