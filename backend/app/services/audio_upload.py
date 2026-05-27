import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import Settings
from app.core.exceptions import InvalidAudioError, UploadNotFoundError

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = frozenset({".mp3", ".wav", ".m4a"})
ALLOWED_MIME = frozenset({
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mp4",
    "audio/x-m4a",
    "audio/m4a",
})
MAX_AUDIO_BYTES = 50 * 1024 * 1024


def sanitize_filename(filename: str) -> str:
    """Strip paths and unsafe characters from client-provided names."""
    name = Path(filename).name
    name = re.sub(r"[^\w.\-]", "_", name, flags=re.ASCII)
    name = name.strip("._")
    return (name[:120] or "audio")


def extension_from_filename(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in ALLOWED_EXTENSIONS:
        return suffix
    raise InvalidAudioError(
        f"Unsupported format. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
    )


def detect_audio_extension(data: bytes) -> str | None:
    """Match file header to allowed audio types."""
    if len(data) < 12:
        return None
    if data[:3] == b"ID3" or (data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return ".mp3"
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return ".wav"
    if len(data) >= 8 and data[4:8] == b"ftyp":
        return ".m4a"
    return None


def validate_audio_content(
    data: bytes,
    *,
    declared_ext: str,
    content_type: str | None,
) -> None:
    if not data:
        raise InvalidAudioError("Audio file is empty")
    if len(data) > MAX_AUDIO_BYTES:
        raise InvalidAudioError("Audio file exceeds 50 MB limit")

    detected = detect_audio_extension(data[:16])
    if detected is None:
        raise InvalidAudioError("File content is not a valid MP3, WAV, or M4A audio file")
    if detected != declared_ext:
        raise InvalidAudioError(
            f"File extension {declared_ext} does not match detected format {detected}"
        )
    if content_type and content_type.split(";")[0].strip().lower() not in ALLOWED_MIME:
        logger.warning("Unexpected content-type %s (continuing after magic-byte check)", content_type)


class AudioUploadService:
    def __init__(self, settings: Settings) -> None:
        self._root = settings.uploads_path
        self._root.mkdir(parents=True, exist_ok=True)

    def _upload_dir(self, upload_id: str) -> Path:
        return self._root / upload_id

    def _meta_path(self, upload_id: str) -> Path:
        return self._upload_dir(upload_id) / "meta.json"

    def _audio_path(self, upload_id: str, ext: str) -> Path:
        return self._upload_dir(upload_id) / f"audio{ext}"

    def save(
        self,
        data: bytes,
        *,
        original_filename: str,
        content_type: str | None = None,
    ) -> dict:
        safe_name = sanitize_filename(original_filename)
        ext = extension_from_filename(safe_name)
        validate_audio_content(data, declared_ext=ext, content_type=content_type)

        upload_id = str(uuid4())
        upload_dir = self._upload_dir(upload_id)
        upload_dir.mkdir(parents=True)

        audio_path = self._audio_path(upload_id, ext)
        audio_path.write_bytes(data)

        meta = {
            "id": upload_id,
            "original_filename": original_filename,
            "sanitized_filename": safe_name,
            "stored_filename": audio_path.name,
            "extension": ext,
            "size_bytes": len(data),
            "content_type": content_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._meta_path(upload_id).write_text(
            json.dumps(meta, indent=2),
            encoding="utf-8",
        )
        logger.info("Stored audio upload %s (%s, %d bytes)", upload_id, ext, len(data))
        return meta

    def get_meta(self, upload_id: str) -> dict:
        path = self._meta_path(upload_id)
        if not path.exists():
            raise UploadNotFoundError(upload_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def get_audio_path(self, upload_id: str) -> Path:
        meta = self.get_meta(upload_id)
        path = self._audio_path(upload_id, meta["extension"])
        if not path.exists():
            raise UploadNotFoundError(upload_id)
        return path

    def attach_to_job(self, upload_id: str, job_audio_base: Path) -> Path:
        """Copy validated upload into a job directory as audio.{ext}."""
        source = self.get_audio_path(upload_id)
        ext = source.suffix
        dest = job_audio_base.with_suffix(ext)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source.read_bytes())
        return dest
