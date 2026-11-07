import json
import logging
import uuid
from collections.abc import Mapping
from datetime import timedelta
from typing import Any, Callable, Dict, Hashable, Optional, Set

from django.apps import apps
from django.conf import settings
from django.core.cache import InvalidCacheBackendError, caches
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from .config import CoordinatorConfig
from .exceptions import AsyncConfigurationError, AsyncDisabledError
from .q2 import Q2Adapter
from .reconstruction import current_binding
from .types import Completion, ManagerSpec, TaskCall

log = logging.getLogger(__name__)

class AsyncManager:
    """Coordinate task keys, shared cache state, progress, and lifecycle events."""

    class STATUSES:
        """Choices for async task statuses"""

        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        SUCCESS = "success"
        FAILED = "failed"
        UNKNOWN = None

    completion_style = "core"

    def __init__(self, *, coordination_config=None, executor=None):
        """Create a manager using explicit or factory-bound coordination data."""
        binding = current_binding()
        config = coordination_config if coordination_config is not None else binding.config if binding else None
        if config is None:
            raise ImproperlyConfigured(
                "Coordinator AsyncManager requires an explicit CoordinatorConfig."
            )
        if not isinstance(config, CoordinatorConfig):
            raise AsyncConfigurationError(
                "Coordinator configuration must be a CoordinatorConfig instance."
            )
        self._coordination_config = config
        self._factory_manager_config = None
        self._q2_adapter = (
            executor
            if executor is not None
            else binding.executor
            if binding and binding.executor is not None
            else Q2Adapter()
        )
        self.cache_name = self.get_cache_name()
        self._require_nonempty_string(self.cache_name, "CACHE_NAME")
        self._require_nonempty_string(config.key_namespace, "Coordinator key namespace")
        if config.key_prefixes is not None and not isinstance(config.key_prefixes, Mapping):
            raise AsyncConfigurationError("Coordinator key_prefixes must be a mapping when defined.")
        if config.key_prefixes is not None:
            unknown_prefixes = set(config.key_prefixes) - {
                "active_prefix",
                "conflict_prefix",
                "conflict_model_prefix",
                "progress_prefix",
            }
            if unknown_prefixes:
                raise AsyncConfigurationError("Coordinator key_prefixes contains an unknown prefix name.")
        prefixes = config.resolved_key_prefixes()
        for prefix_name, prefix_value in prefixes.items():
            self._require_nonempty_string(prefix_value, f"Coordinator {prefix_name}")
        self.cache = self.get_cache()
        self.validate_cache_backend()
        self._qcluster_settings_override = None
        self.conflict_ttl = config.conflict_ttl
        self.progress_ttl = config.progress_ttl
        self.cleanup_grace_period = config.cleanup_grace_period
        self.max_task_duration = config.max_task_duration
        self.active_prefix = prefixes["active_prefix"]
        self.conflict_prefix = prefixes["conflict_prefix"]
        self.conflict_model_prefix = prefixes["conflict_model_prefix"]
        self.progress_prefix = prefixes["progress_prefix"]

    def get_coordination_config(self):
        """Export the effective coordinator settings after manager overrides."""
        return CoordinatorConfig(
            enabled=self._coordination_config.enabled,
            cache_name=self.cache_name,
            key_namespace=self._coordination_config.key_namespace,
            key_prefixes={
                "active_prefix": self.active_prefix,
                "conflict_prefix": self.conflict_prefix,
                "conflict_model_prefix": self.conflict_model_prefix,
                "progress_prefix": self.progress_prefix,
            },
            conflict_ttl=self.conflict_ttl,
            progress_ttl=self.progress_ttl,
            cleanup_grace_period=self.cleanup_grace_period,
            max_task_duration=self.max_task_duration,
            terminal_result_ttl=self._coordination_config.terminal_result_ttl,
        )

    def _async_launch_enabled(self):
        """Return the configured permission for this coordinator to launch work."""
        return self._coordination_config.enabled

    @classmethod
    def prepare_manager_config(cls, config):
        """Return application config unchanged for ordinary coordinator managers."""
        return config

    def export_manager_config(self):
        """Return the application config retained by the construction factory."""
        return self._factory_manager_config

    @property
    def qcluster_settings(self):
        """Expose q2 settings lazily for legacy manager consumers."""
        if self._qcluster_settings_override is not None:
            return self._qcluster_settings_override
        return self._q2_adapter.cluster_settings

    @qcluster_settings.setter
    def qcluster_settings(self, value):
        """Preserve legacy assignment while keeping the adapter authoritative."""
        self._qcluster_settings_override = value
        self._q2_adapter.cluster_settings = value

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
            "status": payload.pop("status", None),
            "message": payload.pop("message", None),
            "progress_payload": payload.pop("progress_payload", None),
            "user": payload.pop("user", None),
            "affected_objects": payload.pop("affected_objects", None),
            "task_kwargs": self._serialise_json(payload.pop("task_kwargs", None)),
            "task_args": self._serialise_json(payload.pop("task_args", None)),
            "result": payload.pop("result", None),
            "timestamp": payload.pop("timestamp", None) or self._current_timestamp(),
            "extra": payload.pop("extra", None),
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
        """Run a q2 task/result probe without claiming separate worker delivery.

        Args:
            timeout_ms: Maximum time in milliseconds to wait for the probe task.

        Returns:
            bool: True if the q2 probe completes, otherwise False.

        Notes:
            Uses a unique group/name to avoid collisions and attempts cleanup of
            Task rows and cached entries afterwards. Synchronous q2 configuration
            may execute inline, so success does not prove a separate worker is live.
        """
        self._q2_adapter.cluster_settings = self.qcluster_settings
        return self._q2_adapter.probe(timeout_ms=timeout_ms)

    # cache helpers

    def get_cache_name(self) -> str:
        """Return the cache alias to use for async features.

        Returns:
            str: The configured coordinator cache alias.
        """
        return self._coordination_config.cache_name

    def get_cache(self):
        """Return the configured Django cache instance.

        Returns:
            BaseCache | None: Cache specified by get_cache_name(), or None if missing.
        """
        if not getattr(settings, "configured", False):
            return None
        try:
            return caches[self.get_cache_name()]
        except (KeyError, InvalidCacheBackendError):
            return None

    @staticmethod
    def _require_nonempty_string(value, label):
        """Require a string cache/key setting without changing its spelling."""
        if not isinstance(value, str) or not value.strip():
            raise AsyncConfigurationError(f"{label} must be a non-empty string.")

    @staticmethod
    def _validate_lifetime(name, value, *, optional=False):
        """Retain documented zero/None values while rejecting invalid lifetimes."""
        if optional and value is None:
            return
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise AsyncConfigurationError(
                f"{name} must be a non-negative integer"
                + (" or None" if optional else "")
                + "."
            )

    def validate_async_configuration(self, *, call=None, options=None):
        """Validate explicit-use prerequisites without probing a worker or cache."""
        if not getattr(settings, "configured", False):
            raise AsyncConfigurationError(
                "Django settings are not configured; configure Django before using async tasks."
            )
        if not apps.ready:
            raise AsyncConfigurationError(
                "Django's app registry is not ready; call django.setup() before using async tasks."
            )

        powercrud_settings = getattr(settings, "POWERCRUD_SETTINGS", None)
        if powercrud_settings is not None and not isinstance(powercrud_settings, dict):
            raise AsyncConfigurationError(
                "POWERCRUD_SETTINGS must be a dictionary when defined."
            )

        enabled = self._async_launch_enabled()
        if not isinstance(enabled, bool):
            raise AsyncConfigurationError("ASYNC_ENABLED must be a boolean value.")
        if not enabled:
            raise AsyncDisabledError(
                "Async task launches are disabled; set POWERCRUD_SETTINGS['ASYNC_ENABLED'] = True."
            )

        self._require_nonempty_string(self.cache_name, "CACHE_NAME")
        self._require_nonempty_string(
            self._coordination_config.key_namespace, "Coordinator key namespace"
        )
        for prefix_name in (
            "active_prefix",
            "conflict_prefix",
            "conflict_model_prefix",
            "progress_prefix",
        ):
            self._require_nonempty_string(
                getattr(self, prefix_name), f"Coordinator {prefix_name}"
            )
        self._validate_lifetime("CONFLICT_TTL", self.conflict_ttl, optional=True)
        self._validate_lifetime("PROGRESS_TTL", self.progress_ttl, optional=True)
        self._validate_lifetime(
            "CLEANUP_GRACE_PERIOD", self.cleanup_grace_period, optional=True
        )
        self._validate_lifetime("MAX_TASK_DURATION", self.max_task_duration, optional=True)

        if call is not None:
            self._validate_launch_call(call)
        self._q2_adapter.validate_configuration(call=call, options=options)

    def _validate_launch_call(self, call):
        """Validate launch-owned identifiers before cache reservations occur."""
        self._require_nonempty_string(call.task_key, "Async task key")
        conflict_ids = call.conflict_ids
        if conflict_ids is None:
            return
        if not isinstance(conflict_ids, Mapping):
            raise AsyncConfigurationError("Conflict resources must be a mapping of model labels to primary keys.")
        for model_label, identifiers in conflict_ids.items():
            self._require_nonempty_string(model_label, "Conflict resource model label")
            try:
                iterator = iter(identifiers)
            except TypeError as exc:
                raise AsyncConfigurationError(
                    f"Conflict resource IDs for '{model_label}' must be iterable."
                ) from exc
            for identifier in iterator:
                if identifier is None:
                    raise AsyncConfigurationError(
                        f"Conflict resource IDs for '{model_label}' cannot contain None."
                    )
                try:
                    hash(identifier)
                except TypeError as exc:
                    raise AsyncConfigurationError(
                        f"Conflict resource IDs for '{model_label}' must be hashable."
                    ) from exc

    def validate_cache_backend(self) -> None:
        """Ensure the configured cache backend supports multi-process access."""
        if not self.cache:
            if not getattr(settings, "configured", False):
                raise AsyncConfigurationError(
                    "Django settings are not configured; configure Django before creating an AsyncManager."
                )
            raise AsyncConfigurationError(
                f"CACHE_NAME refers to undefined cache alias '{self.cache_name}'. "
                "Add the alias to Django CACHES."
            )

        backend_path = (
            f"{self.cache.__class__.__module__}.{self.cache.__class__.__name__}"
        )
        lowered = backend_path.lower()
        if any(token in lowered for token in ("locmem", "dummycache", "dummy")):
            raise AsyncConfigurationError(
                "Coordinator progress tracking requires a shared cache backend. "
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
            cache.set("powercrud_test", "test", 1)
            cache.get("powercrud_test")
            cache.delete("powercrud_test")
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
            log.error("Async system probes did not complete successfully")
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

    def launch(
        self,
        func: Callable,
        *args,
        worker_kwargs=None,
        task_key=None,
        conflict_ids=None,
        user=None,
        affected_objects=None,
        execution_options=None,
    ) -> str:
        """Launch a job through the reusable coordinator API."""
        if worker_kwargs is not None and not isinstance(worker_kwargs, Mapping):
            raise AsyncConfigurationError("worker_kwargs must be a mapping when supplied.")
        if execution_options is not None and not isinstance(execution_options, Mapping):
            raise AsyncConfigurationError("execution_options must be a mapping when supplied.")
        task_name = task_key if task_key is not None else self.generate_task_name()
        manager_config = self.export_manager_config()
        worker_args = tuple(args)
        kwargs = dict(worker_kwargs or {})
        metadata = {
            "task_key": task_name,
            "manager_class": f"{type(self).__module__}.{type(self).__qualname__}",
            "manager_config": manager_config,
            "_coordinator_config": self.get_coordination_config().to_snapshot(),
        }
        for key, value in metadata.items():
            if key in kwargs and kwargs[key] != value:
                raise ValueError(f"worker_kwargs contains conflicting reserved value: {key}")
            kwargs.setdefault(key, value)
        spec = ManagerSpec(
            class_path=metadata["manager_class"],
            config=manager_config,
            completion_style=self.completion_style,
        )
        options = dict(execution_options or {})
        options.setdefault("hook", "powercrud._coordinator.q2.task_completion_hook")
        return self._launch(
            TaskCall(
                func=func,
                args=worker_args,
                kwargs=kwargs,
                task_key=task_name,
                conflict_ids=conflict_ids,
                user=user,
                affected_objects=affected_objects,
                manager=spec,
                coordination=metadata["_coordinator_config"],
                execution_options=options,
            ),
            options=options,
        )

    def _launch(self, call: TaskCall, *, options=None) -> str:
        """Reserve, initialize, submit, register, and announce one task."""
        task_name = call.task_key
        conflict_ids = call.conflict_ids
        options = dict(options or call.execution_options)
        self.validate_async_configuration(call=call, options=options)
        if conflict_ids and not self.add_conflict_ids(task_name, conflict_ids):
            log.error("Conflict reservation failed for task %s", task_name)
            raise Exception("Cannot launch task - conflicts detected with existing operations")
        self.create_progress_key(task_name)
        worker_kwargs = dict(call.kwargs)
        worker_kwargs.setdefault("task_key", task_name)
        try:
            execution_ref = self._q2_adapter.submit(
                TaskCall(
                    func=call.func,
                    args=call.args,
                    kwargs=worker_kwargs,
                    task_key=task_name,
                    conflict_ids=conflict_ids,
                    user=call.user,
                    affected_objects=call.affected_objects,
                    manager=call.manager,
                    coordination=call.coordination,
                    execution_options=call.execution_options,
                ),
                options=options,
            )
            if not execution_ref.id:
                raise Exception("django-q2 async_task returned falsy task_id")
        except Exception as exc:
            log.error("Failed to enqueue task_name %s: %s", task_name, exc)
            if conflict_ids:
                self.remove_conflict_ids(task_name)
            self.remove_progress_key(task_name)
            raise Exception(f"Failed to enqueue async task: {exc}")
        try:
            if not self.add_active_task(task_name, conflict_ids=None):
                log.warning("Failed to register task %s as active - cleanup may be incomplete", task_name)
        except Exception as exc:
            log.error("Failed to register active task %s: %s", task_name, exc)
        lifecycle_kwargs = dict(worker_kwargs)
        lifecycle_kwargs.pop("save", None)
        self._emit_lifecycle(
            event="create",
            task_name=task_name,
            status=self.STATUSES.PENDING,
            message="Task queued",
            user=call.user,
            affected_objects=call.affected_objects,
            django_q2_task_id=execution_ref.id,
            task_kwargs=lifecycle_kwargs,
            task_args=list(call.args),
        )
        log.debug("Successfully launched task_name %s (q2 id: %s)", task_name, execution_ref.id)
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
        lookup = self._q2_adapter.lookup_legacy_name(
            task_name, wait_ms=300, raise_errors=True
        )
        if lookup.kind == "unavailable":
            raise RuntimeError(lookup.reason or "django-q2 result lookup failed")
        if lookup.completion:
            success = lookup.completion.success
            if success is not None:
                return "success" if success else "failed"
            else:
                return "executing"
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
        lookup = self._q2_adapter.lookup_legacy_name(
            task_name, wait_ms=0, raise_errors=True
        )
        if lookup.kind == "unavailable":
            raise RuntimeError(lookup.reason or "django-q2 result lookup failed")
        if lookup.completion:
            success = lookup.completion.success
            if success is not None:
                return self.STATUSES.SUCCESS if success else self.STATUSES.FAILED
            else:
                return self.STATUSES.IN_PROGRESS
        # if task not fetched it means it is either queued or doesn't exist
        return self.STATUSES.UNKNOWN  # None

    def is_task_complete(self, task_name: str) -> bool:
        """Return whether the task has finished (success or failure).
        NB unless q2 is configured with cached=True, this will hit the db back end

        Args:
            task_name: The django-q2 task identifier task.name.

        Returns:
            bool: True if success is not null in Task model, else False.
        """
        task_status = self.get_task_status_nowait(task_name)
        if task_status in [
            self.STATUSES.SUCCESS,
            self.STATUSES.FAILED,
        ]:
            return True
        return False  # covers ['not found', 'in_progress', 'pending']

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
        return "completed"

    def is_task_complete_cache_only(self, task_name: str) -> bool:
        """Returns boolean indicator as to whether task is completed or not.
        Never hits db, even if django-q2 cached=False.

        Args:
            task_name (str): The django-q2 task.name.

        Returns:
            bool: _description_
        """
        task_status = self.get_task_status_cache_only(task_name)
        return task_status == "completed"

    # =============================================================================
    # Conflict Management Functions
    # =============================================================================
    def add_active_task(
        self, task_name: str, conflict_ids: dict[str, set[Hashable]] = None
    ) -> bool:
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
            log.error(
                f"Failed to add active task_name {task_name} to active tasks cache: {e}"
            )
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
        cache_active_tasks = self.cache.get(self.active_prefix, set()) or set()

        for task_name in cache_active_tasks:
            self.remove_active_task(task_name)

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
        max_duration = (
            timedelta(seconds=self.max_task_duration)
            if self.max_task_duration
            else None
        )

        for task_name in active_tasks:
            lookup = self._q2_adapter.lookup_legacy_name(
                task_name, orm_only=True
            )
            if lookup.kind == "unavailable":
                summary["skipped"][task_name] = (
                    f"task lookup failed: {lookup.reason}"
                )
                continue

            if lookup.kind == "missing":
                summary["cleaned"][task_name] = self._cleanup_task_artifacts(
                    task_name,
                    reason="django-q2 task missing",
                    status=self.STATUSES.UNKNOWN,
                )
                continue

            completion = lookup.completion
            success_flag = completion.success
            if success_flag is None:
                started = completion.started_at
                if started and max_duration and (started + max_duration) < now:
                    summary["cleaned"][task_name] = self._cleanup_task_artifacts(
                        task_name,
                        reason="max duration exceeded",
                        status=self.STATUSES.UNKNOWN,
                    )
                else:
                    summary["skipped"][task_name] = "task still running"
                continue

            reason = (
                "completed successfully" if success_flag else "completed with failure"
            )
            status = self.STATUSES.SUCCESS if success_flag else self.STATUSES.FAILED
            result_payload = completion.result

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

    def add_conflict_ids(
        self, task_name: str, conflict_ids: dict[str, set[Hashable]]
    ) -> bool:
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
            log.warning(f"Conflict detected with IDs {conflicts}")
        # else:
        #     log.debug("No conflicts detected")

        return conflicts

    def remove_conflict_ids(
        self, task_name: str, conflict_ids: Optional[dict[Hashable]] = None
    ):
        """Remove all conflict tracking for a task using dual-key cleanup.

        Uses the object tracking set to find all per-object lock keys for this task,
        deletes each lock key, and then deletes the tracking set. Idempotent.

        Args:
            task_name: Unique identifier task.name to clean up.
            conflict_ids: Unused parameter; kept for API compatibility.
        """
        log.debug(
            f"remove_conflict_ids for task_name: {task_name}, conflict_ids: {conflict_ids}"
        )
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
            log.debug(
                f"Created progress key for task_name {task_name} (backend {self.cache.__class__.__module__}.{self.cache.__class__.__name__})"
            )
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
                if self.cache.get(progress_key) is None and self.cache.has_key(
                    progress_key
                ):
                    self.cache.delete(progress_key)
                    log.debug(f"Cleared expired progress key for {task_name}")
            except Exception as e:
                log.warning(f"Failed to clear expired progress for {task_name}: {e}")

    # =============================================================================
    # Lifecycle Events
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
        return

    @classmethod
    def as_view(cls, *, manager_factory, template_name=None):
        """Build a reusable progress endpoint around an explicit manager factory."""
        from .views import progress_view

        return progress_view(manager_factory=manager_factory, template_name=template_name)

    def cleanup_dashboard_data(self, task_name: str) -> int:
        """Clean up any dashboard artifacts tracked for a task.

        Args:
            task_name: The task identifier to clean dashboard artifacts for.
        """
        return 0

    def handle_task_completion(self, task, task_name: str) -> None:
        """Translate a compatibility task object into a core completion value."""
        self.complete(self._q2_adapter.to_completion(task, task_key=task_name))

    def complete(self, completion: Completion) -> None:
        """Apply legacy lifecycle and cleanup behavior to plain completion data."""
        task_name = completion.task_key
        log.debug(f"handle_task_completion started for task_name: {task_name}")
        try:
            # Perform default cleanup
            self.remove_active_task(task_name)

            success_flag = completion.success
            result_payload = completion.result

            if success_flag is True:
                self._emit_lifecycle(
                    event="complete",
                    task_name=task_name,
                    status=self.STATUSES.SUCCESS,
                    message="Task completed successfully",
                    result=result_payload,
                )
            elif success_flag is False:
                failure_message = (
                    str(result_payload) if result_payload else "Task failed"
                )
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

            self._emit_lifecycle(
                event="cleanup", task_name=task_name, status=self.STATUSES.UNKNOWN
            )
            log.debug(
                f"Handled completion for task_name {task_name} (success: {success_flag})"
            )
        except Exception as e:
            log.error(f"Error in handle_task_completion for {task_name}: {e}")

    @classmethod
    def resolve_manager(
        cls, manager_class_path: str | None, config: dict | None = None
    ):
        try:
            from .reconstruction import construct_manager

            return construct_manager(
                ManagerSpec(class_path=manager_class_path, config=config),
                coordination_config=cls._default_coordination_config(),
                executor=cls._default_executor(),
                legacy=True,
                fallback_class_path=f"{cls.__module__}.{cls.__qualname__}",
                prepare_config=lambda manager_cls, value: manager_cls.prepare_manager_config(value)
                if hasattr(manager_cls, "prepare_manager_config")
                else value,
            )
        except Exception as exc:
            log.warning(
                "Failed to import manager '%s': %s. Falling back to coordinator manager",
                manager_class_path,
                exc,
            )
            return cls()

    @classmethod
    def _default_coordination_config(cls):
        """Return explicit defaults for framework-neutral legacy resolution."""
        return CoordinatorConfig()

    @classmethod
    def _default_executor(cls):
        """Return a lightweight default q2 adapter."""
        return Q2Adapter()
