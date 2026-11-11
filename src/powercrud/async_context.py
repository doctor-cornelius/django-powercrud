"""PowerCRUD compatibility exports for coordinator task context."""

from powercrud._coordinator.context import (
    TaskContext,
    _task_context,
    get_current_task,
    skip_nested_async,
    task_context,
)
from powercrud._coordinator.exceptions import DescendantConflictError


def register_descendant_conflicts(model_path, ids):
    """Register descendant locks with the legacy public base manager."""
    from powercrud._coordinator.context import register_descendant_conflicts as register

    def manager_factory():
        """Resolve the public base manager at call time for legacy overrides."""
        from powercrud.async_manager import AsyncManager

        return AsyncManager()

    return register(model_path, ids, manager_factory=manager_factory)


__all__ = [
    "TaskContext",
    "task_context",
    "get_current_task",
    "skip_nested_async",
    "register_descendant_conflicts",
    "DescendantConflictError",
]
