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
