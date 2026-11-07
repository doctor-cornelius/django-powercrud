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
        task_key: Logical task key injected by the coordinator launch API.

    Behavior:
        - Optionally records simple progress messages when task_key is provided
        - Returns a processed string result
    """
    try:
        if task_key:
            # Lazy import to avoid circular imports at module load time
            from coordinator_tests.managers import coordinator_manager_factory
            from powercrud._coordinator.config import CoordinatorConfig
            from powercrud._coordinator.q2 import Q2Adapter
            from powercrud._coordinator.reconstruction import construct_manager
            from powercrud._coordinator.types import ManagerSpec

            snapshot = kwargs.get("_coordinator_config")
            if snapshot is None:
                manager = coordinator_manager_factory()
            else:
                manager = construct_manager(
                    ManagerSpec(class_path=kwargs.get("manager_class"), config=kwargs.get("manager_config")),
                    coordination_config=CoordinatorConfig.from_snapshot(snapshot),
                    executor=Q2Adapter(probe_timeout_ms=1500),
                )
            manager.update_progress(task_key, "Processing started")
            manager.update_progress(task_key, f"Processing: {message}")
            manager.update_progress(task_key, "Processing completed")
    except Exception:
        # Do not fail the worker if progress update fails
        pass

    return f"Processed: {message}"
