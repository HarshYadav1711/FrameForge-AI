import logging
from pathlib import Path

from app.config import Settings

logger = logging.getLogger(__name__)


def check_storage_writable(settings: Settings) -> bool:
    try:
        probe = settings.jobs_path / ".health_probe"
        settings.jobs_path.mkdir(parents=True, exist_ok=True)
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        logger.exception("Storage health check failed")
        return False


def is_ready(settings: Settings) -> tuple[bool, dict[str, bool]]:
    checks = {
        "storage": check_storage_writable(settings),
    }
    return all(checks.values()), checks
