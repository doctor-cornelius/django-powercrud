from django.core.exceptions import ImproperlyConfigured

from powercrud._coordinator.exceptions import AsyncConfigurationError
from powercrud.logging import get_logger

log = get_logger(__name__)


def cleanup_async_artifacts():
    """
    Scheduled entry point for django-q2 to clean async artifacts.
    """
    from powercrud.async_manager import AsyncManager

    try:
        manager = AsyncManager()
    except (AsyncConfigurationError, ImproperlyConfigured) as exc:
        log.error("Async cleanup could not initialize: %s", exc)
        return
    summary = manager.cleanup_completed_tasks()
    cleaned = summary.get("cleaned", {})
    if cleaned:
        log.info("Scheduled cleanup removed %d task(s)", len(cleaned))
    else:
        log.debug("Scheduled cleanup found no stale tasks")
