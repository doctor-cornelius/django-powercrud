"""Explicit configuration and reconstruction contracts for the coordinator."""

from django.test import SimpleTestCase

from coordinator_tests.managers import COORDINATOR_CONFIG
from powercrud._coordinator.config import CoordinatorConfig


class TestCoordinatorConfig(SimpleTestCase):
    """Keep configuration snapshots primitive and independent of Django settings."""

    def test_snapshot_round_trip_preserves_values_and_legacy_prefixes(self):
        config = CoordinatorConfig(
            cache_name="coordinator_async",
            key_namespace="app-work",
            conflict_ttl=0,
            progress_ttl=15,
            cleanup_grace_period=29,
            max_task_duration=None,
            key_prefixes={"active_prefix": "custom:active"},
        )
        snapshot = config.to_snapshot()
        restored = CoordinatorConfig.from_snapshot(snapshot)
        assert snapshot["version"] == 1, "Snapshots must carry the specified version"
        assert restored.to_snapshot() == snapshot, "A version-1 snapshot must preserve its effective values"
        assert snapshot["key_prefixes"] == {
            "active_prefix": "custom:active",
            "conflict_prefix": "app-work:async:conflict:",
            "conflict_model_prefix": "app-work:conflict:model:",
            "progress_prefix": "app-work:async:progress:",
        }, "Snapshots must retain all resolved cache prefixes"

    def test_default_configuration_matches_suite_owned_settings(self):
        assert COORDINATOR_CONFIG.cache_name == "coordinator_async", "Coordinator tests must pass their cache alias explicitly"
        assert COORDINATOR_CONFIG.to_snapshot()["key_prefixes"]["conflict_model_prefix"] == "powercrud:conflict:model:", "The historical model-lock prefix must remain distinct"

    def test_snapshot_rejects_unknown_version(self):
        with self.assertRaisesRegex(ValueError, "Unsupported coordinator configuration snapshot version"):
            CoordinatorConfig.from_snapshot({"version": 2})
