# Maps FrameForgeError.code to HTTP status (extend when adding new error types).
ERROR_HTTP_STATUS: dict[str, int] = {
    "job_not_found": 404,
    "job_not_ready": 409,
    "upload_not_found": 404,
    "invalid_audio": 400,
    "transcription_failed": 422,
    "segmentation_failed": 422,
    "visual_assembly_failed": 422,
    "rendering_failed": 422,
}


def http_status_for_error_code(code: str) -> int:
    if code.startswith("pipeline_"):
        return 422
    return ERROR_HTTP_STATUS.get(code, 500)


def error_response_body(exc: "FrameForgeError") -> dict:
    """JSON body for API error responses."""
    body: dict = {"error": exc.code, "message": exc.message}
    if cause := getattr(exc, "cause", None):
        body["cause"] = cause
    if scene_index := getattr(exc, "scene_index", None):
        body["scene_index"] = scene_index
    if phase := getattr(exc, "phase", None):
        body["phase"] = phase
    if attempt := getattr(exc, "attempt", None):
        if isinstance(attempt, int) and attempt > 0:
            body["attempt"] = attempt
    return body


class FrameForgeError(Exception):
    """Base application error."""

    def __init__(self, message: str, *, code: str = "internal_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class JobNotFoundError(FrameForgeError):
    def __init__(self, job_id: str) -> None:
        super().__init__(f"Job not found: {job_id}", code="job_not_found")


class JobNotReadyError(FrameForgeError):
    def __init__(self, job_id: str) -> None:
        super().__init__(
            f"Job output not ready: {job_id}",
            code="job_not_ready",
        )


class UploadNotFoundError(FrameForgeError):
    def __init__(self, upload_id: str) -> None:
        super().__init__(f"Upload not found: {upload_id}", code="upload_not_found")


class InvalidAudioError(FrameForgeError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="invalid_audio")


class PipelineError(FrameForgeError):
    def __init__(self, message: str, *, step: str) -> None:
        super().__init__(message, code=f"pipeline_{step}")


class TranscriptionError(FrameForgeError):
    def __init__(
        self,
        message: str,
        *,
        cause: str | None = None,
    ) -> None:
        self.cause = cause
        super().__init__(message, code="transcription_failed")


class SegmentationError(FrameForgeError):
    def __init__(
        self,
        message: str,
        *,
        cause: str | None = None,
    ) -> None:
        self.cause = cause
        super().__init__(message, code="segmentation_failed")


class VisualAssemblyError(FrameForgeError):
    def __init__(
        self,
        message: str,
        *,
        scene_index: int | None = None,
        cause: str | None = None,
    ) -> None:
        self.scene_index = scene_index
        self.cause = cause
        super().__init__(message, code="visual_assembly_failed")


class RenderingError(FrameForgeError):
    def __init__(
        self,
        message: str,
        *,
        attempt: int = 1,
        phase: str | None = None,
        cause: str | None = None,
        recoverable: bool = False,
    ) -> None:
        self.attempt = attempt
        self.phase = phase
        self.cause = cause
        self.recoverable = recoverable
        super().__init__(message, code="rendering_failed")
