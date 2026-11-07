"""Lazy django-q2 execution and result adapter."""

import ast
import importlib
import importlib.util
import json
import logging
import time
import uuid
from collections.abc import Mapping
from typing import Any, Callable

from django.apps import apps
from django.conf import settings
from django.core.exceptions import AppRegistryNotReady

from .exceptions import AsyncConfigurationError

from .types import Completion, ExecutionRef, ResultLookup, TaskCall

log = logging.getLogger(__name__)


def async_task(*args, **kwargs):
    """Call q2 submission through a narrow patchable lazy seam."""
    return importlib.import_module("django_q.tasks").async_task(*args, **kwargs)


def fetch(*args, **kwargs):
    """Call q2 fetch through a narrow patchable lazy seam."""
    return importlib.import_module("django_q.tasks").fetch(*args, **kwargs)


def fetch_cached(*args, **kwargs):
    """Call q2 cached fetch through a narrow patchable lazy seam."""
    return importlib.import_module("django_q.tasks").fetch_cached(*args, **kwargs)


def delete_cached(*args, **kwargs):
    """Delete a q2 cached result through a narrow lazy seam."""
    return importlib.import_module("django_q.tasks").delete_cached(*args, **kwargs)


def task_model():
    """Return the q2 Task model through a narrow lazy seam."""
    return importlib.import_module("django_q.models").Task


class Q2Adapter:
    """Own q2 imports, option handling, result access, hooks, and probes."""

    def __init__(
        self,
        *,
        probe_timeout_ms: int = 300,
        broker_factory: Callable[[], object] | None = None,
    ) -> None:
        """Create a lazy adapter without loading q2 or reading its settings."""
        self.probe_timeout_ms = probe_timeout_ms
        self.broker_factory = broker_factory
        self._cluster_settings_override: dict[str, Any] | None = None

    @property
    def cluster_settings(self) -> dict[str, Any]:
        """Return the configured q2 cluster mapping on first use."""
        if self._cluster_settings_override is not None:
            return self._cluster_settings_override
        return getattr(settings, "Q_CLUSTER", {})

    @cluster_settings.setter
    def cluster_settings(self, value: dict[str, Any]) -> None:
        """Keep a legacy-assigned cluster mapping without changing Django settings."""
        self._cluster_settings_override = value

    def _load_task_model(self):
        """Load the q2 Task model only when ORM access is requested."""
        return task_model()

    def _resolve_broker(self, ref: ExecutionRef):
        """Recreate a configured broker for cached lookup when one was supplied."""
        if self.broker_factory:
            return self.broker_factory()
        return None

    def _effective_cluster_settings(self):
        """Return the configured q2 cluster mapping, including the legacy override."""
        cluster = self.cluster_settings
        if cluster is None:
            return {}
        if not isinstance(cluster, Mapping):
            raise AsyncConfigurationError("Q_CLUSTER must be a mapping when defined.")
        return dict(cluster)

    def _prepared_submission(self, call, options=None):
        """Resolve q2's actual option precedence without enqueueing a task."""
        selected_options = call.execution_options if options is None else options
        if not isinstance(selected_options, Mapping):
            raise AsyncConfigurationError("django-q2 execution options must be a mapping.")
        if not isinstance(call.kwargs, Mapping):
            raise AsyncConfigurationError("Async worker keyword arguments must be a mapping.")
        task_options = dict(selected_options)
        worker_kwargs = dict(call.kwargs)
        worker_kwargs.setdefault("task_key", call.task_key)
        save_value = worker_kwargs.pop("save", "not_set")
        local_timeout = task_options.pop("timeout", None)
        if local_timeout is None:
            local_timeout = self._effective_cluster_settings().get("timeout", 60)

        q_options = task_options.pop("q_options", None)
        if q_options is not None and not isinstance(q_options, Mapping):
            raise AsyncConfigurationError("django-q2 option 'q_options' must be a mapping.")
        q_options = dict(q_options) if q_options else {}
        async_task_kwargs = {
            "hook": task_options.pop(
                "hook", "powercrud.async_hooks.task_completion_hook"
            ),
            "group": task_options.pop("group", None),
            "timeout": local_timeout,
            "sync": task_options.pop("sync", False),
            "cached": task_options.pop("cached", False),
            "broker": task_options.pop("broker", None),
            "task_name": task_options.pop("task_name", call.task_key),
            "q_options": q_options,
            **task_options,
            **worker_kwargs,
        }
        if save_value != "not_set":
            async_task_kwargs["save"] = save_value

        effective_options = dict(async_task_kwargs)
        effective_options.update(q_options)
        effective_options["task_name"] = async_task_kwargs["task_name"]
        return async_task_kwargs, q_options, effective_options

    @staticmethod
    def _validate_option_value(name, value):
        """Validate q2 option values while preserving documented value forms."""
        if value is None:
            return
        if name in {"sync", "save", "ack_failure"} and not isinstance(value, bool):
            raise AsyncConfigurationError(f"django-q2 option '{name}' must be a boolean.")
        if name == "cached" and not (
            isinstance(value, bool)
            or (isinstance(value, int) and not isinstance(value, bool) and value >= 0)
        ):
            raise AsyncConfigurationError(
                "django-q2 option 'cached' must be a boolean or non-negative cache lifetime."
            )
        if name == "timeout" and (
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
        ):
            raise AsyncConfigurationError(
                "django-q2 option 'timeout' must be a positive integer."
            )
        if name == "iter_count" and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise AsyncConfigurationError(
                "django-q2 option 'iter_count' must be a non-negative integer."
            )
        if name == "iter_cached" and not isinstance(value, bool):
            raise AsyncConfigurationError("django-q2 option 'iter_cached' must be a boolean.")
        if name == "chain" and not isinstance(value, (list, tuple)):
            raise AsyncConfigurationError("django-q2 option 'chain' must be a list or tuple.")
        if name == "hook" and not (
            callable(value) or (isinstance(value, str) and bool(value.strip()))
        ):
            raise AsyncConfigurationError(
                "django-q2 option 'hook' must be a callable or non-empty import path."
            )
        if name in {"group", "cluster", "task_name"} and not isinstance(value, str):
            raise AsyncConfigurationError(f"django-q2 option '{name}' must be a string.")
        if name in {"group", "cluster", "task_name"} and not value.strip():
            raise AsyncConfigurationError(f"django-q2 option '{name}' cannot be empty.")

    def validate_configuration(self, *, call=None, options=None):
        """Validate q2 configuration and selected dependencies without probing."""
        if not getattr(settings, "configured", False):
            raise AsyncConfigurationError(
                "Django settings are not configured; configure Django before using django-q2."
            )
        if not apps.ready:
            raise AsyncConfigurationError(
                "Django's app registry is not ready; call django.setup() before using django-q2."
            )
        try:
            available = importlib.util.find_spec("django_q") is not None
        except (ImportError, ValueError):
            available = False
        if not available:
            raise AsyncConfigurationError(
                "django-q2 is not installed; install the django-q2 optional dependency to launch background tasks."
            )
        if not apps.is_installed("django_q"):
            raise AsyncConfigurationError(
                "django-q2 is installed but 'django_q' is missing from INSTALLED_APPS."
            )

        cluster = self._effective_cluster_settings()
        orm = cluster.get("orm")
        if orm is True:
            database_alias = "default"
        elif isinstance(orm, str):
            database_alias = orm
            if not database_alias.strip():
                raise AsyncConfigurationError("Q_CLUSTER['orm'] must name a configured database alias.")
        elif orm is not None and orm is not False:
            raise AsyncConfigurationError(
                "Q_CLUSTER['orm'] must be a boolean or configured database alias."
            )
        else:
            database_alias = None
        if database_alias is not None:
            if database_alias not in getattr(settings, "DATABASES", {}):
                raise AsyncConfigurationError(
                    f"Q_CLUSTER['orm'] refers to unknown database alias '{database_alias}'."
                )

        if "sqs" in cluster and cluster["sqs"] is not None and not isinstance(cluster["sqs"], Mapping):
            raise AsyncConfigurationError("Q_CLUSTER['sqs'] must be a mapping when defined.")

        cache_alias = cluster.get("cache", "default")
        if not isinstance(cache_alias, str) or not cache_alias.strip():
            raise AsyncConfigurationError("Q_CLUSTER['cache'] must name a configured cache alias.")
        try:
            from django.core.cache import caches

            caches[cache_alias]
        except Exception as exc:
            raise AsyncConfigurationError(
                f"Q_CLUSTER['cache'] refers to unavailable cache alias '{cache_alias}'."
            ) from exc

        broker_module = None
        custom_broker = cluster.get("broker_class")
        if custom_broker is not None:
            if not isinstance(custom_broker, str) or "." not in custom_broker:
                raise AsyncConfigurationError("Q_CLUSTER['broker_class'] must be a dotted import path.")
            broker_module = custom_broker.rsplit(".", 1)[0]
        elif cluster.get("iron_mq"):
            broker_module = "django_q.brokers.ironmq"
        elif isinstance(cluster.get("sqs"), dict):
            broker_module = "django_q.brokers.aws_sqs"
        elif cluster.get("orm"):
            broker_module = "django_q.brokers.orm"
        elif cluster.get("mongo"):
            broker_module = "django_q.brokers.mongo"
        else:
            broker_module = "django_q.brokers.redis_broker"
        try:
            broker_module_object = importlib.import_module(broker_module)
            if custom_broker and not hasattr(
                broker_module_object, custom_broker.rsplit(".", 1)[1]
            ):
                raise ImportError("configured broker class was not found")
        except Exception as exc:
            raise AsyncConfigurationError(
                f"The configured django-q2 broker dependency '{broker_module}' is unavailable."
            ) from exc

        if call is None:
            return
        _, q_options, effective = self._prepared_submission(call, options)
        for source in (q_options, effective):
            for name in (
                "timeout", "sync", "cached", "save", "ack_failure", "group",
                "cluster", "task_name", "hook", "iter_count", "iter_cached", "chain",
            ):
                if name in source:
                    self._validate_option_value(name, source[name])

    def submit(
        self, call: TaskCall, *, options: dict[str, Any] | None = None
    ) -> ExecutionRef:
        """Submit the original callable and arguments directly to q2."""
        async_task_kwargs, q_options_clean, effective_options = self._prepared_submission(call, options)

        task_id = async_task(
            call.func, *call.args, **async_task_kwargs
        )
        # q2 applies q_options over individual values, while explicit task_name
        # remains authoritative. Preserve that effective route separately from
        # the original options dict passed unchanged into q2.
        serializable_option_names = {
            "group",
            "timeout",
            "sync",
            "cached",
            "task_name",
            "q_options",
            "save",
            "cluster",
            "ack_failure",
        }
        locator_options = {
            key: value
            for key, value in effective_options.items()
            if key in serializable_option_names
        }
        if isinstance(locator_options.get("q_options"), dict):
            locator_options["q_options"] = {
                key: value
                for key, value in locator_options["q_options"].items()
                if key not in {"broker", "hook"}
            }
        locator = {
            "cached": effective_options.get("cached", False),
            "cluster": effective_options.get("cluster"),
            "options": locator_options,
        }
        return ExecutionRef(id=str(task_id) if task_id else None, locator=locator)

    def to_completion(
        self, raw_task: object, *, task_key: str | None = None
    ) -> Completion:
        """Translate a raw q2 task into plain completion data."""
        key = task_key or str(getattr(raw_task, "name", None) or getattr(raw_task, "id", ""))
        task_id = getattr(raw_task, "id", None)
        execution = ExecutionRef(id=str(task_id) if task_id is not None else None)
        return Completion(
            task_key=key,
            execution=execution,
            success=getattr(raw_task, "success", None),
            result=getattr(raw_task, "result", None),
            started_at=getattr(raw_task, "started", None),
            finished_at=getattr(raw_task, "stopped", None),
        )

    def lookup(
        self, ref: ExecutionRef, *, wait_ms: int = 0
    ) -> ResultLookup:
        """Look up an execution by its q2 ID and recorded result route."""
        if ref.id is None:
            return ResultLookup(kind="missing")
        try:
            if ref.locator.get("cached"):
                raw_task = fetch_cached(
                    ref.id, broker=self._resolve_broker(ref)
                )
            else:
                raw_task = fetch(ref.id, wait=wait_ms, cached=False)
            if raw_task is None:
                return ResultLookup(kind="missing")
            return ResultLookup(
                kind="found", completion=self.to_completion(raw_task)
            )
        except Exception as exc:
            return ResultLookup(kind="unavailable", reason=str(exc))

    def lookup_legacy_name(
        self,
        task_key: str,
        *,
        wait_ms: int = 0,
        orm_only: bool = False,
        raise_errors: bool = False,
    ) -> ResultLookup:
        """Look up a task by its legacy q2 name, optionally using ORM only."""
        try:
            if orm_only:
                raw_task = self._load_task_model().objects.filter(name=task_key).first()
            else:
                raw_task = fetch(task_key, wait=wait_ms)
            if raw_task is None:
                return ResultLookup(kind="missing")
            return ResultLookup(
                kind="found",
                completion=self.to_completion(raw_task, task_key=task_key),
            )
        except Exception as exc:
            if raise_errors:
                raise
            return ResultLookup(kind="unavailable", reason=str(exc))

    def parse_task_kwargs(self, raw_task: object) -> dict[str, Any]:
        """Parse q2's dict or serialized kwargs using legacy parser order."""
        raw_kwargs = getattr(raw_task, "kwargs", None)
        if not raw_kwargs:
            return {}
        if isinstance(raw_kwargs, dict):
            return raw_kwargs
        if isinstance(raw_kwargs, str):
            for parser in (json.loads, ast.literal_eval):
                try:
                    parsed_kwargs = parser(raw_kwargs)
                    if isinstance(parsed_kwargs, dict):
                        return parsed_kwargs
                except Exception:
                    continue
        log.debug(
            "Could not parse q2 kwargs for task %s; using legacy manager fallback",
            getattr(raw_task, "name", "unknown"),
        )
        return {}

    def extract_manager_metadata(
        self, raw_task: object
    ) -> tuple[str | None, dict[str, Any] | None]:
        """Return the legacy manager path and dict-only manager config."""
        kwargs = self.parse_task_kwargs(raw_task)
        manager_config = kwargs.get("manager_config")
        if not isinstance(manager_config, dict):
            manager_config = None
        return kwargs.get("manager_class"), manager_config

    def dispatch_completion(
        self,
        raw_task: object,
        *,
        legacy_factory: Callable[[str | None, dict[str, Any] | None], object] | None = None,
    ) -> None:
        """Dispatch either snapshot-based core completion or a legacy raw task."""
        task_key = str(getattr(raw_task, "name", None) or getattr(raw_task, "id", ""))
        kwargs = self.parse_task_kwargs(raw_task)
        snapshot = kwargs.get("_coordinator_config")
        if isinstance(snapshot, dict):
            from .config import CoordinatorConfig
            from .reconstruction import construct_manager
            from .types import ManagerSpec

            manager_path = kwargs.get("manager_class")
            manager_config = kwargs.get("manager_config")
            config = CoordinatorConfig.from_snapshot(snapshot)
            manager = construct_manager(
                ManagerSpec(class_path=manager_path, config=manager_config),
                coordination_config=config,
                executor=self,
                legacy=True,
                fallback_class_path="powercrud._coordinator.manager.AsyncManager",
                prepare_config=lambda manager_cls, value: manager_cls.prepare_manager_config(value)
                if hasattr(manager_cls, "prepare_manager_config")
                else value,
            )
        else:
            manager_path, manager_config = self.extract_manager_metadata(raw_task)
            if legacy_factory is None:
                from .config import CoordinatorConfig
                from .manager import AsyncManager
                from .reconstruction import construct_manager
                from .types import ManagerSpec

                manager = construct_manager(
                    ManagerSpec(class_path=manager_path, config=manager_config),
                    coordination_config=CoordinatorConfig(),
                    executor=self,
                    legacy=True,
                    fallback_class_path="powercrud._coordinator.manager.AsyncManager",
                )
            else:
                manager = legacy_factory(manager_path, manager_config)

        completion_style = getattr(manager, "completion_style", "legacy")
        if completion_style == "core":
            manager.complete(self.to_completion(raw_task, task_key=task_key))
        else:
            manager.handle_task_completion(raw_task, task_key)


    def probe(self, *, timeout_ms: int | None = None) -> bool:
        """Run a q2 task/result probe; synchronous mode may execute it inline."""
        if timeout_ms is None:
            timeout_ms = self.probe_timeout_ms
        task_model_class = None
        task_name = f"q2_probe_{uuid.uuid4().hex}"
        task_id = None

        def cleanup() -> bool:
            success = True
            try:
                task_model_class.objects.filter(name=task_name).delete()
            except Exception as exc:
                log.warning("Could not delete probe ORM record %s: %s", task_name, exc)
                success = False
            try:
                if not self.cluster_settings.get("orm"):
                    delete_cached(task_name)
            except Exception as exc:
                log.warning("Could not delete cached probe %s: %s", task_name, exc)
                success = False
            return success

        try:
            task_model_class = self._load_task_model()
            task_id = async_task(
                "math.floor", 1, group="qcluster_testing", task_name=task_name
            )
            start = time.perf_counter()
            log.debug("Enqueued q2 probe %s with ID %s", task_name, task_id)
            while (time.perf_counter() - start) * 1000 < timeout_ms:
                task = fetch(task_id, wait=0)
                if task:
                    return getattr(task, "success", False)
                time.sleep(0.02)
            log.warning("Q cluster probe %s timed out after %s ms", task_name, timeout_ms)
            return False
        except Exception as exc:
            log.error("qcluster appears to not be running: %s", exc)
            return False
        finally:
            if task_id and not cleanup():
                log.warning("Could not clean up q2 probe %s", task_name)

    @staticmethod
    def is_available() -> bool:
        """Return false quietly when Django or q2 is unavailable or unready."""
        try:
            return (
                getattr(settings, "configured", False)
                and apps.ready
                and importlib.util.find_spec("django_q") is not None
                and apps.is_installed("django_q")
            )
        except (AppRegistryNotReady, ImportError, ValueError):
            return False


def task_completion_hook(raw_task: object) -> None:
    """Internal q2 hook for jobs submitted through the coordinator API."""
    Q2Adapter().dispatch_completion(raw_task)

