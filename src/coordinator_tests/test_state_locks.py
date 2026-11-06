from unittest.mock import patch

from django.test import TestCase

from powercrud.async_manager import AsyncManager


class AsyncManagerTestMixin:
    """Clear only the coordinator cache before each manager test."""

    def setUp(self):
        super().setUp()
        self.async_manager = AsyncManager()
        self.async_manager.cache.clear()


class TestActiveTasks(AsyncManagerTestMixin, TestCase):
    def test_get_active_tasks(self):
        """Test retrieval of active tasks."""
        active_tasks = self.async_manager.get_active_tasks()
        self.assertIsInstance(active_tasks, set, "Expected active tasks to be a set")
        self.assertEqual(len(active_tasks), 0, "Expected no active tasks initially")

    def test_add_and_remove_active_task(self):
        """Test adding and removing an active task."""
        task_id = "test_task_1"
        conflict_ids = {"myapp.TestModel": {1, 2, 3}}

        self.async_manager.add_active_task(task_id, conflict_ids)

        active_tasks = self.async_manager.get_active_tasks()
        self.assertIn(task_id, active_tasks, "Task should be in active tasks after addition")

        self.async_manager.remove_active_task(task_id)
        active_tasks = self.async_manager.get_active_tasks()
        self.assertNotIn(task_id, active_tasks, "Task should not be in active tasks after removal")

    def test_cleanup_active_tasks(self):
        """Test cleanup of active tasks using patched django-q2 Task queryset."""
        task_id_1 = "test_task_1"
        task_id_2 = "test_task_2"
        self.async_manager.add_active_task(task_id_1, {"myapp.TestModel": {1, 2}})
        self.async_manager.add_active_task(task_id_2, {"myapp.TestModel": {3, 4}})
        active_tasks = self.async_manager.get_active_tasks()
        self.assertEqual(len(active_tasks), 2, "Should have 2 active tasks before cleanup")
        self.assertIn(task_id_1, active_tasks)
        self.assertIn(task_id_2, active_tasks)

        with patch("powercrud.async_manager.Task") as mock_task:
            mock_task.objects.filter.return_value.values_list.return_value = [task_id_1, task_id_2]
            self.async_manager.cleanup_active_tasks()

        active_tasks = self.async_manager.get_active_tasks()
        self.assertEqual(len(active_tasks), 0, "All active tasks should be cleaned up")


class TestConflictDetection(AsyncManagerTestMixin, TestCase):
    """Test core conflict detection functionality using dual-key system."""

    def test_add_conflict_ids_success(self):
        """Test successful atomic reservation of conflict IDs."""
        task_id = "task_123"
        result = self.async_manager.add_conflict_ids(
            task_id, {"myapp.Book": {1, 2, 3}, "myapp.Author": {10, 20}}
        )
        self.assertTrue(result, "Should successfully acquire all conflict locks")
        self.assertEqual(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:1"),
            task_id,
            "Per-object lock should contain task ID",
        )
        self.assertEqual(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:2"),
            task_id,
            "Per-object lock should contain task ID",
        )
        self.assertEqual(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Author:10"),
            task_id,
            "Per-object lock should contain task ID",
        )
        tracking_set = self.async_manager.cache.get(f"powercrud:async:conflict:{task_id}")
        self.assertIsInstance(tracking_set, set, "Tracking set should exist")
        self.assertGreater(len(tracking_set), 0, "Tracking set should contain lock keys")

    def test_add_conflict_ids_conflict_detected(self):
        """Test conflict detection when some objects already locked."""
        task_1 = "task_first"
        task_2 = "task_second"
        self.assertTrue(
            self.async_manager.add_conflict_ids(task_1, {"myapp.Book": {1, 2, 3}}),
            "First task should acquire locks",
        )
        self.assertFalse(
            self.async_manager.add_conflict_ids(task_2, {"myapp.Book": {2, 3, 4}}),
            "Second task should fail due to conflicts",
        )
        self.assertEqual(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:2"),
            task_1,
            "Original task should retain its locks",
        )
        self.assertIsNone(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:4"),
            "Failed task should have no locks due to rollback",
        )

    def test_check_conflict_no_conflicts(self):
        """Test conflict checking with no existing locks."""
        conflicts = self.async_manager.check_conflict(
            {"myapp.Book": [1, 2, 3], "myapp.Author": [10, 20]}
        )
        self.assertEqual(len(conflicts), 0, "Should detect no conflicts with empty cache")

    def test_check_conflict_with_conflicts(self):
        """Test conflict detection with existing locks."""
        self.async_manager.add_conflict_ids("existing_task", {"myapp.Book": {2, 5}})
        conflicts = self.async_manager.check_conflict(
            {"myapp.Book": [1, 2, 3], "myapp.Author": [10, 20]}
        )
        self.assertEqual(conflicts, {2}, "Should detect conflict on Book ID 2")

    def test_remove_conflict_ids_cleanup(self):
        """Test complete cleanup of per-object locks and tracking sets."""
        task_id = "cleanup_task"
        self.async_manager.add_conflict_ids(
            task_id, {"myapp.Book": {1, 2}, "myapp.Author": {10}}
        )
        self.assertEqual(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:1"),
            task_id,
            "Lock should exist before cleanup",
        )
        self.async_manager.remove_conflict_ids(task_id)
        self.assertIsNone(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:1"),
            "Per-object lock should be removed",
        )
        self.assertIsNone(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Author:10"),
            "Per-object lock should be removed",
        )
        self.assertIsNone(
            self.async_manager.cache.get(f"powercrud:async:conflict:{task_id}"),
            "Tracking set should be removed",
        )


class TestAtomicReservation(AsyncManagerTestMixin, TestCase):
    """Test atomic behavior and dual-key structure integrity."""

    def test_atomic_reservation_rollback(self):
        """Test that partial conflicts trigger complete rollback."""
        task_1 = "blocker_task"
        self.async_manager.add_conflict_ids(task_1, {"myapp.Book": {2}})
        task_2 = "rollback_task"
        result = self.async_manager.add_conflict_ids(task_2, {"myapp.Book": {1, 2, 3}})
        self.assertFalse(result, "Should fail due to conflict on Book:2")
        self.assertIsNone(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:1"),
            "Book:1 should not be locked (rollback)",
        )
        self.assertIsNone(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:3"),
            "Book:3 should not be locked (rollback)",
        )
        self.assertEqual(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:2"),
            task_1,
            "Original lock should be unchanged",
        )

    def test_dual_key_structure(self):
        """Test that both per-object locks and tracking sets are created correctly."""
        task_id = "dual_key_test"
        self.async_manager.add_conflict_ids(task_id, {"myapp.Book": {100, 200}})
        self.assertEqual(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:100"),
            task_id,
            "Per-object lock should store task ID",
        )
        self.assertEqual(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:200"),
            task_id,
            "Per-object lock should store task ID",
        )
        expected_lock_keys = {
            "powercrud:conflict:model:myapp.Book:100",
            "powercrud:conflict:model:myapp.Book:200",
        }
        self.assertEqual(
            self.async_manager.cache.get(f"powercrud:async:conflict:{task_id}"),
            expected_lock_keys,
            "Tracking set should contain lock keys",
        )

    def test_idempotent_cleanup(self):
        """Test that cleanup operations can be called multiple times safely."""
        task_id = "idempotent_test"
        self.async_manager.add_conflict_ids(task_id, {"myapp.Book": {1}})
        self.async_manager.remove_conflict_ids(task_id)
        try:
            self.async_manager.remove_conflict_ids(task_id)
            cleanup_success = True
        except Exception:
            cleanup_success = False
        self.assertTrue(cleanup_success, "Multiple cleanups should be safe (idempotent)")


class TestConcurrentAccess(AsyncManagerTestMixin, TestCase):
    """Test atomic reservation behavior under sequential access simulation."""

    def test_concurrent_atomic_reservation(self):
        """Preserve the existing rapid sequential reservation check."""
        conflict_ids = {"myapp.Book": {42}}
        self.assertTrue(
            self.async_manager.add_conflict_ids("concurrent_1", conflict_ids),
            "First concurrent task should succeed",
        )
        self.assertFalse(
            self.async_manager.add_conflict_ids("concurrent_2", conflict_ids),
            "Second concurrent task should fail atomically",
        )
        self.assertEqual(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:42"),
            "concurrent_1",
            "Only first task should hold the lock",
        )


class TestCleanupCacheAdd(AsyncManagerTestMixin, TestCase):
    def test_cache_add_atomicity(self):
        """Test that cache.add() provides true test-and-set behavior."""
        key = "powercrud:conflict:model:myapp.Book:999"
        self.assertTrue(self.async_manager.cache.add(key, "task_1", 300), "First cache.add() should succeed")
        self.assertFalse(self.async_manager.cache.add(key, "task_2", 300), "Second cache.add() should fail")
        self.assertEqual(self.async_manager.cache.get(key), "task_1", "Original value should be unchanged")


class TestActiveTaskIntegration(AsyncManagerTestMixin, TestCase):
    def test_add_active_task_no_double_locking(self):
        """Preserve the launch-path check that avoids locking twice."""
        task_key = "no_double_lock_test"
        self.async_manager.add_conflict_ids(task_key, {"myapp.Book": {50, 51}})
        result = self.async_manager.add_active_task(task_key, conflict_ids=None)
        self.assertTrue(result, "Active task should register without reacquiring locks")
        active_tasks = self.async_manager.get_active_tasks()
        self.assertIn(task_key, active_tasks, "Task should be registered as active")
        self.assertEqual(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:50"),
            task_key,
            "Original lock should remain unchanged",
        )
        self.assertEqual(
            self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:51"),
            task_key,
            "Original lock should remain unchanged",
        )
