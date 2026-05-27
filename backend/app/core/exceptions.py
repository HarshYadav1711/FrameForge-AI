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


class PipelineError(FrameForgeError):
    def __init__(self, message: str, *, step: str) -> None:
        super().__init__(message, code=f"pipeline_{step}")
