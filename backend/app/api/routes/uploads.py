import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.deps import get_upload_service
from app.core.exceptions import InvalidAudioError, UploadNotFoundError
from app.models.schemas import AudioUploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", response_model=AudioUploadResponse, status_code=201)
async def upload_audio(
    file: UploadFile = File(..., description="Narration audio (mp3, wav, m4a)"),
) -> AudioUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    content = await file.read()
    service = get_upload_service()

    try:
        meta = service.save(
            content,
            original_filename=file.filename,
            content_type=file.content_type,
        )
    except InvalidAudioError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    return AudioUploadResponse(
        id=meta["id"],
        original_filename=meta["original_filename"],
        sanitized_filename=meta["sanitized_filename"],
        extension=meta["extension"],
        size_bytes=meta["size_bytes"],
        content_type=meta.get("content_type"),
    )


@router.get("/{upload_id}", response_model=AudioUploadResponse)
async def get_upload(upload_id: str) -> AudioUploadResponse:
    service = get_upload_service()
    try:
        meta = service.get_meta(upload_id)
    except UploadNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc

    return AudioUploadResponse(
        id=meta["id"],
        original_filename=meta["original_filename"],
        sanitized_filename=meta["sanitized_filename"],
        extension=meta["extension"],
        size_bytes=meta["size_bytes"],
        content_type=meta.get("content_type"),
    )
