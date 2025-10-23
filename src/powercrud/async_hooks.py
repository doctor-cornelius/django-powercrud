"""
Async task completion hooks and utilities for powercrud.

This module provides importable hook functions for django-q2 task completion.
The hooks are designed to be simple stubs that delegate to AsyncManager methods
which can be overridden by downstream projects.
"""

import ast
import json
import logging
from typing import Optional

from django_q.models import Task

log = logging.getLogger(__name__)


def _extract_manager_class_path(task: Task) -> Optional[str]:
    """
    Attempt to pull the manager_class path out of the stored task kwargs.
    django-q2 persists kwargs as JSON in Task.kwargs, but we play defensively
    in case a different serializer is configured.
    """
    raw_kwargs = getattr(task, "kwargs", None)
    if not raw_kwargs:
        return None

    if isinstance(raw_kwargs, dict):
        return raw_kwargs.get("manager_class")

    parsed_kwargs = None
    if isinstance(raw_kwargs, str):
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed_kwargs = parser(raw_kwargs)
                break
            except Exception:
                continue

    if isinstance(parsed_kwargs, dict):
        return parsed_kwargs.get("manager_class")

    log.debug(
        "task_completion_hook could not parse Task.kwargs for task %s; defaulting to base AsyncManager",
        getattr(task, "name", "unknown"),
    )
    return None


def task_completion_hook(task: Task) -> None:
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
        from powercrud.async_manager import AsyncManager
        
        # Derive task_key from Task.name (preferred) or fallback to Task.id
        # task_key = task.name if task.name else str(task.id)
        task_name = str(task.name)
        
        log.debug(f"async_hooks.task_completion_hook triggered for task_name: {task_name}")
        # Delegate to AsyncManager method (can be overridden by subclasses)
        manager_class_path = _extract_manager_class_path(task)
        manager = AsyncManager.resolve_manager(manager_class_path)
        manager.handle_task_completion(task, task_name)
        
    except Exception as e:
        # Never let hook failures break the worker
        log.error(f"Error in task completion hook for task {getattr(task, 'name', 'unknown')}: {e}")


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
    def wrapper(*args, **kwargs):
        task_name = kwargs.get('task_name')
        
        def progress_callback(message: str) -> None:
            if task_name:
                try:
                    from powercrud.async_manager import AsyncManager
                    manager = AsyncManager()
                    manager.update_progress(task_name, message)
                except Exception as e:
                    log.warning(f"Failed to update progress for task {task_name}: {e}")
        
        # Inject progress callback into kwargs
        kwargs['progress_callback'] = progress_callback
        
        return func(*args, **kwargs)
    
    return wrapper
