import json
import logging
import re
from typing import Any

import httpx

from app.config import Settings
from app.models.schemas import Scene, TranscriptSegment

logger = logging.getLogger(__name__)

SEGMENT_PROMPT = """You are a video editor assistant. Split the following script into distinct visual scenes for a narrated video.

Rules:
- Return ONLY valid JSON (no markdown fences).
- Each scene needs: title (short), narration (exact script portion), visual_prompt (describe background/visual style in one sentence).
- Preserve the full script across scenes — do not omit text.
- Aim for 3-8 scenes depending on length.
- Match pacing to the transcript timing when provided.

Script:
{script}

Transcript timing reference (optional):
{transcript_summary}

Respond with JSON array:
[
  {{"title": "...", "narration": "...", "visual_prompt": "..."}}
]
"""


def _transcript_summary(segments: list[TranscriptSegment]) -> str:
    if not segments:
        return "No transcript available."
    lines = [f"[{s.start:.1f}s-{s.end:.1f}s] {s.text}" for s in segments[:40]]
    if len(segments) > 40:
        lines.append(f"... and {len(segments) - 40} more segments")
    return "\n".join(lines)


def _parse_scenes_json(raw: str) -> list[dict[str, Any]]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in LLM response")
    return json.loads(text[start : end + 1])


def _align_scene_timing(
    scenes: list[Scene],
    segments: list[TranscriptSegment],
    total_duration: float,
) -> list[Scene]:
    """Distribute scene timings proportionally by narration word count."""
    if not scenes or total_duration <= 0:
        return scenes

    weights = [max(len(s.narration.split()), 1) for s in scenes]
    total_weight = sum(weights)
    cursor = 0.0
    aligned: list[Scene] = []

    for scene, weight in zip(scenes, weights):
        span = (weight / total_weight) * total_duration
        start = cursor
        end = min(cursor + span, total_duration)
        aligned.append(
            scene.model_copy(
                update={"start_time": round(start, 3), "end_time": round(end, 3)}
            )
        )
        cursor = end

    if aligned:
        aligned[-1] = aligned[-1].model_copy(
            update={"end_time": round(total_duration, 3)}
        )
    return aligned


async def _segment_with_ollama(
    script: str,
    transcript_summary: str,
    settings: Settings,
) -> list[dict[str, Any]]:
    prompt = SEGMENT_PROMPT.format(
        script=script.strip(),
        transcript_summary=transcript_summary,
    )
    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3},
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    return _parse_scenes_json(data.get("response", ""))


async def _segment_with_gemini(
    script: str,
    transcript_summary: str,
    settings: Settings,
) -> list[dict[str, Any]]:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is required when Gemini is enabled")

    prompt = SEGMENT_PROMPT.format(
        script=script.strip(),
        transcript_summary=transcript_summary,
    )
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    params = {"key": settings.gemini_api_key}
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3},
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, params=params, json=body)
        resp.raise_for_status()
        data = resp.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return _parse_scenes_json(text)


def _segment_heuristic(script: str, total_duration: float) -> list[Scene]:
    """Fallback: split on paragraphs/sentences when LLM is unavailable."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", script.strip()) if p.strip()]
    if len(paragraphs) <= 1:
        sentences = re.split(r"(?<=[.!?])\s+", script.strip())
        chunks: list[str] = []
        buf: list[str] = []
        for sent in sentences:
            buf.append(sent)
            if len(buf) >= 3:
                chunks.append(" ".join(buf))
                buf = []
        if buf:
            chunks.append(" ".join(buf))
        paragraphs = chunks or [script.strip()]

    scenes: list[Scene] = []
    per_scene = max(total_duration / len(paragraphs), 2.0) if total_duration else 5.0
    cursor = 0.0
    for i, para in enumerate(paragraphs):
        title = para[:48].rstrip() + ("…" if len(para) > 48 else "")
        start = cursor
        end = cursor + per_scene
        scenes.append(
            Scene(
                index=i,
                title=title,
                narration=para,
                visual_prompt=f"Cinematic abstract background inspired by: {title}",
                start_time=round(start, 3),
                end_time=round(end, 3),
            )
        )
        cursor = end
    if scenes and total_duration:
        scenes[-1] = scenes[-1].model_copy(
            update={"end_time": round(total_duration, 3)}
        )
    return scenes


async def segment_script(
    script: str,
    segments: list[TranscriptSegment],
    total_duration: float,
    settings: Settings,
) -> list[Scene]:
    summary = _transcript_summary(segments)
    raw_scenes: list[dict[str, Any]] | None = None

    if settings.gemini_enabled:
        try:
            raw_scenes = await _segment_with_gemini(script, summary, settings)
            logger.info("Segmented script with Gemini (%d scenes)", len(raw_scenes))
        except Exception as exc:
            logger.warning("Gemini segmentation failed: %s", exc)

    if raw_scenes is None and settings.ollama_enabled:
        try:
            raw_scenes = await _segment_with_ollama(script, summary, settings)
            logger.info("Segmented script with Ollama (%d scenes)", len(raw_scenes))
        except Exception as exc:
            logger.warning("Ollama segmentation failed: %s", exc)

    if raw_scenes:
        scenes = [
            Scene(
                index=i,
                title=str(item.get("title", f"Scene {i + 1}")),
                narration=str(item.get("narration", "")),
                visual_prompt=str(
                    item.get("visual_prompt", "Minimal dark cinematic gradient")
                ),
            )
            for i, item in enumerate(raw_scenes)
            if item.get("narration")
        ]
        return _align_scene_timing(scenes, segments, total_duration)

    logger.info("Using heuristic scene segmentation")
    return _segment_heuristic(script, total_duration)
