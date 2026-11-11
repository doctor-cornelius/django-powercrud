"""Versioned create-only task identity and retention marker contracts."""

from datetime import datetime, timedelta, timezone

from django.core.cache import caches
from django.test import SimpleTestCase

from powercrud._coordinator.config import CoordinatorConfig
from powercrud._coordinator.state import (
    finished_key,
    get_identity,
    identity_key,
    mark_finished,
    put_identity,
)
from powercrud._coordinator.types import ExecutionRef, ManagerSpec, TaskIdentity

from coordinator_tests.managers import COORDINATOR_CONFIG


class TestTaskIdentityState(SimpleTestCase):
    """Exercise identity reads and create-only writes in the selected cache."""

    def setUp(self):
        """Clear the namespaced test identity before each state contract."""
        self.cache = caches[COORDINATOR_CONFIG.cache_name]
        self.config = CoordinatorConfig(
            **{
                **COORDINATOR_CONFIG.__dict__,
                "key_namespace": "identity-state-tests",
            }
        )
        self.task_key = "logical-task"
        self.cache.delete(identity_key(self.config, self.task_key))
        self.cache.delete(finished_key(self.config, self.task_key, "execution-1"))
        self.identity = TaskIdentity(
            self.task_key,
            ManagerSpec("coordinator_tests.managers.CoordinatorAsyncManager", {"app": (1, 2)}, "legacy"),
            self.config.to_snapshot(),
            ExecutionRef("q2", "execution-1", {"cached": False, "result_cache": "default"}),
        )

    def test_identity_round_trip_is_versioned_and_create_only(self):
        """An identical retry is idempotent and a competing route is rejected."""
        stored = put_identity(self.config, self.identity)
        self.assertEqual(stored, self.identity, "A newly retained identity must round-trip unchanged")
        self.assertEqual(get_identity(self.config, self.task_key), self.identity, "Identity reads must use the selected location")
        self.assertEqual(self.cache.get(identity_key(self.config, self.task_key))["version"], 1, "Stored identities must use mapping version 1")
        self.assertEqual(put_identity(self.config, self.identity), self.identity, "An identical internal write must be idempotent")
        conflict = TaskIdentity(
            self.task_key,
            self.identity.manager,
            self.identity.coordination,
            ExecutionRef("q2", "execution-2", {}),
        )
        with self.assertRaisesRegex(RuntimeError, "conflicting task identity"):
            put_identity(self.config, conflict)

    def test_missing_identity_in_other_namespace_stays_unknown(self):
        """Stored metadata cannot redirect a lookup to another namespace."""
        put_identity(self.config, self.identity)
        other = CoordinatorConfig(
            **{
                **self.config.__dict__,
                "key_namespace": "another-namespace",
            }
        )
        self.assertIsNone(get_identity(other, self.task_key), "A different selected namespace must not discover this identity")

    def test_identity_cannot_be_written_into_another_cache_or_namespace(self):
        """The identity snapshot cannot redirect a write from its selected location."""
        other = CoordinatorConfig(
            **{
                **self.config.__dict__,
                "cache_name": "default",
                "key_namespace": "redirected-namespace",
            }
        )
        redirected = TaskIdentity(
            self.task_key,
            self.identity.manager,
            other.to_snapshot(),
            self.identity.execution,
        )
        with self.assertRaisesRegex(ValueError, "cannot redirect"):
            put_identity(self.config, redirected)
        self.assertIsNone(self.cache.get(identity_key(self.config, self.task_key)))

    def test_silently_failed_create_is_rejected(self):
        """A cache add that claims failure without a stored record blocks delivery."""
        from unittest.mock import patch

        with patch.object(self.cache, "add", return_value=False), patch.object(
            self.cache, "get", return_value=None
        ):
            with self.assertRaisesRegex(RuntimeError, "could not be retained"):
                put_identity(self.config, self.identity)

    def test_corrupt_version_is_rejected(self):
        """Unknown stored schemas cannot be reconstructed as a valid manager."""
        self.cache.set(identity_key(self.config, self.task_key), {"version": 9}, timeout=None)
        with self.assertRaisesRegex(ValueError, "version"):
            get_identity(self.config, self.task_key)

    def test_finished_marker_sets_absolute_expiry_without_refresh(self):
        """Duplicate finish events cannot move a task's retention deadline."""
        put_identity(self.config, self.identity)
        finished = datetime.now(timezone.utc)
        mark_finished(self.config, self.identity, finished_at=finished)
        key = finished_key(self.config, self.task_key, "execution-1")
        marker = self.cache.get(key)
        self.assertEqual(marker["expires_at"], finished + timedelta(seconds=self.config.terminal_result_ttl), "Retention expiry must be absolute from the first finish event")
        mark_finished(self.config, self.identity, finished_at=finished + timedelta(hours=1))
        self.assertEqual(self.cache.get(key), marker, "A duplicate finish event must not refresh the first marker")

    def test_expired_identity_is_unknown(self):
        """An expired logical retention deadline does not imply task success."""
        put_identity(self.config, self.identity)
        self.cache.set(
            finished_key(self.config, self.task_key, "execution-1"),
            {"version": 1, "finished_at": datetime.now(timezone.utc) - timedelta(days=2), "expires_at": datetime.now(timezone.utc) - timedelta(days=1)},
            timeout=None,
        )
        self.assertIsNone(get_identity(self.config, self.task_key), "Expired identity must be reported as unknown")
