## Async Processing

PowerCRUD’s async support lets long-running bulk actions move out of the request
thread while keeping the UX responsive:

- destroy the "spinner of doom": launch the work, return control to the user in seconds.
- show meaningful progress (`updating 7/25`, `completed 25 processed`) in the bulk edit modal while the worker runs if the user elects to wait. More usually, user will close the modal and continue working
- prevent accidental collisions: conflict locks stop users from editing or deleting records that an async job is already touching

These gains are delivered by an opinionated pipeline that builds on django-q2
workers, a shared cache, and HTMX-powered polling. This guide explains how to
enable the pipeline, how each component works, and what parts downstream
projects can override (or simply reuse).

### Overview

PowerCRUD’s async support consists of three cooperating layers:

1. **AsyncManager (`powercrud.async_manager.AsyncManager`)** handles launch orchestration, conflict locking, progress keys, lifecycle callbacks, and the HTMX progress endpoint.
2. **AsyncMixin (`powercrud.mixins.async_mixin.AsyncMixin`)** adds async options to CRUD views: deciding when to queue jobs, checking for conflicts, rendering conflict messages, and dispatching the work to AsyncManager.
3. **Templates & HTMX snippets** such as `bulk_edit_form.html`, `object_form.html`, and their partials render progress updates, conflict messages, and completion notifications while staying inside the modal UI.

### Prerequisites

- **django-q2** must be installed, added to `INSTALLED_APPS`, and running via `python manage.py qcluster`.
- **Shared cache** that both the web process and qcluster workers can reach. AsyncManager defaults to a `DatabaseCache` alias named `powercrud_async`, but Redis or Memcached works as long as it is shared. LocMem/Dummy caches will raise `ImproperlyConfigured`.
- **POWERCRUD_SETTINGS** entries controlling cache alias, TTLs, and optional tuning (see below).

### Configuration Checklist

#### 1. Shared cache alias

The cache stores two critical pieces of state:

- **Conflict locks** (`powercrud:conflict:model:app_label.Model:pk`) so only one async job can operate on a record at a time
- **Progress payloads** (`powercrud:async:progress:{task_name}`) so the UI can show per-record updates

Both the web process and the qcluster worker must read and write the same cache. If you use `LocMemCache` (the default Django dev backend) the worker and web process each see their own in-memory copy—no locks, no progress. That’s why PowerCRUD enforces a shared cache.

```python title="settings.py"
CACHES = {
    "default": {
        # your existing cache configuration
    },
    "powercrud_async": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "powercrud_async_cache",
        "KEY_PREFIX": "powercrud",
        "TIMEOUT": None,
    },
}

POWERCRUD_SETTINGS = {
    # ...
    "CACHE_NAME": "powercrud_async",
    "PROGRESS_TTL": 7200,
    "CONFLICT_TTL": 3600,
    "CLEANUP_GRACE_PERIOD": 86400,
}
```

```bash
python manage.py createcachetable powercrud_async_cache
```

The database cache is shown here because it works everywhere—but Redis or Memcached are fine choices too. The key requirement is that both the web process and the qcluster worker connect to the **same** cache instance.

!!! warning "Avoid LocMem/Dummy Cache"
    If you point `POWERCRUD_SETTINGS["CACHE_NAME"]` at a `LocMemCache` or `DummyCache`, conflict detection silently fails and progress stays blank because each process reads its own private in-memory data. Always choose a cache backend that is shared across processes.

```python title="settings.py"
CACHES = {
    "default": {
        # your existing cache configuration
    },
    "powercrud_async": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "powercrud_async_cache",
        "KEY_PREFIX": "powercrud",
        "TIMEOUT": None,
    },
}

POWERCRUD_SETTINGS = {
    # ...
    "CACHE_NAME": "powercrud_async",
    "PROGRESS_TTL": 7200,
    "CONFLICT_TTL": 3600,
    "CLEANUP_GRACE_PERIOD": 86400,
}
```

Create the database-backed cache table once:

```bash
python manage.py createcachetable powercrud_async_cache
```

Prefer Redis/Memcached? Use those backends instead, as long as the alias named in `POWERCRUD_SETTINGS["CACHE_NAME"]` is shared.

#### 2. Ensure qcluster reads the same settings

When running `python manage.py qcluster`, make sure the environment exports the same `DJANGO_SETTINGS_MODULE` so the worker loads the cache alias. If you use a Procfile or systemd service, include the same env vars as the web process.

#### 3. Optional validation hooks

AsyncManager exposes inexpensive health checks:

```python
from powercrud.async_manager import AsyncManager

def check_powercrud_async():
    manager = AsyncManager()
    ok_cache = manager.validate_async_cache()
    ok_cluster = manager.validate_async_qcluster()
    return ok_cache and ok_cluster
```

Run this in a readiness probe or management command to catch misconfiguration before users do.

### Launch & Conflict Flow

1. **AsyncMixin.should_process_async(record_count)** compares the selected record count against `bulk_min_async_records`. If `False`, operations fall back to synchronous behaviour.
2. **Conflict detection** `_check_for_conflicts(selected_ids)` calls `AsyncManager.check_conflict()` with per-object cache keys. Conflicts return the list of clashing ids; bulk views render `bulk_edit_conflict`, single record views render the `object_form`/`object_confirm_delete` conflict partial.
3. **Launch** `_handle_async_bulk_operation()` (bulk) and `confirm_delete`/`form_valid` (single record) use AsyncManager to:
    - generate a task UUID
    - reserve conflict locks (`add_conflict_ids`)
    - seed the progress key with status `pending`
    - enqueue the task through `django_q.tasks.async_task`
    - record lifecycle metadata (future dashboard hook)

4. **Worker execution** – The worker functions in `powercrud/tasks.py` receive `task_key` via kwargs, so they can push progress updates with `AsyncManager.update_progress(task_key, message)`. If you override `AsyncMixin.get_async_manager_class()` in your view mixin, that manager class path is forwarded to the worker and instantiated there as well, so lifecycle callbacks (progress/completion/failure) run through your subclass.

### Progress Updates & HTMX Polling

PowerCRUD exposes a small JSON endpoint that the modal polls while the worker runs. You can register it in two ways:

- **`AsyncManager.get_url()` helper (recommended)** returns a ready-made `path()` entry so you can drop it straight into your `urlpatterns`:

    ```python title="urls.py"
    from powercrud.async_manager import AsyncManager

    urlpatterns = [
        AsyncManager.get_url(),  # → /powercrud/async/progress/
    ]
    ```

- **`AsyncManager.as_view()`** returns the underlying view function in case you need to customise the URL or wrap it yourself:

    ```python title="urls.py"
    from django.urls import path
    from powercrud.async_manager import AsyncManager

    progress_view = AsyncManager.as_view()

    urlpatterns = [
        path("custom/progress/", progress_view, name="my_async_progress"),
    ]
    ```

Inside the templates (see `bulk_edit_form.html`) HTMX polls this endpoint every second:

```html
<div id="progress-display"
     hx-get="{% url 'powercrud:async_progress' %}"
     hx-vals='{"task_name": "{{ task_name }}"}'
     hx-trigger="every 1s"
     hx-target="#progress-display"
     hx-swap="innerHTML">
    <div class="loading loading-spinner loading-lg mx-auto"></div>
    <p class="mt-2">Starting...</p>
</div>
```

Responses include:

- `status: "in_progress"` with progress text (worker-supplied string)
- `status: "pending"` while the worker spins up
- `status: "success"` (HTTP 286) once complete, stopping the poller
- `status: "failed"` for worker exceptions
- `status: "unknown"` if neither cache nor cluster knows about the task (falls
    back to generic messaging)

When the modal receives `success`/`failed`, the JS stops polling, updates the heading (e.g., “Bulk Operation Completed”), fires `bulkEditSuccess`/`refreshTable` events, and closes the modal.

### Single Record Safeguards

Single-record forms now share the same conflict logic:

- `show_form` checks `_check_for_conflicts([obj.pk])`, rendering the conflict
    partial when the record is locked by an async job.
- `form_valid` re-checks the conflict immediately before saving; if the object
    is locked, it renders the conflict partial instead of saving.
- `confirm_delete` and `process_deletion` consult the same lock to prevent
    delete while a bulk job is touching the record.

### Lifecycle callbacks

PowerCRUD fires lifecycle callbacks whenever task state changes. Override
`AsyncManager.async_task_lifecycle(event, task_name, **payload)` to integrate
with dashboards, notifications, or audit logs.

| Event      | Typical status      | Trigger                                             |
|------------|---------------------|-----------------------------------------------------|
| `create`   | `pending`           | Task queued successfully (includes user/object metadata) |
| `progress` | `in_progress`       | Worker calls `update_progress()` with a new message |
| `complete` | `success` or `unknown` | Worker reports `success=True` or `success=None`        |
| `fail`     | `failed`            | Worker reports `success=False` (message includes error) |
| `cleanup`  | `unknown`           | After completion/failure, when locks are cleared     |

Each payload includes:

- `status`: normalised value from `AsyncManager.STATUSES`
- `message`: human-readable text (`"Task queued"`, progress message, or error)
- `progress_payload`: raw progress string (when applicable)
- `user`: user object or identifier provided at launch
- `affected_objects`: optional descriptor passed at launch
- `task_kwargs`: snapshot of kwargs sent to the worker (best-effort)
- `task_args`: list of positional arguments passed to the worker
- `result`: worker result or error payload on completion
- `timestamp`: timezone-aware timestamp (defaults to `timezone.now()`)

Lifecycle callbacks never raise—exceptions are logged as warnings—so it is safe
to plug in downstream integrations without affecting task execution.

#### Downstream integration pattern

Downstream projects typically subclass `AsyncManager` and persist lifecycle data to their own model. The `sample` app ships with `SampleAsyncManager`, which you can adapt:

```python title="sample/async_manager.py"
from powercrud.async_manager import AsyncManager
from .models import AsyncTaskRecord

class SampleAsyncManager(AsyncManager):
    def async_task_lifecycle(self, event, task_name, **kwargs):
        incoming_status = kwargs.get("status")
        message = kwargs.get("message") or ""
        timestamp = kwargs.get("timestamp")

        record, created = AsyncTaskRecord.objects.get_or_create(
            task_name=task_name,
            defaults={
                "status": incoming_status or AsyncTaskRecord.STATUS.UNKNOWN,
                "message": message,
                "user_label": self._user_label(kwargs.get("user")),
                "affected_objects": self._serialise_objects(kwargs.get("affected_objects")),
                "task_kwargs": kwargs.get("task_kwargs"),
                "task_args": kwargs.get("task_args"),
            },
        )

        if not created:
            if incoming_status is not None:
                record.status = incoming_status
            if message:
                record.message = message

        if event == "progress":
            record.status = AsyncTaskRecord.STATUS.IN_PROGRESS
            record.progress_payload = kwargs.get("progress_payload") or message
        elif event == "complete":
            record.status = AsyncTaskRecord.STATUS.SUCCESS
            record.result_payload = kwargs.get("result")
            record.completed_at = timestamp
        elif event == "fail":
            record.status = AsyncTaskRecord.STATUS.FAILED
            record.result_payload = kwargs.get("result")
            record.failed_at = timestamp
        elif event == "cleanup":
            record.cleaned_up = True

        record.save(update_fields=[
            "status",
            "message",
            "progress_payload",
            "user_label",
            "affected_objects",
            "task_kwargs",
            "task_args",
            "result_payload",
            "cleaned_up",
            "completed_at",
            "failed_at",
            "updated_at",
        ])
```

Key takeaways:

- `status` and `message` should only be overwritten when new values are supplied—cleanup runs with `status=None`.
- Persist the UUID `task_name`; completion hooks use it to rehydrate the same manager class.
- Use `update_fields` so audit signals remain efficient.

#### Manager resolution in workers

When `AsyncMixin` launches a task it passes `manager_class="<module path>"`. Worker functions call `AsyncManager.resolve_manager()` with that path so lifecycle events use the same subclass. The completion hook (`powercrud.async_hooks.task_completion_hook`) reads the stored kwargs from `django_q.Task` and resolves the manager again for the final `complete`/`fail`/`cleanup` events. No extra wiring is needed downstream—just override `get_async_manager_class()` in your view mixin.

#### Testing your lifecycle integration

The repository contains tests you can mirror:

- `src/tests/async_tests/test_sys_functions.py::TestAsyncHookHelpers` covers manager resolution inside the hook.
- `sample/tests.py::SampleAsyncDashboardTests` checks that `SampleAsyncManager` records create/progress/complete/fail/cleanup events correctly.

For your project, add tests that:

- trigger each lifecycle event and assert your dashboard model reflects the change;
- ensure cleanup events do not reset success/failure statuses;
- run a real async bulk update end-to-end (if practical) and assert the dashboard view renders the expected status.

### Settings Reference

`POWERCRUD_SETTINGS` keys relevant to async operations:

- `CACHE_NAME` – shared cache alias for locks/progress (default `powercrud_async`)
- `PROGRESS_TTL` – seconds to keep progress entries alive (default 7200)
- `CONFLICT_TTL` – seconds before conflict locks expire automatically (default 3600)
- `CLEANUP_GRACE_PERIOD` – grace period for active task cleanup (default 86400)
- `MAX_TASK_DURATION`, `CLEANUP_SCHEDULE_INTERVAL` – advanced timers for future
    scheduled cleanup

### Behaviour Without Shared Cache

If you skip the shared cache, async jobs still run and complete, but the UI cannot display incremental progress—workers and web processes hold separate LocMem stores. The modal will show only the initial “Preparing asynchronous job…” message until the completion hook fires. For best UX, always configure a shared cache.

### Sample dashboard (preview)

The `sample` project includes a reference implementation:

- `sample.models.AsyncTaskRecord` stores lifecycle data.
- `sample.async_manager.SampleAsyncManager` overrides the lifecycle hook to persist records.
- `sample.views.AsyncTaskRecordListView` renders an HTMX-friendly dashboard at `/sample/async-dashboard/`.
- `python manage.py cleanup_async_tasks` purges old records.

Use it as a blueprint: copy the model, override `get_async_manager()`, and tailor the dashboard views for your project.
