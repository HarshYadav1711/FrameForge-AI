from fastapi import APIRouter, Response, status

from app.config import get_settings
from app.core.health import is_ready
from app.models.schemas import HealthResponse, LivenessResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        whisper_model=settings.whisper_model,
        ollama_enabled=settings.ollama_enabled,
        gemini_enabled=settings.gemini_enabled,
    )


@router.get("/health/live", response_model=LivenessResponse)
async def liveness() -> LivenessResponse:
    return LivenessResponse()


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness(response: Response) -> ReadinessResponse:
    settings = get_settings()
    ready, checks = is_ready(settings)
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ready" if ready else "not_ready",
        checks=checks,
    )
