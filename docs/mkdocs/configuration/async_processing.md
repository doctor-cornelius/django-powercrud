## Async Processing

PowerCRUD can hand long-running bulk work off to `django-q2`, keeping the UI responsive while still showing progress and preventing conflicting edits. This guide walks you through the flow from “turn it on” to “customise the dashboard”, with the technical details tucked into focused sections.

---

### Quick start

Follow these steps in order:

1. **Install and run django-q2**
   ```bash
   pip install django-q2
   python manage.py migrate django_q
   python manage.py qcluster
   ```
   Add `"django_q"` to `INSTALLED_APPS` and keep a worker process running alongside your web server.

2. **Configure a shared cache**
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
   ```bash
   python manage.py createcachetable powercrud_async_cache
   ```
   Any backend (Redis, Memcached, DatabaseCache) works as long as both web and worker processes share it. A `LocMem`/`Dummy` cache will silently break locks and progress, so avoid those.

3. **Tell views which async manager to use**
   ```python title="settings.py"
   POWERCRUD_SETTINGS = {
       # ...
       "ASYNC_MANAGER_DEFAULT": {
           "manager_class": "powercrud.async_dashboard.ModelTrackingAsyncManager",
           "config": {"record_model_path": "yourapp.AsyncTaskRecord"},
       }
   }
   ```
   or per-view:
   ```python title="views.py"
   class OrderView(PowerCRUDMixin, CRUDView):
       async_manager_class_path = "yourapp.async_manager.OrderDashboardManager"
   ```
   The reusable `ModelTrackingAsyncManager` covers most dashboards. Supply `record_model_path` so it knows where to persist lifecycle events.

4. **Expose the HTMX progress endpoint**
   ```python title="urls.py"
   from powercrud.async_manager import AsyncManager

   urlpatterns = [
       AsyncManager.get_url(),  # /powercrud/async/progress/
       ...
   ]
   ```

5. **Enable async bulk actions in your view**
   ```python
   class OrderView(PowerCRUDMixin, CRUDView):
       bulk_async = True
       bulk_min_async_records = 10  # optional threshold
       bulk_async_conflict_checking = True
   ```

That’s enough to launch a bulk edit, keep the modal open with live progress, and surface the task on your dashboard.

---

### Architecture at a glance

| Layer | Responsibility | You customise by… |
|-------|----------------|-------------------|
| `AsyncMixin` | Decides when to go async, checks for conflicts, starts the job, passes manager metadata to workers and hooks. | Toggling `bulk_async`, `bulk_min_async_records`, or overriding helper methods in your view. |
| `AsyncManager` | Adds/removes cache locks, tracks progress, raises lifecycle events, exposes the polling endpoint, performs cleanup. | Providing a different manager class/config or overriding lifecycle/misc hooks. |
| Dashboard / UI | HTMX modal + optional dashboard view showing running/completed jobs. | Using the provided templates, or pointing the manager at your own dashboard model for richer data. |

---

### Task lifecycle

1. **Launch** – `AsyncMixin` generates a UUID, reserves locks (`add_conflict_ids`), creates a progress key, and enqueues the worker via `django_q.tasks.async_task`. The manager class path plus optional config are stored with the job.
2. **Worker execution** – Functions in `powercrud.tasks` rehydrate the same manager (`AsyncManager.resolve_manager`) so progress updates and lifecycle hooks go to the right place. Progress updates simply call `manager.update_progress(task_key, "updating 3/10")`.
3. **Completion** – The django-q2 completion hook loads the job’s kwargs, resolves the manager again, and calls `handle_task_completion`. Locks, progress keys, and any dashboard records are cleaned up; lifecycle callbacks fire with final status/result.
4. **Cleanup command / schedule** – `python manage.py pcrud_cleanup_async` (or the scheduled helper in `powercrud.schedules`) reconciles cached “active” tasks with django-q2, removing stale locks/progress if a worker died mid-job.

Diagrammatically:

```
view → AsyncMixin → AsyncManager.launch_async_task
     → django-q2 worker → AsyncManager.update_progress(...)
     → completion hook → AsyncManager.handle_task_completion(...)
     → optional scheduled cleanup → AsyncManager.cleanup_completed_tasks()
```

---

### Progress UI and conflict handling

- The modal polls `/powercrud/async/progress/` every second. When the manager returns HTTP 286 the polling stops and the modal emits `bulkEditSuccess`/`refreshTable`.
- `AsyncManager.get_task_status_cache_only()` keeps most checks in the cache; the heavier `get_task_status_nowait()` is only used when the cache indicates completion.
- Single-record forms reuse the same conflict logic: attempting to edit/delete a locked row returns a conflict partial instead of proceeding.

---

### Choosing a dashboard manager

**Recommended:** configure the built-in `ModelTrackingAsyncManager`.

- Set it globally via `POWERCRUD_SETTINGS["ASYNC_MANAGER_DEFAULT"]`.
- Or in a view: `async_manager_class_path = "powercrud.async_dashboard.ModelTrackingAsyncManager"` and optionally `async_manager_config = {"record_model_path": "yourapp.AsyncTaskRecord"}`.
- Extend it only to tweak formatting:
  ```python
  from powercrud.async_dashboard import ModelTrackingAsyncManager

  class MyDashboardManager(ModelTrackingAsyncManager):
      record_model_path = "yourapp.AsyncTaskEvent"

      def format_user(self, user):
          return user.email if user else ""

      def format_affected(self, affected):
          return ", ".join(affected) if isinstance(affected, list) else str(affected)
  ```

**Advanced:** override `async_task_lifecycle`. You still can (and sometimes should) when you need behaviour beyond storing rows—for example firing a notification, pushing metrics, or logging to an audit trail. The lifecycle event carries:

- `event`: `"create"`, `"progress"`, `"complete"`, `"fail"`, `"cleanup"`
- `status`: normalised value (`pending`, `in_progress`, `success`, `failed`, `unknown`)
- `message`, `progress_payload`, `result`
- `user`, `affected_objects`, `task_args`, `task_kwargs`
- Timestamp (`timezone.now()` if none supplied)

The reusable manager consumes this payload to update the dashboard model; your override can call `super()` then add extra behaviour.

---

### Maintenance & troubleshooting

- **Health checks** – Use `AsyncManager.validate_async_cache()` and `validate_async_qcluster()` in a readiness probe.
- **Cleanup** – Run `python manage.py pcrud_cleanup_async` to clear stale locks/progress/dashboard rows. The command prints (or, with `--json`, returns) a summary of what it removed or skipped.
- **Scheduled cleanup** – Add `powercrud.schedules.cleanup_async_artifacts` to your django-q2 schedule if you want automatic cleanup.
- **Important settings**:
  | Setting | Purpose |
  |---------|---------|
  | `CACHE_NAME` | Shared cache alias for locks/progress. |
  | `PROGRESS_TTL` / `CONFLICT_TTL` | How long cache entries live if cleanup never runs (seconds). |
  | `CLEANUP_GRACE_PERIOD` | How long to keep a task in the active set before scheduled cleanup revisits it. |
  | `MAX_TASK_DURATION` | Optional limit used by cleanup to force-remove stuck tasks. |

If the modal keeps polling forever, check the qcluster logs. A worker crash can leave locks behind, in which case running `pcrud_cleanup_async` will free them.

---

### Sample app reference

The `sample` project demonstrates a complete integration:

- `sample.async_manager.SampleAsyncManager` subclasses `ModelTrackingAsyncManager` and customises formatting.
- `sample.views.SampleCRUDMixin` sets `async_manager_class_path` so every sample CRUD view uses the configured manager.
- `sample.models.AsyncTaskRecord` is the dashboard model populated by the reusable manager.
- `sample/tests.py::SampleAsyncDashboardTests` exercises the lifecycle flow, ensuring create/progress/complete/fail/cleanup land in the dashboard as expected.

Copy or adapt those pieces for your own project—or point your own manager config at your bespoke dashboard model and you’re done.
