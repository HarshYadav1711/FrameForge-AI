from functools import lru_cache

from app.config import get_settings, resolve_pipeline_settings
from app.pipeline.orchestrator import PipelineOrchestrator
from app.services.audio_upload import AudioUploadService
from app.services.job_store import JobStore


@lru_cache
def get_job_store() -> JobStore:
    return JobStore(get_settings())


@lru_cache
def get_upload_service() -> AudioUploadService:
    return AudioUploadService(get_settings())


@lru_cache
def get_orchestrator() -> PipelineOrchestrator:
    settings = resolve_pipeline_settings(get_settings())
    return PipelineOrchestrator(get_job_store(), settings)


def reset_cached_deps() -> None:
    """Clear cached singletons (useful in tests)."""
    get_job_store.cache_clear()
    get_upload_service.cache_clear()
    get_orchestrator.cache_clear()
