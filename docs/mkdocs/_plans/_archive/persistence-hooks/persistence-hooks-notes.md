# Persistence Hooks Notes

## Purpose

This note set captures the current state of PowerCRUD persistence, the downstream DDMS use case, and a recommended way to introduce explicit persistence seams without over-coupling workers to CRUD view instances.

The immediate problem is not that PowerCRUD persists incorrectly. The problem is that the persistence extension surface is fragmented across several internal paths, so downstream apps must know too much about framework internals in order to keep business write orchestration consistent.

## Current persistence paths

### 1. Standard form save

PowerCRUD currently persists validated create/update forms in `FormMixin.form_valid()` by calling `form.save()` directly.

Relevant code:

- `src/powercrud/mixins/form_mixin.py:735`
- `src/powercrud/mixins/form_mixin.py:770`
- `neapolitan.views.CRUDView.form_valid()` is also built around `form.save()`

Implication:

- This path is easy to wrap with a dedicated single-object persistence hook.

### 2. Inline row save

PowerCRUD currently persists validated inline forms in `InlineEditingMixin._dispatch_inline_row()` by calling `form.save()` directly after validation and guard checks.

Relevant code:

- `src/powercrud/mixins/inline_editing_mixin.py:39`
- `src/powercrud/mixins/inline_editing_mixin.py:76`

Implication:

- This path is semantically the same shape as standard form persistence.
- It should share the same hook contract as standard form persistence.

### 3. Synchronous bulk update

PowerCRUD currently processes sync bulk update by building normalized payload in `bulk_edit_process_post()` and then delegating to `_perform_bulk_update()`.

Relevant code:

- `src/powercrud/mixins/bulk_mixin/view_mixin.py:282`
- `src/powercrud/mixins/bulk_mixin/view_mixin.py:450`
- `src/powercrud/mixins/bulk_mixin/operation_mixin.py:109`

The actual update logic is not form-shaped:

- `fields_to_update` is built from request payload
- `field_data` is normalized manually
- objects are mutated directly inside a transaction
- m2m updates are handled explicitly
- each row is validated and saved individually

Implication:

- Bulk should have its own contract.
- It should not be forced into a fake `ModelForm` abstraction.

### 4. Async bulk update

Async bulk launch currently happens in `AsyncMixin._handle_async_bulk_operation()`, which passes serializable arguments to worker functions.

Relevant code:

- `src/powercrud/mixins/async_mixin.py:332`
- `src/powercrud/mixins/async_mixin.py:404`

The worker then resolves the model and runs bulk update logic on a bare `BulkMixin()` instance:

- `src/powercrud/tasks.py:79`
- `src/powercrud/tasks.py:118`

Implication:

- Async bulk is already built around worker-safe payload and explicit resolution.
- The missing piece is not async orchestration. The missing piece is a worker-safe persistence backend/strategy abstraction.

### 5. Standalone `AsyncManager`

`AsyncManager` already handles:

- queue launch
- conflict reservation
- progress keys
- completion hooks
- lifecycle events
- manager class/config resolution

Relevant code:

- `src/powercrud/async_manager.py:324`
- `src/powercrud/async_manager.py:486`
- `src/powercrud/async_manager.py:1231`

Implication:

- `AsyncManager` should remain orchestration infrastructure.
- It should not become the place where downstream business persistence logic lives.

## Why sync hooks first

The sync part is the cleanest first release because it lets PowerCRUD solve the real downstream problem immediately without forcing an async abstraction prematurely.

Reasons:

- Standard form and inline are already the same persistence shape.
- Sync bulk is different, but still runs inside the originating view instance and is easy to route through an explicit hook.
- Async bulk has a different execution boundary and should reuse a worker-safe abstraction rather than a view hook.

## Recommended v1 sync hook contracts

### 1. Shared single-object persistence hook

Recommended shape:

```python
def persist_single_object(self, *, form, mode, instance=None):
    """Persist one validated form-backed object and return the saved object."""
    return form.save()
```

Suggested `mode` values:

- `"form"`
- `"inline"`

Recommended semantics:

- Called only after `form.is_valid()` succeeds.
- Returns the saved object instance.
- Used by both `FormMixin.form_valid()` and `InlineEditingMixin._dispatch_inline_row()`.
- Default behavior should preserve current PowerCRUD behavior.

Important ownership rule:

- If an override does not call `form.save()` directly, the override owns any required `form.save_m2m()` handling.
- This should be explicit in docs and docstrings.

Why this matters:

- Downstream apps can route standard form and inline writes through the same domain service.
- PowerCRUD retains responsibility for validation and UI response flow.

### 2. Separate synchronous bulk update hook

Recommended shape:

```python
def persist_bulk_update(
    self,
    *,
    queryset,
    fields_to_update,
    field_data,
    progress_callback=None,
):
    """Persist a bulk update operation and return a standard result payload."""
    return self._perform_bulk_update(
        queryset,
        bulk_fields=self.get_bulk_fields(),
        fields_to_update=fields_to_update,
        field_data=field_data,
        progress_callback=progress_callback,
    )
```

Notes:

- The exact implementation detail can vary, but the contract should remain bulk-shaped.
- The input should be normalized payload such as `fields_to_update` and `field_data`.
- The return shape should stay aligned to PowerCRUD’s current bulk result payload:
  `{"success": bool, "success_records": int, "errors": list}`.

Important scope choice:

- V1 should focus on bulk update.
- Bulk delete can remain separate unless there is a concrete downstream need to route delete through domain services as well.

## Recommended async direction

### Core principle

Do not pass a live CRUD view instance into async workers.

Reasons:

- View instances are request-scoped.
- They contain UI/runtime state that is irrelevant or unsafe in worker execution.
- They may not be serializable.
- They are harder to reason about and test in worker code.

### Recommended async abstraction

Introduce a worker-safe bulk persistence backend/strategy abstraction that can be resolved from import path plus config.

Illustrative shape:

```python
class BulkPersistenceBackend:
    """Worker-safe strategy for bulk persistence."""

    def persist_bulk_update(
        self,
        *,
        queryset,
        fields_to_update,
        field_data,
        context,
        progress_callback=None,
    ):
        """Persist a bulk update and return the standard result payload."""
        ...
```

Potential resolved inputs:

- `bulk_persistence_backend_path`
- `bulk_persistence_backend_config`

Potential `context` contents:

- `model_path`
- `selected_ids`
- `user_id`
- `task_key`
- `mode` such as `"bulk-sync"` or `"bulk-async"`
- optional feature-specific metadata

Important design point:

- `context` should be plain data, not a live view.

### How async bulk could use it

At launch time:

- the view resolves whether a backend is configured
- the view passes backend path/config to the worker
- the worker resolves the backend and delegates persistence

That means the async worker still owns:

- model resolution
- progress reporting
- queue lifecycle

But it no longer owns the business-specific interpretation of how bulk writes should occur.

### How sync bulk could use it

Sync bulk can optionally delegate to the same backend contract when configured.

Benefits:

- consistent semantics between sync and async bulk
- no need to invent two different bulk extension contracts
- workflow-aware downstream apps can disable async until parity is acceptable

### How standalone `AsyncManager` fits

The same backend abstraction can be used outside CRUD views.

Example shape:

- a custom worker launched via `AsyncManager.launch_async_task()`
- the worker accepts `bulk_persistence_backend_path` and config
- the worker resolves the backend and calls the same `persist_bulk_update(...)` contract

This keeps `AsyncManager` reusable without making it responsible for domain write behavior.

## Recommended boundaries

### PowerCRUD should own

- validation and UI flow for normal forms and inline edits
- normalized payload construction for bulk update
- queue orchestration, conflict locks, progress, lifecycle hooks
- default persistence behavior when no hooks/backend are configured

### Downstream apps should own

- domain update services
- workflow revalidation policy
- side effects that are specific to app semantics
- custom persistence backends where async and sync bulk need business-aware orchestration

## Open questions

### 1. Final v1 method names

Current preferred names:

- `persist_single_object(...)`
- `persist_bulk_update(...)`

Alternative naming may be acceptable, but the contract should emphasize persistence rather than UI form semantics.

### 2. Whether bulk delete needs a matching contract

Current recommendation:

- do not include bulk delete unless there is a real downstream requirement

Reason:

- the driving use case is workflow-sensitive updates, not deletes
- keeping scope tight improves the odds of a clean first release

Follow-up note:

- Delete persistence hooks are a valid later enhancement area once the update hooks have shipped and settled.
- If revisited later, delete should be considered across all relevant shapes rather than partially:
    - single-object delete
    - sync bulk delete
    - async bulk delete
- Delete should remain a separate contract family from update persistence because domain delete semantics are usually materially different from update semantics.

### 3. How much of the current `_perform_bulk_update()` result shape becomes public API

Recommendation:

- treat the current result dict shape as the public v1 contract for bulk hooks

Reason:

- the rest of the bulk view flow already expects that shape
- changing it would create unnecessary adaptation work

### 4. Whether PowerCRUD should ship a base backend class for async bulk

Recommendation:

- yes, probably a minimal base class or protocol-like contract

Reason:

- it gives downstreams something explicit to implement
- it keeps docs and tests clearer

## Risks

### 1. Hidden m2m behavior in single-object overrides

Mitigation:

- document ownership explicitly
- add tests showing default path and custom path behavior

### 2. Exposing too much of the current bulk internals

Mitigation:

- make the hook contract public
- keep the rest of the internal helper methods private

### 3. Async parity drift

Mitigation:

- document clearly that sync hooks land first
- introduce the backend contract for async before encouraging workflow-heavy apps to enable async bulk on affected models

### 4. Overloading `AsyncManager`

Mitigation:

- keep persistence backend resolution separate from manager resolution
- use similar patterns, but not the same class responsibility

## Implementation touch points

Likely files for a real implementation:

- `src/powercrud/mixins/form_mixin.py`
- `src/powercrud/mixins/inline_editing_mixin.py`
- `src/powercrud/mixins/bulk_mixin/view_mixin.py`
- `src/powercrud/mixins/bulk_mixin/operation_mixin.py`
- `src/powercrud/mixins/async_mixin.py`
- `src/powercrud/tasks.py`
- likely a new backend module for persistence backend base/resolution helpers
- docs under `guides/` and `reference/`

## Testing notes

Sync tests needed:

- form save path calls the single-object hook
- inline save path calls the same hook
- default behavior remains unchanged when hooks are not overridden
- custom single-object hook can control persistence
- sync bulk update delegates through the public bulk hook
- bulk hook result contract drives the existing success/error UI correctly

Async tests needed in follow-up:

- worker resolves configured backend path/config
- async bulk update uses backend rather than raw `_perform_bulk_update()`
- sync bulk and async bulk can share the same backend semantics
- manager lifecycle/progress behavior remains unchanged
- standalone `AsyncManager` example works with the same backend contract
