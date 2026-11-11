"""Compatibility checks for public PowerCRUD async paths and wrappers."""

from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import URLPattern, URLResolver

from powercrud.async_manager import AsyncManager
from powercrud.async_manager import AsyncConfigurationError, AsyncDisabledError
from powercrud._coordinator.config import CoordinatorConfig
from powercrud._coordinator.reconstruction import current_binding


def _capturing_q2_submit(execution_id):
    """Return a q2 test seam that emits the real adapter pre-enqueue receiver."""
    def submit(func, *args, **kwargs):
        """Prepare a minimal task dictionary and run the registered capture path."""
        from powercrud._coordinator.q2 import _pre_enqueue

        q_options = kwargs.get("q_options") or {}
        task = {
            "id": execution_id,
            "name": kwargs.get("task_name"),
            "args": args,
            "kwargs": kwargs,
            "cached": q_options.get("cached", kwargs.get("cached", False)),
            "cluster": q_options.get("cluster", kwargs.get("cluster")),
        }
        _pre_enqueue(None, task)
        return execution_id

    return submit


class DefaultConfigManager(AsyncManager):
    """Distinguish an omitted constructor argument from an explicit None."""

    def __init__(self, config="constructor-default"):
        """Retain the exact config value selected by the legacy resolver."""
        self.application_config = config
        super().__init__()


class CoercingManager(AsyncManager):
    """Keep resolver customization observable when called on a subclass."""

    @staticmethod
    def _coerce_manager_config(manager_cls, config):
        """Use None as the legacy instruction to omit constructor config."""
        return None


class LegacyRecordingManager(AsyncManager):
    """Capture snapshot completion without taking responsibility for cleanup."""

    received = []

    def __init__(self, config=None):
        """Accept ordinary application config through the scoped factory."""
        super().__init__()
        self.application_config = config

    def handle_task_completion(self, task, task_name):
        """Record the actual q2 task and reconstructed manager state once."""
        self.received.append((task, task_name, self.application_config, self.get_coordination_config()))


class NoConfigManager(AsyncManager):
    """Legacy custom manager accepting no application config argument."""

    def __init__(self):
        super().__init__()


class ConfigManager(AsyncManager):
    """Custom manager retaining application config separately from coordinator config."""

    def __init__(self, config=None):
        self.application_config = config
        super().__init__()


class TestAsyncCompatibility(TestCase):
    """Keep established URL and completion-hook imports observable."""

    def test_get_url_returns_path(self):
        """Test get_url returns proper path object."""
        path_obj = AsyncManager.get_url()
        self.assertIsInstance(path_obj, URLPattern)
        self.assertEqual(str(path_obj.pattern), "powercrud/async/progress/")
        self.assertEqual(path_obj.name, "powercrud_async_progress")
        self.assertTrue(callable(path_obj.callback))

    def test_get_urlpatterns_returns_resolver(self):
        """Ensure get_urlpatterns provides a namespaced include."""
        resolver = AsyncManager.get_urlpatterns()
        self.assertIsInstance(resolver, URLResolver)
        self.assertEqual(str(resolver.pattern), "powercrud/")
        self.assertEqual(resolver.namespace, "powercrud")

    def test_hook_import_path_works(self):
        """Test that the completion hook import path remains callable."""
        from powercrud.async_hooks import task_completion_hook

        self.assertTrue(callable(task_completion_hook))
        mock_task = type(
            "MockTask", (), {"name": "test_hook_task", "id": "mock_id", "success": True}
        )()
        with patch("powercrud._coordinator.q2.task_model"):
            try:
                task_completion_hook(mock_task)
                hook_callable = True
            except Exception as exc:
                hook_callable = False
                self.fail(f"Completion hook raised unexpectedly: {exc}")
        self.assertTrue(hook_callable, "Completion hook should be callable without errors")

    def test_public_hook_preserves_legacy_manager_resolution_arguments(self):
        """Legacy q2 hook passes its parsed path/config to the public resolver once."""
        from types import SimpleNamespace
        from powercrud.async_hooks import task_completion_hook

        manager = SimpleNamespace(handle_task_completion=Mock())
        payload = {"record_model_path": "sample.AsyncTaskRecord"}
        task = SimpleNamespace(
            name="logical-key",
            kwargs={"manager_class": "sample.async_manager.SampleAsyncManager", "manager_config": payload},
        )
        with patch.object(AsyncManager, "resolve_manager", return_value=manager) as resolve:
            task_completion_hook(task)
        resolve.assert_called_once_with(
            "sample.async_manager.SampleAsyncManager", config=payload
        )
        manager.handle_task_completion.assert_called_once_with(task, "logical-key")

        manager.handle_task_completion.reset_mock()
        task.kwargs = {"manager_class": "sample.async_manager.SampleAsyncManager"}
        with patch.object(AsyncManager, "resolve_manager", return_value=manager) as resolve:
            task_completion_hook(task)
        resolve.assert_called_once_with("sample.async_manager.SampleAsyncManager", config=None)
        manager.handle_task_completion.assert_called_once_with(task, "logical-key")

        manager.handle_task_completion.reset_mock()
        task.kwargs = None
        with patch.object(AsyncManager, "resolve_manager", return_value=manager) as resolve:
            task_completion_hook(task)
        resolve.assert_called_once_with(None, config=None)
        manager.handle_task_completion.assert_called_once_with(task, "logical-key")

    def test_completion_override_calls_super_once_with_raw_task(self):
        """Legacy overrides receive the q2 object once and super handles it once."""
        from powercrud.async_hooks import task_completion_hook

        class SuperCallingManager(AsyncManager):
            def __init__(self):
                super().__init__()
                self.received = []

            def handle_task_completion(self, task, task_name):
                self.received.append((task, task_name))
                super().handle_task_completion(task, task_name)

        manager = SuperCallingManager()
        task = type(
            "MockTask",
            (),
            {"name": "completion-key", "id": "execution-id", "success": True, "result": False},
        )()
        with patch.object(AsyncManager, "resolve_manager", return_value=manager):
            with patch.object(manager, "remove_active_task", return_value=True) as remove:
                with patch.object(manager, "_emit_lifecycle") as emit:
                    task_completion_hook(task)

        self.assertEqual(len(manager.received), 1)
        self.assertIs(manager.received[0][0], task)
        self.assertEqual(manager.received[0][1], "completion-key")
        remove.assert_called_once_with("completion-key")
        event_names = [call.kwargs["event"] for call in emit.call_args_list]
        self.assertEqual(event_names.count("complete"), 1)
        self.assertEqual(event_names.count("cleanup"), 1)

    def test_public_manager_translates_settings_and_preserves_falsey_values(self):
        """PowerCRUD settings remain the public source, including explicit falsey values."""
        with override_settings(
            POWERCRUD_SETTINGS={
                "ASYNC_ENABLED": False,
                "CACHE_NAME": "default",
                "CONFLICT_TTL": 0,
                "PROGRESS_TTL": None,
                "CLEANUP_GRACE_PERIOD": 0,
                "MAX_TASK_DURATION": 0,
            }
        ):
            manager = AsyncManager()
        self.assertFalse(manager._coordination_config.enabled)
        self.assertEqual(manager.conflict_ttl, 0)
        self.assertIsNone(manager.progress_ttl)
        self.assertEqual(manager.cleanup_grace_period, 0)
        self.assertEqual(manager.max_task_duration, 0)

    def test_public_manager_rechecks_current_launch_enablement(self):
        """A manager created while enabled must honor a later disable before launch."""
        with override_settings(POWERCRUD_SETTINGS={"ASYNC_ENABLED": True}):
            manager = AsyncManager()
        with (
            override_settings(POWERCRUD_SETTINGS={"ASYNC_ENABLED": False}),
            patch.object(manager._q2_adapter, "submit") as submit,
            patch.object(manager, "add_conflict_ids") as reserve,
            patch.object(manager, "create_progress_key") as progress,
        ):
            with self.assertRaisesRegex(AsyncDisabledError, "ASYNC_ENABLED"):
                manager.launch_async_task(lambda: "done", task_key="later-disabled")
        submit.assert_not_called()
        reserve.assert_not_called()
        progress.assert_not_called()

    def test_public_tracking_types_and_mro_remain_compatible(self):
        """Public tracking keeps the same config object and public manager ancestry."""
        from powercrud.async_dashboard import AsyncDashboardConfig, ModelTrackingAsyncManager
        from powercrud._coordinator.tracking import AsyncDashboardConfig as CoreConfig
        from powercrud._coordinator.tracking import ModelTrackingMixin

        self.assertIs(AsyncDashboardConfig, CoreConfig)
        self.assertTrue(issubclass(ModelTrackingAsyncManager, AsyncManager))
        self.assertIn(ModelTrackingMixin, ModelTrackingAsyncManager.__mro__)
        self.assertEqual(ModelTrackingAsyncManager.__mro__.count(AsyncManager), 1)

    def test_public_context_and_descendant_helper_keep_legacy_behavior(self):
        """Public context exports share the core context and bind the public base manager."""
        from powercrud.async_context import TaskContext, task_context, get_current_task, register_descendant_conflicts
        from powercrud._coordinator.context import TaskContext as CoreTaskContext, get_current_task as core_get_current_task

        self.assertIs(TaskContext, CoreTaskContext, "Public context must re-export the same dataclass")

        added = []

        class ManagerStub:
            def add_conflict_ids(self, task_name, conflicts):
                added.append((task_name, conflicts))

        with patch("powercrud.async_manager.AsyncManager", return_value=ManagerStub()):
            with task_context("parent-task"):
                self.assertIs(get_current_task(), core_get_current_task())
                register_descendant_conflicts("sample.Book", [1, "2", None])
        self.assertEqual(added, [("parent-task", {"sample.book": {1, "2"}})])

    def test_progress_decorator_remains_a_public_compatibility_helper(self):
        """Legacy progress callback lookup continues to use task_name."""
        from powercrud.async_hooks import progress_update_decorator

        updates = []

        class ManagerStub:
            def update_progress(self, task_name, message):
                updates.append((task_name, message))

        with patch(
            "powercrud.async_manager.AsyncManager.resolve_manager",
            return_value=ManagerStub(),
        ):
            @progress_update_decorator
            def worker(data, progress_callback=None, **kwargs):
                """Exercise repeated callbacks and the retained task_name lookup."""
                for item in data:
                    progress_callback(f"Processed {item}")
                return True

            self.assertTrue(worker([1, 2], task_name="task-key"), "The decorator must retain the worker result")
            self.assertTrue(worker([3], task_key="normalized-key"), "The decorator must recognize the normalized task_key field")
        self.assertEqual(updates, [("task-key", "Processed 1"), ("task-key", "Processed 2"), ("normalized-key", "Processed 3")], "Progress callbacks must use either supported task key spelling")

    def test_public_legacy_launch_still_consumes_trailing_uuid(self):
        """The compatibility launch keeps its old positional UUID convention."""
        import uuid

        task_key = str(uuid.uuid4())
        with patch("powercrud._coordinator.q2.async_task", side_effect=_capturing_q2_submit("execution-id")) as enqueue:
            returned = AsyncManager().launch_async_task(lambda value: value, "payload", task_key)
        self.assertEqual(returned, task_key)
        self.assertEqual(enqueue.call_args.args[1], "payload")
        self.assertEqual(enqueue.call_args.kwargs["hook"], "powercrud.async_hooks.task_completion_hook")

    def test_public_resolver_preserves_custom_constructor_shapes_and_fallback(self):
        """Public reconstruction keeps no-argument, config, and invalid-path behavior."""
        no_config_path = f"{NoConfigManager.__module__}.{NoConfigManager.__qualname__}"
        config_path = f"{ConfigManager.__module__}.{ConfigManager.__qualname__}"
        no_config = AsyncManager.resolve_manager(no_config_path)
        configured = AsyncManager.resolve_manager(config_path, config={"app": "value"})
        with self.assertRaises(AsyncConfigurationError):
            AsyncManager.resolve_manager("missing.module.Manager")
        self.assertIsInstance(no_config, NoConfigManager)
        self.assertEqual(configured.application_config, {"app": "value"})

    def test_public_tracking_config_mapping_is_coerced(self):
        """Legacy dictionary configuration still creates the public tracking config."""
        from powercrud.async_dashboard import AsyncDashboardConfig, ModelTrackingAsyncManager

        manager = AsyncManager.resolve_manager(
            "powercrud.async_dashboard.ModelTrackingAsyncManager",
            config={"record_model_path": "sample.AsyncTaskRecord"},
        )
        self.assertIsInstance(manager, ModelTrackingAsyncManager)
        self.assertIsInstance(manager._config, AsyncDashboardConfig)
        self.assertEqual(manager._config.record_model_path, "sample.AsyncTaskRecord")

    def test_subclass_resolver_accepts_siblings_and_keeps_subclass_fallback(self):
        """Legacy resolution accepts every public manager while fallback uses cls."""
        path = f"{ConfigManager.__module__}.{ConfigManager.__qualname__}"
        resolved = NoConfigManager.resolve_manager(path, config={"app": "value"})
        self.assertIs(type(resolved), ConfigManager, "A sibling public manager must remain selectable")
        self.assertEqual(resolved.application_config, {"app": "value"}, "The selected constructor must receive config")
        with self.assertRaises(AsyncConfigurationError, msg="Invalid explicit manager paths must fail visibly"):
            NoConfigManager.resolve_manager("missing.module.Manager")

    def test_resolver_omits_config_for_absent_path_or_none_coercion(self):
        """Preserve the legacy distinction between missing config and explicit None."""
        manager = DefaultConfigManager.resolve_manager(None, config={"ignored": True})
        self.assertEqual(manager.application_config, "constructor-default", "No path must retain the default constructor route")
        path = f"{DefaultConfigManager.__module__}.{DefaultConfigManager.__qualname__}"
        manager = CoercingManager.resolve_manager(path, config={"drop": True})
        self.assertIs(type(manager), DefaultConfigManager, "Resolver coercion must not change the selected class")
        self.assertEqual(manager.application_config, "constructor-default", "A None coercion result must omit the config keyword")
        self.assertIsNone(current_binding(), "Legacy resolver scopes must not leak")

    def test_legacy_uuid_spelling_and_explicit_falsey_key_are_preserved(self):
        """Legacy parsing validates UUIDs without rewriting caller supplied strings."""
        values = ["ABCDEFAB-CDEF-4ABC-8DEF-ABCDEFABCDEF", "abcdefabcdef4abc8defabcdefabcdef", "{abcdefab-cdef-4abc-8def-abcdefabcdef}"]
        manager = AsyncManager()
        for value in values:
            with self.subTest(value=value), patch("powercrud._coordinator.q2.async_task", side_effect=_capturing_q2_submit("exec")) as enqueue:
                returned = manager.launch_async_task("worker", "payload", value)
                self.assertEqual(returned, value, "Valid trailing UUID text must remain byte-for-byte unchanged")
                self.assertEqual(enqueue.call_args.args, ("worker", "payload"), "Only the final UUID argument is consumed")
                self.assertEqual(enqueue.call_args.kwargs["task_name"], value, "Transport identity must retain the original spelling")
        with patch("powercrud._coordinator.q2.async_task", return_value="exec") as enqueue:
            with self.assertRaisesRegex(AsyncConfigurationError, "task_key must be a non-empty string"):
                manager.launch_async_task("worker", values[0], task_key="")
        enqueue.assert_not_called()

    def test_equal_task_key_aliases_are_accepted_and_explicit_uuid_args_are_preserved(self):
        """Equivalent aliases work while an explicitly keyed UUID remains a worker arg."""
        import uuid

        manager = AsyncManager()
        literal_uuid = str(uuid.uuid4())
        with patch("powercrud._coordinator.q2.async_task", side_effect=_capturing_q2_submit("alias-exec")) as enqueue:
            returned = manager.launch_async_task(
                "worker", literal_uuid, task_key="same-key", task_name="same-key",
                q_options={"task_name": "same-key"},
            )
        self.assertEqual(returned, "same-key", "Equal public aliases must normalize to one logical key")
        self.assertEqual(enqueue.call_args.args, ("worker", literal_uuid), "Explicit task_key must preserve positional UUID worker data")

    def test_trailing_uuid_parsing_emits_deprecation_warning(self):
        """The legacy UUID convention remains available with a warning."""
        import uuid
        import warnings

        with patch("powercrud._coordinator.q2.async_task", side_effect=_capturing_q2_submit("warn-exec")):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", DeprecationWarning)
                AsyncManager().launch_async_task("worker", "payload", str(uuid.uuid4()))
        self.assertTrue(any(item.category is DeprecationWarning for item in caught), "Legacy positional UUID parsing must warn callers to use task_key=.")

    def test_conflicting_q_options_task_name_fails_before_reservation(self):
        """A q2 task-name alias cannot silently diverge from the logical key."""
        manager = AsyncManager()
        with patch("powercrud._coordinator.q2.async_task") as enqueue:
            with self.assertRaisesRegex(AsyncConfigurationError, "task_key conflicts"):
                manager.launch_async_task(
                    "worker", task_key="logical-key", q_options={"task_name": "other-key"},
                    conflict_ids={"sample.Book": {123}},
                )
        enqueue.assert_not_called()
        self.assertIsNone(manager.get_progress("logical-key"), "Alias conflicts must fail before progress or reservation")

    def test_public_launch_rejects_conflicting_manager_and_task_alias_metadata(self):
        """Caller metadata cannot contradict the selected manager or logical key."""
        manager = AsyncManager()
        with patch("powercrud._coordinator.q2.async_task") as enqueue:
            with self.assertRaisesRegex(AsyncConfigurationError, "task_key conflicts"):
                manager.launch_async_task("application.worker", task_key="logical", task_name="other")
            with self.assertRaisesRegex(AsyncConfigurationError, "Caller manager metadata conflicts"):
                manager.launch_async_task(
                    "application.worker", task_key="logical",
                    manager_class="application.Manager", manager_config={"app": True},
                )
        enqueue.assert_not_called()

    def test_all_falsey_enqueue_ids_roll_back_legacy_launch(self):
        """Adapter translation must not turn an enqueue failure into a truthy ID."""
        manager = AsyncManager()
        for execution_id in (None, "", False, 0):
            with self.subTest(execution_id=execution_id), patch("powercrud._coordinator.q2.async_task", side_effect=_capturing_q2_submit(execution_id)):
                with self.assertRaisesRegex(Exception, "execution identifier|Failed to enqueue"):
                    manager.launch_async_task("worker", task_key="rejected", conflict_ids={"sample.Book": {987654}})
                self.assertIsNone(manager.get_progress("rejected"), "Failed enqueue must remove progress")
                self.assertNotIn("rejected", manager.get_active_tasks(), "Failed enqueue must not register active work")
                self.assertIsNone(manager.cache.get(f"{manager.conflict_model_prefix}sample.Book:987654"), "Failed enqueue must release its reservation")

    def test_qcluster_settings_are_lazy_and_assignment_stays_local(self):
        """Ordinary construction must defer queue settings and preserve assignment."""
        from types import SimpleNamespace

        queue_settings = SimpleNamespace()
        with patch("powercrud._coordinator.q2.settings", queue_settings):
            manager = AsyncManager()
            queue_settings.Q_CLUSTER = {"timeout": 123}
            self.assertIs(manager.qcluster_settings, queue_settings.Q_CLUSTER, "Settings must be read lazily")
            override = {"timeout": 9}
            manager.qcluster_settings = override
            self.assertIs(manager.qcluster_settings, override, "The public property must retain assigned mappings")
            self.assertIs(manager._q2_adapter.cluster_settings, override, "The executor must use the same override")
            self.assertEqual(queue_settings.Q_CLUSTER, {"timeout": 123}, "Assignment must not mutate Django settings")

    def test_snapshot_legacy_completion_retains_raw_task_and_python_config(self):
        """Snapshot dispatch must call a no-super legacy override once, under its config."""
        from types import SimpleNamespace
        from powercrud.async_hooks import task_completion_hook

        LegacyRecordingManager.received.clear()
        app_config = ("application", frozenset({1, 2}))
        config = CoordinatorConfig(cache_name="default", key_namespace="snapshot-legacy", conflict_ttl=37)
        task = SimpleNamespace(name="logical", id="exec", success=True, result=False, kwargs={
            "manager_class": f"{LegacyRecordingManager.__module__}.{LegacyRecordingManager.__qualname__}",
            "manager_config": app_config, "_coordinator_config": config.to_snapshot(),
        })
        with patch.object(LegacyRecordingManager, "complete") as complete:
            task_completion_hook(task)
        self.assertEqual(len(LegacyRecordingManager.received), 1, "A legacy override must receive exactly one completion call")
        raw, key, received_config, effective = LegacyRecordingManager.received[0]
        self.assertIs(raw, task, "The actual q2 task must reach legacy overrides")
        self.assertEqual(key, "logical", "Completion must use the logical task name")
        self.assertIs(received_config, app_config, "Snapshot config must retain supported Python values")
        self.assertEqual(effective.to_snapshot(), config.to_snapshot(), "Completion must reconstruct the supplied coordination location")
        complete.assert_not_called()
        self.assertIsNone(current_binding(), "Completion reconstruction must reset its scope")

    def test_public_tracking_overrides_super_chain_and_falsey_config(self):
        """Public tracking must initialize once and persist overridden lifecycle behavior."""
        from powercrud.async_dashboard import AsyncDashboardConfig, ModelTrackingAsyncManager
        from sample.models import AsyncTaskRecord

        calls = []
        base_init = AsyncManager.__init__

        def counted_init(manager, **kwargs):
            """Count actual public base initialization while retaining its behavior."""
            calls.append(manager)
            base_init(manager, **kwargs)

        class CustomTrackingManager(ModelTrackingAsyncManager):
            """Retain application overrides that call through the shared tracking mixin."""

            record_model_path = "sample.AsyncTaskRecord"

            def format_user(self, user):
                """Decorate the inherited user formatter through super."""
                return "override:" + super().format_user(user)

            def async_task_lifecycle(self, event, task_name, **kwargs):
                """Delegate persistence through the public manager's MRO."""
                return super().async_task_lifecycle(event, task_name, **kwargs)

        with patch.object(AsyncManager, "__init__", counted_init):
            manager = CustomTrackingManager(config=AsyncDashboardConfig(record_model_path="sample.AsyncTaskRecord"))
            fallback = CustomTrackingManager(config={})
        self.assertEqual(calls, [manager, fallback], "Each tracking manager must initialize its public manager base exactly once")
        self.assertEqual(fallback.export_manager_config().record_model_path, "sample.AsyncTaskRecord", "Falsey tracking config must retain class-attribute fallback")
        manager.async_task_lifecycle("create", "b4-tracking", user="reviewer")
        record = AsyncTaskRecord.objects.get(task_name="b4-tracking")
        self.assertEqual(record.user_label, "override:reviewer", "An override using super must persist through the shared mixin")

    def test_effective_snapshot_preserves_custom_initialization_hooks(self):
        """Public cache and validation overrides must influence exported snapshots."""
        class CustomManager(AsyncManager):
            """Override the effective location and attributes after initialization."""

            def get_cache_name(self):
                """Select the application cache independently of the supplied default."""
                return "default"

            def get_cache(self):
                """Keep custom cache acquisition participating in initialization."""
                self.cache_hook_called = True
                return super().get_cache()

            def validate_cache_backend(self):
                """Keep application cache validation participating in initialization."""
                self.validation_hook_called = True
                return super().validate_cache_backend()

            def __init__(self):
                """Apply application prefix and TTL overrides after base construction."""
                super().__init__(coordination_config=CoordinatorConfig(cache_name="not-selected"))
                self.conflict_ttl = 19
                self.progress_prefix = "application:progress:"

        manager = CustomManager()
        snapshot = manager.get_coordination_config().to_snapshot()
        self.assertTrue(manager.cache_hook_called, "Custom cache acquisition must run")
        self.assertTrue(manager.validation_hook_called, "Custom cache validation must run")
        self.assertEqual(snapshot["cache_name"], "default", "Snapshots must export the selected cache alias")
        self.assertEqual(snapshot["conflict_ttl"], 19, "Snapshots must export effective TTL overrides")
        self.assertEqual(snapshot["key_prefixes"]["progress_prefix"], "application:progress:", "Snapshots must export effective prefix overrides")

    def test_public_hook_suppresses_legacy_override_errors(self):
        """An application completion override must retain the public hook boundary."""
        from types import SimpleNamespace
        from powercrud.async_hooks import task_completion_hook

        manager = SimpleNamespace(handle_task_completion=Mock(side_effect=RuntimeError("application hook failure")))
        task = SimpleNamespace(name="failing-hook", kwargs=None)
        with patch.object(AsyncManager, "resolve_manager", return_value=manager):
            self.assertIsNone(task_completion_hook(task), "Application hook failures must remain suppressed")
        manager.handle_task_completion.assert_called_once_with(task, "failing-hook")

    def test_public_explicit_executor_wins_over_construction_binding(self):
        """Optional public dependencies must use None-only selection precedence."""
        from powercrud._coordinator.q2 import Q2Adapter
        from powercrud._coordinator.reconstruction import construction_scope

        class FalseyExecutor(Q2Adapter):
            """Keep executor presence distinct from its boolean value."""

            def __bool__(self):
                """Represent an application executor whose truth value is false."""
                return False

        explicit = FalseyExecutor()
        config = CoordinatorConfig(cache_name="default", key_namespace="bound-public")
        with construction_scope(config, Q2Adapter()):
            manager = AsyncManager(executor=explicit)
        self.assertIs(manager._q2_adapter, explicit, "Explicit public executors must override the scoped default")
        self.assertEqual(manager.get_coordination_config().to_snapshot(), config.to_snapshot(), "The bound configuration must still supply the coordination location")
        self.assertIsNone(current_binding(), "Public construction must not retain a completed binding")
