"""Focused contracts for the lazy q2 execution boundary."""

import os
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from powercrud._coordinator.q2 import Q2Adapter
from powercrud._coordinator.config import CoordinatorConfig
from powercrud._coordinator.types import ExecutionRef, TaskCall
from coordinator_tests.managers import CompletionRecordingManager


class TestQ2Adapter(SimpleTestCase):
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

