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

The fix needs to keep async optional: PowerCRUD should import cleanly without django-q, and async behaviour should only activate when both `POWERCRUD_SETTINGS["ASYNC_ENABLED"]` and django-q are configured.

## Issues to Address

- Eager imports in `powercrud.async_manager` and `powercrud.async_hooks`.
- `AsyncMixin` falls back to `bulk_async=False` but still imports the async stack during module load.
- No regression tests guarantee a basic project (no `POWERCRUD_SETTINGS`, no django-q) can import `PowerCRUDMixin`.
- Test suite only runs with the rich async settings module; we need a minimal settings file (no django_q, no POWERCRUD_SETTINGS) plus pytest hooks so core tests run there without exploding.
- Documentation doesn’t mention that django-q is optional/guarded—users assume it is required.

## Plan of Attack

1. [ ] Add tests that simulate the “no django-q” environment.
   - [ ] Create a minimal test settings module without `POWERCRUD_SETTINGS` and without `django_q` in `INSTALLED_APPS`; run a smoke test under that module to prove imports/CRUD views still work.
   - [ ] Reload `powercrud.mixins` while `django_q` is blocked; ensure imports succeed and `POWERCRUD_SETTINGS` absence does not crash.
   - [ ] Instantiate `AsyncManager` under that scenario and verify async methods raise clean `ImproperlyConfigured` only when used.
   - [ ] Ensure async-only tests use `pytest.importorskip("django_q")` so running the core suite under minimal settings does not explode.
2. [ ] Implement lazy-import guards.
   - [ ] Move `django_q` imports inside helper that caches the modules and raises a friendly error when async is used without django-q.
   - [ ] Delay reading `settings.Q_CLUSTER` until async is explicitly enabled and Django settings are configured.
   - [ ] Update `AsyncMixin` to short-circuit when async is disabled globally or dependencies are missing.
3. [ ] Harden docs and developer guidance.
   - [ ] Update async guide + README to clarify optional dependency and configuration flags.
   - [ ] Document how to run the minimal-settings test suite (so contributors can reproduce the “no async” path) and add a release-note entry describing the guard/test coverage improvements.
