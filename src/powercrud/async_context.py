"""Async task context helpers.

This module keeps track of "which async job am I in right now?" without
threading a ``task_key`` argument through every function. We use Python's
``contextvars`` (a standard library feature similar to thread-local storage)
so each worker execution gets its own little pocket of state.

Usage summary:

* ``task_context(task_name, manager_class_path)`` — context manager that sets
  the current task metadata for the duration of a ``with`` block. Our bulk
  workers enter this context automatically when launched via
  ``AsyncManager``.
* ``get_current_task()`` — fetch the active task info (or ``None`` if not
  inside an async job). Helpful for downstream code like model ``save()``
  overrides that want to know the parent task key.
* ``skip_nested_async()`` — quick boolean to ask "am I already in an async
  job?". Downstream code can use this to suppress launching child tasks.
* ``register_descendant_conflicts(model_path, ids)`` — convenience helper to
  add child object IDs to the same conflict lock as the parent job.

Because the data lives in a ``ContextVar``, it respects Django's threading
and async behaviour: each worker / request gets its own context and we reset
it automatically when the ``with`` block exits. In other words, this lets
you call ``skip_nested_async()`` anywhere in the call stack i.e. no need to
pass ``task_key`` around manually.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterable, Optional

@dataclass
class TaskContext:
    task_name: str
    manager_class_path: Optional[str] = None


_task_context: ContextVar[Optional[TaskContext]] = ContextVar("powercrud_task_context", default=None)


@contextmanager
def task_context(task_name: str, manager_class_path: Optional[str] = None):
    """Context manager to set the current async task metadata."""
    token = _task_context.set(TaskContext(task_name=task_name, manager_class_path=manager_class_path))
    try:
        yield
    finally:
        _task_context.reset(token)


def get_current_task() -> Optional[TaskContext]:
    """Return the current task context, if any."""
    return _task_context.get()


def skip_nested_async() -> bool:
    """Return True if the current call stack is already inside an async task."""
    return get_current_task() is not None


def register_descendant_conflicts(model_path: str, ids: Iterable[int]) -> None:
    """
    Register descendant objects in the conflict store under the current task.

    Args:
        model_path: dotted app_label.ModelName string.
        ids: iterable of primary keys to register.
    """
    context = get_current_task()
    if not context:
        return

    id_set = {int(pk) for pk in ids if pk is not None}
    if not id_set:
        return

    model_label = model_path
    try:
        from django.apps import apps

        model = apps.get_model(model_path)
        model_label = f"{model._meta.app_label}.{model._meta.model_name}"
    except Exception:
        pass

    from powercrud.async_manager import AsyncManager

    manager = AsyncManager()
    manager.add_conflict_ids(context.task_name, {model_label: id_set})
