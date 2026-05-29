"""Render retry and failure recovery."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

from app.core.exceptions import RenderingError
from app.services.rendering.config import RenderOutputConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


def run_with_recovery(
    render_fn: Callable[[int], T],
    config: RenderOutputConfig,
    *,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> T:
    """
    Execute ``render_fn(attempt)`` with retries on failure.

    ``render_fn`` should perform full cleanup for the attempt before raising.
    """
    last_exc: Exception | None = None
    attempts = config.max_attempts

    for attempt in range(1, attempts + 1):
        try:
            return render_fn(attempt)
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Render attempt %d/%d failed: %s",
                attempt,
                attempts,
                exc,
            )
            if on_retry:
                on_retry(attempt, exc)
            if attempt < attempts:
                time.sleep(config.retry_delay_seconds)
            continue

    message = f"Render failed after {attempts} attempt(s)"
    raise RenderingError(
        message,
        attempt=attempts,
        cause=str(last_exc) if last_exc else None,
        recoverable=False,
    ) from last_exc
