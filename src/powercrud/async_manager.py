"""PowerCRUD compatibility layer for the reusable async coordinator."""

import logging
import warnings
import uuid
from collections.abc import Mapping
from typing import Callable

from django.urls import include, path
from django.core.exceptions import ImproperlyConfigured

from powercrud.conf import DEFAULTS, get_powercrud_setting
from powercrud._coordinator.config import CoordinatorConfig
from powercrud._coordinator.exceptions import AsyncConfigurationError, AsyncDisabledError
from powercrud._coordinator.manager import AsyncManager as CoordinatorAsyncManager
from powercrud._coordinator.q2 import Q2Adapter
from powercrud._coordinator.reconstruction import construct_manager
from powercrud._coordinator.reconstruction import current_binding
from powercrud._coordinator.types import ManagerSpec, TaskCall

log = logging.getLogger(__name__)


def _powercrud_coordination_config():
    """Translate public PowerCRUD settings into explicit coordinator values."""
    try:
        return CoordinatorConfig(
            enabled=get_powercrud_setting("ASYNC_ENABLED", DEFAULTS["ASYNC_ENABLED"]),
            cache_name=get_powercrud_setting("CACHE_NAME", DEFAULTS["CACHE_NAME"]),
            conflict_ttl=get_powercrud_setting("CONFLICT_TTL", DEFAULTS["CONFLICT_TTL"]),
            progress_ttl=get_powercrud_setting("PROGRESS_TTL", DEFAULTS["PROGRESS_TTL"]),
            cleanup_grace_period=get_powercrud_setting(
                "CLEANUP_GRACE_PERIOD", DEFAULTS["CLEANUP_GRACE_PERIOD"]
            ),
            max_task_duration=get_powercrud_setting(
                "MAX_TASK_DURATION", DEFAULTS["MAX_TASK_DURATION"]
            ),
            terminal_result_ttl=get_powercrud_setting(
                "TERMINAL_RESULT_TTL", DEFAULTS["TERMINAL_RESULT_TTL"]
            ),
            terminal_result_max_bytes=get_powercrud_setting(
                "TERMINAL_RESULT_MAX_BYTES", DEFAULTS["TERMINAL_RESULT_MAX_BYTES"]
            ),
        )
    except ImproperlyConfigured as exc:
        raise AsyncConfigurationError(str(exc)) from exc


class AsyncManager(CoordinatorAsyncManager):
    """Public manager preserving PowerCRUD settings and legacy call behavior."""

    completion_style = "legacy"

    def __init__(self, *, coordination_config=None, executor=None):
        """Build a public manager with an explicit or translated configuration."""
        try:
            self.cleanup_schedule_interval = get_powercrud_setting(
                "CLEANUP_SCHEDULE_INTERVAL", DEFAULTS["CLEANUP_SCHEDULE_INTERVAL"]
            )
            self._probe_timeout_ms = get_powercrud_setting(
                "QCLUSTER_PROBE_TIMEOUT_MS", DEFAULTS["QCLUSTER_PROBE_TIMEOUT_MS"]
            )
        except ImproperlyConfigured as exc:
            raise AsyncConfigurationError(str(exc)) from exc
        binding = current_binding()
        super().__init__(
            coordination_config=(
                coordination_config
                if coordination_config is not None
                else binding.config if binding else _powercrud_coordination_config()
            ),
            executor=(
                executor
                if executor is not None
                else binding.executor
                if binding and binding.executor is not None
                else Q2Adapter(probe_timeout_ms=self._probe_timeout_ms)
            ),
        )

    def validate_async_qcluster(self, timeout_ms=None):
        """Probe q2 using the translated PowerCRUD probe timeout by default."""
        return super().validate_async_qcluster(
            self._probe_timeout_ms if timeout_ms is None else timeout_ms
        )

    def _async_launch_enabled(self):
        """Read current PowerCRUD launch permission, not a retained snapshot."""
        try:
            return get_powercrud_setting("ASYNC_ENABLED", DEFAULTS["ASYNC_ENABLED"])
        except ImproperlyConfigured as exc:
            raise AsyncConfigurationError(str(exc)) from exc

    def launch_async_task(
        self,
        func: Callable,
        *args,
        conflict_ids=None,
        user=None,
        affected_objects=None,
        task_key=None,
        group=None,
        timeout=None,
        sync=False,
        cached=False,
        broker=None,
        q_options=None,
        ack_failure=None,
        **kwargs,
    ) -> str:
        """Launch using the established PowerCRUD signature and UUID convention."""
        worker_args = list(args)
        key = task_key
        task_name_alias = kwargs.pop("task_name", None)
        options = {
            "hook": "powercrud.async_hooks.task_completion_hook",
            "group": group,
            "timeout": timeout,
            "sync": sync,
            "cached": cached,
            "broker": broker,
            "task_name": key,
            "q_options": q_options,
        }
        if ack_failure is not None:
            options["ack_failure"] = ack_failure
        elif not (isinstance(q_options, Mapping) and "ack_failure" in q_options):
            configured_ack = getattr(self.qcluster_settings, "get", lambda *_: None)("ack_failures")
            options["ack_failure"] = True if configured_ack is None else configured_ack
        q_options_task_name = q_options.get("task_name") if isinstance(q_options, Mapping) else None
        aliases = [value for value in (task_name_alias, q_options_task_name) if value is not None]
        if key is not None and any(alias != key for alias in aliases):
            raise AsyncConfigurationError("task_key conflicts with task_name or q_options.task_name.")
        if key is None and aliases:
            if any(alias != aliases[0] for alias in aliases):
                raise AsyncConfigurationError("task_name conflicts with q_options.task_name.")
            key = aliases[0]
        if key is None and worker_args and isinstance(worker_args[-1], str):
            try:
                uuid.UUID(worker_args[-1])
                key = worker_args.pop()
                warnings.warn(
                    "Passing task_key as the final positional UUID is deprecated; use task_key=.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            except (ValueError, TypeError):
                pass
        if key is None:
            key = self.generate_task_name()
        if not isinstance(key, str) or not key.strip():
            raise AsyncConfigurationError("task_key must be a non-empty string.")
        manager_spec = self.get_manager_spec()
        manager_path = manager_spec.class_path
        manager_config = manager_spec.config
        supplied_path = kwargs.pop("manager_class", manager_path)
        supplied_config = kwargs.pop("manager_config", manager_config)
        if supplied_path != manager_path or supplied_config != manager_config:
            raise AsyncConfigurationError("Caller manager metadata conflicts with the selected manager instance.")
        coordinator_snapshot = self.get_coordination_config().to_snapshot()
        caller_snapshot = kwargs.pop("_coordinator_config", coordinator_snapshot)
        if caller_snapshot != coordinator_snapshot:
            raise AsyncConfigurationError("Caller coordinator metadata conflicts with the selected manager instance.")
        worker_kwargs = dict(kwargs)
        worker_kwargs.update({
            "task_key": key,
            "manager_class": manager_path,
            "manager_config": manager_config,
            "_coordinator_config": coordinator_snapshot,
        })
        options["task_name"] = key
        return self._launch(
            TaskCall(
                func=func,
                args=tuple(worker_args),
                kwargs=worker_kwargs,
                task_key=key,
                conflict_ids=conflict_ids,
                user=user,
                affected_objects=affected_objects,
                manager=manager_spec,
                coordination=coordinator_snapshot,
                execution_options=options,
            ),
            options=options,
        )

    @classmethod
    def resolve_manager(cls, manager_class_path, config=None):
        """Resolve an explicit manager path without hiding invalid metadata."""
        if not manager_class_path:
            return cls()
        binding = current_binding()
        try:
            return construct_manager(
                ManagerSpec(class_path=manager_class_path, config=config, completion_style="legacy"),
                coordination_config=(binding.config if binding else _powercrud_coordination_config()),
                executor=(
                    binding.executor
                    if binding and binding.executor is not None
                    else Q2Adapter(probe_timeout_ms=get_powercrud_setting(
                        "QCLUSTER_PROBE_TIMEOUT_MS", DEFAULTS["QCLUSTER_PROBE_TIMEOUT_MS"]
                    ))
                ),
                legacy=False,
                prepare_config=lambda target, value: cls._coerce_manager_config(target, value),
            )
        except AsyncConfigurationError:
            raise
        except Exception as exc:
            raise AsyncConfigurationError(
                f"Could not reconstruct explicitly selected manager '{manager_class_path}'."
            ) from exc

    @staticmethod
    def _coerce_manager_config(manager_cls, config):
        """Retain the legacy tracking-config coercion extension point."""
        if config is not None and isinstance(config, dict):
            try:
                from powercrud.async_dashboard import (
                    AsyncDashboardConfig,
                    ModelTrackingAsyncManager,
                )
            except ImportError:
                return config
            if issubclass(manager_cls, ModelTrackingAsyncManager):
                return AsyncDashboardConfig(**config)
        return config

    @classmethod
    def as_view(cls, template_name=None):
        """Bind the PowerCRUD manager factory to the reusable progress endpoint."""
        from powercrud._coordinator.views import progress_view

        view = progress_view(manager_factory=cls, template_name=template_name)
        view.__qualname__ = f"{cls.__qualname__}.as_view.<locals>.progress_view"
        return view

    @classmethod
    def get_url(cls, pattern="powercrud/async/progress/", name="powercrud_async_progress"):
        """Return the legacy bare progress URL pattern."""
        return path(pattern, cls.as_view(), name=name)

    @classmethod
    def get_urlpatterns(cls, prefix="powercrud/"):
        """Return the established namespaced PowerCRUD URL include."""
        return path(prefix, include(("powercrud.urls", "powercrud"), namespace="powercrud"))


__all__ = [
    "AsyncConfigurationError",
    "AsyncDisabledError",
    "AsyncManager",
    "CoordinatorConfig",
]
