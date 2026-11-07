"""PowerCRUD compatibility layer for the reusable async coordinator."""

import importlib
import logging
import uuid
from typing import Callable

from django.urls import include, path

from powercrud.conf import DEFAULTS, get_powercrud_setting
from powercrud._coordinator.config import CoordinatorConfig
from powercrud._coordinator.manager import AsyncManager as CoordinatorAsyncManager
from powercrud._coordinator.q2 import Q2Adapter
from powercrud._coordinator.reconstruction import construct_manager
from powercrud._coordinator.reconstruction import current_binding
from powercrud._coordinator.types import ManagerSpec, TaskCall

log = logging.getLogger(__name__)


def _powercrud_coordination_config():
    """Translate public PowerCRUD settings into explicit coordinator values."""
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
    )


class AsyncManager(CoordinatorAsyncManager):
    """Public manager preserving PowerCRUD settings and legacy call behavior."""

    completion_style = "legacy"

    def __init__(self, *, coordination_config=None, executor=None):
        """Build a public manager with an explicit or translated configuration."""
        self.cleanup_schedule_interval = get_powercrud_setting(
            "CLEANUP_SCHEDULE_INTERVAL", DEFAULTS["CLEANUP_SCHEDULE_INTERVAL"]
        )
        self._probe_timeout_ms = get_powercrud_setting(
            "QCLUSTER_PROBE_TIMEOUT_MS", DEFAULTS["QCLUSTER_PROBE_TIMEOUT_MS"]
        )
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
        **kwargs,
    ) -> str:
        """Launch using the established PowerCRUD signature and UUID convention."""
        worker_args = list(args)
        key = task_key
        if key is None and worker_args and isinstance(worker_args[-1], str):
            try:
                uuid.UUID(worker_args[-1])
                key = worker_args.pop()
            except (ValueError, TypeError):
                pass
        if key is None:
            key = self.generate_task_name()
        worker_kwargs = dict(kwargs)
        worker_kwargs.setdefault("task_key", key)
        return self._launch(
            TaskCall(
                func=func,
                args=tuple(worker_args),
                kwargs=worker_kwargs,
                task_key=key,
                conflict_ids=conflict_ids,
                user=user,
                affected_objects=affected_objects,
            ),
            options={
                "hook": "powercrud.async_hooks.task_completion_hook",
                "group": group,
                "timeout": timeout,
                "sync": sync,
                "cached": cached,
                "broker": broker,
                "task_name": key,
                "q_options": q_options,
            },
        )

    @classmethod
    def resolve_manager(cls, manager_class_path, config=None):
        """Resolve a legacy manager with scoped coordination configuration."""
        if not manager_class_path:
            return cls()
        target_path = manager_class_path
        try:
            module_path, class_name = target_path.rsplit(".", 1)
            manager_cls = getattr(importlib.import_module(module_path), class_name)
            if not issubclass(manager_cls, AsyncManager):
                raise TypeError(f"{target_path} is not an AsyncManager subclass")
            return construct_manager(
                ManagerSpec(class_path=target_path, config=config, completion_style="legacy"),
                coordination_config=(current_binding().config if current_binding() else _powercrud_coordination_config()),
                executor=(
                    current_binding().executor
                    if current_binding() and current_binding().executor is not None
                    else Q2Adapter(probe_timeout_ms=get_powercrud_setting(
                        "QCLUSTER_PROBE_TIMEOUT_MS", DEFAULTS["QCLUSTER_PROBE_TIMEOUT_MS"]
                    ))
                ),
                legacy=True,
                fallback_class_path=f"{cls.__module__}.{cls.__qualname__}",
                prepare_config=lambda target, value: cls._coerce_manager_config(target, value),
            )
        except Exception as exc:
            log.warning("Failed to import manager '%s': %s. Falling back to AsyncManager", target_path, exc)
            return cls()

    @staticmethod
    def _coerce_manager_config(manager_cls, config):
        """Retain the legacy tracking-config coercion extension point."""
        if config is not None and isinstance(config, dict):
            try:
                from powercrud.async_dashboard import (
                    AsyncDashboardConfig,
                    ModelTrackingAsyncManager,
                )

                if issubclass(manager_cls, ModelTrackingAsyncManager):
                    return AsyncDashboardConfig(**config)
            except Exception:
                return config
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


__all__ = ["AsyncManager", "CoordinatorConfig"]
