"""Timeline-aware narration mapping and timestamp alignment."""

from __future__ import annotations

import logging

from app.models.schemas import TranscriptSegment, TranscriptTimelineBlock
from app.services.segmentation.base import SceneDraft

logger = logging.getLogger(__name__)


def propose_from_timeline_blocks(
    blocks: list[TranscriptTimelineBlock],
) -> list[SceneDraft]:
    """Create scene drafts directly from transcript timeline blocks."""
    drafts: list[SceneDraft] = []
    for block in blocks:
        text = block.text.strip()
        if not text:
            continue
        title = text[:48].rstrip() + ("…" if len(text) > 48 else "")
        drafts.append(
            SceneDraft(
                title=title,
                narration=text,
                visual_prompt=f"Cinematic visual inspired by: {title}",
                semantic_group=f"block_{block.index}",
            )
        )
    return drafts


def align_drafts_to_timeline(
    drafts: list[SceneDraft],
    segments: list[TranscriptSegment],
    total_duration: float,
) -> list[SceneDraft]:
    """Map narration drafts to contiguous transcript segment ranges."""
    if not drafts:
        return drafts
    if not segments:
        return drafts

    seg_idx = 0
    aligned: list[SceneDraft] = []

    for draft in drafts:
        words_needed = max(len(draft.narration.split()), 1)
        consumed = 0
        start_idx = seg_idx

        while seg_idx < len(segments) and consumed < words_needed:
            consumed += max(len(segments[seg_idx].text.split()), 1)
            seg_idx += 1

        if seg_idx == start_idx and seg_idx < len(segments):
            seg_idx += 1

        end_idx = max(seg_idx - 1, start_idx)
        aligned.append(
            SceneDraft(
                title=draft.title,
                narration=draft.narration,
                visual_prompt=draft.visual_prompt,
                semantic_group=draft.semantic_group,
                transcript_segment_start=start_idx,
                transcript_segment_end=end_idx,
            )
        )

    return aligned


def apply_timestamps(
    drafts: list[SceneDraft],
    segments: list[TranscriptSegment],
    total_duration: float,
) -> list[tuple[SceneDraft, float, float]]:
    """Pair drafts with start/end times derived from transcript or proportions."""
    if not drafts:
        return []

    if segments:
        return _timestamps_from_segments(drafts, segments, total_duration)

    return _timestamps_proportional(drafts, total_duration)


def _timestamps_from_segments(
    drafts: list[SceneDraft],
    segments: list[TranscriptSegment],
    total_duration: float,
) -> list[tuple[SceneDraft, float, float]]:
    mapped = align_drafts_to_timeline(drafts, segments, total_duration)
    timed: list[tuple[SceneDraft, float, float]] = []

    for draft in mapped:
        start_idx = draft.transcript_segment_start
        end_idx = draft.transcript_segment_end
        if start_idx is not None and end_idx is not None:
            start = segments[start_idx].start
            end = segments[min(end_idx, len(segments) - 1)].end
        else:
            start, end = 0.0, total_duration

        timed.append((draft, round(start, 3), round(end, 3)))

    if timed and total_duration > 0:
        last_draft, last_start, _ = timed[-1]
        timed[-1] = (last_draft, last_start, round(total_duration, 3))

    return timed


def _timestamps_proportional(
    drafts: list[SceneDraft],
    total_duration: float,
) -> list[tuple[SceneDraft, float, float]]:
    weights = [max(len(d.narration.split()), 1) for d in drafts]
    total_weight = sum(weights)
    cursor = 0.0
    timed: list[tuple[SceneDraft, float, float]] = []

    for draft, weight in zip(drafts, weights):
        span = (weight / total_weight) * total_duration if total_weight else 0
        start = cursor
        end = min(cursor + span, total_duration)
        timed.append((draft, round(start, 3), round(end, 3)))
        cursor = end

    if timed and total_duration > 0:
        last = timed[-1]
        timed[-1] = (last[0], last[1], round(total_duration, 3))

    return timed
