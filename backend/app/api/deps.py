from functools import lru_cache

from app.config import Settings, get_settings
from app.pipeline.orchestrator import PipelineOrchestrator
from app.services.audio_upload import AudioUploadService
from app.services.job_store import JobStore
from app.services.transcription import get_transcription_service


@lru_cache
def get_job_store() -> JobStore:
    return JobStore(get_settings())


@lru_cache
def get_upload_service() -> AudioUploadService:
    return AudioUploadService(get_settings())


@lru_cache
def get_orchestrator() -> PipelineOrchestrator:
    return PipelineOrchestrator(get_job_store(), get_settings())


@lru_cache
def get_transcription_service_cached():
    return get_transcription_service(get_settings())


def reset_cached_deps() -> None:
    get_job_store.cache_clear()
    get_upload_service.cache_clear()
    get_orchestrator.cache_clear()
    get_transcription_service_cached.cache_clear()
