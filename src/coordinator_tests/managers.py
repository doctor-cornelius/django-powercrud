"""Explicit suite-owned configuration and factories for coordinator tests."""

from powercrud._coordinator.config import CoordinatorConfig
from powercrud._coordinator.manager import AsyncManager as InternalAsyncManager
from powercrud._coordinator.q2 import Q2Adapter
from powercrud._coordinator.reconstruction import current_binding
from powercrud._coordinator.tracking import ModelTrackingMixin

COORDINATOR_CONFIG = CoordinatorConfig(
    enabled=True,
    cache_name="coordinator_async",
    conflict_ttl=3600,
    progress_ttl=7200,
    cleanup_grace_period=86400,
    max_task_duration=3600,
)


def coordinator_dependencies(coordination_config=None, executor=None):
    """Select explicit or factory-bound values before suite-owned defaults."""
    binding = current_binding()
    return {
        "coordination_config": coordination_config if coordination_config is not None else binding.config if binding else COORDINATOR_CONFIG,
        "executor": executor if executor is not None else binding.executor if binding and binding.executor is not None else Q2Adapter(probe_timeout_ms=1500),
    }


def coordinator_manager_factory():
    """Create a coordinator manager with explicit suite-owned settings."""
    return CoordinatorAsyncManager()


class CoordinatorAsyncManager(InternalAsyncManager):
    """Importable manager stand-in for generic reconstruction tests."""

    def __init__(self, config=None, *, coordination_config=None, executor=None):
        """Use suite-owned defaults and retain application config separately."""
        super().__init__(**coordinator_dependencies(coordination_config, executor))
        self.test_config = config

    @classmethod
    def _default_coordination_config(cls):
        """Keep suite legacy reconstruction at its explicit coordination location."""
        return COORDINATOR_CONFIG

    @classmethod
    def _default_executor(cls):
        """Keep suite reconstruction probes at the established test timeout."""
        return Q2Adapter(probe_timeout_ms=1500)


class CoordinatorTrackingManager(ModelTrackingMixin, InternalAsyncManager):
    """Importable tracking manager backed by suite-owned explicit config."""

    def __init__(self, config=None, *, coordination_config=None, executor=None):
        """Bind suite-owned coordinator settings through the tracking mixin."""
        super().__init__(
            config=config,
            **coordinator_dependencies(coordination_config, executor),
        )


class CompletionRecordingManager(CoordinatorAsyncManager):
    """Importable test manager recording normalized completion values."""

    completions = []
    instances = []

    def complete(self, completion):
        """Record core completion dispatch without changing production behavior."""
        type(self).completions.append(completion)
        type(self).instances.append(self)
