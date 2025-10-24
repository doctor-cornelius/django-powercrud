---
date: 2025-10-22
categories:
  - async
  - django
  - dashboard
---
# Async Dashboard Subclass

I implemented a dashboard but the steps in the downstream project to wire everything up are a bit clunky. This post outlines a possible reusable subclass to allow easier setup of the dashboard.
<!-- more -->

## Background

Right now a project that wants async lifecycle visibility has to:

- build a custom `AsyncManager` subclass that manually persists lifecycle events
- wire that subclass into every CRUD view through `get_async_manager_class`
- keep the implementation in sync with PowerCRUD changes (status handling, payload shapes, completion hook metadata)

The result works, but it repeats a lot of boilerplate (user labels, JSON serialisation, selective field updates) and makes it easy to miss edge cases like cleanup events landing with `status=None`.

## Plan

Introduce a reusable `ModelTrackingAsyncManager` in PowerCRUD that downstream apps can configure instead of subclassing from scratch:

- Accept a config object (or constructor kwargs) that points to the dashboard model and maps lifecycle fields (status, message, progress, result, timestamps, extras).
- Provide built-in helpers for serialising kwargs/args and formatting labels so most projects can rely on sensible defaults.
- Expose lightweight extension hooks (`format_user`, `format_objects`, `format_payload`) for custom formatting without reimplementing the lifecycle method.
- Update the async hook tests and documentation to show how views opt in by returning the configured manager class, keeping the worker and hook pipeline unchanged.

This should let downstream teams enable the dashboard by declaring a config rather than rewriting lifecycle plumbing, while still allowing bespoke dashboards to override the manager when needed.

## Design

### Base manager

- Ship `powercrud.async_dashboard.ModelTrackingAsyncManager`, a concrete `AsyncManager` that persists lifecycle events to a configured dashboard model (default schema matching `AsyncTaskRecord`).
- Allow configuration via class attributes or an optional `AsyncDashboardConfig` that names the record model and maps fields (status, message, progress payloads, timestamps, etc.).
- Provide overridable helpers (`format_user`, `format_affected`, `format_payload`) so projects can tweak stored values without rewriting the lifecycle handler.

### Wiring into views

- Extend `PowerCRUDMixin.get_async_manager_class()` to consult either a view attribute (`async_dashboard_manager = "myapp.async_manager.MyManager"`) or a global `POWERCRUD_SETTINGS["ASYNC_MANAGER_DEFAULT"]`.
- Downstream views keep using `PowerCRUDMixin`; they simply declare which manager to use:

```python
class OrdersCRUDView(PowerCRUDMixin, CRUDView):
    model = Order
    async_dashboard_manager = "myapp.async_manager.MyDashboardManager"
```

### Downstream configuration examples

- Settings-only configuration:

```python
POWERCRUD_SETTINGS = {
    "ASYNC_MANAGER_DEFAULT": {
        "manager_class": "powercrud.async_dashboard.ModelTrackingAsyncManager",
        "record_model": "myapp.AsyncTaskEvent",
    }
}
```

- Custom subclass for field formatting:

```python
from powercrud.async_dashboard import ModelTrackingAsyncManager

class MyDashboardManager(ModelTrackingAsyncManager):
    record_model_path = "myapp.AsyncTaskEvent"

    def format_user(self, user):
        return user.email if user else ""

    def format_affected(self, affected):
        return ", ".join(affected) if isinstance(affected, list) else str(affected)
```

### Sample/demo integration

- Update the sample project to adopt the base manager so the demo dashboard works out of the box.
- Document how bulk updates automatically populate the dashboard and how to override formatting when bespoke data is required.

## Detailed Steps

### Progress (2025-10-25)

- ✅ Step 1 – Base manager scaffolded (`powercrud.async_dashboard.ModelTrackingAsyncManager`) with config resolution and formatting helpers.
- ✅ Step 2 – Lifecycle persistence implemented with safe field updates plus payload normalisation.
- ✅ Step 3 – Configuration APIs delivered via AsyncDashboardConfig and class attributes.
- ✅ Step 4 – `AsyncMixin` now resolves dashboard manager from view or settings default.
- ✅ Step 5 – Hook + worker plumbing now propagate manager config through completion callbacks.
- ✅ Step 6 – Sample app now reuses ModelTrackingAsyncManager with minimal formatting overrides.
- ✅ Step 8 – Sample docs/tests updated; demo wiring now uses the reusable manager end-to-end.
- ✅ Step 7 – Regression tests expanded (manager resolution, cleanup flow) and all suites green.
- ✅ Step 8 – Docs need to be expanded after wiring lands.

1. ✅ **Design the base manager**

      - Define the `ModelTrackingAsyncManager` subclass of `AsyncManager`.
      - Decide the required metadata (status, message, payloads, timestamps, user info, affected objects).
      - Provide reasonable defaults for mapping lifecycle events to model fields and expose overridable formatters.

2. ✅ **Implement lifecycle persistence**

    - Implement `async_task_lifecycle` to `get_or_create` the dashboard record and update only the fields provided by each event.
    - Ensure cleanup events don’t overwrite meaningful values with `None` and rely on helper serializers for kwargs/args.
    - Track timestamps (`created`, `updated`, `completed`, `failed`) and result/progress payloads.

3. ✅ **Expose configuration APIs**

    - Allow downstream apps to instantiate the manager with a config object describing the model, field names, and optional formatters.
    - Offer constructor kwargs for simple cases while supporting reusable config classes for larger projects.

4. ✅ **Integrate with view mixins**

    - Provide a helper (or mixin override) that returns the configured manager so CRUD views don’t need bespoke subclasses.
    - Make sure `AsyncMixin` continues forwarding `manager_class` through task launch so workers and hooks instantiate the same configured manager.

5. ✅ **Update async hooks**

    - Confirm `task_completion_hook` works unchanged with the base manager; adjust only if new metadata needs to flow.
    - Add tests verifying that completion and failure events trigger the configured manager via the hook.

6. ✅ **Sample App Implementation**

    - Implement in the `sample` app, replacing the current wiring of the async dashboard
    - Update docs related to sample app if appropriate
    - Update / implement tests for the sample app as needed.

7. ✅ **Testing**

    - Add unit tests for the base manager covering create/progress/complete/fail/cleanup events and serialization edge cases.
    - Include integration-style tests ensuring view mixins launch tasks that generate dashboard records through the configured manager.

8. ✅ **Documentation & examples**

    - Document how to configure the reusable manager, including default field mapping and optional overrides.
    - Provide sample code in the docs repo showing a downstream project wiring the dashboard with minimal code.

 
