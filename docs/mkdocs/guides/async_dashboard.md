# Async dashboard add-on

Turn lifecycle events into visible status. Whether you use the bundled `ModelTrackingAsyncManager` or build your own, this chapter covers how to persist task metadata, expose it in a dashboard, and customise formats.

---

## 1. Use the reusable dashboard manager

```python
from powercrud.async_dashboard import ModelTrackingAsyncManager

class AppAsyncManager(ModelTrackingAsyncManager):
    record_model_path = "myapp.AsyncTaskRecord"

    def format_user(self, user):
        if not user:
            return "Anonymous"
        if hasattr(user, "get_username"):
            return user.get_username()
        return str(user)

    def format_affected(self, affected):
        if isinstance(affected, (list, tuple, set)):
            return ", ".join(map(str, affected))
        return str(affected) if affected else ""
```

Then configure PowerCRUD (and other launch sites) to use it:

```python
POWERCRUD_SETTINGS = {
    "ASYNC_MANAGER_DEFAULT": {
        "manager_class": "myapp.async_manager.AppAsyncManager",
    }
}
```

If your dashboard model uses different field names, supply a `field_map` (either as a manager class attribute or inside the `config`) so lifecycle payload keys map cleanly to your columns.

The built-in manager handles:

- Creating/updating a dashboard record per task.
- Persisting progress messages, results, timestamps.
- Marking records cleaned up once locks are removed.

---

## 2. Dashboard model (example)

Reuse the sample model or tailor fields to your needs. If your field names differ, provide a `field_map` in the manager config so lifecycle payload keys line up with your model columns.

```python
class AsyncTaskRecord(models.Model):
    task_name = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, choices=STATUS.choices, default=STATUS.PENDING)
    message = models.TextField(blank=True)
    progress_payload = models.TextField(blank=True)
    user_label = models.CharField(max_length=255, blank=True)
    affected_objects = models.TextField(blank=True)
    result_payload = models.JSONField(blank=True, null=True)
    cleaned_up = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    failed_at = models.DateTimeField(blank=True, null=True)
```

Adjust types (e.g., JSON vs TextField) to suit the data you store.

---

## 3. Surfacing the dashboard

The sample app includes a CRUD view and detail page at `/sample/async-dashboard/`. You can copy that approach:

```python
class AsyncTaskRecordView(PowerCRUDMixin, CRUDView):
    model = AsyncTaskRecord
    namespace = "async"
    use_htmx = True
    use_modal = True
    fields = ["task_name", "status", "user_label", "updated_at"]
    detail_fields = ["task_name", "status", "message", "progress_payload", "result_payload", "completed_at", "failed_at"]
```

The detail view can poll the same progress endpoint to show live updates.

---

## 4. Custom lifecycle logic

If you need additional side-effects:

```python
class NotifyingAsyncManager(ModelTrackingAsyncManager):
    record_model_path = "myapp.AsyncTaskRecord"

    def async_task_lifecycle(self, event, task_name, **payload):
        super().async_task_lifecycle(event, task_name, **payload)
        if event == "fail":
            notify_ops(f"Task {task_name} failed: {payload.get('result')}")
        elif event == "complete":
            log_success(task_name, payload.get("result"))
```

Events you can handle:

- `create` – task queued
- `progress` – `update_progress` called
- `complete` – worker succeeded (may include `result`)
- `fail` – worker returned/raised failure
- `cleanup` – locks cleared (always fired after `complete`/`fail`)

---

## 5. Clean-up utilities

`cleanup_completed_tasks()` (called via `pcrud_cleanup_async`) sets `cleaned_up = True` on dashboard rows once locks and progress are removed. You can override `cleanup_dashboard_data` if you store additional related objects.

```python
class AppAsyncManager(ModelTrackingAsyncManager):
    def cleanup_dashboard_data(self, task_name):
        # return count of records deleted if you remove anything extra
        return 0
```

---

## 6. Sample app recap

Reference implementation lives in the `sample` project:

- `sample/models.AsyncTaskRecord`
- `sample/async_manager.SampleAsyncManager`
- `sample/views.AsyncTaskRecordCRUDView`
- `sample/tests.SampleAsyncDashboardTests`

Use it as a starting point or lift pieces directly into your project.

### Key options

| Setting / Hook | Default | Purpose |
|----------------|---------|---------|
| `async_manager_class_path` / `ASYNC_MANAGER_DEFAULT` | resolves to `AsyncManager` | Choose the manager that persists lifecycle events. |
| `record_model_path` | required | Tell `ModelTrackingAsyncManager` which model to write to. |
| `format_user`, `format_affected`, `format_payload` | basic formatters | Override formatting of stored metadata. |
| `async_task_lifecycle` | no-op | Hook into task events (`create`, `progress`, `complete`, `fail`, `cleanup`) for custom behaviour. |
| `cleanup_dashboard_data` | returns `0` | Remove dashboard artefacts during cleanup. |

See the sample app and reference for full implementations.

---

## Next steps

If you want to tweak the look and feel—modals, tables, Tailwind safelist—continue with [Styling & Tailwind](styling_tailwind.md). Otherwise, consult the [reference](../reference/mgmt_commands.md) for clean-up commands and settings.
