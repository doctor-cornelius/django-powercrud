# 04. Bulk editing (async)

When bulk updates take too long for a request/response cycle, move them to the background with django-q2. This chapter builds on [Section 02](./02_bulk_edit_sync.md) by adding async queueing, conflict locks, progress polling, and cleanup.

---

## Prerequisites

- [Section 02](./02_bulk_edit_sync.md) completed (synchronous bulk editing works).
- [Section 03](./03_async_manager.md) reviewed so you understand the async infrastructure.
- `django-q2` installed and a worker process ready (`python manage.py qcluster`).
- Shared cache configured (Redis, DatabaseCache, etc.). LocMem/Dummy caches will not work.

If you need a refresher on cache setup, see the checklist in the [async architecture reference](../reference/async.md#cache-design).

---

## 1. Ensure django-q2 is running

```bash
pip install django-q2
python manage.py migrate django_q
python manage.py qcluster   # run this in a separate process
```

Add `django_q` to `INSTALLED_APPS` and keep `qcluster` running alongside your web server. You can sanity-check the setup at any time with `AsyncManager().validate_async_system()` (or call `validate_async_cache` / `validate_async_qcluster` individually).

---

## 2. Configure a shared cache

```python title="settings.py"
CACHES = {
    "default": {...},
    "powercrud_async": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "powercrud_async_cache",
        "KEY_PREFIX": "powercrud",
        "TIMEOUT": None,
    },
}

POWERCRUD_SETTINGS = {
    "ASYNC_ENABLED": True,
    "CACHE_NAME": "powercrud_async",
    "PROGRESS_TTL": 7200,
    "CONFLICT_TTL": 3600,
    "CLEANUP_GRACE_PERIOD": 86400,
}
```

Create the cache table if you use the database backend:

```bash
python manage.py createcachetable powercrud_async_cache
```

See the [async architecture reference](../reference/async.md#cache-design) for deeper background on how PowerCRUD uses the cache.

???+ note "Redis Backend"

    Prefer a Redis (or other network) backend once you move beyond local demos. For example:

    ```python title="settings.py"
    CACHES = {
        "powercrud_async": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://:{REDIS_PASSWORD}@redis.example.com:6379/3",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
            },
            "KEY_PREFIX": "powercrud",
            "TIMEOUT": None,
        },
    }
    ```

---

## 3. Optional: configure dashboard persistence

You can add dashboard tracking later—async queueing works without it. When you are ready, point `ASYNC_MANAGER_DEFAULT` at `ModelTrackingAsyncManager` and follow [Section 05](05_async_dashboard.md) to create the dashboard model. For per-view overrides use `async_manager_class_path` / `async_manager_config`.

---

## 4. Update the view

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # … existing configuration …

    bulk_async = True                    # turn async on
    bulk_min_async_records = 20          # threshold before queueing
    bulk_async_conflict_checking = True  # enable lock checks
```

- When a user selects >= `bulk_min_async_records`, the job is queued via django-q2.
- Conflict checking prevents overlapping operations on the same objects.

---

## 5. Expose the progress endpoint in project-level `urls.py`

```python
# urls.py
from powercrud.async_manager import AsyncManager

urlpatterns = [
    AsyncManager.get_urlpatterns(),  # registers /powercrud/async/progress/ under powercrud namespace
    # …
]
```

The modal polls this endpoint automatically and stops once it receives HTTP 286.

!!! warning "Project Level Not App Level"

    Add this once in your **project-level** `urlpatterns` so Django registers the `powercrud` namespace. Do not also call `get_url()` separately; the include already exposes `/powercrud/async/progress/`.

---

## 6. Understand the lifecycle

1. **Launch** – The view reserves locks, creates a progress key, and enqueues `powercrud.tasks.bulk_update_task` or `bulk_delete_task`.
2. **Worker** – The task runs inside `qcluster`, updating progress (e.g., `updating: 3/20`) and ultimately returning success/failure.
3. **Completion hook** – `powercrud.async_hooks.task_completion_hook` cleans up locks/progress and fires lifecycle events (which the dashboard manager consumes).
4. **Cleanup command** – If a worker dies midway, `python manage.py pcrud_cleanup_async` removes stale locks and progress entries.

You can run the cleanup manually or add `powercrud.schedules.cleanup_async_artifacts` to the qcluster schedule.

---

## 7. Monitoring & troubleshooting

| Symptom | Likely fix |
|---------|------------|
| Modal keeps polling forever | Check qcluster logs; if the worker crashed, run `pcrud_cleanup_async`. |
| “Conflict detected” message | Another async job holds locks on the same records; the dashboard shows the culprit. |
| `ImproperlyConfigured` about cache | Ensure `CACHE_NAME` points to a shared backend (not LocMem/Dummy). |
| Manager class errors | Confirm the manager path is importable and subclasses `AsyncManager`. |
| `'powercrud' is not a registered namespace` | Include `AsyncManager.get_urlpatterns()` (or `powercrud.urls`) once in the project-level `urlpatterns`. |
| `bulk_update_task() got an unexpected keyword argument 'manager_class'` | The worker is running an older PowerCRUD version—upgrade the package in the worker environment and restart `qcluster`. |

Whenever you change async settings, update PowerCRUD, or adjust cache configuration, restart the `qcluster` worker so it reloads the latest code and settings.

---

## 8. Optional Async Task Dashboard

If you configured `ModelTrackingAsyncManager`, you already have basic dashboard persistence—[Section 05](05_async_dashboard.md) dives into customising it. If you rolled your own manager, make sure lifecycle events (`create`, `progress`, `complete`, `fail`, `cleanup`) are handled or at least logged.

Full command/reference details live in [configuration reference](../reference/config_options.md) and [management commands](../reference/mgmt_commands.md).

## Key options

| Setting | Default | Typical values | Purpose |
|---------|---------|----------------|---------|
| `bulk_async` | `False` | bool | Enable async queueing for bulk operations. |
| `bulk_min_async_records` | `20` | int | Threshold before a job is queued instead of run synchronously. |
| `bulk_async_conflict_checking` | `True` | bool | Guard against overlapping operations. |
| `POWERCRUD_SETTINGS["ASYNC_ENABLED"]` | `False` | bool | Global master switch for async features. |
| `CACHE_NAME` | `'default'` | cache alias | Cache used for locks and progress. |
| `CONFLICT_TTL`, `PROGRESS_TTL` | `3600`, `7200` | seconds | TTLs for lock/progress entries. |
| `CLEANUP_GRACE_PERIOD` | `86400` | seconds | How long to keep tasks in the active set. |
| `MAX_TASK_DURATION` | `3600` | seconds | Consider tasks “stuck” after this time. |
| `CLEANUP_SCHEDULE_INTERVAL` | `300` | seconds | Suggested interval when scheduling cleanup jobs. |
| `ASYNC_MANAGER_DEFAULT` / `async_manager_class_path` | manager path | string | Optional: point at `ModelTrackingAsyncManager` (or a subclass) when you add dashboard persistence. |

_Details for each option live in the [configuration reference](../reference/config_options.md)._ 

---

## Next steps

### Nested workflows

If child objects perform additional work during `save()` while the parent task is running async, call `skip_nested_async()` and `register_descendant_conflicts()` (Section 03) to avoid launching new tasks inside the existing job and to bring descendant IDs under the same conflict lock. The sample project’s `Book.save()` shows this pattern in practice.

---

## Next steps

- Need a refresher on the underlying helpers? Revisit [03 Async manager outside PowerCRUD](03_async_manager.md).
- Ready to surface lifecycle data? Continue with [05 Async dashboard add-on](05_async_dashboard.md).
