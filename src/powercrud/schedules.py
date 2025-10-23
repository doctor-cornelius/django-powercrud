from powercrud.conf import get_powercrud_setting
from powercrud.logging import get_logger

log = get_logger(__name__)


def cleanup_async_artifacts():
    """
    Scheduled entry point for django-q2 to clean async artifacts.
    """
    if not get_powercrud_setting("ASYNC_ENABLED", False):
        log.debug("Skipping scheduled cleanup: async disabled")
        return

    from powercrud.async_manager import AsyncManager

    manager = AsyncManager()
    summary = manager.cleanup_completed_tasks()
    cleaned = summary.get("cleaned", {})
    if cleaned:
        log.info("Scheduled cleanup removed %d task(s)", len(cleaned))
    else:
        log.debug("Scheduled cleanup found no stale tasks")
