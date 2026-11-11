"""Focused contracts for the lazy q2 execution boundary."""

import os
import multiprocessing
import tempfile
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import TestCase

from powercrud._coordinator.q2 import Q2Adapter
from powercrud._coordinator.config import CoordinatorConfig
from powercrud._coordinator.types import ExecutionRef, ManagerSpec, TaskCall
from powercrud._coordinator.context import get_current_task
from coordinator_tests.managers import CompletionRecordingManager


class TestQ2Adapter(TestCase):
    """Exercise q2 call translation without claiming real worker behavior."""

    def test_import_and_construction_do_not_load_q2_runtime(self):
        """Importing plain adapter modules stays safe without configured Django."""
        source = (
            "import sys; "
            "from powercrud._coordinator.q2 import Q2Adapter; "
            "from powercrud._coordinator.config import CoordinatorConfig; "
            "from powercrud._coordinator.manager import AsyncManager; "
            "from powercrud._coordinator.context import task_context; "
            "from powercrud._coordinator.tracking import AsyncDashboardConfig; "
            "from powercrud._coordinator.views import progress_view; "
            "from powercrud._coordinator.types import Completion; "
            "from django.conf import settings; "
            "Q2Adapter(); "
            "assert not settings.configured; "
            "assert not Q2Adapter.is_available(); "
            "assert not any(name in sys.modules for name in ('powercrud.conf', 'powercrud.logging', 'powercrud.async_manager', 'powercrud.async_hooks', 'powercrud.async_context', 'powercrud.async_dashboard')); "
            "assert 'django_q' not in sys.modules; "
            "assert 'django_q.tasks' not in sys.modules; "
            "assert 'django_q.models' not in sys.modules"
        )
        env = os.environ.copy()
        env.pop("DJANGO_SETTINGS_MODULE", None)
        result = subprocess.run(
            [sys.executable, "-c", source],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_q2_absence_in_isolated_import_environment(self):
        """Explicit async validation diagnoses q2 when its distribution is absent."""
        site_roots = [
            Path(path)
            for path in sys.path
            if path and Path(path).is_dir() and "site-packages" in path
        ]
        self.assertTrue(site_roots, "The test process must expose an installed dependency directory")
        with tempfile.TemporaryDirectory(prefix="powercrud-no-q2-") as temp_dir:
            isolated_site = Path(temp_dir) / "site-packages"
            isolated_site.mkdir()
            for entry in site_roots[0].iterdir():
                if entry.name == "django_q" or entry.name.startswith("django_q2-"):
                    continue
                destination = isolated_site / entry.name
                try:
                    destination.symlink_to(entry, target_is_directory=entry.is_dir())
                except OSError as exc:
                    self.fail(f"Could not expose dependency {entry.name} to the isolated process: {exc}")

            source_root = Path(__file__).resolve().parents[1]
            source = f"""
import importlib.metadata
import importlib.util
import sys
sys.path[:0] = [{str(isolated_site)!r}, {str(source_root)!r}]
from powercrud._coordinator.q2 import Q2Adapter
assert importlib.util.find_spec("django_q") is None
try:
    importlib.metadata.distribution("django-q2")
except importlib.metadata.PackageNotFoundError:
    pass
else:
    raise AssertionError("q2 distribution must be absent from the isolated environment")
assert not Q2Adapter.is_available()
"""
            result = subprocess.run(
                [sys.executable, "-I", "-S", "-c", source],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_unready_app_registry_is_reported_without_loading_broker(self):
        """Explicit q2 validation waits until Django has completed app setup."""
        from powercrud._coordinator.exceptions import AsyncConfigurationError

        with patch("powercrud._coordinator.q2.apps", SimpleNamespace(ready=False)):
            with self.assertRaisesRegex(AsyncConfigurationError, "app registry is not ready"):
                Q2Adapter().validate_configuration()

    def test_missing_q2_app_registration_is_targeted(self):
        """An installed q2 distribution must also be enabled in INSTALLED_APPS."""
        from django.apps import apps
        from powercrud._coordinator.exceptions import AsyncConfigurationError

        installed_apps = [config.name for config in apps.get_app_configs() if config.name != "django_q"]
        with self.settings(INSTALLED_APPS=installed_apps):
            with self.assertRaisesRegex(AsyncConfigurationError, "missing from INSTALLED_APPS"):
                Q2Adapter().validate_configuration()

    def test_snapshot_completion_reconstructs_core_manager(self):
        """Snapshot submissions complete through the selected internal manager."""
        CompletionRecordingManager.completions.clear()
        CompletionRecordingManager.instances.clear()
        config = CoordinatorConfig(cache_name="default", key_namespace="completion-snapshot", progress_ttl=31)
        application_config = ("application", frozenset({1, 2}))
        task = SimpleNamespace(
            name="logical-key",
            id="execution-id",
            success=True,
            result={"ok": True},
            kwargs={
                "manager_class": (
                    f"{CompletionRecordingManager.__module__}."
                    f"{CompletionRecordingManager.__qualname__}"
                ),
                "manager_config": application_config,
                "_coordinator_config": config.to_snapshot(),
            },
        )
        adapter = Q2Adapter()
        adapter.dispatch_completion(task)
        self.assertEqual(len(CompletionRecordingManager.completions), 1)
        completion = CompletionRecordingManager.completions[0]
        self.assertEqual(completion.task_key, "logical-key")
        self.assertEqual(completion.execution.id, "execution-id")
        self.assertEqual(completion.result, {"ok": True})
        manager = CompletionRecordingManager.instances[0]
        self.assertEqual(manager.get_coordination_config().to_snapshot(), config.to_snapshot(), "Completion must use the supplied snapshot rather than suite defaults")
        self.assertIs(manager.export_manager_config(), application_config, "Core completion must retain supported Python application config")
        self.assertIs(manager._q2_adapter, adapter, "Completion reconstruction must bind the dispatching adapter")

    @patch("powercrud._coordinator.q2.async_task")
    def test_submit_preserves_direct_call_options_and_distinct_ids(self, async_task):
        """The adapter passes the callable directly and keeps identity values apart."""
        async_task.return_value = "q2-execution-id"
        broker = object()
        worker = Mock()
        task = TaskCall(
            func=worker,
            args=(1, "value"),
            kwargs={"task_key": "logical-key", "save": True, "hook": "custom.hook"},
            task_key="logical-key",
        )
        options = {
            "hook": "powercrud.async_hooks.task_completion_hook",
            "group": "bulk",
            "timeout": None,
            "sync": False,
            "cached": False,
            "broker": broker,
            "task_name": "logical-key",
            "q_options": {"timeout": 17},
        }

        ref = Q2Adapter().submit(task, options=options)

        self.assertEqual(async_task.call_args.args, (worker, 1, "value"))
        passed = async_task.call_args.kwargs
        self.assertEqual(passed["task_key"], "logical-key")
        self.assertEqual(passed["hook"], "custom.hook")
        self.assertEqual(passed["q_options"], {"timeout": 17})
        self.assertEqual(passed["timeout"], 30)
        self.assertIs(passed["broker"], broker)
        self.assertIs(passed["save"], True)
        self.assertEqual(ref.id, "q2-execution-id")
        self.assertEqual(ref.locator["cached"], False)
        self.assertEqual(ref.locator["options"]["timeout"], 17)
        self.assertNotIn("broker", ref.locator)

    @patch("powercrud._coordinator.q2.async_task")
    def test_submit_preserves_worker_override_and_falsy_identifier(self, async_task):
        """Worker keyword collisions retain the legacy dict merge semantics."""
        async_task.return_value = None
        task = TaskCall(
            func="tests.worker",
            args=(),
            kwargs={"task_name": "worker-name", "task_key": "logical"},
            task_key="logical",
        )

        ref = Q2Adapter().submit(task, options={"task_name": "logical"})

        self.assertEqual(async_task.call_args.kwargs["task_name"], "worker-name")
        self.assertIsNone(ref.id)

    @patch("powercrud._coordinator.q2.async_task", return_value="exec")
    def test_q_options_effective_result_route_is_recorded(self, async_task):
        """Result lookup metadata reflects q2 option overrides, including cached."""
        task = TaskCall(
            func="tests.worker", args=(), kwargs={}, task_key="logical"
        )

        ref = Q2Adapter().submit(
            task,
            options={"cached": False, "task_name": "logical", "q_options": {"cached": True, "task_name": "other"}},
        )

        self.assertFalse(async_task.call_args.kwargs["cached"])
        self.assertTrue(ref.locator["cached"])
        self.assertEqual(ref.locator["options"]["task_name"], "logical")

    @patch("powercrud._coordinator.q2.async_task")
    def test_pre_enqueue_retains_identity_before_return_without_callable_kwargs(self, async_task):
        """The real pre-enqueue boundary receives identity outside callable arguments."""
        from powercrud._coordinator.q2 import _pre_enqueue
        from powercrud._coordinator.state import get_identity
        from coordinator_tests.managers import COORDINATOR_CONFIG, CoordinatorAsyncManager

        config = CoordinatorConfig(
            **{**COORDINATOR_CONFIG.__dict__, "key_namespace": "q2-capture-test"}
        )
        task_key = "capture-logical-key"
        spec = ManagerSpec(
            f"{CoordinatorAsyncManager.__module__}.{CoordinatorAsyncManager.__qualname__}",
            {"app": (1, "two")},
            "legacy",
        )
        call = TaskCall(
            func="coordinator_tests.workers.sample_worker",
            args=("payload",),
            kwargs={"task_key": task_key},
            task_key=task_key,
            manager=spec,
            coordination=config.to_snapshot(),
        )
        task_envelopes = []

        def submit(func, *args, **kwargs):
            """Simulate q2 preparing its dictionary and emitting pre_enqueue."""
            q_options = kwargs.get("q_options", {})
            task = {
                "id": "q2-captured-id",
                "name": task_key,
                "args": args,
                "kwargs": kwargs,
                "cached": q_options.get("cached", kwargs.get("cached", False)),
                "cluster": q_options.get("cluster", kwargs.get("cluster")),
            }
            _pre_enqueue(None, task)
            task_envelopes.append(task)
            return task["id"]

        async_task.side_effect = submit
        ref = Q2Adapter().submit(
            call,
            options={"task_name": task_key, "q_options": {"cached": 3600, "cluster": "blue"}},
        )
        self.assertEqual(ref.id, "q2-captured-id", "Adapter return must match the pre-enqueue reference")
        self.assertEqual(get_identity(config, task_key).execution.id, ref.id, "Identity must be retained before q2 returns")
        self.assertIn("_coordinator_identity", task_envelopes[0], "Identity must travel in q2's top-level task envelope")
        self.assertNotIn("_coordinator_identity", async_task.call_args.kwargs, "Identity must not become a worker callable kwarg")
        self.assertEqual(async_task.call_args.args, ("coordinator_tests.workers.sample_worker", "payload"), "The original callable and arguments must remain unchanged")
        self.assertEqual(ref.locator["cluster"], "blue", "The effective q2 cluster route must be retained")
        self.assertEqual(ref.locator["cached"], 3600, "The effective cached result mode must be retained")

    def test_worker_signals_reconstruct_context_and_restore_it_after_execution(self):
        """q2 worker signal handling binds manager identity and adds result metadata."""
        from datetime import datetime, timezone
        from powercrud._coordinator.q2 import _pre_execute, _post_execute_in_worker
        from powercrud._coordinator.state import put_identity
        from powercrud._coordinator.types import TaskIdentity
        from coordinator_tests.managers import COORDINATOR_CONFIG, CoordinatorAsyncManager

        config = CoordinatorConfig(
            **{**COORDINATOR_CONFIG.__dict__, "key_namespace": "worker-signal-test"}
        )
        task_key = "worker-logical-key"
        spec = ManagerSpec(
            f"{CoordinatorAsyncManager.__module__}.{CoordinatorAsyncManager.__qualname__}",
            {"app": ("native", 3)},
            "legacy",
        )
        identity = TaskIdentity(
            task_key, spec, config.to_snapshot(), ExecutionRef("q2", "worker-exec", {"cached": False})
        )
        put_identity(config, identity)
        task = {
            "id": "worker-exec",
            "name": task_key,
            "kwargs": {"task_key": task_key},
            "_coordinator_identity": identity.to_mapping(),
        }
        _pre_execute(None, task)
        active = get_current_task()
        self.assertEqual(active.task_name, task_key, "Worker context must use the logical task key")
        self.assertIsNotNone(active.manager, "Worker context must retain the reconstructed manager")
        task.update({"stopped": datetime.now(timezone.utc), "success": True, "result": "done"})
        _post_execute_in_worker(None, task)
        self.assertIsNone(get_current_task(), "Worker signal cleanup must reset context")
        self.assertEqual(task["kwargs"]["_coordinator_identity"], identity.to_mapping(), "Saved result kwargs must carry the identity envelope")

    def test_failed_attempt_without_acknowledgement_retains_identity_without_terminal_marker(self):
        """A q2 failure that may be redelivered cannot start identity expiry."""
        from datetime import datetime, timezone
        from powercrud._coordinator.q2 import _pre_execute, _post_execute_in_worker
        from powercrud._coordinator.state import get_identity, is_finished, put_identity
        from powercrud._coordinator.types import TaskIdentity
        from coordinator_tests.managers import COORDINATOR_CONFIG, CoordinatorAsyncManager

        config = CoordinatorConfig(
            **{**COORDINATOR_CONFIG.__dict__, "key_namespace": "worker-redelivery-test"}
        )
        task_key = "redeliverable-key"
        identity = TaskIdentity(
            task_key,
            ManagerSpec(
                f"{CoordinatorAsyncManager.__module__}.{CoordinatorAsyncManager.__qualname__}",
                None,
                "legacy",
            ),
            config.to_snapshot(),
            ExecutionRef("q2", "redeliverable-exec", {"options": {"ack_failure": False}}),
        )
        put_identity(config, identity)
        task = {
            "id": identity.execution.id,
            "name": task_key,
            "kwargs": {"task_key": task_key},
            "_coordinator_identity": identity.to_mapping(),
        }
        _pre_execute(None, task)
        task.update({"stopped": datetime.now(timezone.utc), "success": False})
        _post_execute_in_worker(None, task)

        self.assertIsNone(get_current_task(), "Failed attempts must still reset worker context")
        self.assertEqual(get_identity(config, task_key), identity, "Unacknowledged failure must retain identity")
        self.assertFalse(is_finished(config, identity), "Unacknowledged failure must not create terminal retention evidence")

    def test_acknowledged_failure_records_terminal_retention_evidence(self):
        """q2 failure acknowledgement makes the result terminal for identity retention."""
        from datetime import datetime, timezone
        from powercrud._coordinator.q2 import _pre_execute, _post_execute_in_worker
        from powercrud._coordinator.state import is_finished, put_identity
        from powercrud._coordinator.types import TaskIdentity
        from coordinator_tests.managers import COORDINATOR_CONFIG, CoordinatorAsyncManager

        config = CoordinatorConfig(
            **{**COORDINATOR_CONFIG.__dict__, "key_namespace": "worker-ack-failure-test"}
        )
        task_key = "acknowledged-failure-key"
        identity = TaskIdentity(
            task_key,
            ManagerSpec(
                f"{CoordinatorAsyncManager.__module__}.{CoordinatorAsyncManager.__qualname__}",
                None,
                "legacy",
            ),
            config.to_snapshot(),
            ExecutionRef("q2", "acknowledged-failure-exec", {"options": {"ack_failure": True}}),
        )
        put_identity(config, identity)
        task = {
            "id": identity.execution.id,
            "name": task_key,
            "kwargs": {"task_key": task_key},
            "_coordinator_identity": identity.to_mapping(),
        }
        _pre_execute(None, task)
        task.update({"stopped": datetime.now(timezone.utc), "success": False, "ack_failure": True})
        _post_execute_in_worker(None, task)

        self.assertIsNone(get_current_task(), "Acknowledged failure must reset worker context")
        self.assertTrue(is_finished(config, identity), "Acknowledged failure must record terminal retention evidence")

    def test_registered_signals_cross_a_separate_process_with_shared_file_cache(self):
        """A spawned worker reconstructs identity through the suite-owned file cache."""
        from django.conf import settings
        from powercrud._coordinator.state import get_identity, put_identity
        from powercrud._coordinator.types import TaskIdentity
        from coordinator_tests.managers import COORDINATOR_CONFIG, CoordinatorAsyncManager
        from coordinator_tests.workers import run_q2_signal_process

        config = CoordinatorConfig(
            **{**COORDINATOR_CONFIG.__dict__, "key_namespace": "process-signal-test"}
        )
        task_key = "process-logical-key"
        spec = ManagerSpec(
            f"{CoordinatorAsyncManager.__module__}.{CoordinatorAsyncManager.__qualname__}",
            None,
            "legacy",
        )
        identity = TaskIdentity(
            task_key, spec, config.to_snapshot(), ExecutionRef("q2", "process-exec", {"cached": False})
        )
        put_identity(config, identity)
        task = {
            "id": "process-exec",
            "name": task_key,
            "kwargs": {"task_key": task_key, "value": "payload"},
            "_coordinator_identity": identity.to_mapping(),
        }
        context = multiprocessing.get_context("spawn")
        result_queue = context.Queue()
        process = context.Process(
            target=run_q2_signal_process,
            args=(task, result_queue, settings.TEST_CACHE_DIR),
        )
        previous_cache_dir = os.environ.get("POWERCRUD_COORDINATOR_CACHE_DIR")
        os.environ["POWERCRUD_COORDINATOR_CACHE_DIR"] = settings.TEST_CACHE_DIR
        try:
            process.start()
        finally:
            if previous_cache_dir is None:
                os.environ.pop("POWERCRUD_COORDINATOR_CACHE_DIR", None)
            else:
                os.environ["POWERCRUD_COORDINATOR_CACHE_DIR"] = previous_cache_dir
        process.join(timeout=20)
        if process.is_alive():
            process.terminate()
            process.join()
            self.fail("Separate worker signal process exceeded the bounded 20 second limit")
        self.assertEqual(process.exitcode, 0, "Separate process must initialize q2 signal handling successfully")
        result, result_identity = result_queue.get(timeout=2)
        self.assertEqual(result, f"{task_key}:payload", "Worker business code must see the reconstructed parent context")
        self.assertEqual(result_identity, identity.to_mapping(), "Result kwargs must retain the identity across the process boundary")
        self.assertEqual(get_identity(config, task_key), identity, "The shared file cache must retain the same task identity")

    def test_q2_real_sync_signing_and_worker_keep_callable_arguments_unchanged(self):
        """Real q2 signing and inline worker signals retain identity without argument injection."""
        from django_q.tasks import fetch
        from powercrud._coordinator.state import get_identity
        from coordinator_tests.managers import COORDINATOR_CONFIG, CoordinatorAsyncManager

        config = CoordinatorConfig(
            **{**COORDINATOR_CONFIG.__dict__, "key_namespace": "real-q2-boundary-test"}
        )
        task_key = "real-q2-logical-key"
        call = TaskCall(
            func="coordinator_tests.workers.signal_context_worker",
            args=("signed-payload",),
            kwargs={"task_key": task_key},
            task_key=task_key,
            manager=ManagerSpec(
                f"{CoordinatorAsyncManager.__module__}.{CoordinatorAsyncManager.__qualname__}",
                None,
                "legacy",
            ),
            coordination=config.to_snapshot(),
        )
        reference = Q2Adapter().submit(
            call,
            options={
                "hook": "powercrud._coordinator.q2.task_completion_hook",
                "sync": True,
                "cached": False,
                "task_name": task_key,
            },
        )
        result = fetch(reference.id)
        self.assertIsNotNone(result, "Real q2 sync execution must produce a saved result")
        self.assertEqual(result.result, f"{task_key}:signed-payload", "The original worker arguments must execute under reconstructed context")
        self.assertEqual(get_identity(config, task_key).execution.id, reference.id, "The retained execution ID must match the real q2 result")
        self.assertIn("_coordinator_identity", result.kwargs, "Saved q2 result kwargs must carry transport identity for completion reconstruction")

    def test_q2_real_cached_result_uses_the_recorded_lookup_route(self):
        """A real cached q2 result is found through its retained execution reference."""
        from coordinator_tests.managers import COORDINATOR_CONFIG, CoordinatorAsyncManager

        config = CoordinatorConfig(
            **{**COORDINATOR_CONFIG.__dict__, "key_namespace": "real-q2-cached-test"}
        )
        task_key = "real-q2-cached-key"
        call = TaskCall(
            func="coordinator_tests.workers.signal_context_worker",
            args=("cached-payload",),
            kwargs={"task_key": task_key},
            task_key=task_key,
            manager=ManagerSpec(
                f"{CoordinatorAsyncManager.__module__}.{CoordinatorAsyncManager.__qualname__}",
                None,
                "legacy",
            ),
            coordination=config.to_snapshot(),
        )
        adapter = Q2Adapter()
        reference = adapter.submit(
            call,
            options={
                "hook": "powercrud._coordinator.q2.task_completion_hook",
                "sync": True,
                "cached": True,
                "task_name": task_key,
            },
        )
        lookup = adapter.lookup(reference)
        self.assertEqual(reference.locator["result_cache"], "default", "Identity must record q2's effective result cache separately")
        self.assertEqual(lookup.kind, "found", "Cached q2 results must use the retained route")
        self.assertEqual(lookup.completion.execution.id, reference.id, "Cached lookup must preserve the q2 execution ID")
        self.assertEqual(lookup.completion.result, f"{task_key}:cached-payload", "Cached lookup must return the original worker result")

    @patch("powercrud._coordinator.q2.fetch")
    def test_lookup_reports_found_missing_and_unavailable(self, fetch):
        """Lookup preserves the difference between absence and adapter failure."""
        adapter = Q2Adapter()
        fetch.return_value = SimpleNamespace(
            name="logical", id="exec", success=False, result=False
        )
        found = adapter.lookup(ExecutionRef(id="exec"), wait_ms=12)
        self.assertEqual(found.kind, "found")
        self.assertIs(found.completion.success, False)
        self.assertIs(found.completion.result, False)
        fetch.assert_called_once_with("exec", wait=12, cached=False)

        fetch.reset_mock(return_value=True, side_effect=True)
        fetch.return_value = None
        self.assertEqual(adapter.lookup(ExecutionRef(id="exec")).kind, "missing")

        fetch.side_effect = RuntimeError("backend unavailable")
        unavailable = adapter.lookup(ExecutionRef(id="exec"))
        self.assertEqual(unavailable.kind, "unavailable")
        self.assertEqual(unavailable.reason, "backend unavailable")
        with self.assertRaisesRegex(RuntimeError, "backend unavailable"):
            adapter.lookup_legacy_name("logical", raise_errors=True)

    @patch("powercrud._coordinator.q2.fetch_cached")
    def test_cached_reference_uses_cached_lookup(self, fetch_cached):
        """Cached executions route through q2 cached result access."""
        fetch_cached.return_value = SimpleNamespace(name="logical", success=True)
        adapter = Q2Adapter()
        ref = ExecutionRef(id="exec", locator={"cached": 3600})

        lookup = adapter.lookup(ref)

        self.assertEqual(lookup.kind, "found")
        fetch_cached.assert_called_once_with("exec", broker=None)

    @patch("powercrud._coordinator.q2.fetch_cached")
    def test_cached_reference_recreates_configured_broker(self, fetch_cached):
        """A configured factory supplies a live broker without serializing it."""
        fetch_cached.return_value = SimpleNamespace(name="logical", success=True)
        broker = object()
        factory = Mock(return_value=broker)
        adapter = Q2Adapter(broker_factory=factory)

        adapter.lookup(ExecutionRef(id="exec", locator={"cached": True}))

        factory.assert_called_once_with()
        fetch_cached.assert_called_once_with("exec", broker=broker)

    @patch("powercrud._coordinator.q2.task_model")
    def test_legacy_name_lookup_orm_only(self, task_model):
        """Cleanup lookup uses the ORM task name query and normalized result."""
        task_model.return_value.objects.filter.return_value.first.return_value = (
            SimpleNamespace(name="logical", id="exec", success=True, result=1)
        )

        lookup = Q2Adapter().lookup_legacy_name("logical", orm_only=True)

        task_model.return_value.objects.filter.assert_called_once_with(name="logical")
        self.assertEqual(lookup.completion.result, 1)

    @patch("powercrud._coordinator.q2.task_model")
    @patch("powercrud._coordinator.q2.fetch")
    def test_probe_runs_and_cleans_up(self, fetch, task_model):
        """Probe result and ORM cleanup remain owned by the adapter."""
        task_model.return_value.objects.filter.return_value.delete.return_value = None
        fetch.return_value = SimpleNamespace(success=True)
        adapter = Q2Adapter()
        adapter.cluster_settings = {"orm": True}
        with patch("powercrud._coordinator.q2.async_task", return_value="probe-id") as enqueue:
            self.assertTrue(adapter.probe(timeout_ms=50))
        enqueue.assert_called_once()
        self.assertEqual(fetch.call_args.args, ("probe-id",))
        self.assertEqual(fetch.call_args.kwargs, {"wait": 0})
        task_model.return_value.objects.filter.assert_called_once()

    @patch("powercrud._coordinator.q2.task_model")
    @patch("powercrud._coordinator.q2.async_task", return_value="probe-id")
    @patch("powercrud._coordinator.q2.fetch", return_value=None)
    def test_probe_timeout_and_cleanup(self, fetch, _enqueue, task_model):
        """A timed-out probe returns false and still removes its ORM row."""
        task_model.return_value.objects.filter.return_value.delete.return_value = None
        adapter = Q2Adapter()
        adapter.cluster_settings = {"orm": True}
        with patch("powercrud._coordinator.q2.time.perf_counter", side_effect=[0, 1]):
            self.assertFalse(adapter.probe(timeout_ms=1))
        task_model.return_value.objects.filter.assert_called_once()

    @patch("powercrud._coordinator.q2.task_model")
    @patch("powercrud._coordinator.q2.async_task", return_value="probe-id")
    @patch("powercrud._coordinator.q2.fetch", return_value=SimpleNamespace(success=False))
    def test_probe_reports_worker_failure_and_cleans_up(self, _fetch, _enqueue, task_model):
        """A completed unsuccessful probe is unhealthy and still cleaned up."""
        task_model.return_value.objects.filter.return_value.delete.return_value = None
        adapter = Q2Adapter()
        adapter.cluster_settings = {"orm": True}

        self.assertFalse(adapter.probe(timeout_ms=50))

        task_model.return_value.objects.filter.assert_called_once()

