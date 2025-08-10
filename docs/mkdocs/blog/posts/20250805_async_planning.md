---
date: 2025-08-05
categories:
  - django
  - async
---
# Async Planning

I've been thinking about this a bit more and this post is to progress detailed planning.

!!! note

    Within this post I refer sometimes to "wrapped" method or function or task. What I mean by that is the (synchronous) function that is "wrapped" by `django_q.tasks.async_task()`.

## Issues

There are 5 issues, each of which need to be considered at the level of `powercrud` as well as of downstream projects:

1. **Conflict detection**: maintain records of object ids that are subject to currently running async tasks. Prevent initiation of update (synchronous or asynchronous) if there is a clash. The conflict management framework needs to be shared across both levels. Need to use either (redis) cache or custom database model.
2. **Dashboard**: I'd prefer to keep this at the downstream project level if possible, rather than bogging `powercrud` down with extraneous models required to support this stuff. But if a dashboard (and supporting model) is needed, then we need some way of getting `powercrud` bulk update async tasks into the dashboard. So need hooks or override methods or something.
3. **Progress Updates**: the "easy" pattern is to always write from within the "wrapped" task (ie the synchronous task that is called using `async_task()`) to the redis cache (or a custom model) and then use `htmx` polling on the front end where needed. We need front end progress updates probably in `powercrud` on the modals that pop-up to indicate conflict with existing async task. If we use redis then there's no need to worry about extraneous models.
4. **Launching async task**: this is more about having a common pattern for launching, since at both levels there is a need to share common conflict management framework, and possibly also the dashboard and progress frameworks.
5. **Error handling cascades**: we need a way to ensure cleanup of problematic task instances, including cleaning up associated progress and conflict and custom dashboard data.

<!-- more -->

## Conflict Detection

The strategy is to maintain a record for all pending and running async tasks, what are the objects pending update. And if a new update or delete operation is selected (whether synchronous or asynchronous), we send the expected list of objects to be affected by that update and check the conflict. If no conflict, go ahead with async tasks.

Brainstorm stuff:

- use `redis` if running else fallback to `powercrud.models.AsyncConflict`. Or just say screw it - if you want this stuff you have to have `redis` (at least for release 1)?
- 3 methods (different mechanics for `redis` vs model):
    - `check_conflict(ids: List[Dict]) -> bool` - provide list of model + id pairs or else `{'model_name':[id1, id2, ...]}` and get back conflict as True or False.
    - `add_ids(task_id: str, model_name: str, ids: list) -> bool` - add to the existing id's associated with a task
    - `remove_ids(task_id: str)` - remove all for specified task (triggered on post task execution whether successful or failed)
- So the record of ids subject to running async tasks basically is unique on model + id + task_id
- do we run the confict check **before** we run `async_task`? Or do we run as a `django_q.signals.pre-enqueue` callback in signals?
    - I dunno. I have an aversion to using signals (too easy to forget them), but it does feel convenient.
    - Let's always leave the choice up to downstream. And for `powercrud` bulk tasks and the checking on edit or delete, do not use the signal but just call directly. Otherwise we are bogging all downstream projects down with the effects of `powercrud.signals`.

!!! note "Conflict Checking of Single Record Update Delete in `powercrud`"

    In `powercrud` we prevent user from opening `Edit` or `Delete` form if this will conflict with a running async task. However we also need to check not just before allowing form to be shown, but also on form save right? Because user may have left the form sitting there for a while, and in the meantime an async task affecting that object may have been launched and still running.

!!! warning "Downstream Project `save()` async descendant updates"

    In a current downstream project that I have, in the `save()` method of a number of models we have extensive updates (and creates, but that's not relevant to conflict checking) of descendant objects. And I will probably make these run async as part of the `save()` method. Of course I would want to flag them for conflict detection and management in the same framework.

    However if we do this, then if we had a bulk update of a number of objects we would have a problem:

    - send all objects to be updated async. We do not know about the descendant objects from within `powercrud` so only have parent id's.
    - call `save()` for object
    - then within `save()` try to call async task for descendant updates
    - the async sub-tasks all appear to complete immediately and our parent task ends, even though subtasks are continuing (perhaps for quite a while)

    So what we want is a `kwarg` in the `save()` method - let's say `skip_async`. And if that's the case then we **do not** raise the descendant update as a new async task, however what we do is add all those descendant objects to the conflict store.

## Progress Updates

We probably want a common pattern for this. I am thinking it's like this:

1. Assume `redis` for now (otherwise need a model `powercrud.models.AsyncProgress`)
2. Key is the `task_id` (or `f"async_{task_id}"`)
      1. To aid with cleanup, consider setting `redis` `TTL` (time to live) value when creating (eg 60 min, 120min to be safe) 
3. Value is populated from the underlying "wrapped" task. I think as a `str` to allow flexibility
4. `htmx` polling (say every 1 second) to view which returns the current progress value. If not found then go looking for the task status and show I guess 'success' or 'failed' (or even 'pending' or 'running' - surely they would always be in `django-q2`)? Also gracefully handle if nothing can be found.
5. The keys need to be cleared out. See below re the suggested pattern for launching `async_task()`. Also as noted above consider setting `TTL` or using a scheduled cleanup task (even better) that cleans out keys where `django_q2.Task` instances have completed.

In `powercrud` we try to detect even with the single record update and delete operations whether that record conflicts with a runnung async task. I want to be able to show some kind of progress on the modal that comes up, if possible (whatever is being 'pushed' from the underlying process). So that means we need a way of allowing for `htmx` polling to pick up the correct task stuff.

!!! question "Do we have a single view for this stuff?"

    It would work, right? `htmx` polls that view and sends `task_id` somehow (eg `hx-vals`), then the view just uses `task_id` to get what it needs.

    And if we have that in `powercrud` do we allow that to be accessed from downstream? Because if we do, it needs to be outside `PowerCRUDMixin` and just be a stand-alone method (or a static class method I guess, now that I think about it).

## Custom Async Task Dashboard

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

## Launching `async_task()`

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

## Error Handling Cascades

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

## `powercrud` Method Architecture 

It would be beneficial for downstream projects to have the option to use the same methods for progress update and/or conflict management as we use for bulk operations in `powercrud`. 

To share these, it's better (for semantic clarity and appropriate mental model) if they are stand-alone functions, rather than static methods of `PowerCRUDMixin`. So let's have a module `powercrud.async_utils` and allow imports of these helper methods from there.

So, to support downstream projects using the same async infrastructure as `powercrud`, we'll provide a comprehensive utility module with the following functions:

### Core Async Operations
- `check_conflict(object_ids)` - Check if objects conflict with running tasks
- `add_conflict_ids(task_id, model_name, ids)` - Add objects to conflict tracking
- `remove_conflict_ids(task_id)` - Remove all conflict tracking for a task
- `update_progress(task_id, progress_data)` - Update task progress information
- `get_progress(task_id)` - Retrieve current progress for a task

### System Detection
- `is_q_cluster_configured()` - Check if Q_CLUSTER settings are present
- `can_import_django_q2()` - Test if django-q2 can be imported
- `is_q_cluster_running()` - Check if qcluster instance is actually running
- `is_redis_available()` - Test Redis connectivity (not just configuration)
- `get_redis_connection()` - Get working Redis connection or None
- `is_django_redis_available()` - if `django_redis` is available then may provide greater options (eg for `Q_CLUSTER` configuration)
- `get_preferred_backend()` - Return 'redis' or 'database' based on availability

### Task Management
- `get_task_status(task_id)` - Get status from django-q2 Task model
- `is_task_complete(task_id)` - Boolean check for task completion
- `cleanup_completed_tasks()` - Clean up artifacts for completed tasks (for scheduled cleanup)
- `validate_async_system()` - Health check for all async components

### Configuration Helpers
- `get_conflict_ttl()` - Get TTL setting for conflict tracking
- `get_progress_ttl()` - Get TTL setting for progress updates
- `generate_task_id()` - Generate consistent task ID patterns (if needed)

### Dashboard Integration
- `async_task_lifecycle(event, task_id, **kwargs)` - Default implementation of lifecycle hook
- `cleanup_dashboard_data(task_id)` - Clean up custom dashboard artifacts

This structure allows downstream projects to import exactly what they need while maintaining consistency with `powercrud`'s internal async handling.

## Consider `POWERCRUD_SETTINGS`

Also consider something in `settings.py`. These settings will handle the backend detection automatically (Redis vs database fallback), so downstream developers don't need to worry about implementation details.

```python
POWERCRUD_SETTINGS = {
    'ASYNC_ENABLED': True,
    'CONFLICT_TTL': 3600,  # 1 hour  
    'PROGRESS_TTL': 7200,  # 2 hours
    'PREFERRED_BACKEND': 'auto',  # 'redis', 'database', 'auto'
    'CLEANUP_GRACE_PERIOD': 86400,  # 24 hours
    'REDIS_KEY_PREFIX': 'powercrud:',
    'MAX_TASK_DURATION': 3600,  # For detecting stuck tasks
    'CLEANUP_SCHEDULE_INTERVAL': 300,  # 5 minutes for scheduled cleanup
}
```

And have a `powercrud.async_utils.get_powercrud_settings(key, default=None)` function to easily retrieve the dictionary.