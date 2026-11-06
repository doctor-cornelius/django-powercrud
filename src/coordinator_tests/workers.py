"""
Test-only worker functions for async E2E tests.

These functions are defined at module (top) level so they are pickleable by
django-q2 worker processes. Do not import app code at module load time to
avoid circular imports; import lazily inside functions if needed.
"""


def simple_test_worker(message: str, task_key: str | None = None, **kwargs) -> str:
    """
    Top-level importable worker used by tests and examples.

    Args:
        message: Arbitrary message payload
        task_key: PowerCRUD task key injected by AsyncManager.launch_async_task()

    Behavior:
        - Optionally records simple progress messages when task_key is provided
        - Returns a processed string result
    """
    try:
        if task_key:
            # Lazy import to avoid circular imports at module load time
            from powercrud.async_manager import AsyncManager

            manager = AsyncManager()
            manager.update_progress(task_key, "Processing started")
            manager.update_progress(task_key, f"Processing: {message}")
            manager.update_progress(task_key, "Processing completed")
    except Exception:
        # Do not fail the worker if progress update fails
        pass

    return f"Processed: {message}"
