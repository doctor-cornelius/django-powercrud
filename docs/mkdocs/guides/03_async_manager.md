# 03. Async Manager

PowerCRUD ships a full async infrastructure (conflict locks, progress cache, lifecycle hooks) that you can reuse in plain Django code—no PowerCRUD views required. This chapter shows the building blocks so you can launch background work from management commands, signals, admin actions, or bespoke views. For a deeper architectural walkthrough, see the [async architecture reference](../reference/async.md).

---

## Why reuse the manager?

- Consistent conflict management and cleanup across the whole project.
- Shared progress reporting via the same HTMX endpoint (or your own UI).
- Lifecycle hooks feed dashboards, notifications, audit logs, etc.
- One set of conventions whether work originates from PowerCRUD or anywhere else.

---

## 1. Basic pattern

```python
from powercrud.async_manager import AsyncManager

def launch_custom_task(*, user, affected_objects):
    manager = AsyncManager()

    # Optional: prevent overlapping work
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

Key points:

- `launch_async_task` accepts any callable path (string or callable) plus args/kwargs for the worker.
- `conflict_ids` is a dict of `{ "app_label.Model": {pk, …} }`. Skip it if you do not need locking.
- `user` / `affected_objects` travel through lifecycle events—useful for dashboards or notifications.

---

## 2. Worker functions

Workers mirror the PowerCRUD ones: accept `task_key` in kwargs and call `update_progress`.

```python
# myapp/tasks.py
def rebuild_project(project_id, *, task_key=None, manager_class=None, **kwargs):
    from powercrud.async_manager import AsyncManager

    manager = AsyncManager.resolve_manager(manager_class)
    project = Project.objects.get(pk=project_id)

    steps = [...]
    for idx, step in enumerate(steps, start=1):
        step.run(project)
        manager.update_progress(task_key, f"Step {idx}/{len(steps)}: {step.label}")

    return {"project": project_id, "steps": len(steps)}
```

- Workers can be regular functions or dotted-path strings.
- Always return a result payload (serialisable) so completion hooks can persist it.

---

## 3. Launch sites (examples)

The same helper can be triggered from almost anywhere in your project—admin actions, management commands, regular views—without touching PowerCRUD views directly. Below are a few common entry points to illustrate how little glue code is needed.

### Example integration points

Import the helper wherever you need it (for example `from .async_helpers import launch_custom_task`). You can then call it from multiple entry points.

```python
@admin.action(description="Rebuild projects in background")
def rebuild_projects(modeladmin, request, queryset):
    launch_custom_task(user=request.user, affected_objects=queryset)
```

### Management command

```python
class Command(BaseCommand):
    def handle(self, *args, **options):
        projects = Project.objects.filter(needs_refresh=True)
        launch_custom_task(user=None, affected_objects=projects)
```

### Regular view

```python
def start_rebuild(request, pk):
    project = get_object_or_404(Project, pk=pk)
    launch_custom_task(user=request.user, affected_objects=[project])
    return redirect("project-dashboard")
```

---

## 4. Progress API

Even when the work is not tied to a PowerCRUD view, you can reuse the HTMX polling endpoint:

```python
urlpatterns = [
    AsyncManager.get_url(name="async-progress"),
]
```

In your custom template, poll the endpoint with the `task_name` returned from `launch_async_task`.

---

## 5. Lifecycle hooks

If you need custom behaviour when tasks are created, progress, complete, or fail:

```python
class NotificationsAsyncManager(AsyncManager):
    def async_task_lifecycle(self, event, task_name, **payload):
        if event == "create":
            send_email(payload.get("user"), f"Task {task_name} queued")
        elif event == "fail":
            report_error(task_name, payload.get("result"))
```

Point `async_manager_class_path` (or the default setting) at your subclass so both launch sites and workers resolve the same logic.

---

## 6. Cleanup and maintenance

All the same tooling applies:

- `python manage.py pcrud_cleanup_async` clears stale locks/progress.
- `AsyncManager.cleanup_completed_tasks()` returns a summary dict if you want to run it yourself.
- Scheduled cleanup via `powercrud.schedules.cleanup_async_artifacts`.

Remember to call `remove_conflict_ids` / `remove_active_task` only through the manager (typically the completion hook does it automatically).

### Key options

| Option / Method | Default | Purpose |
|-----------------|---------|---------|
| `AsyncManager.launch_async_task` | n/a | Queue arbitrary callables with conflict IDs, metadata, and manager config. |
| `AsyncManager.add_conflict_ids` / `remove_conflict_ids` | n/a | Reserve and release locks manually. |
| `AsyncManager.update_progress` | n/a | Push progress messages from custom workers. |
| `AsyncManager.resolve_manager` | falls back to `AsyncManager` | Rehydrate the correct manager class in workers/hooks. |
| `AsyncManager.cleanup_completed_tasks` | returns summary dict | Programmatic cleanup summary (used by `pcrud_cleanup_async`). |

Refer back to this guide or the API reference when wiring bespoke integrations.

---

## Next steps

Use the manager to power any asynchronous workflow you need. When you are ready to queue bulk operations inside PowerCRUD, continue with [04 Bulk editing (async)](04_bulk_edit_async.md). For dashboards and lifecycle persistence, see [05 Async dashboard add-on](05_async_dashboard.md). Grab deeper architectural detail in the [async architecture reference](../reference/async.md).
