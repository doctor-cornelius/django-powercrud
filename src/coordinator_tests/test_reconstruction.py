"""Manager constructors retain application config under scoped bindings."""

from django.test import SimpleTestCase
from django.core.exceptions import ImproperlyConfigured

from coordinator_tests.managers import COORDINATOR_CONFIG, CoordinatorAsyncManager
from powercrud._coordinator.config import CoordinatorConfig
from powercrud._coordinator.manager import AsyncManager as InternalAsyncManager
from powercrud._coordinator.q2 import Q2Adapter
from powercrud._coordinator.reconstruction import (
    bind_construction,
    construct_manager,
    current_binding,
    reset_construction,
)
from powercrud._coordinator.types import ManagerSpec


class ConfigManager(CoordinatorAsyncManager):
    """Capture a constructor config while consuming the normal super binding."""

    def __init__(self, config=None):
        self.application_config = config
        super().__init__(config=config)


class NoConfigManager(CoordinatorAsyncManager):
    """Represent an older custom manager with a no-argument constructor."""

    def __init__(self):
        super().__init__()


class FailingManager(CoordinatorAsyncManager):
    """Fail during construction so binding cleanup can be checked."""

    def __init__(self, config=None):
        raise RuntimeError("expected constructor failure")


class PreparedManager(InternalAsyncManager):
    """Use the core preparation hook without an application callback."""

    @classmethod
    def prepare_manager_config(cls, config):
        """Keep supported Python application values while converting the wrapper."""
        return {"prepared": config}

    def __init__(self, config=None):
        """Consume the factory binding through an ordinary no-keyword super call."""
        self.application_config = config
        super().__init__()


class TestManagerReconstruction(SimpleTestCase):
    """Exercise constructor binding, fallback, and reset behavior."""

    def construct(self, manager_cls, config=None, **kwargs):
        """Construct a suite manager through the production factory."""
        return construct_manager(
            ManagerSpec(
                class_path=f"{manager_cls.__module__}.{manager_cls.__qualname__}",
                config=config,
            ),
            coordination_config=COORDINATOR_CONFIG,
            executor=Q2Adapter(),
            **kwargs,
        )

    def test_constructor_config_stays_separate_and_is_exported(self):
        app_config = {"tracking": "custom"}
        manager = self.construct(ConfigManager, app_config)
        self.assertEqual(manager.application_config, app_config)
        self.assertEqual(manager.export_manager_config(), app_config)
        effective = manager.get_coordination_config()
        self.assertEqual(effective.cache_name, COORDINATOR_CONFIG.cache_name)
        self.assertEqual(effective.resolved_key_prefixes(), COORDINATOR_CONFIG.resolved_key_prefixes())

    def test_internal_manager_requires_explicit_or_bound_configuration(self):
        """Reusable manager construction must never fall back to PowerCRUD settings."""
        with self.assertRaisesRegex(ImproperlyConfigured, "explicit CoordinatorConfig"):
            InternalAsyncManager()

    def test_legacy_no_argument_constructor_uses_scoped_configuration(self):
        manager = self.construct(NoConfigManager, {"ignored_by_legacy_ctor": True}, legacy=True)
        self.assertIsInstance(manager, NoConfigManager)
        self.assertEqual(manager._coordination_config, COORDINATOR_CONFIG)
        self.assertIsNone(current_binding(), "The factory must reset its binding after construction")

    def test_nested_bindings_restore_the_outer_scope(self):
        outer = bind_construction(COORDINATOR_CONFIG, Q2Adapter())
        try:
            outer_binding = current_binding()
            self.construct(ConfigManager)
            self.assertIs(current_binding(), outer_binding)
        finally:
            reset_construction(outer)
        self.assertIsNone(current_binding(), "The outer binding must also reset cleanly")

    def test_failed_constructor_resets_binding(self):
        with self.assertRaisesRegex(RuntimeError, "expected constructor failure"):
            self.construct(FailingManager)
        self.assertIsNone(current_binding(), "Failed construction must not leak its binding")

    def test_invalid_class_uses_the_specified_legacy_fallback(self):
        manager = construct_manager(
            ManagerSpec(class_path="missing.module.Manager"),
            coordination_config=COORDINATOR_CONFIG,
            legacy=True,
            fallback_class_path=f"{CoordinatorAsyncManager.__module__}.{CoordinatorAsyncManager.__qualname__}",
        )
        self.assertIsInstance(manager, CoordinatorAsyncManager)

    def test_factory_uses_selected_class_preparation_hook_by_default(self):
        """Direct core reconstruction must perform the selected manager conversion."""
        values = ("application", frozenset({1, 2}))
        manager = self.construct(PreparedManager, values)
        self.assertEqual(manager.application_config, {"prepared": values}, "The class preparation hook must run without an explicit callback")
        self.assertEqual(manager.export_manager_config(), manager.application_config, "Factory exports must retain prepared application values")

    def test_distinct_nested_binding_restores_configuration_and_executor(self):
        """A nested constructor must consume its own binding and restore the outer one."""
        outer_config = CoordinatorConfig(cache_name="default", key_namespace="outer")
        inner_config = CoordinatorConfig(cache_name="coordinator_async", key_namespace="inner")
        outer_executor, inner_executor = Q2Adapter(probe_timeout_ms=17), Q2Adapter(probe_timeout_ms=29)
        token = bind_construction(outer_config, outer_executor)
        try:
            manager = construct_manager(
                ManagerSpec(class_path=f"{ConfigManager.__module__}.{ConfigManager.__qualname__}"),
                coordination_config=inner_config, executor=inner_executor,
            )
            self.assertEqual(manager.get_coordination_config().to_snapshot(), inner_config.to_snapshot(), "Normal custom constructors must consume the inner configuration")
            self.assertIs(manager._q2_adapter, inner_executor, "Normal custom constructors must consume the inner executor")
            outer = InternalAsyncManager()
            self.assertIs(outer._coordination_config, outer_config, "Construction must restore the outer configuration")
            self.assertIs(outer._q2_adapter, outer_executor, "Construction must restore the outer executor")
            fallback = construct_manager(
                ManagerSpec(class_path=f"{FailingManager.__module__}.{FailingManager.__qualname__}"),
                coordination_config=inner_config, executor=inner_executor, legacy=True,
                fallback_class_path="powercrud._coordinator.manager.AsyncManager",
            )
            self.assertIs(fallback._coordination_config, inner_config, "Fallback construction must keep the supplied configuration")
            self.assertIs(fallback._q2_adapter, inner_executor, "Fallback construction must keep the supplied executor")
            self.assertIs(current_binding().config, outer_config, "Failed construction and fallback must restore the outer scope")
        finally:
            reset_construction(token)
        self.assertIsNone(current_binding(), "Nested construction must leave no binding behind")

    def test_tracking_mapping_preparation_without_public_wrappers(self):
        """The core factory must convert tracking mappings using the mixin hook."""
        from powercrud._coordinator.tracking import AsyncDashboardConfig

        manager = construct_manager(
            ManagerSpec(class_path="powercrud._coordinator.tracking.ModelTrackingAsyncManager", config={"record_model_path": "coordinator_testapp.AsyncTaskRecord"}),
            coordination_config=COORDINATOR_CONFIG,
        )
        self.assertIsInstance(manager.export_manager_config(), AsyncDashboardConfig, "Tracking mappings must be prepared without public resolver imports")

    def test_falsey_executor_is_retained_when_explicit_or_factory_bound(self):
        """Only None requests a default executor; supplied objects retain identity."""
        class FalseyExecutor(Q2Adapter):
            """Represent a lightweight application executor with false truth value."""

            def __bool__(self):
                """Keep object presence independent of its truth value."""
                return False

        executor = FalseyExecutor()
        manager = InternalAsyncManager(coordination_config=COORDINATOR_CONFIG, executor=executor)
        self.assertIs(manager._q2_adapter, executor, "Explicit executor selection must use None-only fallback")
        manager = construct_manager(
            ManagerSpec(class_path="powercrud._coordinator.manager.AsyncManager"),
            coordination_config=COORDINATOR_CONFIG, executor=executor,
        )
        self.assertIs(manager._q2_adapter, executor, "Factory-bound executor selection must retain the supplied object")
