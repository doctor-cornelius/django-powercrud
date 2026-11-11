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


def signal_context_worker(value: str, **kwargs) -> str:
    """Return a value while proving a q2 pre-execute context reached the worker."""
    from powercrud._coordinator.context import get_current_task

    context = get_current_task()
    if context is None or context.manager is None:
        raise RuntimeError("q2 signal context was not installed in the worker")
    if "_coordinator_identity" in kwargs:
        raise RuntimeError("Coordinator transport identity leaked into callable kwargs")
    return f"{context.task_name}:{value}"


def run_q2_signal_process(task: dict, result_queue, cache_dir: str) -> None:
    """Run registered q2 worker signals in a separate process with shared file cache."""
    import os

    os.environ["DJANGO_SETTINGS_MODULE"] = "coordinator_tests.settings"
    os.environ["POWERCRUD_COORDINATOR_CACHE_DIR"] = cache_dir
    import django

    django.setup()
    from django_q.signals import post_execute_in_worker, pre_execute
    from powercrud._coordinator.q2 import register_signals

    register_signals()
    pre_execute.send(sender=None, task=task, func=signal_context_worker)
    result = signal_context_worker(**task["kwargs"])
    task.update(
        {
            "result": result,
            "success": True,
            "stopped": django.utils.timezone.now(),
            "ack_failure": False,
        }
    )
    post_execute_in_worker.send(sender=None, task=task, func=signal_context_worker)
    result_queue.put((result, task["kwargs"].get("_coordinator_identity")))
