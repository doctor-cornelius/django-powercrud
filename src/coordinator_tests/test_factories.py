"""Verify that factories and worker metadata select the real coordination location."""

import json
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from coordinator_tests.workers import simple_test_worker
from coordinator_tests.q2_testing import q2_submission
from powercrud._coordinator.config import CoordinatorConfig
from powercrud._coordinator.context import get_current_task, register_descendant_conflicts, task_context
from powercrud._coordinator.manager import AsyncManager
from powercrud._coordinator.types import ExecutionRef, TaskIdentity
from powercrud._coordinator.views import progress_view


class TestCoordinationFactories(SimpleTestCase):
    """Exercise real cache effects without a q2 worker or consumer dependencies."""

    def setUp(self):
        """Use different configured cache aliases and namespaces for each location."""
        self.first = AsyncManager(coordination_config=CoordinatorConfig(enabled=True, cache_name="default", key_namespace="factory-first"))
        self.second = AsyncManager(coordination_config=CoordinatorConfig(enabled=True, cache_name="coordinator_async", key_namespace="factory-second"))
        self.first.cache.clear()
        self.second.cache.clear()

    def test_progress_endpoint_factory_selects_cache_and_namespace(self):
        """The bound factory must control polling even when logical keys match."""
        self.first.update_progress("shared-key", "first location")
        self.second.update_progress("shared-key", "second location")
        for manager, execution_id in ((self.first, "factory-first-exec"), (self.second, "factory-second-exec")):
            manager.put_task_identity(TaskIdentity(
                "shared-key", manager.get_manager_spec(), manager.get_coordination_config().to_snapshot(),
                ExecutionRef(id=execution_id),
            ))
        request = RequestFactory().post("/progress/", {"task_name": "shared-key"})
        for manager, expected in ((self.first, "first location"), (self.second, "second location")):
            with self.subTest(expected=expected):
                response = progress_view(manager_factory=lambda: manager, template_name="still-ignored.html")(request)
                self.assertEqual(response.status_code, 200, "Live progress must retain the current response code")
                self.assertEqual(json.loads(response.content)["progress"], expected, "Polling must inspect the factory-selected location")

    def test_descendant_factory_selects_cache_and_namespace(self):
        """Context metadata must not replace the explicitly supplied manager factory."""
        with task_context("parent", "ignored.until.phase.C.Manager"):
            register_descendant_conflicts("coordinator_testapp.Book", [1, "2", None], manager_factory=lambda: self.second)
        key = f"{self.second.conflict_model_prefix}coordinator_testapp.book:1"
        self.assertEqual(self.second.cache.get(key), "parent", "The selected factory must receive descendant reservations")
        self.assertIsNone(self.first.cache.get(key), "Descendant registration must not use the other cache")

    def test_inline_worker_reconstructs_supplied_metadata_and_keeps_result(self):
        """Inline signal execution must bind the manager and retain its cache location."""
        observed = []

        def context_worker(message, **kwargs):
            """Record automatic context before running the existing suite worker."""
            current = get_current_task()
            observed.append((current.task_name, current.manager.get_coordination_config().key_namespace))
            return simple_test_worker(message, **kwargs)

        with patch("powercrud._coordinator.q2.async_task", side_effect=q2_submission("execution-id", execute=True)):
            key = self.second.launch(context_worker, "metadata worker", task_key="worker-key")
        self.assertEqual(key, "worker-key", "Inline launch must retain its logical key")
        self.assertEqual(observed, [("worker-key", "factory-second")], "The selected manager and logical key must be available in worker context")
        self.assertEqual(self.second.get_progress(key), "Processing completed", "The worker-only seam must preserve worker progress")
        self.assertEqual(self.second.get_task_status_cache_only(key), "success", "Terminal evidence must survive launch return")
        self.assertIsNone(self.first.get_progress(key), "Worker progress must not leak into another location")

    def test_internal_launch_rejects_reserved_worker_metadata_conflicts(self):
        """Reserved metadata must fail before enqueue or any cache reservation."""
        for field in ("task_key", "manager_class", "manager_config", "_coordinator_config"):
            with self.subTest(field=field), patch("powercrud._coordinator.q2.async_task") as enqueue:
                with self.assertRaisesRegex(Exception, field):
                    self.second.launch("worker", task_key="reserved-key", worker_kwargs={field: "conflicting"})
                enqueue.assert_not_called()
                self.assertIsNone(self.second.get_progress("reserved-key"), "Conflicting worker metadata must not create task state")

    def test_shared_launch_order_and_registration_failure_handling(self):
        """Preparation still emits create when best-effort registration fails."""
        for raises in (False, True):
            with self.subTest(raises=raises):
                events = []

                def register(*args, **kwargs):
                    """Represent both legacy registration failure forms."""
                    events.append("register")
                    if raises:
                        raise RuntimeError("registration failed")
                    return False

                def submit(*args, **kwargs):
                    """Run real signal preparation before simulating broker delivery."""
                    execution_id = q2_submission("exec")(*args, **kwargs)
                    events.append("deliver")
                    return execution_id

                with (
                    patch.object(self.second, "add_conflict_ids", side_effect=lambda *a: events.append("reserve") or True),
                    patch("powercrud._coordinator.q2.async_task", side_effect=submit),
                    patch.object(self.second, "add_active_task", side_effect=register),
                    patch.object(self.second, "_emit_lifecycle", side_effect=lambda **kw: events.append(kw["event"])),
                    patch.object(self.second, "remove_conflict_ids") as rollback,
                ):
                    task_key = f"order-key-{raises}"
                    key = self.second.launch("worker", task_key=task_key, conflict_ids={"app.Model": {1}})
                self.assertEqual(key, task_key, "Successful enqueue must keep the logical return key after registration failure")
                self.assertEqual(events, ["reserve", "register", "create", "deliver"], "Initial launch state must precede delivery")
                rollback.assert_not_called()
