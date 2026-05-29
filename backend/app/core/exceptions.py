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
