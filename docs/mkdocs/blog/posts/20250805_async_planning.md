---
date: 
  created: 2025-08-05
  updated: 2025-09-04
categories:
  - django
  - async
---
# Async Planning

This is a detailed architectural and implementation plan for async support for `PowerCRUD`. 

<!-- more -->

!!! note

    Within this post I refer sometimes to "wrapped" method or function or task. What I mean by that is the (synchronous) function that is "wrapped" by `django_q.tasks.async_task()`.

## Issues

There are 5 issues, each of which need to be considered at the level of `powercrud` as well as of downstream projects:

1. **Conflict detection**: maintain records of object ids that are subject to currently running async tasks. Prevent initiation of update (synchronous or asynchronous) if there is a clash. We will use the Django cache, regardless of backend.
2. **Dashboard**: I'd prefer to keep this at the downstream project level if possible, rather than bogging `powercrud` down with extraneous models required to support this stuff. But if a dashboard (and supporting model) is needed, then we need some way of getting `powercrud` bulk update async tasks into the dashboard. So need hooks or override methods or something.
3. **Progress Updates**: the "easy" pattern is to always write from within the "wrapped" task (ie the synchronous task that is called using `async_task()`) to the django cache and then use `htmx` polling on the front end where needed. We need front end progress updates probably in `powercrud` on the modals that pop-up to indicate conflict with existing async task. The cache-based approach avoids the need for extraneous models entirely.
4. **Launching async task**: this is more about having a common pattern for launching, since at both levels there is a need to share common conflict management framework, and possibly also the dashboard and progress frameworks.
5. **Error handling cascades**: we need a way to ensure cleanup of problematic task instances, including cleaning up associated progress and conflict and custom dashboard data.

## Architecture Strategy

### Conflict Management

The strategy is to maintain a record for all pending and running async tasks, what are the objects pending update. And if a new update or delete operation is selected (whether synchronous or asynchronous), we send the expected list of objects to be affected by that update and check the conflict. If no conflict, go ahead with async tasks.

**Backend**: Use a nominated cache (`POWERCRUD_SETTINGS.CACHE_NAME`).

**Important**: All conflict tracking uses Django's cache API as the sole abstraction. No backend-specific features (e.g., Redis pipelines/Lua scripts) are used to ensure compatibility with any cache backend.

- 3 methods:
    - `check_conflict(object_data: Dict[str, List]) -> Set[Hashable]`: provide list of dicts with model names as keys and ID lists as values (e.g., `{'myapp.User': [1, 2, 3], 'myapp.Order': [101, 102]}`) and get back set of conflicting IDs (empty set if no conflicts).
    - `add_conflict_ids(task_id: str, object_data: Dict[str, List]) -> bool`: add the specified model+ID combinations to conflict tracking for the given task using atomic reservation.
    - `remove_conflict_ids(task_id: str, object_data: Dict[str, List] = None)`: remove conflict tracking for specified task. If object_data is provided, only remove those specific model+ID combinations, otherwise remove all for the task

**Storage Implementation**

Maintain two complementary types of cache keys to efficiently manage conflicts and cleanup using Django's cache API.

???+ info "Cache Key Structure Explained"

    The cache is a flat key→value store, not nested dictionaries. Each object lock is its own top-level cache entry.

    !!! question ""Why not nested?"" 
    
        We can't atomically modify nested structures across all cache backends. Using separate top-level keys for each object allows us to use `cache.add()` for atomic "test-and-set" behavior - only one task can create a given object lock key.

    Think of it like this Python dict (conceptually):
    
    ```python
    cache = {
        # Per-object exclusive locks (one entry per row)
        "powercrud:conflict:model:myapp.User:42": "task_1234",
        "powercrud:conflict:model:myapp.User:43": "task_1234",
        "powercrud:conflict:model:myapp.Order:7": "task_1234",
        
        # Per-task tracking set (cleanup checklist)
        "powercrud:conflict:task:task_1234": {"myapp.User:42", "myapp.User:43", "myapp.Order:7"}
    }
    ```

    So the *key* is a concatenation of these identifying elements:

    - **namespace** (eg `powercrud`): Namespace for this package. Prevents collisions with other app keys.
    - **sub-namespace** (eg `conflict`): identifies the conflict locking feature (distinct from `progress`, etc).. Maybe we could benefit from even `async:conflict` 
    - **model** (ie literally `model`): type of lock indicating this is the model key lock not the task key lock
    - **model_name** (eg `powercrud.Book`): The Django model identifier used consistently across the system. Example: "myapp.User" (app_label.ModelClass). Must match what you pass into conflict functions and what’s stored in per-task tracking.
    - **object_id** (eg `7`): the object id of the model that is to be locked
  
    And the **value** is the **task_id** (eg `7`). So each model object gets its own key and is individually locked.

- **Per-task tracking:**
    Key format: `powercrud:conflict:task:{task_id}`
    Value: Python set of strings representing locked objects in the form `{model_name}:{object_id}`
    Example:
    ```
    powercrud:conflict:task:1234 → {
        "myapp.User:1",
        "myapp.User:3",
        "myapp.User:5",
        "myapp.Order:42",
        "myapp.Order:45"
    }
    ```
    Purpose: When the task completes, use this set's members to identify which per-model locks to remove during cleanup.

- **Per-model exclusive locks:**
    The key format `powercrud:conflict:model:{model_name}:{object_id}` is a **concatenated string**, not a nested path. Each combination of model+ID gets its own exclusive lock entry in the flat cache namespace.

    Key format: `powercrud:conflict:model:{model_name}:{object_id}`
    Value: String containing the task ID currently owning this object lock
    Example:
    ```
    powercrud:conflict:model:myapp.User:1   → "1234"
    powercrud:conflict:model:myapp.User:3   → "1234"
    powercrud:conflict:model:myapp.User:5   → "1234"
    powercrud:conflict:model:myapp.Order:42 → "1234"
    powercrud:conflict:model:myapp.Order:45 → "1234"
    ```
    Purpose: Quickly detect if an object is locked by checking if the key exists. Exclusive ownership ensures only one task can lock an object.

- **Adding conflicts (atomic reservation):**
    For each object, attempt `cache.add(per_model_key, task_id, ttl)`. If any `add()` fails (key exists), rollback all previously acquired locks for this task and return conflict. If all succeed, store the per-task tracking set.

- **Removing conflicts:**
    Read the per-task set to get all locked objects. For each object, delete the per-model lock key only if its current value equals this task_id (idempotent). Finally, delete the per-task key.


**Atomic Lodgement**: To avoid race conditions where two tasks check for conflicts at the same time and both think it's safe, conflict checking and reservation must happen atomically using Django's cache API.

**Implementation using `cache.add()` for atomic reservation:**
- Per-model locks use exclusive ownership via `cache.add(key, task_id, ttl)`
- `cache.add()` only succeeds if the key doesn't exist, providing atomic "test-and-set" behavior
- Algorithm:
  1. For each object to be locked, attempt `cache.add(per_model_key, task_id, ttl)`
  2. If any `add()` fails, immediately rollback all previously acquired locks and return conflict
  3. If all `add()` operations succeed, store the per-task tracking set
  4. Only then proceed with `async_task()` enqueue

**Execution timing:**
- Run conflict check and reservation **before** calling `async_task()`, not as a signal callback
- For `powercrud` bulk tasks and single-record edit/delete operations, call directly to avoid downstream signal dependencies
- Downstream projects can choose their own integration approach (direct calls vs signals)

**Notes**

!!! note "Conflict Checking of Single Record Update Delete in `powercrud`"

    In `powercrud` we prevent user from opening `Edit` or `Delete` form if this will conflict with a running async task. However we also need to check not just before allowing form to be shown, but also on form save. Because user may have left the form sitting there for a while, and in the meantime an async task affecting that object may have been launched and still running.

!!! warning "Downstream Project `save()` async descendant updates"

    In a current downstream project that I have, in the `save()` method of a number of models we have extensive updates (and creates, but that's not relevant to conflict checking) of descendant objects. And I will probably make these run async as part of the `save()` method. Of course I would want to flag them for conflict detection and management in the same framework.

    However if we do this, then if we had a bulk update of a number of objects we would have a problem:

    - send all objects to be updated async. We do not know about the descendant objects from within `powercrud` so only have parent id's.
    - call `save()` for object
    - then within `save()` try to call async task for descendant updates
    - the async sub-tasks all appear to complete immediately and our parent task ends, even though subtasks are continuing (perhaps for quite a while)

    So what we want is a `kwarg` in the `save()` method - let's say `skip_async`. And if that's the case then we **do not** raise the descendant update as a new async task, however what we do is add all those descendant objects to the conflict store.

### Progress Updates

In `powercrud` we try to detect even with the single record update and delete operations whether that record conflicts with a running async task. I want to be able to show some kind of progress on the modal that comes up, if possible (whatever is being 'pushed' from the underlying process). So that means we need a way of allowing for `htmx` polling to pick up the correct task stuff. We probably want a common pattern for this. I am thinking it's like this:

1. Use the cache.
2. Key is the `task_id` (or `f"async_{task_id}"`)
      1. To aid with cleanup, consider setting `TTL` (time to live) value when creating (eg 60 min, 120min to be safe) 
      2. For cleanup, use a scheduled `django-q2` task that only runs when async is enabled (check `POWERCRUD_SETTINGS[ASYNC_ENABLED]` flag). We could also make it conditional on having any active tasks: if no tasks are running and no progress records exist, the cleanup task does nothing. This keeps overhead minimal.
3. Value is populated from the underlying "wrapped" task. I think as a `str` to allow flexibility
4. `htmx` polling (say every 1 second) to view which returns the current progress value. If not found then go looking for the task status and show I guess 'success' or 'failed' (or even 'pending' or 'running' - surely they would always be in `django-q2`)? Also gracefully handle if nothing can be found.
      1. Consider allowing this as a parameter for bulk with default = 1s
      2. Consider adaptive polling: calculate in view and pass `estimated_time_per_task` back as context var, and/or adjust polling integer in the partial returned. 
5. The keys need to be cleared out. See below re the suggested pattern for launching `async_task()`. Also as noted above consider setting `TTL` or using a scheduled cleanup task (even better) that cleans out keys where `django_q2.Task` instances have completed.


!!! note "Use a single view for this stuff"

    `htmx` polls that view and sends `task_id` somehow (eg `hx-vals`), then the view just uses `task_id` to get what it needs. Put in `powercrud.async_utils` as it needs to be outside `PowerCRUDMixin`.

### Custom Async Task Dashboard

??? question "Why Have Separate Task Dashboard"

    We are using `django-q2` which already has the `Task` model. So why might we want a separate specialised task dashboard, potentially with a separate underlying model? 

    - additional data like the `user` that spawned the async task. For debugging but also if you want to present the user with their own tasks.
    - show specific details like id's affected, or other details that are downstream specific.

!!! note "Dashboards Always Configured in Downstream Project"

    By the way, this should **always** be configured in the downstream project. We are not putting this in `powercrud`. 

    What we need in `powercrud` are hooks for maintenance of the dashboard model if bulk tasks are to be included there.

What we need to support a custom dashboard:

- a way of storing required data (custom model or extract from `django_q2.Task`)

    ??? question "Is a Dashboard Model Always Needed?"

        Not always. We could have a view for the dashboard which interrogates the `django_q2.Task` model and even unpickles `args` and `kwargs` to get required data elements. Could be a little slow at high volume, but should be fine for <1000 open tasks.

        Another option less than a full dashboard table is a scheduled task that unpickles open tasks and extracts the required field (eg user) into a simple index table (eg `user`, `task_id`). Or even populates the task.

- a view to provide the data
- a template to present the data
- possibly, mechanisms to populate the store (eg on creation, changes, completion) **if** we are not extracting from `django_q2.Tasks`

What we need in `powercrud` is a task lifecycle function that can can be overridden. This would live in `powercrud.async_utils`: 

```python
def async_task_lifecycle(self, event, task_id, **kwargs):
    if event == 'create':
        # Dashboard creation logic here
        user = kwargs.get('user')
        affected_objects = kwargs.get('affected_objects')
        # ...
    elif event == 'progress':
        # Progress update logic
        progress_data = kwargs.get('progress_data')
        # ...
    elif event == 'complete':
        # Completion logic
        # ...
    elif event == 'cleanup':
        # task cleanup logic (would also be called under complete block)
        # ...
    elif event == 'error':
        # Error handling logic
        error = kwargs.get('error')
        # ...
```

### Launching `async_task()`

Whenever we launch `async_task()` -- whether from `powercrud` or a downstream project -- if we want to have shared access to conflict management, progress updates and/or custom dashboards then we need to have a common pattern that does this:

1. Check conflict before enqueuing.
2. Add conflict objects to the data collection before task starts executing (can be before or after enqueuing but after successful conflict check)
3. Create custom dashboard instance if needed
4. From within "wrapped" task:
      1. Progress updates if required
      2. Dashboard instance updates if required
5. On task completion:
      1. Remove objects from conflict data store
      2. Remove progress key (depending on design)
      3. Finalise custom dashboard instance
      4. Any addititional tasks (NB can be provided to `django_q2` as post completion `hook` when `async_task` is called)

### Error Handling Cascades

!!! note "The problem: Inconsistent State" 

    If your main task completes but cleanup fails, you get inconsistent state:

    - Task completed successfully
    - But conflict locks remain (blocking future operations)
    - Progress keys accumulate
    - Dashboard shows incorrect status

The error handling approaches to work in are:

- **Idempotent**: We need to have idempotent cleanup methods so they can be tried again and again (eg first check if exists and then only attempt to remove within a try/except block)
- **Scheduled Cleanup**: periodically cleanup (progress, conflict, dashboard) as a scheduled task:
    - clean up for all `django_q2.Task` instances that have completed
    - for all running instances that exceed a "grace period" (eg 2 hours, 1 day, whatever is a safe maximum longer than longest task)
    - for any pending tasks that are old, I guess we consider grace period or we wonder if `qcluster` is even running (and can we check that?)

### `powercrud` Method Architecture

It would be beneficial for downstream projects to have the option to use the same methods for progress update and/or conflict management as we use for bulk operations in `powercrud`.

To share these effectively, we'll use a hybrid approach combining **classes for stateful operations** and **standalone functions for utilities**. This provides the best balance of performance, extensibility, and ease of use. Classes allow us to cache backend connections and share state, while functions provide simple interfaces for one-off operations.

We'll have a package `powercrud.async_utils` that provides both class-based and function-based APIs, allowing downstream projects to choose the approach that best fits their needs.

### `POWERCRUD_SETTINGS`

Also consider something in `settings.py`. These settings use Django's cache abstraction (via 'CACHE_NAME'), automatically handling any configured backend without implementation details for downstream developers.

```python
POWERCRUD_SETTINGS = {
    'ASYNC_ENABLED': True,
    'CONFLICT_TTL': 3600,  # 1 hour
    'PROGRESS_TTL': 7200,  # 2 hours
    'CLEANUP_GRACE_PERIOD': 86400,  # 24 hours
    'MAX_TASK_DURATION': 3600,  # For detecting stuck tasks
    'CLEANUP_SCHEDULE_INTERVAL': 300,  # 5 minutes for scheduled cleanup

    'CACHE_NAME': 'default',  # Which cache from CACHES to use for conflict/progress
}
```

## Implementation Plan

### Phase 1: Foundation — Build the async core first

#### Task 1: Core Infrastructure Setup

- ✅ Create `src/powercrud/async_task_manager.py` with system detection functions
- ✅ Add `POWERCRUD_SETTINGS` configuration handling
- ✅ Add basic config and settings functions and `__init__`
- ✅ Write simple tests

#### Task 2: Conflict Detection Cache-Based Functions

- ✅ Implement dual-key conflict system using Django cache API only (no DB models)
- ✅ Implement core conflict functions: 
- ✅ Use `cache.add()` for atomic reservation of per-model locks
- ✅ Test conflict detection with simple scenarios and atomic reservation behavior

#### Task 3: Task Lifecycle & Launch Pattern

- ✅ Implement `launch_async_task()` wrapper function
- ✅ Add `async_task_lifecycle()` hook system
- ✅ Integrate conflict checking into launch pattern
- Add cleanup handling on task completion
- ✅ Test the complete launch → execute → cleanup cycle

#### Task 4: Progress Tracking Infrastructure

- ✅ Implement `update_progress()` and `get_progress()` functions  
- ✅ Add TTL handling and cleanup logic  
- ✅ Create basic progress polling view for HTMX  
- ✅ Test progress updates work across different Django cache configurations (e.g., default database and Redis).

#### Task 5: PowerCRUD Bulk Operations Integration

- ✅ Modify `src/powercrud/mixins/bulk_mixin.py` to use new async infrastructure  
- ✅ Update bulk edit/delete to check conflicts before proceeding  
- ✅ Integrate progress reporting into existing bulk tasks  
- ✅ Ensure backward compatibility with current bulk operation 
- ✅ Ensure bulk edit async conflict detection works

---

### Phase 2: Single-record safety

#### Task 6: Single Record Conflict Prevention

- ✅ Modify edit/delete views to check conflicts before showing forms  
- ✅ Add conflict checking on form submission  
- ✅ Create modal templates to show "operation in progress" messages  
- ✅ Add HTMX polling for progress display in conflict modals
- ✅ Write passing tests

#### Task 7: Dashboard Integration and Sample App Implementation

- ✅ Formalize lifecycle callback contract (`AsyncManager.async_task_lifecycle` / completion hook)
- ✅ Design lightweight async task record (fields: task name, status, user, timestamps, payload)
- ✅ Implement dashboard model & migrations inside `sample` app (so downstream projects can copy/adapt)
- ✅ Wire lifecycle callbacks to persist and update dashboard records
- ✅ Build dashboard views/templates (list + detail, with HTMX polling for active tasks)
- ✅ Provide management/cleanup utilities to purge completed/expired dashboard entries
- ✅ Remove legacy `powercrud.BulkTask` or migrate its usage to the new dashboard model
- ✅ Document how downstream apps can override lifecycle handlers or supply their own dashboard

##### Task 7 – Detailed Plan
1. **Lifecycle Contract**
    - ✅ Document required payload for `async_task_lifecycle(event, task_name, **kwargs)`
    - ✅ Ensure progress/completion hooks call lifecycle with consistent metadata
    - ✅ Write passing tests
2. **Data Model**
    - ✅ Define `sample.AsyncTaskRecord` (fields for identifiers, user, payload JSON, timestamps, status)
    - ✅ Add admin registration for debugging/visibility
3. **Lifecycle Wiring**
    - ✅ Hook `launch_async_task` (create), `update_progress` (progress), `handle_task_completion` (complete/fail) into model
    - ✅ Guarantee idempotent updates (e.g., `update_or_create`)
4. **UI / Views**
    - ✅ Create list view with filtering (status, user), HTMX-powered progress refresh
    - ✅ Optional detail modal showing payload/progress history
5. **Cleanup Utilities**
    - ✅ Management command or scheduled task to remove tasks older than TTL
    - ✅ Expose `AsyncManager.cleanup_dashboard_data(task_name)` for downstream overrides
6. **Legacy Removal**
    - ✅ Deprecate/remove `powercrud.BulkTask` (if unused) or move it to `sample` as historical reference
7. **Documentation & Tests**
    - ✅ Update docs with lifecycle guidance and dashboard integration steps
    - ✅ Write unit/integration tests covering lifecycle events -> dashboard records, UI responses, cleanup path

---

### Phase 3: Stability & Maintenance — Ensure reliability long-term

#### Task 8: Scheduled Cleanup System

- Create management command for cleanup operations  
- Implement `cleanup_completed_tasks()` function  
- Add scheduled task registration (django-q2 integration)  
- Handle cleanup of stale conflicts, progress, and dashboard data  
- Test cleanup works for various edge cases  

##### Task 8 – Detailed Plan

1. **Cleanup primitives**
    - Implement cache cleanup helpers for conflict locks (`powercrud:conflict:*`) and progress keys (`powercrud:async:progress:*`).
    - Add dashboard cleanup stub to `AsyncManager.cleanup_dashboard_data()` and wire the sample app to purge old `AsyncTaskRecord` rows.
    - Ensure helpers are idempotent and log what they remove.
2. **Orchestration API**
    - Add `AsyncManager.cleanup_completed_tasks()` (or similar) that calls the helpers and returns a summary dict.
    - Expose settings to tweak retention windows (`CLEANUP_GRACE_PERIOD`, `MAX_TASK_DURATION`).
3. **Management command**
    - Create `powercrud_cleanup_async` (or reuse sample’s command) that instantiates the manager, runs cleanup, and prints human-readable output.
    - Guard against running when async is disabled; exit with informative message.
4. **Scheduling integration**
    - Document how to schedule the command via cron/systemd.
    - Provide optional django-q2 schedule entry (e.g., add to `Q_CLUSTER['schedule']`) controlled by `POWERCRUD_SETTINGS['CLEANUP_SCHEDULE_INTERVAL']`.
5. **Testing**
    - Add unit tests that seed cache entries / dashboard rows, run cleanup, and assert the stale data is gone while active tasks remain.
    - Test the management command via Django’s `call_command` API to ensure it reports counts and respects the “async disabled” guard.
6. **Documentation**
    - Update `async_processing.md` with cleanup usage, configuration knobs, and scheduling examples.

#### Task 9: Error Handling & Robustness

- Make all cleanup operations idempotent  
- Add comprehensive error handling to async utilities  
- Implement graceful degradation when backends are unavailable  
- Add logging throughout the async system  
- Test error scenarios and recovery  

#### Task 10: Documentation & Examples

- Update README with async configuration examples  
- Create sample downstream integration examples  
- Document the lifecycle hooks and utility functions  
- Add configuration reference to docs  

---

**Execution strategy:**  
- **MVP = Tasks 1–5** (usable async core for bulk operations)  
- **Enhancements = Tasks 3 & 6** (progress UI + single-record safety)  
- **Stability = Tasks 7–9** (cleanup, error handling, docs)  


## Dual-Key Conflict System — Atomic Design and Cleanup

This section clarifies the final dual-key design used in PowerCRUD’s async conflict management. It explains the object lock keys, the object tracking set, atomic reservation via cache.add(), and the rollback/cleanup behavior.

- Terminology
    - Object lock keys (per-object exclusive locks)
      - Key: powercrud:conflict:model:{model_name}:{object_id}
      - Value: task_id string that currently owns the lock
      - Purpose: Atomic reservation using Django’s cache.add() so that only one task can acquire the lock for a given object at a time. This prevents race conditions.
      - Example keys:
          - powercrud:conflict:model:myapp.Book:2 -> "task_abc"
          - powercrud:conflict:model:myapp.Author:10 -> "task_abc"
      - Object tracking set (per-task cleanup index)
          - Key: powercrud:async:conflict:{task_id}
          - Value: a Python set of the exact lock key strings acquired by this task (e.g., {"powercrud:conflict:model:myapp.Book:2", ...})
          - Purpose: Enables complete, efficient, and idempotent cleanup of all object lock keys owned by a task without scanning the cache

- Why the cache is “flat”
    - We do not store nested structures for conflict state. Each object has its own dedicated lock entry.
    - This enables true atomic “test-and-set” using cache.add(key, value, ttl), which only succeeds if the key is absent across all supported Django cache backends.

- Atomic reservation (all-or-nothing)
    - For each requested object, try cache.add(per_object_lock_key, task_id, ttl).
    - If any add() fails (i.e., key exists and someone else holds that lock), we immediately:
        - Roll back all previously acquired locks for this task by deleting those lock keys
        - Return False to the caller so they know no objects were reserved
    - Only if all lock acquisitions succeed do we write the object tracking set for the task

- Cleanup
    - Lookup the object tracking set at key powercrud:async:conflict:{task_id}
    - For each member (which is a full object lock key string), delete that key from the cache
    - Finally, delete the tracking set itself
    - This cleanup is idempotent and safe to repeat; missing keys are simply ignored by the cache

- Code locations
    - Async manager implementation and docstrings reside in [src/powercrud/async_manager.py](src/powercrud/async_manager.py)

- Pseudocode reference

    Atomic reservation:

    ```python
    def add_conflict_ids(task_id, conflict_ids):
        acquired = []
        for model_name, ids in conflict_ids.items():
            for obj_id in ids:
                lock_key = f"powercrud:conflict:model:{model_name}:{obj_id}"
                # ATOMIC: only succeeds if key does not already exist
                if cache.add(lock_key, task_id, ttl):
                    acquired.append(lock_key)
                else:
                    # Rollback previously acquired locks
                    for k in acquired:
                        cache.delete(k)
                    return False
        # Store tracking set for cleanup
        tracking_key = f"powercrud:async:conflict:{task_id}"
        cache.set(tracking_key, set(acquired), ttl)
        return True
    ```

    Cleanup:

    ```python
    def remove_conflict_ids(task_id):
        tracking_key = f"powercrud:async:conflict:{task_id}"
        lock_keys = cache.get(tracking_key, set())
        for k in lock_keys:
            cache.delete(k)    # remove each object’s lock
        cache.delete(tracking_key)  # remove the tracking set
    ```

- Behavioral implications
    - No partial reservations: If a batch contains conflicting objects, either all objects are reserved or none are.
    - Conflict checks are O(n) direct lookups: To check whether a set of objects is locked, we look up the object lock keys directly. No scanning of all tasks is required.
    - Consistent cleanup: The object tracking set guarantees we can always remove the exact set of object locks we created for a task.

This final design is implemented and tested. See [src/powercrud/async_manager.py](src/powercrud/async_manager.py) for the production code with detailed docstrings that align with this document.
