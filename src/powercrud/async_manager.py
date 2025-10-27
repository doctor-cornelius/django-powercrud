import time
import uuid
from typing import Dict, List, Set, Any, Callable, Optional, Hashable
from datetime import timedelta
import importlib
import json
from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured
from django.http import JsonResponse
from django_q.models import Task
from django_q.tasks import async_task, fetch, delete_cached
from django.utils import timezone

from powercrud.conf import get_powercrud_setting

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class AsyncManager:
    """Manager for async task lifecycle with dual-key conflict detection system.
    
    This class provides a complete async task management system including:
    - Atomic conflict detection using Django's cache API
    - Task lifecycle management (launch, monitor, cleanup)
    - Progress tracking for long-running operations (Task 4)
    - Backend-agnostic implementation (works with any Django cache backend)
    - Pre-enqueue conflict reservation with automatic rollback
    - Module-level completion hooks for distributed cleanup
    
    The core innovation is the dual-key conflict detection system that prevents
    race conditions while ensuring complete cleanup:
    
    Key Types:
        - Object lock keys: Per-object exclusive locks for atomic reservation
        - Object tracking sets: Per-task cleanup indices for reliable removal
        - Progress keys: Per-task progress storage for UI polling (Task 4)
        - Active task registry: Central tracking of running tasks
        
    Task 3 Launch Pattern:
        The launch_async_task() method implements atomic task launching:
        1. Generate unique task_key (UUID)
        2. Reserve object locks (if conflict_ids provided)
        3. Initialize progress tracking
        4. Enqueue task with completion hook and task_key
        5. Register in active tasks (without re-locking)
        6. Fire lifecycle 'create' event
        
    Completion Pattern:
        Tasks use the module-level completion hook which:
        1. Derives task_key from Task.name
        2. Calls handle_task_completion() (overridable by subclasses)
        3. Default stub allows downstream projects to implement cleanup
        
    Example:
        ```python
        manager = AsyncManager()
        
        # Launch with conflict detection and lifecycle events
        try:
            task_key = manager.launch_async_task(
                func='my_app.tasks.bulk_update',
                data=[...],
                conflict_ids={'myapp.Book': {1, 2, 3}},
                user=request.user
            )
            # Use task_key for progress polling, etc.
        except Exception as e:
            # Handle conflicts or launch failures
            pass
        ```
        
    Attributes:
        cache: Django cache instance for conflict and progress storage
        conflict_ttl: Time-to-live for conflict locks (seconds)
        progress_ttl: Time-to-live for progress data (seconds)
        cleanup_grace_period: Grace period before cleanup (seconds)
        task_key: Unique application-level task identifier (independent of django-q2)
    """

    class STATUSES:
        """Choices for async task statuses"""
        PENDING = 'pending'
        IN_PROGRESS = 'in_progress'
        SUCCESS = 'success'
        FAILED = 'failed'
        UNKNOWN = None

    def __init__(self):

        self.cache_name = self.get_cache_name()
        self.cache = self.get_cache()
        self.validate_cache_backend()
        self.qcluster_settings = getattr(settings, 'Q_CLUSTER', {})
        self.conflict_ttl = get_powercrud_setting('CONFLICT_TTL')
        self.progress_ttl = get_powercrud_setting('PROGRESS_TTL')
        self.cleanup_grace_period = get_powercrud_setting('CLEANUP_GRACE_PERIOD')
        self.max_task_duration = get_powercrud_setting('MAX_TASK_DURATION')
        self.cleanup_schedule_interval = get_powercrud_setting('CLEANUP_SCHEDULE_INTERVAL')

        # Prefixes for cache keys
        self.active_prefix = "powercrud:async:active_tasks"
        self.conflict_prefix = "powercrud:async:conflict:"
        self.conflict_model_prefix = "powercrud:conflict:model:"  # For per-object locks
        self.progress_prefix = "powercrud:async:progress:"

        # leave async validation to calling methods
        # self.async_enabled = get_powercrud_setting('ASYNC_ENABLED')
        # if self.async_enabled:
        #     if not self.validate_async_system():
        #         # set flag so that any instead of calling async_task, wrapped func will be called synchronously
        #         log.warning("Async system validation failed, disabling async features")
        #         self.async_enabled = False

    def _current_timestamp(self):
        """Return a timezone-aware timestamp for lifecycle events."""
        return timezone.now()

    def _serialise_json(self, value: Any) -> Any:
        try:
            json.dumps(value)
            return value
        except Exception:
            if isinstance(value, dict):
                return {str(k): self._serialise_json(v) for k, v in value.items()}
            if isinstance(value, (list, tuple, set)):
                return [self._serialise_json(v) for v in value]
            return str(value)

    def _emit_lifecycle(self, event: str, task_name: str, **payload) -> None:
        """Safely invoke async_task_lifecycle with a normalised payload."""
        data = {
            'status': payload.pop('status', None),
            'message': payload.pop('message', None),
            'progress_payload': payload.pop('progress_payload', None),
            'user': payload.pop('user', None),
            'affected_objects': payload.pop('affected_objects', None),
            'task_kwargs': self._serialise_json(payload.pop('task_kwargs', None)),
            'task_args': self._serialise_json(payload.pop('task_args', None)),
            'result': payload.pop('result', None),
            'timestamp': payload.pop('timestamp', None) or self._current_timestamp(),
            'extra': payload.pop('extra', None),
        }
        data.update(payload)
        try:
            self.async_task_lifecycle(event=event, task_name=task_name, **data)
        except Exception as exc:
            log.warning(f"async_task_lifecycle error for {event} on {task_name}: {exc}")

    # =============================================================================
    # System Detection
    # =============================================================================

    def validate_async_qcluster(self, timeout_ms: Optional[int] = None) -> bool:
        """Validate that django-q2 workers are running by executing a probe.

        Args:
            timeout_ms: Maximum time in milliseconds to wait for the probe task.

        Returns:
            bool: True if the probe completes (cluster healthy), otherwise False.

        Notes:
            Uses a unique group/name to avoid collisions and attempts cleanup of
            Task rows and cached entries afterwards.
        """
        if timeout_ms is None:
            timeout_ms = get_powercrud_setting('QCLUSTER_PROBE_TIMEOUT_MS', 300)

        group = "qcluster_testing"
        task_name = f"q2_probe_{uuid.uuid4().hex}"

        def _cleanup(task_name: str) -> bool:
            """Clean up probe task from both ORM and cache."""
            success = True
            try:
                # Clean up Task ORM record
                Task.objects.filter(name=task_name).delete()
            except Exception as e:
                log.warning(f"Could not delete test task ORM record {task_name}: {e}")
                success = False
            
            try:
                # Clean up cached entry if not using ORM broker
                if not self.qcluster_settings.get('orm'):
                    delete_cached(task_name)
            except Exception as e:
                log.warning(f"Failed to delete cached task_name {task_name}: {e}")
                success = False
                
            return success

        task_id: Optional[str] = None
        try:
            task_id = async_task(
                'math.floor',
                1,
                group=group,
                task_name=task_name,
            )
            start = time.perf_counter()
            log.debug(f"Enqueued probe task {task_name} with ID {task_id} at {start:.2f} seconds")

            while (time.perf_counter() - start) * 1000 < timeout_ms:
                task = fetch(task_id, wait=0)  # non-blocking
                if task:
                    ok = getattr(task, 'success', False)
                    return ok
                time.sleep(0.02)  # 20 ms

            log.warning(f"Q cluster probe task {task_name} timed out after {timeout_ms} ms")
            return False
            
        except Exception as e:
            log.error(f"qcluster appears to not be running: {e}")
            return False
        finally:
            # Always attempt cleanup in finally block
            if task_id:
                if not _cleanup(task_name):
                    log.warning(f"Could not clean up test task {task_name}")

    # cache helpers

    def get_cache_name(self) -> str:
        """Return the cache alias to use for async features.

        Returns:
            str: POWERCRUD_SETTINGS['CACHE_NAME'] or 'default'.
        """
        return get_powercrud_setting('CACHE_NAME', 'default')

    def get_cache(self):
        """Return the configured Django cache instance.

        Returns:
            BaseCache | None: Cache specified by get_cache_name(), or None if missing.
        """
        try:
            return caches[self.get_cache_name()]
        except KeyError:
            log.warning(f"Cache '{self.get_cache_name()}' not found in caches.")
            return None

    def validate_cache_backend(self) -> None:
        """Ensure the configured cache backend supports multi-process access."""
        if not self.cache:
            raise ImproperlyConfigured(
                f"AsyncManager requires cache alias '{self.cache_name}' to be defined. "
                "Update POWERCRUD_SETTINGS['CACHE_NAME'] or add the alias to CACHES."
            )

        backend_path = f"{self.cache.__class__.__module__}.{self.cache.__class__.__name__}"
        lowered = backend_path.lower()
        if any(token in lowered for token in ('locmem', 'dummycache', 'dummy')):
            raise ImproperlyConfigured(
                "POWERCRUD async progress tracking requires a shared cache backend. "
                f"Alias '{self.cache_name}' currently resolves to '{backend_path}', "
                "which is single-process only. Configure a shared backend such as "
                "django.core.cache.backends.db.DatabaseCache, django_redis, or Memcached."
            )

    def validate_async_cache(self):
        """Check basic cache connectivity for async features.

        Returns:
            bool: True when set/get/delete operations succeed; False otherwise.
        """
        try:
            cache = self.get_cache()
            # Test cache connectivity
            cache.set('powercrud_test', 'test', 1)
            cache.get('powercrud_test')
            cache.delete('powercrud_test')
            return True
        except Exception as e:
            log.warning(f"Async cache validation failed: {e}")
            return False

    def validate_async_system(self) -> bool:
        """Validate both queue cluster and cache subsystems.

        Returns:
            bool: True if both subsystems are healthy; otherwise False.
        """
        if self.validate_async_qcluster() and self.validate_async_cache():
            return True
        else:
            log.error("Async system validation failed, disabling async features")
            return False

    # =============================================================================
    # Task Management Functions
    # =============================================================================

    def generate_task_name(self) -> str:
        """Generate a unique task identifier.

        Returns:
            str: Random UUID4 string.
        """
        return str(uuid.uuid4())

    def launch_async_task(
            self,

            # signature for async_task: see django-q2 docs
            func: Callable,
            *args, # args for the function to be called

            # optional keyword with conflict ids (not part of django-q2.async_task)
            conflict_ids: Optional[Dict[str, Set[Hashable]]] = None,

            # optional metadata for lifecycle events
            user=None,
            affected_objects=None,

            # optional explicit task identifier (UUID string)
            task_key: Optional[str] = None,

            # signature for async_task: see django-q2 docs
            group: str = None,
            timeout=None,
            sync=False,
            cached=False,
            broker=None,
            q_options=None,
            **kwargs # kwargs for the function to be called

        ) -> str:
        """Launch an async task with atomic pre-enqueue conflict reservation.

        Implements the launch pattern:
        1. Generate unique task_key
        2. Reserve object locks (if conflict_ids provided)
        3. Initialize progress tracking
        4. Enqueue task with completion hook
        5. Register as active task (skip re-locking)
        6. Fire lifecycle 'create' event

        Args:
            func: The callable to run asynchronously.
            *args: Positional arguments for the callable.
            conflict_ids: Optional mapping of model names to object ID sets for
                atomic reservation prior to enqueueing.
            user: Optional user metadata for lifecycle events.
            affected_objects: Optional affected objects metadata for lifecycle events.
            task_key: Optional explicit task identifier to reuse instead of generating one.
            group: Optional django-q2 task group.
            timeout: Optional task timeout (seconds).
            save: Persist task to ORM (per django-q2 semantics).
            sync: Execute synchronously (testing/dev only).
            cached: Use cached broker (per django-q2 semantics).
            broker: Optional broker name.
            q_options: Extra options passed to django-q2.
            **kwargs: Keyword arguments for the callable.

        Returns:
            str: The task_key for tracking progress and lifecycle.
            
        Raises:
            Exception: If conflict reservation fails or enqueue fails.
        """

        # Phase 1: Determine task identifier and worker args
        worker_args_list = list(args)
        task_name = task_key

        if task_name is None and worker_args_list:
            potential_task_name = worker_args_list[-1]
            if isinstance(potential_task_name, str):
                try:
                    uuid.UUID(str(potential_task_name))
                    task_name = str(potential_task_name)
                    worker_args_list.pop()
                except (ValueError, TypeError):
                    # Not a UUID-like value; leave args untouched
                    pass

        if task_name is None:
            task_name = self.generate_task_name()  # Generate if not provided

        worker_args = tuple(worker_args_list)

        # Phase 2: Atomic conflict reservation (if requested)
        if conflict_ids:
            if not self.add_conflict_ids(task_name, conflict_ids):
                log.error(f"Conflict reservation failed for task {task_name}")
                raise Exception("Cannot launch task - conflicts detected with existing operations")

        # Phase 3: Initialize progress tracking
        self.create_progress_key(task_name)
        
        # Phase 4: Enqueue the task with completion hook
        try:
            worker_kwargs = dict(kwargs)

            # Expose task identifier to worker functions
            worker_kwargs.setdefault('task_key', task_name)

            save_value = worker_kwargs.pop('save', 'not_set')

            # Ensure timeout is a real number for django-q2 worker timer
            local_timeout = timeout if timeout is not None else self.qcluster_settings.get('timeout', 60)

            q_options_clean = dict(q_options) if q_options else {}

            # construct the kwargs to pass to async_task
            async_task_kwargs = {
                'hook': "powercrud.async_hooks.task_completion_hook",
                'group': group,
                'timeout': local_timeout,
                'sync': sync,
                'cached': cached,
                'broker': broker,
                'task_name': task_name,
                'q_options': q_options_clean,
                **worker_kwargs
            }

            # Only add save parameter if it was explicitly provided
            if save_value != 'not_set':
                async_task_kwargs['save'] = save_value
 
            # DEBUG: Check what we're actually passing to django-q2
            log.debug(f"[LAUNCH DEBUG] About to call async_task")
            log.debug(f"[LAUNCH DEBUG] func={func}")
            log.debug(f"[LAUNCH DEBUG] worker_args length={len(worker_args)}")
            log.debug(f"[LAUNCH DEBUG] worker_args content={worker_args}")
            log.debug(f"[LAUNCH DEBUG] async_task_kwargs keys={list(async_task_kwargs.keys())}")
            log.debug(f"[LAUNCH DEBUG] task_name in async_task_kwargs: {async_task_kwargs.get('task_name')}")

            django_q2_task_id = async_task(func, *worker_args, **async_task_kwargs)
           
            if not django_q2_task_id:
                raise Exception("django-q2 async_task returned falsy task_id")
                
            log.debug(f"launch_async_task created django_q2_task_id: {django_q2_task_id}")

        except Exception as e:
            # Phase 4 failed - rollback reservations and progress
            log.error(f"Failed to enqueue task_name {task_name}: {e}")
            if conflict_ids:
                self.remove_conflict_ids(task_name)
            self.remove_progress_key(task_name)
            raise Exception(f"Failed to enqueue async task: {e}")

        # Phase 5: Register as active task (skip conflict reservation since already done)
        try:
            if not self.add_active_task(task_name, conflict_ids=None):
                log.warning(f"Failed to register task {task_name} as active - cleanup may be incomplete")
        except Exception as e:
            log.error(f"Failed to register active task {task_name}: {e}")
            # Don't raise here since the task is already enqueued

        lifecycle_kwargs = dict(worker_kwargs)
        lifecycle_args = list(worker_args)
        self._emit_lifecycle(
            event="create",
            task_name=task_name,
            status=self.STATUSES.PENDING,
            message="Task queued",
            user=user,
            affected_objects=affected_objects,
            django_q2_task_id=django_q2_task_id,
            task_kwargs=lifecycle_kwargs,
            task_args=lifecycle_args,
        )

        log.debug(f"Successfully launched async task_name {task_name} (django-q2 id: {django_q2_task_id})")
        return task_name


    def get_task_status(self, task_name: str) -> Optional[str]:
        """Fetch task execution status from django-q2 with blocking wait.

        Args:
            task_name: The django-q2 task.name.

        Returns:
            Optional[str]: 'success', 'failed', 'executing', or None if unknown.
            
        Warning:
            This method blocks for up to 300 seconds. For UI/request paths,
            prefer get_task_status_nowait() instead.
        """
        task = fetch(task_name, wait=300)
        if task:
            if task.success is not None:
                return 'success' if task.success else 'failed'
            else:
                return 'executing'
        # if task not fetched it means it is either queued or doesn't exist
        return None

    def get_task_status_nowait(self, task_name: str) -> Optional[str]:
        """Fetch task execution status from django-q2 without blocking.
        NB unless q2 is configured with cached=True, this will hit the db back end 

        Args:
            task_id: The django-q2 task identifier.

        Returns:
            Optional[str]: self.STATUSES.[SUCCESS, FAILED, IN_PROGRESS, UNKNOWN]
            
        Note:
            This method returns immediately and is suitable for UI/request paths.
        """
        task = fetch(task_name, wait=0)  # non-blocking
        if task:
            if task.success is not None:
                return self.STATUSES.SUCCESS if task.success else self.STATUSES.FAILED
            else:
                return self.STATUSES.IN_PROGRESS
        # if task not fetched it means it is either queued or doesn't exist
        return self.STATUSES.UNKNOWN # None

    def is_task_complete(self, task_name: str) -> bool:
        """Return whether the task has finished (success or failure).
        NB unless q2 is configured with cached=True, this will hit the db back end 

        Args:
            task_name: The django-q2 task identifier task.name.

        Returns:
            bool: True if success is not null in Task model, else False.
        """
        task_status = self.get_task_status_nowait(task_name)
        if task_status in [self.STATUSES.SUCCESS, self.STATUSES.FAILED,]:
            return True
        return False # covers ['not found', 'in_progress', 'pending']

    def get_task_status_cache_only(self, task_name: str) -> str:
        """Relies on contents of the cache progress key to determine status.
        Advantage is never hits db, even if django-q2 cached=False. 

        Args:
            task_name (str): The django-q2 task identifier.

        Returns:
            str: status indicator
        """
        progress_data = self.get_progress(task_name)
        if progress_data == self.STATUSES.PENDING:
            return self.STATUSES.PENDING
        elif progress_data is not None:
            return self.STATUSES.IN_PROGRESS  # Has actual progress data
        # not pending but progress key has been cleaned up. 
        # So either complete or unknown. 
        # But if unknown, then progress key would not be cleared (ideally)
        return 'completed'

    def is_task_complete_cache_only(self, task_name: str) -> bool:
        """Returns boolean indicator as to whether task is completed or not.
        Never hits db, even if django-q2 cached=False. 

        Args:
            task_name (str): The django-q2 task.name.

        Returns:
            bool: _description_
        """
        task_status = self.get_task_status_cache_only(task_name)
        return task_status == 'completed'
    
    # =============================================================================
    # Conflict Management Functions
    # =============================================================================
    def add_active_task(self, task_name: str, conflict_ids: dict[str, set[Hashable]] = None) -> bool:
        """Register a task as active, with optional atomic conflict reservation.

        This first attempts to acquire object locks via add_conflict_ids(). If
        locking fails, the task is not added and False is returned.

        Args:
            task_name: The task identifier created by django-q2.
            conflict_ids: Optional mapping of model names to sets of IDs to lock.

        Returns:
            bool: True if registered successfully; False if locking failed or errors occurred.
        """
        if not task_name:
            raise ValueError("task_name cannot be empty")
        try:
            # add the conflict ids for this task first (atomic reservation)
            if conflict_ids:
                if not self.add_conflict_ids(task_name, conflict_ids):
                    log.error(f"Failed to acquire conflict locks for task {task_name}")
                    return False
            
            # add the new active_task to the cache
            current_tasks = self.get_active_tasks()
            updated_tasks = set(current_tasks)  # copy
            updated_tasks.add(task_name)
            self.cache.set(self.active_prefix, updated_tasks, self.cleanup_grace_period)

            # initialize progress tracking for this task
            self.create_progress_key(task_name)
            return True
        
        except Exception as e:
            log.error(f"Failed to add active task_name {task_name} to active tasks cache: {e}")
            return False
        
    def get_active_tasks(self) -> Set[str]:
        """Return the set of active task IDs tracked in cache.

        Returns:
            Set[str]: Current active tasks (may be empty).
        """
        return self.cache.get(self.active_prefix, set()) or set()
    
    def is_active_task(self, task_name: str) -> bool:
        active_tasks = self.get_active_tasks()
        if task_name in active_tasks:
            return True
        return False

    def remove_active_task(self, task_name: str) -> bool:
        """Remove a task from active tracking and clean associated artifacts.

        This also:
            - Removes all object locks via remove_conflict_ids()
            - Deletes the progress key for the task

        Args:
            task_name: The task identifier task.name to remove.

        Returns:
            bool: Always True after attempting cleanup.
        """
        log.debug(f"remove_active_tasks for task_name: {task_name}")

        current_tasks = self.get_active_tasks()
        updated_tasks = set(current_tasks)  # copy
        updated_tasks.discard(task_name)
        self.cache.set(self.active_prefix, updated_tasks, self.cleanup_grace_period)

        # remove conflict tracking for this task (dual-key cleanup)
        self.remove_conflict_ids(task_name)
        
        # remove progress tracking
        progress_key = f"{self.progress_prefix}{task_name}"
        self.cache.delete(progress_key)

        return True
    
    def cleanup_active_tasks(self) -> None:
        """Prune active tasks that django-q2 reports as completed recently.

        Uses a grace period window to avoid racing recent writes.
        """

        # get all cache active tasks
        cache_active_tasks = self.cache.get(self.active_prefix, set()) or set()

        # cutoff datetime
        cutoff = timezone.now() - timedelta(seconds=self.cleanup_grace_period)

        # # completed tasks since cutoff
        # recent_tasks = Task.objects.filter(
        #     created__gte=cutoff,
        #     success__isnull=False
        # ).values_list("id", flat=True)

        # recent_completed_task_ids = {str(task_name) for task_name in recent_tasks}

        # remove any active task that Q2 says is completed
        for task_name in cache_active_tasks: # & recent_completed_task_ids:
            self.remove_active_task(task_name)

        # Clean up expired progress keys
        self.clear_expired_progress_keys()

    def cleanup_completed_tasks(self) -> dict[str, Any]:
        """Remove stale artifacts (locks, progress, dashboard) for finished tasks."""
        summary: dict[str, Any] = {
            "active_tasks": 0,
            "cleaned": {},
            "skipped": {},
        }

        active_tasks = list(self.get_active_tasks())
        summary["active_tasks"] = len(active_tasks)

        now = timezone.now()
        max_duration = timedelta(seconds=self.max_task_duration) if self.max_task_duration else None

        for task_name in active_tasks:
            try:
                task = Task.objects.filter(name=task_name).first()
            except Exception as exc:
                summary["skipped"][task_name] = f"task lookup failed: {exc}"
                continue

            if task is None:
                summary["cleaned"][task_name] = self._cleanup_task_artifacts(
                    task_name,
                    reason="django-q2 task missing",
                    status=self.STATUSES.UNKNOWN,
                )
                continue

            success_flag = getattr(task, "success", None)
            if success_flag is None:
                started = getattr(task, "started", None)
                if started and max_duration and (started + max_duration) < now:
                    summary["cleaned"][task_name] = self._cleanup_task_artifacts(
                        task_name,
                        reason="max duration exceeded",
                        status=self.STATUSES.UNKNOWN,
                    )
                else:
                    summary["skipped"][task_name] = "task still running"
                continue

            reason = "completed successfully" if success_flag else "completed with failure"
            status = self.STATUSES.SUCCESS if success_flag else self.STATUSES.FAILED
            result_payload = getattr(task, "result", None)

            summary["cleaned"][task_name] = self._cleanup_task_artifacts(
                task_name,
                reason=reason,
                status=status,
                result=result_payload,
            )

        return summary

    def _cleanup_task_artifacts(
        self,
        task_name: str,
        reason: str,
        status: Optional[str],
        result: Any = None,
    ) -> dict[str, Any]:
        """Internal helper to remove cache + dashboard data for a task."""
        tracking_key = f"{self.conflict_prefix}{task_name}"
        conflict_keys = self.cache.get(tracking_key, set()) or set()

        progress_key = f"{self.progress_prefix}{task_name}"
        had_progress = False
        try:
            progress_value = self.cache.get(progress_key, None)
            if progress_value is not None:
                had_progress = True
            elif hasattr(self.cache, "has_key") and self.cache.has_key(progress_key):  # type: ignore[attr-defined]
                had_progress = True
        except Exception:
            pass

        # remove_active_task also clears conflicts & progress keys
        self.remove_active_task(task_name)

        dashboard_removed = self.cleanup_dashboard_data(task_name) or 0

        self._emit_lifecycle(
            event="cleanup",
            task_name=task_name,
            status=status or self.STATUSES.UNKNOWN,
            message=reason,
            result=result,
        )

        return {
            "reason": reason,
            "conflict_lock_keys": len(conflict_keys),
            "progress_entries": 1 if had_progress else 0,
            "dashboard_records": dashboard_removed,
        }


    def add_conflict_ids(self, task_name: str, conflict_ids: dict[str, set[Hashable]]) -> bool:
        """Atomically reserve exclusive locks on objects for a task.
  
        Implements all-or-nothing lock acquisition using cache.add() to ensure
        atomic "test-and-set" behavior. If any object is already locked, all
        previously acquired locks for this task are rolled back.
  
        Dual-key storage:
            1) Object lock keys (per-object exclusive locks)
               Format: "powercrud:conflict:model:{model_name}:{obj_id}" → task_name
            2) Object tracking set (per-task cleanup index)
               Format: "powercrud:async:conflict:{task_name}" → {lock_key_1, ...}
  
        Args:
            task_name: Unique identifier task.name for the task requesting locks.
            conflict_ids: Dict mapping model names to sets of object IDs.
                Example: {'myapp.Book': {1, 2, 3}, 'myapp.Author': {10}}
  
        Returns:
            bool: True if all objects locked successfully; False if any conflicts.
        """
        acquired_locks = []
        
        # Try to acquire per-object lock for each ID in all models
        for model_name, obj_ids in conflict_ids.items():
            for obj_id in obj_ids:
                lock_key = f"{self.conflict_model_prefix}{model_name}:{obj_id}"
                
                # Atomic test-and-set using cache.add()
                success = self.cache.add(lock_key, task_name, self.conflict_ttl)
                
                if success:
                    acquired_locks.append(lock_key)
                else:
                    # Conflict detected - ROLLBACK all acquired locks
                    for rollback_key in acquired_locks:
                        self.cache.delete(rollback_key)
                    return False
        
        # All locks acquired successfully - store tracking set for cleanup
        tracking_key = f"{self.conflict_prefix}{task_name}"
        tracking_set = set()
        
        # Get existing tracking set if any
        existing_tracking = self.cache.get(tracking_key, set())
        if existing_tracking:
            tracking_set.update(existing_tracking)
        
        # Add new lock keys to tracking set
        for lock_key in acquired_locks:
            tracking_set.add(lock_key)
        
        # Store tracking set
        self.cache.set(tracking_key, tracking_set, self.conflict_ttl)
        
        return True

    def check_conflict(self, object_data: dict[str, list[Hashable]]) -> set[Hashable]:
        """Check if objects are currently locked by other tasks.

        Performs direct per-object lock key lookups (no task scanning).

        Args:
            object_data: Dict mapping model names to lists of object IDs.
                Example: {'myapp.Book': [1, 2, 3], 'myapp.Author': [10, 20]}

        Returns:
            set: Set of object IDs that are currently locked by other tasks.
        """
        conflicts = set()
        
        for model_name, obj_ids in object_data.items():
            for obj_id in obj_ids:
                lock_key = f"{self.conflict_model_prefix}{model_name}:{obj_id}"
                locked_task_name = self.cache.get(lock_key)
                
                if locked_task_name is not None:
                    conflicts.add(obj_id)
        
        if conflicts:
            log.debug(f"Conflict detected with IDs {conflicts}")
        else:
            log.debug("No conflicts detected")
            
        return conflicts

    def remove_conflict_ids(self, task_name: str, conflict_ids: Optional[dict[Hashable]] = None):
        """Remove all conflict tracking for a task using dual-key cleanup.
  
        Uses the object tracking set to find all per-object lock keys for this task,
        deletes each lock key, and then deletes the tracking set. Idempotent.
  
        Args:
            task_name: Unique identifier task.name to clean up.
            conflict_ids: Unused parameter; kept for API compatibility.
        """
        log.debug(f"remove_conflict_ids for task_name: {task_name}, conflict_ids: {conflict_ids}")
        tracking_key = f"{self.conflict_prefix}{task_name}"
        tracking_set = self.cache.get(tracking_key, set())
        
        # Remove all per-object locks tracked by this task
        for lock_key in tracking_set:
            self.cache.delete(lock_key)
        
        # Remove the tracking set itself
        self.cache.delete(tracking_key)

    # =============================================================================
    # Progress Tracking Functions
    # =============================================================================
    def create_progress_key(self, task_name: str) -> str:
        """Create/initialize the progress key for a task.
  
        Args:
            task_name: The task identifier task.name
  
        Returns:
            str: The cache key used to store progress for this task.
        """
        if not task_name:
            raise ValueError("task_name cannot be empty")
        progress_key = f"{self.progress_prefix}{task_name}"
        try:
            self.cache.set(progress_key, self.STATUSES.PENDING, self.progress_ttl)
            log.debug(f"Created progress key for task_name {task_name} (backend {self.cache.__class__.__module__}.{self.cache.__class__.__name__})")
        except Exception as e:
            log.warning(f"Failed to create progress key for {task_name}: {e}")
        return progress_key
    
    def remove_progress_key(self, task_name: str) -> None:
        """Remove the per-task progress key (idempotent)."""
        if not task_name:
            return  # Silently ignore empty task_name
        progress_key = f"{self.progress_prefix}{task_name}"
        try:
            self.cache.delete(progress_key)
            log.debug(f"Removed progress key for task_name {task_name}")
        except Exception as e:
            log.warning(f"Failed to remove progress key for {task_name}: {e}")
    
    def update_progress(self, task_name: str, progress_data: str) -> None:
        """Update task progress information.
  
        Args:
            task_name: The task identifier.
            progress_data: A serialized payload (string) to store for UI polling.
        """
        if not task_name:
            raise ValueError("task_name cannot be empty")
        if not isinstance(progress_data, str):
            raise ValueError("Progress data must be a string")
        progress_key = f"{self.progress_prefix}{task_name}"
        try:
            self.cache.set(progress_key, progress_data, self.progress_ttl)
            log.debug(f"Updated progress for {task_name}: {progress_data}")
            self._emit_lifecycle(
                event="progress",
                task_name=task_name,
                status=self.STATUSES.IN_PROGRESS,
                message=progress_data,
                progress_payload=progress_data,
            )
        except Exception as e:
            log.warning(f"Failed to update progress for {task_name}: {e}")

    def get_progress(self, task_name: str) -> Optional[str]:
        """Retrieve current progress payload for a task (if any).
  
        Args:
            task_name: The task identifier.
  
        Returns:
            Optional[str]: The serialized progress payload, or None if missing.
        """
        if not task_name:
            raise ValueError("task_name cannot be empty")
        progress_key = f"{self.progress_prefix}{task_name}"
        try:
            result = self.cache.get(progress_key, None)
            return result
        except Exception as e:
            log.warning(f"Failed to get progress for {task_name}: {e}")
            return None

    def clear_expired_progress_keys(self) -> None:
        """Clear expired progress keys based on active tasks."""
        active_tasks = self.get_active_tasks()
        for task_name in active_tasks:
            progress_key = f"{self.progress_prefix}{task_name}"
            try:
                # Check if key exists but value is None (expired or cleared)
                if self.cache.get(progress_key) is None and self.cache.has_key(progress_key):
                    self.cache.delete(progress_key)
                    log.debug(f"Cleared expired progress key for {task_name}")
            except Exception as e:
                log.warning(f"Failed to clear expired progress for {task_name}: {e}")

    # =============================================================================
    # Dashboard Integration
    # =============================================================================

    def async_task_lifecycle(self, event, task_name, **kwargs):
        """Lifecycle hook for task-related events.

        Args:
            event: One of {'create', 'progress', 'complete', 'cleanup', 'error'}.
            task_name: The task identifier.
            **kwargs: Event-specific payload (e.g., user, affected_objects, progress_data).

        Note:
            Designed to be overridden by downstream projects for dashboard integration.
        """
        if event == 'create':
            user = kwargs.get('user')
            affected_objects = kwargs.get('affected_objects')
            # ...
        elif event == 'progress':
            progress_data = kwargs.get('progress_data')
            # ...
        elif event == 'complete':
            pass
        elif event == 'cleanup':
            pass
        elif event == 'error':
            error = kwargs.get('error')
            pass


    @classmethod
    def as_view(cls, template_name=None):
        """
        Return a Django view function for HTMX progress polling.
        
        Usage:
            In urls.py:
            from powercrud.async_manager import AsyncManager
            urlpatterns = [
                AsyncManager.get_url(),
                # ...
            ]
        
        HTMX example:
            <div hx-get="/powercrud/async/progress/"
                 hx-vals='{"task_name": "{{ task_key }}"}'
                 hx-trigger="every 1s"
                 hx-target="#progress-display">
                Loading...
            </div>
        
        Key Design Decisions:
        - task_name Parameter: Expects the task_key (UUID) returned by launch_async_task()
        - Non-blocking: Uses get_task_status_nowait() to avoid request timeouts
        - JSON Default: Simple JSON structure that's easy to consume with HTMX
        - Error Handling: Returns appropriate HTTP status codes for missing parameters
        - Minimal Dependencies: Local imports to avoid import-time issues
        """
        
        def progress_view(request):
            # Get required task_name parameter
            task_name = request.GET.get('task_name') or request.POST.get('task_name')
            if not task_name:
                return JsonResponse({'error': 'task_name required'}, status=400)
            
            # Create manager instance
            manager = cls()
            
            try:
                # Try to get progress data first
                status = manager.get_task_status_cache_only(task_name)
                is_complete = manager.is_task_complete_cache_only(task_name)
                raw_progress = manager.get_progress(task_name)
                progress_data = None if raw_progress == manager.STATUSES.PENDING else raw_progress

                if is_complete:
                    # verify by checking with django-q2 directly
                    is_task_complete = manager.is_task_complete(task_name)
                    display_status = manager.STATUSES.SUCCESS if status == 'completed' else (status or manager.STATUSES.SUCCESS)
                    display_progress = progress_data or 'Completed successfully!'
                    return JsonResponse({
                        'task_name': task_name,
                        'status': display_status,
                        'progress': display_progress,
                        'message': 'Task completed'
                    }, status=286) # 286 will stop polling as per htmx docs

                poll_interval = 1000  # default to 1s polling cadence

                if progress_data is not None:
                    return JsonResponse({
                        'task_name': task_name,
                        'status': status,
                        'progress': progress_data,
                    })
                
                # No progress data - check if task is complete via django-q2
                # Note: This assumes task_name is our task_key (UUID) which matches Task.name
                status = manager.get_task_status_nowait(task_name)
                
                return JsonResponse({
                    'task_name': task_name,
                    'status': status or 'unknown',
                    'progress': None,
                    'poll_interval': poll_interval
                })
            except Exception as e:
                log.error(f"Error in progress_view for task {task_name}: {e}")
                return JsonResponse({'error': str(e)}, status=500)
        
        return progress_view

    @classmethod
    def get_url(cls, pattern="powercrud/async/progress/", name="powercrud_async_progress"):
        """
        Return a Django path object for the progress polling endpoint.
        
        Usage:
            urlpatterns = [
                AsyncManager.get_url(),
                # ...
            ]
        """
        from django.urls import path
        return path(pattern, cls.as_view(), name=name)

    def cleanup_dashboard_data(self, task_name: str) -> int:
        """Clean up any dashboard artifacts tracked for a task.

        Args:
            task_name: The task identifier to clean dashboard artifacts for.
        """
        return 0

    def handle_task_completion(self, task, task_name: str) -> None:
        """
        Handle task completion cleanup and lifecycle events.
        
        This method is called by the module-level completion hook and is designed
        to be overridden by downstream projects for custom completion behavior.
        
        Args:
            task: The completed django-q2 Task instance
            task_name: The derived task name (UUID from Task.name)
            
        Note:
            Default implementation is a minimal stub. Downstream projects should
            override this method to implement their specific cleanup and lifecycle
            handling requirements.
        """
        log.debug(f"handle_task_completion started for task_name: {task_name}")
        try:
            # Perform default cleanup
            self.remove_active_task(task_name)

            success_flag = getattr(task, 'success', None)
            result_payload = getattr(task, 'result', None)

            if success_flag is True:
                self._emit_lifecycle(
                    event="complete",
                    task_name=task_name,
                    status=self.STATUSES.SUCCESS,
                    message="Task completed successfully",
                    result=result_payload,
                )
            elif success_flag is False:
                failure_message = str(result_payload) if result_payload else "Task failed"
                self._emit_lifecycle(
                    event="fail",
                    task_name=task_name,
                    status=self.STATUSES.FAILED,
                    message=failure_message,
                    result=result_payload,
                )
            else:
                self._emit_lifecycle(
                    event="complete",
                    task_name=task_name,
                    status=self.STATUSES.UNKNOWN,
                    message="Task finished with unknown status",
                    result=result_payload,
                )

            self._emit_lifecycle(event="cleanup", task_name=task_name, status=self.STATUSES.UNKNOWN)
            log.debug(f"Handled completion for task_name {task_name} (success: {success_flag})")
        except Exception as e:
            log.error(f"Error in handle_task_completion for {task_name}: {e}")
    @classmethod
    def resolve_manager(cls, manager_class_path: str | None, config: dict | None = None):
        if not manager_class_path:
            return cls()
        try:
            module_path, class_name = manager_class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            manager_cls = getattr(module, class_name)
            if not issubclass(manager_cls, AsyncManager):
                raise TypeError
            log.debug(f"AsyncManager resolving manager class '{manager_class_path}'")
            if config is not None:
                coerced_config = cls._coerce_manager_config(manager_cls, config)
                if coerced_config is not None:
                    try:
                        return manager_cls(config=coerced_config)
                    except TypeError:
                        log.debug("Resolved manager class does not accept config kwarg; falling back to default constructor")
            return manager_cls()
        except Exception as exc:
            log.warning(f"Failed to import manager '{manager_class_path}': {exc}. Falling back to AsyncManager")
            return cls()

    @staticmethod
    def _coerce_manager_config(manager_cls, config):
        if config is None:
            return None

        if isinstance(config, dict):
            try:
                from powercrud.async_dashboard import AsyncDashboardConfig, ModelTrackingAsyncManager

                if issubclass(manager_cls, ModelTrackingAsyncManager):
                    return AsyncDashboardConfig(**config)
            except Exception:
                return config

        return config
