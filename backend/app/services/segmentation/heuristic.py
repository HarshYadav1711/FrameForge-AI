"""Heuristic scene proposer (no LLM required)."""

from __future__ import annotations

import logging

from app.services.segmentation.base import SceneDraft, SegmentationContext
from app.services.segmentation.semantic import propose_from_script_structure
from app.services.segmentation.timeline import propose_from_timeline_blocks

logger = logging.getLogger(__name__)


async def propose_heuristic(ctx: SegmentationContext) -> list[SceneDraft]:
    """Fallback proposer using timeline blocks or script structure."""
    if ctx.timeline_blocks:
        drafts = propose_from_timeline_blocks(ctx.timeline_blocks)
        if drafts:
            logger.info("Heuristic: %d scenes from timeline blocks", len(drafts))
            return drafts

    drafts = propose_from_script_structure(ctx.script)
    logger.info("Heuristic: %d scenes from script structure", len(drafts))
    return drafts
