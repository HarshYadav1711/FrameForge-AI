"""In-process render queue — one encode at a time."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_queue_instance: RenderQueue | None = None


class RenderQueue:
    """
    Serializes CPU-heavy render work so concurrent jobs do not contend.

    Uses an asyncio lock; callers should ``await queue.run(sync_fn)``.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._active_job_id: str | None = None

    @property
    def active_job_id(self) -> str | None:
        return self._active_job_id

    async def run(
        self,
        func: Callable[[], T],
        *,
        job_id: str | None = None,
    ) -> T:
        async with self._lock:
            self._active_job_id = job_id
            logger.debug("Render queue acquired (job=%s)", job_id)
            try:
                return await asyncio.to_thread(func)
            finally:
                self._active_job_id = None
                logger.debug("Render queue released (job=%s)", job_id)


def get_render_queue() -> RenderQueue:
    global _queue_instance
    if _queue_instance is None:
        _queue_instance = RenderQueue()
    return _queue_instance
