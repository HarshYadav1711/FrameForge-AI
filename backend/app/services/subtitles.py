import logging
from pathlib import Path

from app.models.schemas import TranscriptSegment

logger = logging.getLogger(__name__)


def _format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_srt(
    segments: list[TranscriptSegment],
    output_path: Path,
) -> str:
    """Write SRT subtitles from transcript segments."""
    lines: list[str] = []
    for i, seg in enumerate(segments, start=1):
        if not seg.text.strip():
            continue
        lines.append(str(i))
        lines.append(
            f"{_format_timestamp(seg.start)} --> {_format_timestamp(seg.end)}"
        )
        lines.append(seg.text.strip())
        lines.append("")

    content = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    logger.info("Wrote subtitles %s (%d cues)", output_path.name, len(segments))
    return str(output_path)
