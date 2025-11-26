---
date: 2025-11-25
categories:
  - async
  - error
---
# System Crashes on Load if Async Not Configured

Oops. I configured a small downstream project with `powercrud` without requiring `ASYNC_ENABLED` (actually without even `settings.POWERCRUD_SETTINGS` which is an bigger fail gievn it didn't report that was the issue). The system crashed on load because it tries to load `django_q` and requires `settings.Q_CLUSTER` even when not required.

We need to put some guards in to m ake the system robust. I got too caught up in my current dev environment with a very sophisticated setup for `powercrud` and forgot about the basic use cases. Oops.

<!-- more -->

## Summary

PowerCRUD currently assumes the async stack (django-q + `Q_CLUSTER`) exists the moment `powercrud.mixins` is imported. `PowerCRUDMixin` inherits `AsyncMixin`, which imports `AsyncManager`, which immediately imports `django_q` objects and touches `settings.Q_CLUSTER`. On lightweight installs (like the nanodjango demo) there is no `POWERCRUD_SETTINGS`, no `django_q` in `INSTALLED_APPS`, and no `Q_CLUSTER`, so simple imports crash before Django even configures settings. Downstream apps cannot opt out because the import happens at module load, not when async is explicitly enabled. We also need to confirm whether `POWERCRUD_SETTINGS` itself is optional: the guard logic should treat the setting as optional unless a project explicitly enables async, but we currently blow up even when the dict is absent.

Diagnostics so far:

- `AsyncManager` performs eager imports (`from django_q.models import Task`, etc.) and accesses `settings.Q_CLUSTER` in `__init__`, so import order alone can trigger ImproperlyConfigured.
- `AsyncMixin.get_bulk_async_enabled()` only checks per-view flags; it never verifies that async is globally enabled or that django-q exists, so the guardrail is ineffective.
- Tests only run under the “full” settings module where django-q is installed, so we never exercised the “no async” scenario in CI.

The fix needs to keep async optional: PowerCRUD should import cleanly without django-q, and async behaviour should only activate when both `POWERCRUD_SETTINGS["ASYNC_ENABLED"]` and django-q are configured. Architecturally, that means treating async as an explicit add-on: the default `PowerCRUDMixin` should stay synchronous and lightweight, while async capabilities are layered on via `AsyncMixin` (and a convenience composite mixin) in projects that intentionally opt into django-q.

## Issues to Address

- Eager imports in `powercrud.async_manager` and `powercrud.async_hooks`.
- `AsyncMixin` falls back to `bulk_async=False` but still imports the async stack during module load.
- No regression tests guarantee a basic project (no `POWERCRUD_SETTINGS`, no django-q) can import `PowerCRUDMixin`.
- Test suite only runs with the rich async settings module; we need a minimal settings file (no django_q, no POWERCRUD_SETTINGS) plus pytest hooks so core tests run there without exploding.
- Documentation doesn’t mention that django-q is optional/guarded—users assume it is required.

## Phased Plan

1. [ ] Decouple async from the default mixin and add minimal test coverage.
   1.1. [X] Remove `AsyncMixin` from `PowerCRUDMixin` and introduce a `PowerCRUDAsyncMixin` (or similar) that composes `AsyncMixin` and `PowerCRUDMixin` for downstream convenience.
   1.2. [X] Update any tests that relied on async being present in the default `PowerCRUDMixin` (e.g. views that implicitly exercised async behaviour) so they explicitly include the async mixin/composite.
   1.3. [X] Create a minimal test settings module without `POWERCRUD_SETTINGS` and without `django_q` in `INSTALLED_APPS`; add smoke tests under that module to prove imports/CRUD views still work in a “no async” configuration.
   1.4. [X] Ensure async-only tests use `pytest.importorskip("django_q")` (or equivalent) so running the core suite under the minimal settings does not explode.
   1.5. [X] Introduce clearer `ImproperlyConfigured` messages where appropriate (e.g. missing `POWERCRUD_SETTINGS` when async is explicitly enabled, or async mixins/managers used without django-q/Q_CLUSTER) and document the breaking change in the changelog/release notes.
   1.6 [X] update docs appropriately to reflect new approach for async
2. [ ] Harden async guards and error paths inside the async modules.
   2.1. [ ] Move `django_q` imports inside a helper that caches the modules and raises a friendly error when async is used without django-q.
   2.2. [ ] Delay reading `settings.Q_CLUSTER` until async is explicitly enabled and Django settings are configured, and ensure calls made too early produce a targeted configuration error rather than a low-level traceback.
   2.3. [ ] Update `AsyncMixin` and `AsyncManager` to short-circuit gracefully when async is disabled globally or dependencies are missing, with log messages that make it obvious why async is inactive.
   2.4. [ ] Expand tests for misconfigured async (wrong/missing `POWERCRUD_SETTINGS`, partial django-q setup) so we get clean, localised failures instead of crashes from deep inside django-q.
   2.5. [ ] Update async guide + README to clarify the “sync by default, async opt-in” model, document how to run the minimal-settings test suite, and add a release-note entry describing the guard and test coverage improvements.
