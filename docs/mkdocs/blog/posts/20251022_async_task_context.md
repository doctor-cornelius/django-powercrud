---
date: 2025-10-22
categories:
  - async
  - django
---
# Async Task Context

This is to provision functionality which addresses this issue:

!!! warning "Downstream Project `save()` async descendant updates"

    In a current downstream project that I have, in the `save()` method of a number of models we have extensive updates (and creates, but that's not relevant to conflict checking) of descendant objects. And I will probably make these run async as part of the `save()` method. Of course I would want to flag them for conflict detection and management in the same framework.

    However if we do this, then if we had a bulk update of a number of objects we would have a problem:

    - send all objects to be updated async. We do not know about the descendant objects from within `powercrud` so only have parent id's.
    - call `save()` for object
    - then within `save()` try to call async task for descendant updates
    - the async sub-tasks all appear to complete immediately and our parent task ends, even though subtasks are continuing (perhaps for quite a while)

    So what we want is a `kwarg` in the `save()` method - let's say `skip_async`. And if that's the case then we **do not** raise the descendant update as a new async task, however what we do is add all those descendant objects to the conflict store.
    
<!-- more -->

## Background

Our async bulk workers already coordinate conflict locks, progress updates, and dashboard entries, but downstream code (model `save()` overrides, helpers) has no way to know whether it is running inside an existing async job. Without that context, nested saves may kick off their own async tasks, causing race conditions:

- Parent async task launches bulk updates with only parent IDs reserved.
- `save()` on each parent spins up child async work; the parent job sees no errors and the dashboard reports “success” even though descendants are still running.
- Child records are not added to the conflict store, so subsequent updates can race against in-flight descendant jobs.

We need a shared task context so nested code can:

1. Detect the outer async job and suppress additional async launches.
2. Register descendant object IDs in the conflict store under the same parent task key.
3. Emit progress messages under the parent task key.

## Plan

### ✅ Task 1 – Context utilities

- Create `powercrud.async_context` with a `ContextVar` that stores task metadata (`task_name`, manager class path, optional manager instance).
- Provide helpers:
    - `set_current_task(task_name, manager_class_path, manager)` (context manager or decorator).
    - `get_current_task()` → returns the metadata dict or `None`.
    - `skip_nested_async()` → `True` if a task context exists.
    - `register_descendant_conflicts(model_name, ids)` → reuses current manager to call `add_conflict_ids`.

### ✅ Task 2 – Wire the workers

- In `powercrud.tasks.bulk_update_task` and `bulk_delete_task`, wrap the business logic with the new context (using manager class path passed via kwargs).
- Ensure context is cleared at the end (context manager handles this).
- When downstream workers are resolved via `AsyncManager.resolve_manager`, include the class path so the context has it.

### ✅ Task 3 – AsyncManager integration

- Update `AsyncManager.launch_async_task` to pass `manager_class_path` and `task_name` into worker kwargs (if not already).
- Provide a helper `get_manager_for_context(manager_class_path)` to instantiate the manager on demand within `register_descendant_conflicts`.

### ✅ Task 4 – Downstream usage helper

- Add a utility (e.g., `powercrud.async_context.register_descendants(model_name, ids)`) that downstream `save()` methods can call.
- Document pattern for `save(self, *args, task_key=None, **kwargs)`:
    - If `skip_nested_async()` is `True`, call `register_descendants()`, carry out work synchronously, and emit progress.
    - Otherwise launch a new async task.

### ✅ Task 5 – Tests

1. Unit tests for `async_context` helpers (set/get, skip flag, register conflicts).
2. Worker tests ensuring context is set during execution and cleaned up afterwards.
3. Integration test simulating parent → child flow:
    - Parent worker calls `register_descendants`.
    - Confirm conflict lock set for child IDs and no additional async tasks enqueued.

### ✅ Task 6 – Documentation

- Extend `async_processing.md` with a “Nested async saves” section showing how to use the new helpers.
- Update the planning post (this page) as tasks are completed.
- Optionally add a sample snippet in the demo project illustrating `skip_nested_async` usage.

### ✅ Task 7 – Sample demo

- Add demonstration models (e.g., Parent/Child) in the `sample` app that exercise the new context helpers.
- Provide a view or management command that launches the parent async workflow and surfaces progress/conflict registration for descendants.
- Include artificial delays so the progress modal clearly shows nested updates.
- Implementation outline:
    1. Update `sample.models.Book.save()` (or a dedicated helper) to simulate child processing with a short loop, leveraging `get_current_task()` / `skip_nested_async()` to register descendant conflicts and push progress messages when running inside an async job.
    2. Ensure an entry point (bulk update or small demo view/management command) triggers the async workflow so the UI displays the nested progress.
    3. Add unit tests that patch `AsyncManager.update_progress` / `add_conflict_ids`, wrap `Book.save()` in `task_context(...)`, and assert child work runs synchronously without spawning extra async tasks.
*** End Patch
