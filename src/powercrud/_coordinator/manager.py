import json
import inspect
import logging
import pickle
import uuid
from collections.abc import Mapping
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
from .types import Completion, ManagerSpec, TaskCall, TaskIdentity
from .state import (
    get_identity as read_task_identity,
    get_terminal_record,
    get_unresolved_record,
    is_finished,
    mark_finished,
    publish_terminal,
    put_identity as write_task_identity,
)

log = logging.getLogger(__name__)

class AsyncManager:
    """Coordinate task keys, shared cache state, progress, and lifecycle events."""

    class STATUSES:
        """Choices for async task statuses"""

        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        SUCCESS = "success"
        FAILED = "failed"
        UNKNOWN = "unknown"

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
        if isinstance(config.terminal_result_ttl, bool) or not isinstance(config.terminal_result_ttl, int) or config.terminal_result_ttl <= 0:
            raise AsyncConfigurationError("TERMINAL_RESULT_TTL must be a positive integer.")
        if isinstance(config.terminal_result_max_bytes, bool) or not isinstance(config.terminal_result_max_bytes, int) or config.terminal_result_max_bytes < 1024:
            raise AsyncConfigurationError("TERMINAL_RESULT_MAX_BYTES must be an integer of at least 1024.")
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
            terminal_result_max_bytes=self._coordination_config.terminal_result_max_bytes,
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

    def get_manager_spec(self) -> ManagerSpec:
        """Validate and describe this initialized manager for worker reconstruction."""
        manager_config = self.export_manager_config()
        manager_path = f"{type(self).__module__}.{type(self).__qualname__}"
        completion_style = self.completion_style
        if not isinstance(completion_style, str) or completion_style not in {
            "core",
            "legacy",
        }:
            raise AsyncConfigurationError(
                "The selected manager completion_style must be 'core' or 'legacy'."
            )
        try:
            from .reconstruction import import_string

            if import_string(manager_path) is not type(self):
                raise AsyncConfigurationError(
                    "The selected manager class path does not resolve to the initialized manager class."
                )
            pickle.dumps(manager_config)
            signature = inspect.signature(type(self).__init__)
            config_parameter = signature.parameters.get("config")
            accepts_config = (
                config_parameter is not None
                and config_parameter.kind != inspect.Parameter.POSITIONAL_ONLY
            ) or any(
                parameter.kind == inspect.Parameter.VAR_KEYWORD
                for parameter in signature.parameters.values()
            )
            if manager_config is not None and not accepts_config:
                raise AsyncConfigurationError(
                    "The selected manager exports configuration but its constructor cannot accept config."
                )
            unresolved = [
                parameter.name
                for parameter in signature.parameters.values()
                if parameter.name != "self"
                and parameter.kind
                not in {
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                }
                and parameter.default is inspect.Parameter.empty
                and not (parameter.name == "config" and manager_config is not None and accepts_config)
            ]
            if unresolved:
                raise AsyncConfigurationError(
                    "The selected manager cannot be reconstructed without required constructor arguments: "
                    + ", ".join(unresolved)
                    + "."
                )
        except AsyncConfigurationError:
            raise
        except Exception as exc:
            raise AsyncConfigurationError(
                "The selected manager identity/configuration cannot cross the q2 serialization boundary."
            ) from exc
        return ManagerSpec(manager_path, manager_config, completion_style)

    def get_task_identity(self, task_key: str) -> TaskIdentity | None:
        """Read task identity from this manager's configured cache location."""
        return read_task_identity(self.get_coordination_config(), task_key)

    def reconstruct_task_manager(self, task_key: str):
        """Reconstruct the retained manager while keeping lookup location bound."""
        identity = self.get_task_identity(task_key)
        if identity is None:
            return None, None
        config = CoordinatorConfig.from_snapshot(identity.coordination)
        if (config.cache_name, config.key_namespace) != (
            self.cache_name,
            self._coordination_config.key_namespace,
        ):
            raise AsyncConfigurationError("Retained identity does not match the selected coordination location.")
        from .reconstruction import construct_manager

        manager = construct_manager(
            identity.manager,
            coordination_config=config,
            executor=self._q2_adapter,
            legacy=False,
            prepare_config=lambda manager_cls, value: manager_cls.prepare_manager_config(value),
        )
        return identity, manager

    def put_task_identity(self, identity: TaskIdentity) -> TaskIdentity:
        """Create an immutable identity record in this manager's cache location."""
        return write_task_identity(self.get_coordination_config(), identity)

    def mark_task_finished(self, identity: TaskIdentity, *, finished_at) -> bool:
        """Retain the first confirmed terminal timestamp for this execution."""
        return mark_finished(
            self.get_coordination_config(), identity, finished_at=finished_at
        )

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
        if isinstance(self._coordination_config.terminal_result_max_bytes, bool) or not isinstance(self._coordination_config.terminal_result_max_bytes, int) or self._coordination_config.terminal_result_max_bytes < 1024:
            raise AsyncConfigurationError("TERMINAL_RESULT_MAX_BYTES must be an integer of at least 1024.")

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
        manager_spec = self.get_manager_spec()
        manager_config = manager_spec.config
        manager_path = manager_spec.class_path
        worker_args = tuple(args)
        kwargs = dict(worker_kwargs or {})
        metadata = {
            "task_key": task_name,
            "manager_class": manager_path,
            "manager_config": manager_config,
            "_coordinator_config": self.get_coordination_config().to_snapshot(),
        }
        for key, value in metadata.items():
            if key in kwargs and kwargs[key] != value:
                raise AsyncConfigurationError(f"worker_kwargs contains conflicting reserved value: {key}")
            kwargs.setdefault(key, value)
        spec = manager_spec
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
        observation = self.get_task_observation(task_name, cache_only=False, wait_ms=300)
        return observation["status"]

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
        return self.get_task_observation(task_name, cache_only=False)["status"]

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
        return self.get_task_observation(task_name, cache_only=True)["status"]

    def is_task_complete_cache_only(self, task_name: str) -> bool:
        """Returns boolean indicator as to whether task is completed or not.
        Never hits db, even if django-q2 cached=False.

        Args:
            task_name (str): The django-q2 task.name.

        Returns:
            bool: _description_
        """
        return self.get_task_observation(task_name, cache_only=True)["terminal"]

    def get_task_observation(self, task_key: str, *, cache_only: bool = True, wait_ms: int = 0):
        """Return the canonical terminal-first observation for one task."""
        base = {
            "status": self.STATUSES.UNKNOWN,
            "terminal": False,
            "reason": "identity_missing_or_expired",
            "progress": None,
            "message": None,
            "execution_outcome": None,
            "business_outcome": None,
            "details": None,
            "finished_at": None,
            "expires_at": None,
        }
        try:
            identity = self.get_task_identity(task_key)
        except Exception as exc:
            log.warning("Could not read task %s identity: %s", task_key, exc)
            base["reason"] = "identity_invalid_or_unavailable"
            return base
        if identity is None:
            return base
        try:
            config = CoordinatorConfig.from_snapshot(identity.coordination)
            terminal_record = get_terminal_record(config, identity)
            if terminal_record is not None:
                base.update({
                    "status": terminal_record["status"],
                    "terminal": terminal_record["status"] in {self.STATUSES.SUCCESS, self.STATUSES.FAILED},
                    "reason": terminal_record.get("reason"),
                    "execution_outcome": terminal_record.get("execution_outcome"),
                    "business_outcome": terminal_record.get("business_outcome"),
                    "details": terminal_record.get("details"),
                    "finished_at": terminal_record.get("finished_at"),
                    "expires_at": terminal_record.get("expires_at"),
                })
                return base
            if is_finished(config, identity):
                base["reason"] = "retention_only_outcome_unavailable"
                return base
            unresolved = get_unresolved_record(config, identity)
            if unresolved is not None:
                base["reason"] = unresolved["reason"]
                base["finished_at"] = unresolved["observed_at"]
                return base
        except Exception as exc:
            log.warning("Could not read task %s retained outcome: %s", task_key, exc)
            base["reason"] = "coordination_state_unavailable_or_invalid"
            return base

        progress = self.get_progress(task_key)
        if progress == self.STATUSES.PENDING:
            base.update(status=self.STATUSES.PENDING, reason=None, progress=None, message="Task queued")
            return base
        if progress is not None:
            base.update(status=self.STATUSES.IN_PROGRESS, reason=None, progress=progress, message=progress)
            return base
        base["reason"] = "progress_missing"
        if not cache_only:
            lookup = self._q2_adapter.lookup(identity.execution, wait_ms=wait_ms)
            if lookup.kind == "unavailable":
                base["reason"] = "result_lookup_unavailable"
            elif lookup.kind == "found" and lookup.completion is not None:
                completion = self._q2_adapter.finalize_completion(lookup.completion, identity=identity)
                if completion.finality:
                    try:
                        publish_terminal(config, identity, completion)
                    except Exception:
                        log.exception("Could not retain q2 completion for task %s", task_key)
                    return self.get_task_observation(task_key, cache_only=True)
                if completion.success is None:
                    base.update(status=self.STATUSES.IN_PROGRESS, reason="execution_finality_uncertain")
                    return base
                base["reason"] = completion.finality_reason or "execution_finality_uncertain"
            else:
                base["reason"] = "result_missing"
        return base

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
        """Delegate cleanup to retained identity and execution evidence."""
        self.cleanup_completed_tasks()

    def cleanup_completed_tasks(self) -> dict[str, Any]:
        """Remove stale artifacts (locks, progress, dashboard) for finished tasks."""
        summary: dict[str, Any] = {
            "active_tasks": 0,
            "cleaned": {},
            "skipped": {},
        }

        active_tasks = list(self.get_active_tasks())
        summary["active_tasks"] = len(active_tasks)

        for task_name in active_tasks:
            try:
                identity, manager = self.reconstruct_task_manager(task_name)
            except Exception as exc:
                summary["skipped"][task_name] = f"task identity invalid: {exc}"
                continue
            if identity is None:
                summary["skipped"][task_name] = "task identity missing or expired"
                continue
            observation = manager.get_task_observation(task_name, cache_only=True)
            if not observation["terminal"]:
                lookup = manager._q2_adapter.lookup(identity.execution, wait_ms=0)
                if lookup.kind == "found" and lookup.completion is not None:
                    completion = manager._q2_adapter.finalize_completion(lookup.completion, identity=identity)
                    if completion.finality:
                        try:
                            publish_terminal(CoordinatorConfig.from_snapshot(identity.coordination), identity, completion)
                        except Exception:
                            log.exception("Could not retain cleanup outcome for task %s", task_name)
                    elif completion.success is False:
                        from .state import record_unresolved
                        try:
                            record_unresolved(
                                CoordinatorConfig.from_snapshot(identity.coordination), identity,
                                reason=completion.finality_reason or "failed_attempt_finality_uncertain",
                                observed_at=completion.finished_at or manager._current_timestamp(),
                            )
                        except Exception:
                            log.exception("Could not retain uncertain failure evidence for task %s", task_name)
                    observation = manager.get_task_observation(task_name, cache_only=True)
                elif lookup.kind in {"missing", "unavailable"}:
                    summary["skipped"][task_name] = lookup.reason or "q2 execution result missing"
                    continue
            if not observation["terminal"]:
                summary["skipped"][task_name] = observation["reason"] or "execution finality is uncertain"
                continue

            reason = observation["reason"] or f"completed with {observation['status']} outcome"
            status = observation["status"]
            result_payload = observation["details"]

            summary["cleaned"][task_name] = manager._cleanup_task_artifacts(
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
            timestamp=self.get_task_observation(task_name, cache_only=True).get("finished_at"),
            canonical_terminal=True,
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
            observation = self.get_task_observation(task_name, cache_only=True)
            if observation["terminal"]:
                return
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
        completion = self._q2_adapter.to_completion(task, task_key=task_name)
        identity = self.get_task_identity(task_name)
        if identity is not None:
            completion = self._q2_adapter.finalize_completion(
                completion, identity=identity, raw_task=task
            )
        self.complete(completion)

    def complete(self, completion: Completion) -> None:
        """Retain terminal evidence before best-effort cleanup and reporting."""
        task_name = completion.task_key
        log.debug(f"handle_task_completion started for task_name: {task_name}")
        try:
            identity = self.get_task_identity(task_name)
            if identity is None or not completion.finality:
                log.warning("Ignoring completion without retained finality evidence for task %s", task_name)
                return
            if completion.execution and completion.execution.id != identity.execution.id:
                log.warning("Ignoring completion for stale execution on task %s", task_name)
                return
            config = CoordinatorConfig.from_snapshot(identity.coordination)
            accepted = publish_terminal(config, identity, completion)
            if accepted is None:
                log.warning("Ignoring expired completion evidence for task %s", task_name)
                return
            status = accepted["status"]
            result_payload = accepted["details"]
            detail_message = result_payload.get("message") if isinstance(result_payload, Mapping) else None
            result_text = result_payload.get("value") if isinstance(result_payload, Mapping) else None
            message = detail_message or (result_text if isinstance(result_text, str) else None) or accepted["reason"] or status
            if status == self.STATUSES.SUCCESS:
                self._emit_lifecycle(
                    event="complete",
                    task_name=task_name,
                    status=status,
                    message=message,
                    result=result_payload,
                    timestamp=accepted["finished_at"],
                )
            else:
                self._emit_lifecycle(
                    event="fail",
                    task_name=task_name,
                    status=status,
                    message=message,
                    result=result_payload,
                    timestamp=accepted["finished_at"],
                )
            try:
                self.remove_active_task(task_name)
            except Exception:
                log.exception("Could not clean active task state for %s", task_name)
            self._emit_lifecycle(event="cleanup", task_name=task_name, status=status)
            log.debug(
                "Handled completion for task_name %s (status: %s)", task_name, status
            )
        except Exception as e:
            log.error(f"Error in handle_task_completion for {task_name}: {e}")

    @classmethod
    def resolve_manager(
        cls, manager_class_path: str | None, config: dict | None = None
    ):
        """Resolve explicit manager metadata strictly; default only when absent."""
        if not manager_class_path:
            return cls()
        try:
            from .reconstruction import construct_manager

            return construct_manager(
                ManagerSpec(class_path=manager_class_path, config=config),
                coordination_config=cls._default_coordination_config(),
                executor=cls._default_executor(),
                legacy=False,
                prepare_config=lambda manager_cls, value: manager_cls.prepare_manager_config(value)
                if hasattr(manager_cls, "prepare_manager_config")
                else value,
            )
        except Exception as exc:
            if isinstance(exc, AsyncConfigurationError):
                raise
            raise AsyncConfigurationError(
                f"Could not reconstruct explicitly selected manager '{manager_class_path}'."
            ) from exc

    @classmethod
    def _default_coordination_config(cls):
        """Return explicit defaults for framework-neutral legacy resolution."""
        return CoordinatorConfig()

    @classmethod
    def _default_executor(cls):
        """Return a lightweight default q2 adapter."""
        return Q2Adapter()
