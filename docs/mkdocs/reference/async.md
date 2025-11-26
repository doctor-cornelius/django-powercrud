# Async Architecture & Reference

This page collects the deeper details behind PowerCRUD’s async infrastructure so you can understand how it works under the hood, reuse it outside PowerCRUD views, or extend it for future backends.

---

!!! info "Sync by default, async opt-in"

    PowerCRUD does **not** enable async automatically. Async behaviour is only active when:

    - You have installed and configured `django-q2` (`django_q` in `INSTALLED_APPS`, `Q_CLUSTER`, shared cache).
    - Async is enabled in `POWERCRUD_SETTINGS["ASYNC_ENABLED"]` (or you deliberately call the async helpers).
    - Your views or launch sites opt in via `AsyncMixin`, `PowerCRUDAsyncMixin`, or direct use of `AsyncManager`.

## Overview

PowerCRUD’s async support consists of four cooperating pieces:

| Layer | Responsibility | You customise by… |
|-------|----------------|-------------------|
| `AsyncMixin` | Decides when to queue work, runs conflict checks, and forwards metadata (manager path/config) to the worker. | Enabling `bulk_async`, setting thresholds, overriding helper methods. |
| `AsyncManager` | Reserves & releases locks, stores progress, raises lifecycle events, exposes the HTMX polling view, performs cleanup. | Supplying a different manager class/config or overriding lifecycle hooks. |
| Worker functions (`powercrud.tasks`) | Execute the bulk update/delete in the background, calling `update_progress` and returning a result payload. | Writing your own worker functions or adding custom behavior. |
| Dashboard / lifecycle consumers | Persist task status, show progress, notify users. | Using `ModelTrackingAsyncManager`, building your own manager, or wiring lifecycle events elsewhere. |

The guides (Async Manager → Bulk editing (async) → Async dashboard add-on) explain how to configure these layers in your project. This reference dives into the architecture, cache layout, lifecycle flow, and troubleshooting patterns.

---

## Architecture

### Lifecycle

1. **Launch** – The view (via `AsyncMixin`) generates a UUID, optionally reserves locks (`add_conflict_ids`), seeds a progress key, and enqueues a worker via `django_q.tasks.async_task`. The manager class path/config is stored with the task.
2. **Worker execution** – The worker rehydrates the same manager (`AsyncManager.resolve_manager`), updates progress (`update_progress`), and returns a serialisable result.
3. **Completion hook** – `powercrud.async_hooks.task_completion_hook` resolves the manager again, removes locks/progress, emits lifecycle events (`complete`, `fail`, always followed by `cleanup`), and persists any dashboard data.
4. **Cleanup** – `AsyncManager.cleanup_completed_tasks()` (and the `pcrud_cleanup_async` command) reconcile the “active task” cache with `django_q.Task`, removing stale locks/progress/dashboard records if a worker died mid-flight.

### Cache design

PowerCRUD uses a “dual key” cache strategy so locks and cleanup are reliable:

- **Lock keys**: `powercrud:conflict:model:{app_label.Model}:{pk}` → `task_name`. Created with `cache.add` for atomicity—if another task holds the lock, reservation fails.
- **Tracking set**: `powercrud:async:conflict:{task_name}` → set of lock keys held by this task. Used during cleanup to delete all locks for a task without scanning the cache blindly.
- **Progress key**: `powercrud:async:progress:{task_name}` → latest status/progress string (or `pending`). Polled by HTMX.
- **Active tasks**: `powercrud:async:active_tasks` → set of task names still considered active. Cleaned by `cleanup_completed_tasks`.

Always configure a **shared** cache (Redis, Memcached, DatabaseCache). LocMem/Dummy caches will break conflict detection and progress because the worker and web processes maintain separate memory.

---

## Key settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `ASYNC_ENABLED` | `False` | Global master switch for async features. |
| `CACHE_NAME` | `'default'` | Cache alias used for locks/progress. |
| `CONFLICT_TTL` | `3600` | TTL (seconds) for conflict lock entries. |
| `PROGRESS_TTL` | `7200` | TTL (seconds) for progress entries. |
| `CLEANUP_GRACE_PERIOD` | `86400` | Grace period before scheduled cleanup reclaims tasks. |
| `MAX_TASK_DURATION` | `3600` | Consider tasks “stuck” after this duration (can trigger cleanup). |
| `CLEANUP_SCHEDULE_INTERVAL` | `300` | Suggested interval (seconds) when scheduling cleanup via django-q2. |
| `ASYNC_MANAGER_DEFAULT` | `AsyncManager` | Manager class/config used by views and workers when no per-view override is supplied. |

These live inside `POWERCRUD_SETTINGS`. Override them in your project’s `settings.py`.

---

## Health checks

Use the lightweight validation helpers before launching tasks (or in a readiness probe):

```python
from powercrud.async_manager import AsyncManager

manager = AsyncManager()

manager.validate_async_cache()     # returns bool
manager.validate_async_qcluster()  # returns bool
manager.validate_async_system()    # cache + qcluster
```

- `validate_async_cache()` ensures the configured cache alias exists and supports multi-process access.
- `validate_async_qcluster()` enqueues a quick job and waits briefly to confirm the worker is running.
- `validate_async_system()` runs both checks; you can gate async launch on its result.

---

## Progress & HTMX endpoint

The polling endpoint uses `AsyncManager.as_view()` (exposed via `AsyncManager.get_url()` or the namespaced `get_urlpatterns()`). Polling stops when the manager returns HTTP 286 with a final status:

```json
{
  "task_name": "...",
  "status": "success",
  "progress": "Completed successfully!"
}
```

If you need to integrate the progress API elsewhere, import the view and mount it under your own URL. The modal markup in PowerCRUD’s templates is an example you can copy.

!!! important
    Add `AsyncManager.get_urlpatterns()` once in your **project-level** `urlpatterns` so Django registers the `powercrud` namespace. Only fall back to `get_url()` if you also wire the namespace yourself.

---

## Cleanup utilities

- **Manual command**: `python manage.py pcrud_cleanup_async` (pass `--json` for structured output).
- **Programmatic**: `AsyncManager().cleanup_completed_tasks()` returns a summary dict you can log or inspect.
- **Scheduled cleanup**: add `powercrud.schedules.cleanup_async_artifacts` to `Q_CLUSTER["schedule"]` using `CLEANUP_SCHEDULE_INTERVAL` as a guideline.

Cleanup works even if a worker died mid-task—it cross-references the cache and `django_q.Task` to reclaim locks and progress safely.

---

## Reusing async helpers outside PowerCRUD

To launch tasks from admin actions, management commands, signals, or custom views:

```python
from powercrud.async_manager import AsyncManager

def launch_custom_task(user, affected_objects):
    manager = AsyncManager()
    conflict_ids = {"myapp.Project": {obj.pk for obj in affected_objects}}

    if not manager.add_conflict_ids("custom-task", conflict_ids):
        raise RuntimeError("Another task already processes these projects")

    manager.launch_async_task(
        func="myapp.tasks.rebuild_project",
        conflict_ids=conflict_ids,
        user=user,
        affected_objects=[str(obj) for obj in affected_objects],
        task_kwargs={"extra": "info"},
    )
```

Workers should accept `task_key` and call `update_progress`:

```python
def rebuild_project(project_id, *, task_key=None, manager_class=None, **kwargs):
    from powercrud.async_manager import AsyncManager
    manager = AsyncManager.resolve_manager(manager_class)
    # do work…
    manager.update_progress(task_key, "Step 2/3")
    return {"project": project_id}
```

All launch sites (PowerCRUD views, custom code) end up sharing the same lifecycle behaviour because the manager class is resolved each time.

---

## Dashboard & lifecycle integration

- `ModelTrackingAsyncManager` persists lifecycle events to your dashboard model automatically. Override `format_user`, `format_affected`, `format_payload`, or `async_task_lifecycle` for custom behaviour.
- If your dashboard schema differs, supply `record_model_path` and (optionally) `field_map` so payload keys map cleanly to columns.
- Lifecycle events you can handle: `create`, `progress`, `complete`, `fail`, `cleanup`.
- For a working reference, inspect the sample app (`sample/async_manager.py`, `sample/models.py`, `sample/views.py`, `sample/tests.py`).

---

## Troubleshooting

| Symptom | Checks / Fixes |
|---------|----------------|
| Modal keeps polling forever | Inspect qcluster logs; if the worker crashed, run `pcrud_cleanup_async`. |
| “Conflict detected” | Another task holds locks on those objects; inspect the dashboard or cleanup if stale. |
| Cache errors | Ensure `CACHE_NAME` points to a shared backend (not LocMem/Dummy). |
| Manager import errors | Verify `async_manager_class_path` or `ASYNC_MANAGER_DEFAULT` is importable and subclasses `AsyncManager`. |
| Long-running tasks accumulate | Schedule cleanup or adjust `MAX_TASK_DURATION` and `CLEANUP_GRACE_PERIOD`. |

When in doubt, rerun the health checks (`validate_async_system`) to make sure both cache and qcluster are healthy.

---

## Further reading

- [Bulk editing (async)](../guides/bulk_edit_async.md) – end-to-end setup in a PowerCRUD view.
- [Async Manager](../guides/async_manager.md) – using the helpers in custom code.
- [Async dashboard add-on](../guides/async_dashboard.md) – persisting lifecycle data.
- [Management commands](../reference/mgmt_commands.md) – cleanup and template utilities.
- [Configuration options](../reference/config_options.md) – full list of async-related settings and defaults.
