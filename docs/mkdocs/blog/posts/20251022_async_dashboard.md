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

## Detailed Steps

1. **Design the base manager**

      - Define the `ModelTrackingAsyncManager` subclass of `AsyncManager`.
      - Decide the required metadata (status, message, payloads, timestamps, user info, affected objects).
      - Provide reasonable defaults for mapping lifecycle events to model fields and expose overridable formatters.

2. **Implement lifecycle persistence**

    - Implement `async_task_lifecycle` to `get_or_create` the dashboard record and update only the fields provided by each event.
    - Ensure cleanup events don’t overwrite meaningful values with `None` and rely on helper serializers for kwargs/args.
    - Track timestamps (`created`, `updated`, `completed`, `failed`) and result/progress payloads.

3. **Expose configuration APIs**

    - Allow downstream apps to instantiate the manager with a config object describing the model, field names, and optional formatters.
    - Offer constructor kwargs for simple cases while supporting reusable config classes for larger projects.

4. **Integrate with view mixins**

    - Provide a helper (or mixin override) that returns the configured manager so CRUD views don’t need bespoke subclasses.
    - Make sure `AsyncMixin` continues forwarding `manager_class` through task launch so workers and hooks instantiate the same configured manager.

5. **Update async hooks**

    - Confirm `task_completion_hook` works unchanged with the base manager; adjust only if new metadata needs to flow.
    - Add tests verifying that completion and failure events trigger the configured manager via the hook.

6. **Documentation & examples**

    - Document how to configure the reusable manager, including default field mapping and optional overrides.
    - Provide sample code in the docs repo showing a downstream project wiring the dashboard with minimal code.

7. **Testing**

    - Add unit tests for the base manager covering create/progress/complete/fail/cleanup events and serialization edge cases.
    - Include integration-style tests ensuring view mixins launch tasks that generate dashboard records through the configured manager.

8. **Migration guidance**

    - Outline steps for projects currently using bespoke managers to migrate to the configurable base (e.g., supply a config, remove old overrides).
    - Keep backwards compatibility so existing overrides continue to function alongside the new path.
