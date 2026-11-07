"""Explicit-use configuration checks before coordinator side effects."""

from dataclasses import replace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from coordinator_tests.managers import COORDINATOR_CONFIG
from powercrud._coordinator.exceptions import AsyncConfigurationError, AsyncDisabledError
from powercrud._coordinator.manager import AsyncManager


class TestExplicitAsyncConfiguration(SimpleTestCase):
    """Reject invalid launches before they reserve or publish task state."""

    def make_manager(self, **changes):
        """Create an internal manager using the isolated coordinator cache."""
        return AsyncManager(coordination_config=replace(COORDINATOR_CONFIG, **changes))

    def test_disabled_launch_fails_before_reservations_or_progress(self):
        """Disabled explicit launches must not touch task state or q2."""
        manager = self.make_manager(enabled=False)
        with (
            patch.object(manager, "add_conflict_ids") as reserve,
            patch.object(manager, "create_progress_key") as progress,
            patch.object(manager, "add_active_task") as register,
            patch.object(manager._q2_adapter, "submit") as submit,
        ):
            with self.assertRaisesRegex(AsyncDisabledError, "ASYNC_ENABLED"):
                manager.launch(
                    "coordinator_tests.workers.simple_test_worker",
                    task_key="disabled-task",
                    conflict_ids={"coordinator_testapp.Book": {1}},
                )
        reserve.assert_not_called()
        progress.assert_not_called()
        register.assert_not_called()
        submit.assert_not_called()

    def test_invalid_enablement_is_rejected_without_coercion(self):
        """Truthy strings do not silently enable coordinator launches."""
        manager = self.make_manager(enabled="false")
        with self.assertRaisesRegex(AsyncConfigurationError, "must be a boolean"):
            manager.validate_async_configuration()

    def test_invalid_lifetime_and_empty_prefix_are_targeted(self):
        """Configuration value failures identify the relevant setting."""
        negative_ttl = self.make_manager()
        negative_ttl.conflict_ttl = -1
        with self.assertRaisesRegex(AsyncConfigurationError, "CONFLICT_TTL"):
            negative_ttl.validate_async_configuration()

        empty_prefix = self.make_manager()
        empty_prefix.progress_prefix = "  "
        with self.assertRaisesRegex(AsyncConfigurationError, "progress_prefix"):
            empty_prefix.validate_async_configuration()

    def test_bad_resource_keys_fail_before_reservation(self):
        """Invalid task and resource identifiers do not create partial state."""
        manager = self.make_manager()
        cases = (
            {"task_key": "", "conflict_ids": None},
            {"task_key": "bad-model", "conflict_ids": {" ": {1}}},
            {"task_key": "bad-id", "conflict_ids": {"app.Model": {None}}},
            {"task_key": "unhashable", "conflict_ids": {"app.Model": [[1]]}},
        )
        for case in cases:
            with self.subTest(case=case), patch.object(manager, "add_conflict_ids") as reserve:
                with self.assertRaises(AsyncConfigurationError):
                    manager.launch(
                        "coordinator_tests.workers.simple_test_worker",
                        task_key=case["task_key"],
                        conflict_ids=case["conflict_ids"],
                    )
                reserve.assert_not_called()

    def test_bad_qcluster_shape_fails_before_reservation(self):
        """Malformed queue settings produce a setup error without enqueueing."""
        manager = self.make_manager()
        with (
            override_settings(Q_CLUSTER=["invalid"]),
            patch.object(manager._q2_adapter, "submit") as submit,
            patch.object(manager, "create_progress_key") as progress,
        ):
            with self.assertRaisesRegex(AsyncConfigurationError, "Q_CLUSTER"):
                manager.launch(
                    "coordinator_tests.workers.simple_test_worker",
                    task_key="invalid-cluster",
                )
        submit.assert_not_called()
        progress.assert_not_called()

    def test_qcluster_aliases_and_adapter_override_are_validated(self):
        """Queue aliases and the legacy cluster override share one preflight."""
        manager = self.make_manager()
        with override_settings(Q_CLUSTER={"cache": "coordinator_missing"}):
            with self.assertRaisesRegex(AsyncConfigurationError, r"Q_CLUSTER\['cache'\]"):
                manager.validate_async_configuration()

        manager._q2_adapter.cluster_settings = []
        with self.assertRaisesRegex(AsyncConfigurationError, "Q_CLUSTER must be a mapping"):
            manager.validate_async_configuration()

    def test_malformed_q_options_are_typed_configuration_errors(self):
        """q_options shapes are checked before the adapter can submit."""
        manager = self.make_manager()
        with self.assertRaisesRegex(AsyncConfigurationError, "q_options"):
            manager.launch(
                "coordinator_tests.workers.simple_test_worker",
                task_key="invalid-options",
                execution_options={"q_options": ["not", "a mapping"]},
            )

        with self.assertRaisesRegex(AsyncConfigurationError, "iter_count"):
            manager.launch(
                "coordinator_tests.workers.simple_test_worker",
                task_key="invalid-iter-count",
                execution_options={"iter_count": -1},
            )

    def test_missing_powercrud_settings_uses_defaults(self):
        """An absent PowerCRUD settings mapping retains its documented defaults."""
        manager = self.make_manager()
        with override_settings(POWERCRUD_SETTINGS=None):
            manager.validate_async_configuration()

    def test_wrong_powercrud_settings_shape_is_targeted(self):
        """A non-mapping PowerCRUD setting fails when async use is explicit."""
        manager = self.make_manager()
        with override_settings(POWERCRUD_SETTINGS="invalid"):
            with self.assertRaisesRegex(AsyncConfigurationError, "POWERCRUD_SETTINGS"):
                manager.validate_async_configuration()

    def test_required_shared_cache_is_still_checked_without_a_probe(self):
        """A missing coordinator cache alias fails with its configured name."""
        with self.assertRaisesRegex(AsyncConfigurationError, "CACHE_NAME"):
            AsyncManager(
                coordination_config=replace(
                    COORDINATOR_CONFIG, cache_name="coordinator_missing"
                )
            )
