"""
Async task completion hooks and utilities for powercrud.

This module provides importable hook functions for django-q2 task completion.
The hooks are designed to be simple stubs that delegate to AsyncManager methods
which can be overridden by downstream projects.
"""

from powercrud.logging import get_logger
from powercrud._coordinator.q2 import Q2Adapter
from powercrud._coordinator.context import get_current_task
from functools import wraps

log = get_logger(__name__)
_q2_adapter = Q2Adapter()


def task_completion_hook(task: object) -> None:
    """
    Completion hook function for django-q2 tasks.

    This function is called automatically by django-q2 when a task completes
    (success or failure). It delegates to AsyncManager.handle_task_completion()
    which can be overridden by downstream projects.

    Args:
        task: The completed django-q2 Task instance

    Note:
        This is a simple importable stub required by django-q2. The actual
        logic is in AsyncManager.handle_task_completion() which can be overridden.
    """
    try:
        def legacy_factory(manager_class_path, manager_config):
            """Resolve managers through the public compatibility API."""
            from powercrud.async_manager import AsyncManager

            return AsyncManager.resolve_manager(
                manager_class_path, config=manager_config
            )

        _q2_adapter.dispatch_completion(task, legacy_factory=legacy_factory)

    except Exception as e:
        # Never let hook failures break the worker
        log.error(
            f"Error in task completion hook for task {getattr(task, 'name', 'unknown')}: {e}"
        )


def progress_update_decorator(func):
    """
    Decorator to provide easy progress updates within worker functions.

    This decorator injects a progress_callback function into the wrapped
    function's kwargs, allowing easy progress reporting during execution.

    Example:
        @progress_update_decorator
        def my_worker_function(data, progress_callback=None, **kwargs):
            for i, item in enumerate(data):
                # Do work...
                if progress_callback:
                    progress_callback(f"Processed {i+1}/{len(data)} items")

    Args:
        func: The worker function to decorate

    Returns:
        The decorated function with progress_callback injected

    Note:
        The worker function must accept task_key in kwargs for this to work.
        This is prep work for Task 4 (Progress Tracking).
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        context = get_current_task()
        task_name = (
            context.task_name if context is not None else
            kwargs.get("task_key") or kwargs.get("task_name")
        )

        def progress_callback(message: str) -> None:
            if task_name:
                try:
                    if context is not None and context.manager is not None:
                        manager = context.manager
                    else:
                        from powercrud.async_manager import AsyncManager

                        manager = AsyncManager.resolve_manager(
                            kwargs.get("manager_class"),
                            config=kwargs.get("manager_config"),
                        )
                    manager.update_progress(task_name, message)
                except Exception as e:
                    log.warning(f"Failed to update progress for task {task_name}: {e}")

        # Inject progress callback into kwargs
        kwargs["progress_callback"] = progress_callback

        return func(*args, **kwargs)

    return wrapper
