import json
import threading
import time
import uuid
from datetime import date
from types import SimpleNamespace

import pytest
from unittest.mock import Mock, patch
from django.conf import settings
from django.test import TestCase, TransactionTestCase, RequestFactory, override_settings
from django.utils import timezone

pytest.importorskip("django_q")
from django_q.cluster import Cluster
from django_q.models import Task

from powercrud.async_manager import AsyncManager
from powercrud.async_dashboard import AsyncDashboardConfig, ModelTrackingAsyncManager
from powercrud.async_hooks import _extract_manager_class_path, task_completion_hook
from powercrud.mixins.async_mixin import AsyncMixin

from tests.async_tests.workers import simple_test_worker
from sample.models import Book, Author, Genre, AsyncTaskRecord
from sample.async_manager import SampleAsyncManager


class AsyncManagerTestMixin:
    def setUp(self):
        super().setUp()
        self.async_manager = AsyncManager()
        self.async_manager.cache.delete(self.async_manager.active_prefix)
        self.async_manager.cache.clear()  # Simple nuclear option

class BaseAsyncQ2Instance(AsyncManagerTestMixin, TransactionTestCase):
    """Base test class with shared cluster setup for async tests."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Start a test cluster
        cls.cluster = Cluster()
        cls.cluster_thread = threading.Thread(target=cls.cluster.start)
        cls.cluster_thread.daemon = True
        cls.cluster_thread.start()
        time.sleep(1)  # Give it a moment to start
   
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'cluster'):
            cls.cluster.stop()
        super().tearDownClass()

class TestSysFunctions(BaseAsyncQ2Instance):

    def test_cache_working(self):
        self.assertTrue(self.async_manager.validate_async_cache()), "Async cache should be valid"

    def test_q2_cluster_working(self):
        self.assertTrue(self.async_manager.validate_async_qcluster()), "Async QCluster should be valid"

    def test_async_working(self):
        """Test if async functionality is working."""
        self.assertTrue(self.async_manager.validate_async_system()), "Async system should be valid"
        

class TestActiveTasks(AsyncManagerTestMixin, TestCase):

    def test_get_active_tasks(self):
        """Test retrieval of active tasks."""
        active_tasks = self.async_manager.get_active_tasks()
        self.assertIsInstance(active_tasks, set), "Expected active tasks to be a set"
        self.assertEqual(len(active_tasks), 0), "Expected no active tasks initially"

    def test_add_and_remove_active_task(self):
        """Test adding and removing an active task."""
        task_id = "test_task_1"
        conflict_ids = {'myapp.TestModel': {1, 2, 3}}
        
        self.async_manager.add_active_task(task_id, conflict_ids)
        
        active_tasks = self.async_manager.get_active_tasks()
        self.assertIn(task_id, active_tasks), "Task should be in active tasks after addition"

        self.async_manager.remove_active_task(task_id)
        active_tasks = self.async_manager.get_active_tasks()
        self.assertNotIn(task_id, active_tasks), "Task should not be in active tasks after removal"

    def test_cleanup_active_tasks(self):
        """Test cleanup of active tasks using patched django-q2 Task queryset."""
        conflict_ids_1 = {'myapp.TestModel': {1, 2}}
        conflict_ids_2 = {'myapp.TestModel': {3, 4}}
        
        task_id_1 = "test_task_1"
        task_id_2 = "test_task_2"
        
        self.async_manager.add_active_task(task_id_1, conflict_ids_1)
        self.async_manager.add_active_task(task_id_2, conflict_ids_2)
        
        # Verify tasks were added
        active_tasks = self.async_manager.get_active_tasks()
        self.assertEqual(len(active_tasks), 2, "Should have 2 active tasks before cleanup")
        self.assertIn(task_id_1, active_tasks)
        self.assertIn(task_id_2, active_tasks)
        
        # Patch the Task queryset used inside AsyncManager.cleanup_active_tasks
        with patch('powercrud.async_manager.Task') as MockTask:
            # Mock chain: Task.objects.filter(...).values_list("id", flat=True) -> [task_id_1, task_id_2]
            MockTask.objects.filter.return_value.values_list.return_value = [task_id_1, task_id_2]
            
            self.async_manager.cleanup_active_tasks()
        
        active_tasks = self.async_manager.get_active_tasks()
        self.assertEqual(len(active_tasks), 0, "All active tasks should be cleaned up")



# =============================================================================
# Task 2: Conflict Detection System Tests
# =============================================================================

class TestConflictDetection(AsyncManagerTestMixin, TestCase):
    """Test core conflict detection functionality using dual-key system."""

    def test_add_conflict_ids_success(self):
        """Test successful atomic reservation of conflict IDs."""
        task_id = "task_123"
        conflict_ids = {
            'myapp.Book': {1, 2, 3},
            'myapp.Author': {10, 20}
        }
        
        # Should successfully acquire all locks
        result = self.async_manager.add_conflict_ids(task_id, conflict_ids)
        self.assertTrue(result, "Should successfully acquire all conflict locks")
        
        # Verify per-object locks exist in cache
        book_lock_1 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:1")
        book_lock_2 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:2")
        author_lock_10 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Author:10")
        
        self.assertEqual(book_lock_1, task_id, "Per-object lock should contain task ID")
        self.assertEqual(book_lock_2, task_id, "Per-object lock should contain task ID")
        self.assertEqual(author_lock_10, task_id, "Per-object lock should contain task ID")
        
        # Verify tracking set exists for cleanup
        tracking_set = self.async_manager.cache.get(f"powercrud:async:conflict:{task_id}")
        self.assertIsInstance(tracking_set, set, "Tracking set should exist")
        self.assertGreater(len(tracking_set), 0, "Tracking set should contain lock keys")

    def test_add_conflict_ids_conflict_detected(self):
        """Test conflict detection when some objects already locked."""
        task_1 = "task_first"
        task_2 = "task_second"
        
        # Task 1 acquires locks on books 1,2,3
        conflict_ids_1 = {'myapp.Book': {1, 2, 3}}
        result_1 = self.async_manager.add_conflict_ids(task_1, conflict_ids_1)
        self.assertTrue(result_1, "First task should acquire locks")
        
        # Task 2 tries to acquire overlapping locks (should fail)
        conflict_ids_2 = {'myapp.Book': {2, 3, 4}}  # 2,3 overlap with task_1
        result_2 = self.async_manager.add_conflict_ids(task_2, conflict_ids_2)
        self.assertFalse(result_2, "Second task should fail due to conflicts")
        
        # Verify first task still has its locks
        book_lock_2 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:2")
        self.assertEqual(book_lock_2, task_1, "Original task should retain its locks")
        
        # Verify second task has no locks (atomic rollback)
        book_lock_4 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:4")
        self.assertIsNone(book_lock_4, "Failed task should have no locks due to rollback")

    def test_check_conflict_no_conflicts(self):
        """Test conflict checking with no existing locks."""
        object_data = {
            'myapp.Book': [1, 2, 3],
            'myapp.Author': [10, 20]
        }
        
        conflicts = self.async_manager.check_conflict(object_data)
        self.assertEqual(len(conflicts), 0, "Should detect no conflicts with empty cache")

    def test_check_conflict_with_conflicts(self):
        """Test conflict detection with existing locks."""
        # Setup: Task 1 locks some objects
        task_1 = "existing_task"
        conflict_ids_1 = {'myapp.Book': {2, 5}}
        self.async_manager.add_conflict_ids(task_1, conflict_ids_1)
        
        # Test: Check for conflicts with overlapping objects
        object_data = {
            'myapp.Book': [1, 2, 3],     # 2 conflicts
            'myapp.Author': [10, 20]     # no conflicts
        }
        
        conflicts = self.async_manager.check_conflict(object_data)
        self.assertEqual(conflicts, {2}, "Should detect conflict on Book ID 2")

    def test_remove_conflict_ids_cleanup(self):
        """Test complete cleanup of per-object locks and tracking sets."""
        task_id = "cleanup_task"
        conflict_ids = {
            'myapp.Book': {1, 2},
            'myapp.Author': {10}
        }
        
        # Setup: Add conflict IDs
        self.async_manager.add_conflict_ids(task_id, conflict_ids)
        
        # Verify locks exist before cleanup
        book_lock = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:1")
        self.assertEqual(book_lock, task_id, "Lock should exist before cleanup")
        
        # Perform cleanup
        self.async_manager.remove_conflict_ids(task_id)
        
        # Verify all per-object locks removed
        book_lock_after = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:1")
        author_lock_after = self.async_manager.cache.get("powercrud:conflict:model:myapp.Author:10")
        self.assertIsNone(book_lock_after, "Per-object lock should be removed")
        self.assertIsNone(author_lock_after, "Per-object lock should be removed")
        
        # Verify tracking set removed
        tracking_set = self.async_manager.cache.get(f"powercrud:async:conflict:{task_id}")
        self.assertIsNone(tracking_set, "Tracking set should be removed")


class TestAtomicReservation(AsyncManagerTestMixin, TestCase):
    """Test atomic behavior and dual-key structure integrity."""

    def test_atomic_reservation_rollback(self):
        """Test that partial conflicts trigger complete rollback."""
        # Setup: Task 1 locks Book:2
        task_1 = "blocker_task"
        self.async_manager.add_conflict_ids(task_1, {'myapp.Book': {2}})
        
        # Test: Task 2 tries to lock Books:1,2,3 (2 conflicts, should rollback all)
        task_2 = "rollback_task"
        conflict_ids_2 = {'myapp.Book': {1, 2, 3}}  # 2 conflicts
        result = self.async_manager.add_conflict_ids(task_2, conflict_ids_2)
        
        self.assertFalse(result, "Should fail due to conflict on Book:2")
        
        # Verify NO locks acquired by task_2 (complete rollback)
        book_1_lock = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:1")
        book_3_lock = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:3")
        self.assertIsNone(book_1_lock, "Book:1 should not be locked (rollback)")
        self.assertIsNone(book_3_lock, "Book:3 should not be locked (rollback)")
        
        # Verify task_1's lock unchanged
        book_2_lock = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:2")
        self.assertEqual(book_2_lock, task_1, "Original lock should be unchanged")

    def test_dual_key_structure(self):
        """Test that both per-object locks and tracking sets are created correctly."""
        task_id = "dual_key_test"
        conflict_ids = {'myapp.Book': {100, 200}}
        
        # Add conflict IDs
        self.async_manager.add_conflict_ids(task_id, conflict_ids)
        
        # Verify per-object locks (type 1 keys)
        lock_100 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:100")
        lock_200 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:200")
        self.assertEqual(lock_100, task_id, "Per-object lock should store task ID")
        self.assertEqual(lock_200, task_id, "Per-object lock should store task ID")
        
        # Verify tracking set (type 2 key)
        tracking_set = self.async_manager.cache.get(f"powercrud:async:conflict:{task_id}")
        expected_lock_keys = {
            "powercrud:conflict:model:myapp.Book:100",
            "powercrud:conflict:model:myapp.Book:200"
        }
        self.assertEqual(tracking_set, expected_lock_keys, "Tracking set should contain lock keys")

    def test_idempotent_cleanup(self):
        """Test that cleanup operations can be called multiple times safely."""
        task_id = "idempotent_test"
        conflict_ids = {'myapp.Book': {1}}
        
        # Setup locks
        self.async_manager.add_conflict_ids(task_id, conflict_ids)
        
        # First cleanup
        self.async_manager.remove_conflict_ids(task_id)
        
        # Second cleanup (should not raise errors)
        try:
            self.async_manager.remove_conflict_ids(task_id)
            cleanup_success = True
        except Exception:
            cleanup_success = False
            
        self.assertTrue(cleanup_success, "Multiple cleanups should be safe (idempotent)")


class TestConcurrentAccess(AsyncManagerTestMixin, TestCase):
    """Test atomic reservation behavior under concurrent access patterns."""

    def test_concurrent_atomic_reservation(self):
        """Test atomic reservation behavior with sequential access simulation."""
        # Simulate concurrent access by rapid sequential attempts
        task_1 = "concurrent_1"
        task_2 = "concurrent_2"
        
        conflict_ids = {'myapp.Book': {42}}
        
        # First task should succeed
        result_1 = self.async_manager.add_conflict_ids(task_1, conflict_ids)
        self.assertTrue(result_1, "First concurrent task should succeed")
        
        # Second task should fail immediately due to cache.add() atomicity
        result_2 = self.async_manager.add_conflict_ids(task_2, conflict_ids)
        self.assertFalse(result_2, "Second concurrent task should fail atomically")
        
        # Verify only first task has the lock
        lock = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:42")
        self.assertEqual(lock, task_1, "Only first task should hold the lock")


class TestCleanupUtilities(AsyncManagerTestMixin, TestCase):

    def _prepare_active_task(self, task_name: str, conflict_ids: dict[str, set[int]]):
        self.async_manager.add_conflict_ids(task_name, conflict_ids)
        self.async_manager.add_active_task(task_name)

    def test_cleanup_completed_tasks_removes_artifacts(self):
        task_name = "cleanup-task-success"
        conflict_ids = {'sample.Book': {42}}
        self._prepare_active_task(task_name, conflict_ids)

        with patch("powercrud.async_manager.Task") as mock_task_model:
            mock_task_model.objects.filter.return_value.first.return_value = SimpleNamespace(
                success=True,
                result={"ok": True},
            )
            summary = self.async_manager.cleanup_completed_tasks()

        self.assertIn(task_name, summary["cleaned"])
        clean_details = summary["cleaned"][task_name]
        self.assertEqual(clean_details["conflict_lock_keys"], 1)
        self.assertEqual(clean_details["progress_entries"], 1)
        self.assertIsNone(
            self.async_manager.cache.get(f"{self.async_manager.conflict_model_prefix}sample.Book:42")
        )
        self.assertNotIn(task_name, self.async_manager.get_active_tasks())

    def test_cleanup_skips_running_tasks(self):
        task_name = "cleanup-task-running"
        conflict_ids = {'sample.Book': {99}}
        self._prepare_active_task(task_name, conflict_ids)

        with patch("powercrud.async_manager.Task") as mock_task_model:
            mock_task_model.objects.filter.return_value.first.return_value = SimpleNamespace(
                success=None,
                started=timezone.now(),
            )
            summary = self.async_manager.cleanup_completed_tasks()

        self.assertIn(task_name, summary["skipped"])
        self.assertIn(task_name, self.async_manager.get_active_tasks())

    def test_cache_add_atomicity(self):
        """Test that cache.add() provides true atomic test-and-set behavior."""
        key = "powercrud:conflict:model:myapp.Book:999"
        
        # First add should succeed
        success_1 = self.async_manager.cache.add(key, "task_1", 300)
        self.assertTrue(success_1, "First cache.add() should succeed")
        
        # Second add should fail (key exists)
        success_2 = self.async_manager.cache.add(key, "task_2", 300)
        self.assertFalse(success_2, "Second cache.add() should fail (atomic)")
        
        # Verify first value unchanged
        value = self.async_manager.cache.get(key)
        self.assertEqual(value, "task_1", "Original value should be unchanged")


# =============================================================================
# Task 3: Launch Pattern & Lifecycle Tests
# =============================================================================

class TestTask3LaunchPattern(AsyncManagerTestMixin, TestCase):
    """Test the Task 3 launch pattern implementation."""

    def test_launch_async_task_success_without_conflicts(self):
        """Test successful launch without conflict detection."""
        def dummy_worker(message, task_key=None, **kwargs):
            return f"Processed: {message}"
        
        # Launch task without conflicts
        with patch('powercrud.async_manager.async_task') as mock_async_task:
            mock_async_task.return_value = "django_q2_task_123"

            with patch.object(self.async_manager, 'async_task_lifecycle') as mock_lifecycle:
                task_key = self.async_manager.launch_async_task(
                    func=dummy_worker,
                    message="test message",
                    user="test_user"
                )

            # Verify task_key is a UUID
            self.assertIsInstance(task_key, str)
            self.assertEqual(len(task_key), 36)  # UUID4 length
            
            # Verify async_task was called with correct parameters
            self.assertTrue(mock_async_task.called)
            call_args = mock_async_task.call_args
            
            # Check function and args
            self.assertEqual(call_args[0][0], dummy_worker)
            self.assertEqual(call_args[1]['message'], "test message")

            # Check hook and task_name
            self.assertEqual(call_args[1]['hook'], "powercrud.async_hooks.task_completion_hook")
            self.assertEqual(call_args[1]['task_name'], task_key)

            # Check task_key passed to worker
            self.assertEqual(call_args[1]['task_key'], task_key)

            mock_lifecycle.assert_called()
            lifecycle_kwargs = mock_lifecycle.call_args.kwargs
            self.assertEqual(lifecycle_kwargs['event'], 'create')
            self.assertEqual(lifecycle_kwargs['task_name'], task_key)
            self.assertEqual(lifecycle_kwargs['status'], self.async_manager.STATUSES.PENDING)
            self.assertEqual(lifecycle_kwargs['message'], 'Task queued')

    def test_launch_async_task_with_conflict_ids_success(self):
        """Test successful launch with conflict reservation."""
        def dummy_worker():
            return "success"
            
        conflict_ids = {'myapp.Book': {1, 2, 3}}
        
        with patch('powercrud.async_manager.async_task') as mock_async_task:
            mock_async_task.return_value = "django_q2_task_456"
            
            task_key = self.async_manager.launch_async_task(
                func=dummy_worker,
                conflict_ids=conflict_ids,
                user="test_user",
                affected_objects=["Book:1", "Book:2", "Book:3"]
            )
            
            # Verify conflict locks were created
            lock_1 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:1")
            lock_2 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:2")
            lock_3 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:3")
            
            self.assertEqual(lock_1, task_key)
            self.assertEqual(lock_2, task_key)
            self.assertEqual(lock_3, task_key)
            
            # Verify tracking set was created
            tracking_set = self.async_manager.cache.get(f"powercrud:async:conflict:{task_key}")
            self.assertIsInstance(tracking_set, set)
            self.assertEqual(len(tracking_set), 3)
            
            # Verify progress key was created
            progress_key = f"powercrud:async:progress:{task_key}"
            progress_value = self.async_manager.cache.get(progress_key)
            self.assertIsNotNone(progress_value)  # Should be empty string initially
            
            # Verify task is in active set
            active_tasks = self.async_manager.get_active_tasks()
            self.assertIn(task_key, active_tasks)

    def test_launch_blocks_on_conflict(self):
        """Test that launch fails BEFORE enqueuing if conflicts exist."""
        def dummy_worker():
            return "should not run"
            
        # Setup: Create existing conflict
        existing_task = "existing_task_123"
        self.async_manager.add_conflict_ids(existing_task, {'myapp.Book': {2, 3}})
        
        # Test: Try to launch with overlapping conflict
        conflict_ids = {'myapp.Book': {1, 2, 4}}  # 2 conflicts with existing
        
        with patch('powercrud.async_manager.async_task') as mock_async_task:
            with self.assertRaises(Exception) as cm:
                self.async_manager.launch_async_task(
                    func=dummy_worker,
                    conflict_ids=conflict_ids
                )
            
            # Verify exception message
            self.assertIn("conflicts detected", str(cm.exception))
            
            # Verify async_task was NOT called (no enqueuing)
            self.assertFalse(mock_async_task.called)
            
            # Verify no locks were created for the failed task
            lock_1 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:1")
            lock_4 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:4")
            self.assertIsNone(lock_1)
            self.assertIsNone(lock_4)
            
            # Verify existing lock is unchanged
            lock_2 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:2")
            self.assertEqual(lock_2, existing_task)

    def test_resolve_manager_from_path(self):
        path = f"{DummyCustomManager.__module__}.{DummyCustomManager.__name__}"
        instance = AsyncManager.resolve_manager(path)
        self.assertIsInstance(instance, DummyCustomManager)

    def test_resolve_manager_with_config(self):
        path = "powercrud.async_dashboard.ModelTrackingAsyncManager"
        instance = AsyncManager.resolve_manager(
            path,
            config={"record_model_path": "sample.AsyncTaskRecord"},
        )
        self.assertIsInstance(instance, ModelTrackingAsyncManager)

    def test_resolve_manager_fallback(self):
        instance = AsyncManager.resolve_manager("non.existent.Manager")
        self.assertIsInstance(instance, AsyncManager)

    def test_launch_rollback_on_enqueue_failure(self):
        """Test cleanup when async_task() fails or returns falsy."""
        def dummy_worker():
            return "should not run"
            
        conflict_ids = {'myapp.Book': {10, 11}}
        
        # Test 1: async_task raises exception
        with patch('powercrud.async_manager.async_task') as mock_async_task:
            mock_async_task.side_effect = Exception("Enqueue failed!")
            
            with self.assertRaises(Exception) as cm:
                self.async_manager.launch_async_task(
                    func=dummy_worker,
                    conflict_ids=conflict_ids
                )
            
            self.assertIn("Failed to enqueue async task", str(cm.exception))
            
            # Verify rollback: no conflict locks
            lock_10 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:10")
            lock_11 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:11")
            self.assertIsNone(lock_10)
            self.assertIsNone(lock_11)
        
        # Test 2: async_task returns falsy
        with patch('powercrud.async_manager.async_task') as mock_async_task:
            mock_async_task.return_value = None  # Falsy return
            
            with self.assertRaises(Exception) as cm:
                self.async_manager.launch_async_task(
                    func=dummy_worker,
                    conflict_ids=conflict_ids
                )
            
            self.assertIn("returned falsy task_id", str(cm.exception))

    def test_task_key_consistency(self):
        """Test task_key flows consistently through all phases."""
        def dummy_worker(data, task_key=None, **kwargs):
            return f"Received task_key: {task_key}"
            
        with patch('powercrud.async_manager.async_task') as mock_async_task:
            mock_async_task.return_value = "django_q2_task_789"
            
            returned_task_key = self.async_manager.launch_async_task(
                func=dummy_worker,
                data="test"
            )
            
            # Verify the same task_key was used for task_name
            call_args = mock_async_task.call_args
            task_name_arg = call_args[1]['task_name']
            task_key_kwarg = call_args[1]['task_key']
            
            self.assertEqual(returned_task_key, task_name_arg)
            self.assertEqual(returned_task_key, task_key_kwarg)
            
            # Verify progress key uses same task_key
            progress_key = f"powercrud:async:progress:{returned_task_key}"
            self.assertIsNotNone(self.async_manager.cache.get(progress_key))


class TestTask3CompletionHooks(AsyncManagerTestMixin, TestCase):
    """Test the completion hook system."""
    
    def test_completion_hook_wired_correctly(self):
        """Test that completion hook string is properly wired."""
        def dummy_worker():
            return "test"
            
        with patch('powercrud.async_manager.async_task') as mock_async_task:
            mock_async_task.return_value = "task_id_hook_test"
            
            self.async_manager.launch_async_task(func=dummy_worker)
            
            # Verify hook parameter was passed correctly
            call_args = mock_async_task.call_args
            hook_arg = call_args[1]['hook']
            
            self.assertEqual(hook_arg, "powercrud.async_hooks.task_completion_hook")

    def test_handle_task_completion_customizable(self):
        """Test that downstream projects can override completion behavior."""
        class CustomAsyncManager(AsyncManager):
            def __init__(self):
                super().__init__()
                self.completion_called = False
                self.completion_task_key = None
                
            def handle_task_completion(self, task, task_key: str):
                self.completion_called = True
                self.completion_task_key = task_key
        
        # Create mock Task object
        mock_task = type('MockTask', (), {
            'name': 'test_task_key_123',
            'id': 'mock_task_id',
            'success': True
        })()
        
        custom_manager = CustomAsyncManager()
        custom_manager.handle_task_completion(mock_task, 'test_task_key_123')
        
        # Verify custom method was called
        self.assertTrue(custom_manager.completion_called)
        self.assertEqual(custom_manager.completion_task_key, 'test_task_key_123')

    def test_lifecycle_events_fired(self):
        """Test that 'create' event is fired with correct metadata."""
        class LifecycleTrackingManager(AsyncManager):
            def __init__(self):
                super().__init__()
                self.lifecycle_events = []

            def async_task_lifecycle(self, event, task_name=None, **kwargs):
                self.lifecycle_events.append({
                    'event': event,
                    'task_id': task_name,
                    'kwargs': kwargs
                })
        
        manager = LifecycleTrackingManager()
        
        with patch('powercrud.async_manager.async_task') as mock_async_task:
            mock_async_task.return_value = "lifecycle_test_task"
            
            task_key = manager.launch_async_task(
                func=lambda: "test",
                user="test_user",
                affected_objects=["obj1", "obj2"]
            )
            
            # Verify 'create' event was fired
            self.assertEqual(len(manager.lifecycle_events), 1)
            
            event = manager.lifecycle_events[0]
            self.assertEqual(event['event'], 'create')
            self.assertEqual(event['task_id'], task_key)
            self.assertEqual(event['kwargs']['user'], 'test_user')
            self.assertEqual(event['kwargs']['affected_objects'], ["obj1", "obj2"])
            self.assertEqual(event['kwargs']['django_q2_task_id'], "lifecycle_test_task")

    def test_handle_task_completion_emits_events(self):
        class TrackingManager(AsyncManager):
            def __init__(self):
                super().__init__()
                self.events = []

            def async_task_lifecycle(self, event, task_name, **kwargs):
                self.events.append((event, task_name, kwargs))

        manager = TrackingManager()
        mock_task = type('MockTask', (), {'success': True, 'result': 'ok'})()

        with patch.object(manager, 'remove_active_task', return_value=True):
            manager.handle_task_completion(mock_task, 'task-123')

        event_names = [call[0] for call in manager.events]
        self.assertIn('complete', event_names)
        self.assertIn('cleanup', event_names)
        complete_kwargs = next(kwargs for event, _, kwargs in manager.events if event == 'complete')
        self.assertEqual(complete_kwargs['status'], manager.STATUSES.SUCCESS)
        self.assertEqual(complete_kwargs['message'], 'Task completed successfully')

    def test_handle_task_completion_failure_event(self):
        class TrackingManager(AsyncManager):
            def __init__(self):
                super().__init__()
                self.events = []

            def async_task_lifecycle(self, event, task_name, **kwargs):
                self.events.append((event, task_name, kwargs))

        manager = TrackingManager()
        mock_task = type('MockTask', (), {'success': False, 'result': 'boom'})()

        with patch.object(manager, 'remove_active_task', return_value=True):
            manager.handle_task_completion(mock_task, 'task-456')

        event_names = [call[0] for call in manager.events]
        self.assertIn('fail', event_names)
        fail_kwargs = next(kwargs for event, _, kwargs in manager.events if event == 'fail')
        self.assertEqual(fail_kwargs['status'], manager.STATUSES.FAILED)
        self.assertIn('boom', fail_kwargs['message'])


class TestTask3ActiveTasksIntegration(AsyncManagerTestMixin, TestCase):
    """Test active tasks integration with new launch pattern."""
    
    def test_add_active_task_no_double_locking(self):
        """Test that add_active_task skips locking when conflict_ids=None."""
        task_key = "no_double_lock_test"
        
        # Pre-create some conflict locks manually
        conflict_ids = {'myapp.Book': {50, 51}}
        self.async_manager.add_conflict_ids(task_key, conflict_ids)
        
        # Now call add_active_task with conflict_ids=None (new launch pattern)
        result = self.async_manager.add_active_task(task_key, conflict_ids=None)
        
        # Should succeed without attempting to re-lock
        self.assertTrue(result)
        
        # Verify task is in active set
        active_tasks = self.async_manager.get_active_tasks()
        self.assertIn(task_key, active_tasks)
        
        # Verify original locks still exist (not modified)
        lock_50 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:50")
        lock_51 = self.async_manager.cache.get("powercrud:conflict:model:myapp.Book:51")
        self.assertEqual(lock_50, task_key)
        self.assertEqual(lock_51, task_key)


class TestTask3ProgressIntegration(AsyncManagerTestMixin, TestCase):
    """Test progress API integration (prep for Task 4)."""
    
    def test_progress_key_lifecycle(self):
        """Test progress key creation, update, retrieval, cleanup."""
        task_key = "progress_test_123"
        
        # Test creation
        progress_key = self.async_manager.create_progress_key(task_key)
        expected_key = f"powercrud:async:progress:{task_key}"
        self.assertEqual(progress_key, expected_key)
        
        # Verify initial empty value
        initial_value = self.async_manager.get_progress(task_key)
        self.assertEqual(initial_value, self.async_manager.STATUSES.PENDING)
        
        # Test update
        self.async_manager.update_progress(task_key, "50% complete")
        updated_value = self.async_manager.get_progress(task_key)
        self.assertEqual(updated_value, "50% complete")
        
        # Test another update
        self.async_manager.update_progress(task_key, "100% complete")
        final_value = self.async_manager.get_progress(task_key)
        self.assertEqual(final_value, "100% complete")
        
        # Test cleanup
        self.async_manager.remove_progress_key(task_key)
        cleaned_value = self.async_manager.get_progress(task_key)
        self.assertIsNone(cleaned_value)

    def test_update_progress_emits_lifecycle(self):
        task_key = "lifecycle_progress"
        self.async_manager.create_progress_key(task_key)

        with patch.object(self.async_manager, 'async_task_lifecycle') as mock_lifecycle:
            self.async_manager.update_progress(task_key, "50% complete")

        mock_lifecycle.assert_called()
        kwargs = mock_lifecycle.call_args.kwargs
        self.assertEqual(kwargs['event'], 'progress')
        self.assertEqual(kwargs['task_name'], task_key)
        self.assertEqual(kwargs['status'], self.async_manager.STATUSES.IN_PROGRESS)
        self.assertEqual(kwargs['message'], "50% complete")

    def test_worker_receives_task_key(self):
        """Test that worker functions receive task_key in kwargs."""
        received_kwargs = {}
        
        def capturing_worker(**kwargs):
            received_kwargs.update(kwargs)
            return "captured"
            
        with patch('powercrud.async_manager.async_task') as mock_async_task:
            mock_async_task.return_value = "worker_kwargs_test"
            
            task_key = self.async_manager.launch_async_task(
                func=capturing_worker,
                test_param="test_value"
            )
            
            # Check that task_key was added to kwargs passed to async_task
            call_args = mock_async_task.call_args
            passed_kwargs = call_args[1]
            
            self.assertEqual(passed_kwargs['task_key'], task_key)
            self.assertEqual(passed_kwargs['test_param'], "test_value")


class TestTask3StatusMethods(AsyncManagerTestMixin, TestCase):
    """Test both blocking and non-blocking status methods."""
    
    def test_status_methods_behavior(self):
        """Test both blocking and non-blocking status methods."""
        task_id = "status_test_task"
        
        # Mock successful task
        mock_success_task = type('MockTask', (), {
            'success': True,
            'id': task_id
        })()
        
        # Mock running task
        mock_running_task = type('MockTask', (), {
            'success': None,
            'id': task_id
        })()
        
        # Test blocking method with successful task
        with patch('powercrud.async_manager.fetch') as mock_fetch:
            mock_fetch.return_value = mock_success_task
            
            status = self.async_manager.get_task_status(task_id)
            self.assertEqual(status, 'success')
            
            # Verify it was called with wait=300 (blocking)
            mock_fetch.assert_called_with(task_id, wait=300)
        
        # Test non-blocking method with running task
        with patch('powercrud.async_manager.fetch') as mock_fetch:
            mock_fetch.return_value = mock_running_task
            
            status = self.async_manager.get_task_status_nowait(task_id)
            self.assertEqual(status, 'in_progress')
            
            # Verify it was called with wait=0 (non-blocking)
            mock_fetch.assert_called_with(task_id, wait=0)
        
        # Test no task found
        with patch('powercrud.async_manager.fetch') as mock_fetch:
            mock_fetch.return_value = None
            
            status_blocking = self.async_manager.get_task_status(task_id)
            status_nowait = self.async_manager.get_task_status_nowait(task_id)
            
            self.assertIsNone(status_blocking)
            self.assertIsNone(status_nowait)


class TestTask3EndToEndIntegration(BaseAsyncQ2Instance):
    """Test complete end-to-end launch → execute → cleanup cycle with real qcluster."""
    
    def test_e2e_launch_execute_cleanup_cycle(self):
        """Test complete lifecycle with actual django-q2 execution."""
        # Execute worker synchronously by patching async_task call
        progress_messages = []

        def run_sync(func, *args, **kwargs):
            result = func(*args, **kwargs)
            progress_messages.append(self.async_manager.get_progress(kwargs['task_key']))
            return "mock_django_q_task_id"

        with patch('powercrud.async_manager.async_task', side_effect=run_sync):
            task_key = self.async_manager.launch_async_task(
                func=simple_test_worker,
                message="E2E Test Message",
                user="e2e_test_user"
            )
        
        # Verify task_key was returned
        self.assertIsInstance(task_key, str)
        self.assertEqual(len(task_key), 36)  # UUID length
        
        # Verify task is in active set
        active_tasks = self.async_manager.get_active_tasks()
        self.assertIn(task_key, active_tasks)
        
        # The synchronous worker run should have produced progress updates
        self.assertTrue(progress_messages, "Worker should update progress synchronously")
        final_progress = progress_messages[-1]
        self.assertIn("Processing completed", final_progress)

    def test_hook_import_path_works(self):
        """Test that the completion hook import path is valid."""
        # Test that we can import the hook function
        from powercrud.async_hooks import task_completion_hook
        
        # Verify it's callable
        self.assertTrue(callable(task_completion_hook))
        
        # Create a mock Task and verify hook doesn't crash
        mock_task = type('MockTask', (), {
            'name': 'test_hook_task',
            'id': 'mock_id',
            'success': True
        })()
        
        # This should not raise an exception
        try:
            task_completion_hook(mock_task)
            hook_callable = True
        except Exception as e:
            hook_callable = False
            print(f"Hook failed: {e}")
        
        self.assertTrue(hook_callable, "Completion hook should be callable without errors")


# =============================================================================
# Task 4: Progress Polling Tests
# =============================================================================

class TestProgressPolling(AsyncManagerTestMixin, TestCase):
    """Test progress polling classmethods (as_view and get_url)."""
    
    def setUp(self):
        super().setUp()
        from django.test import RequestFactory
        self.factory = RequestFactory()
        self.task_name = str(uuid.uuid4())
        self.progress_data = '{"percent": 50, "message": "Processing books"}'
    
    def test_as_view_missing_task_name(self):
        """Test as_view returns 400 when task_name is missing."""
        view = AsyncManager.as_view()
        request = self.factory.get('/progress/')
        response = view(request)
        
        self.assertEqual(response.status_code, 400)
        # JsonResponse doesn't have .json() method, need to parse content
        import json
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_data, {'error': 'task_name required'})
    
    def test_as_view_with_progress_data(self):
        """Test as_view returns progress when available."""
        # Setup progress data
        manager = AsyncManager()
        manager.update_progress(self.task_name, self.progress_data)
        
        view = AsyncManager.as_view()
        request = self.factory.get(f'/progress/?task_name={self.task_name}')
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'in_progress')
        self.assertEqual(data['progress'], self.progress_data)
        self.assertNotIn('poll_interval', data)
    
    def test_as_view_no_progress_fallback_status(self):
        """Test as_view falls back to task status when no progress."""
        # Mock get_task_status_nowait to return 'success'
        with patch.object(AsyncManager, 'get_task_status_nowait', return_value='success'):
            view = AsyncManager.as_view()
            request = self.factory.get(f'/progress/?task_name={self.task_name}')
            response = view(request)
        
        self.assertEqual(response.status_code, 286)
        import json
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['progress'], 'Completed successfully!')
        self.assertNotIn('poll_interval', data)
    
    def test_as_view_unknown_status(self):
        """When cache indicates completion but status lookup returns None, treat as success."""
        with patch.object(AsyncManager, 'get_task_status_nowait', return_value=None):
            view = AsyncManager.as_view()
            request = self.factory.get(f'/progress/?task_name={self.task_name}')
            response = view(request)
        
        self.assertEqual(response.status_code, 286)
        import json
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['progress'], 'Completed successfully!')
    
    def test_get_url_returns_path(self):
        """Test get_url returns proper path object."""
        path_obj = AsyncManager.get_url()
        
        from django.urls import URLPattern
        self.assertIsInstance(path_obj, URLPattern)
        self.assertEqual(str(path_obj.pattern), 'powercrud/async/progress/')
        self.assertEqual(path_obj.name, 'powercrud_async_progress')
        self.assertTrue(callable(path_obj.callback))

    def test_get_urlpatterns_returns_resolver(self):
        """Ensure get_urlpatterns provides a namespaced include."""
        resolver = AsyncManager.get_urlpatterns()

        from django.urls import URLResolver
        self.assertIsInstance(resolver, URLResolver)
        self.assertEqual(str(resolver.pattern), 'powercrud/')
        self.assertEqual(resolver.namespace, 'powercrud')
    
    def test_as_view_error_handling(self):
        """Test as_view handles internal errors gracefully."""
        # Mock the get_progress method on the AsyncManager class
        with patch.object(AsyncManager, 'get_progress', side_effect=Exception('Test error')):
            view = AsyncManager.as_view()
            request = self.factory.get(f'/progress/?task_name={self.task_name}')
            response = view(request)
        
        self.assertEqual(response.status_code, 500)
        import json
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertIn('error', response_data)
    
    def test_progress_polling_with_manual_data(self):
        """Test end-to-end polling flow with real progress update."""
        # Launch a mock task to get task_id
        def dummy_worker(task_key, **kwargs):
            manager = AsyncManager()
            manager.update_progress(task_key, self.progress_data)
            return "done"
        
        with patch('powercrud.async_manager.async_task') as mock_async:
            mock_async.return_value = "mock_task_id"
            task_id = self.async_manager.launch_async_task(func=dummy_worker)
        
        # Since we're mocking async_task, the dummy_worker doesn't actually run
        # So we need to manually set the progress data for this test
        self.async_manager.update_progress(task_id, self.progress_data)
        
        # Now test the view with this task_id
        view = AsyncManager.as_view()
        request = self.factory.get(f'/progress/?task_name={task_id}')
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'in_progress')
        self.assertEqual(data['progress'], self.progress_data)
    
    def test_as_view_post_method(self):
        """Test as_view works with POST requests (for hx-vals)."""
        manager = AsyncManager()
        manager.update_progress(self.task_name, self.progress_data)
        view = AsyncManager.as_view()
        request = self.factory.post('/progress/', {'task_name': self.task_name})
        response = view(request)
        
        self.assertEqual(response.status_code, 200)  # Should work with POST data
        import json
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_data['task_name'], self.task_name)
    
    def test_poll_interval_adaptive(self):
        """Test adaptive poll_interval based on status."""
        # Test in_progress (1000ms)
        manager = AsyncManager()
        manager.update_progress(self.task_name, self.progress_data)
        view = AsyncManager.as_view()
        request = self.factory.get(f'/progress/?task_name={self.task_name}')
        response = view(request)
        import json
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertNotIn('poll_interval', response_data)
        
        # Test pending state (should continue polling)
        manager.remove_progress_key(self.task_name)
        manager.create_progress_key(self.task_name)
        request = self.factory.get(f'/progress/?task_name={self.task_name}')
        response = view(request)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_data['status'], 'unknown')
        self.assertIn('poll_interval', response_data)
        self.assertEqual(response_data['poll_interval'], 1000)
        
        # Test success (terminal state)
        manager.remove_progress_key(self.task_name)
        with patch.object(AsyncManager, 'get_task_status_nowait', return_value='success'):
            response = view(request)
            response_data = json.loads(response.content.decode('utf-8'))
            self.assertEqual(response_data['status'], 'success')
            self.assertEqual(response.status_code, 286)
            self.assertNotIn('poll_interval', response_data)
        
        # Test unknown (1000ms) - progress data still cleared
        with patch.object(AsyncManager, 'get_task_status_nowait', return_value=None):
            response = view(request)
            response_data = json.loads(response.content.decode('utf-8'))
            self.assertNotIn('poll_interval', response_data)


class DummyConflictView(AsyncMixin):
    model = Book
    templates_path = "powercrud/daisyUI"
    bulk_async = True
    bulk_async_conflict_checking = True
    bulk_min_async_records = 1
    namespace = "sample"
    pk_url_kwarg = "pk"
    bulk_async_backend = "q2"


class TestSingleRecordConflicts(TestCase):
    """Task 6: ensure single-record operations respect async locks."""

    def setUp(self):
        self.manager = AsyncManager()
        self.view = DummyConflictView()
        self.author = Author.objects.create(name="Author Name")
        self.genre = Genre.objects.create(name="Genre Name")

    def _make_book(self, title):
        book = Book.objects.create(
            title=title,
            author=self.author,
            published_date=date(2020, 1, 1),
            bestseller=False,
            isbn=str(uuid.uuid4())[:17],
            pages=10,
        )
        book.genres.add(self.genre)
        return book

    def test_check_for_conflicts_single_pk(self):
        book = self._make_book("Async Test")
        task_name = "conflict_task"
        model_name = f"{book._meta.app_label}.{book._meta.model_name}"
        self.manager.add_conflict_ids(task_name, {model_name: {book.pk}})

        self.assertTrue(self.view._check_for_conflicts(selected_ids=[book.pk]))

    def test_render_conflict_response_htmx_update(self):
        book = self._make_book("HTMX Conflict")
        request = RequestFactory().get("/book/1/edit/", HTTP_HX_REQUEST="true")
        request.htmx = True
        self.view.object = book
        response = self.view._render_conflict_response(request, book.pk, "update")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Edit Conflict", content)
        self.assertIn("Please try again later", content)

    def test_render_conflict_response_htmx_delete(self):
        book = self._make_book("HTMX Delete Conflict")
        request = RequestFactory().get("/book/1/delete/", HTTP_HX_REQUEST="true")
        request.htmx = True
        self.view.object = book
        response = self.view._render_conflict_response(request, book.pk, "delete")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Edit Conflict", content)
        self.assertIn("Please try again later", content)


class TestAsyncHookHelpers(TestCase):

    def test_extract_manager_class_from_dict_kwargs(self):
        task = SimpleNamespace(name="dummy", kwargs={'manager_class': 'sample.async_manager.SampleAsyncManager'})
        path = _extract_manager_class_path(task)
        self.assertEqual(path, 'sample.async_manager.SampleAsyncManager')

    def test_extract_manager_class_from_serialized_kwargs(self):
        json_payload = '{"manager_class": "sample.async_manager.SampleAsyncManager"}'
        task = SimpleNamespace(name="dummy", kwargs=json_payload)
        path = _extract_manager_class_path(task)
        self.assertEqual(path, 'sample.async_manager.SampleAsyncManager')

    def test_extract_manager_class_returns_none_for_unparseable_payload(self):
        task = SimpleNamespace(name="dummy", kwargs="not valid json")
        path = _extract_manager_class_path(task)
        self.assertIsNone(path)

    @patch("powercrud.async_manager.AsyncManager")
    def test_task_completion_hook_uses_resolved_manager(self, mock_async_manager):
        mock_manager = Mock()
        mock_async_manager.resolve_manager.return_value = mock_manager

        task = SimpleNamespace(
            name="task123",
            kwargs={'manager_class': 'sample.async_manager.SampleAsyncManager'}
        )

        task_completion_hook(task)

        mock_async_manager.resolve_manager.assert_called_once_with('sample.async_manager.SampleAsyncManager', config=None)
        mock_manager.handle_task_completion.assert_called_once_with(task, "task123")

    @patch("powercrud.async_manager.AsyncManager")
    def test_task_completion_hook_handles_missing_manager(self, mock_async_manager):
        mock_manager = Mock()
        mock_async_manager.resolve_manager.return_value = mock_manager

        task = SimpleNamespace(name="task456", kwargs=None)

        task_completion_hook(task)

        mock_async_manager.resolve_manager.assert_called_once_with(None, config=None)
        mock_manager.handle_task_completion.assert_called_once_with(task, "task456")

    @patch("powercrud.async_manager.AsyncManager")
    def test_task_completion_hook_passes_manager_config(self, mock_async_manager):
        mock_manager = Mock()
        mock_async_manager.resolve_manager.return_value = mock_manager

        cfg = {"record_model_path": "sample.AsyncTaskRecord"}
        task = SimpleNamespace(
            name="task789",
            kwargs={
                'manager_class': 'powercrud.async_dashboard.ModelTrackingAsyncManager',
                'manager_config': cfg,
            }
        )

        task_completion_hook(task)

        mock_async_manager.resolve_manager.assert_called_once_with(
            'powercrud.async_dashboard.ModelTrackingAsyncManager',
            config=cfg,
        )
        mock_manager.handle_task_completion.assert_called_once_with(task, "task789")


class TestModelTrackingAsyncManager(TestCase):

    def setUp(self):
        AsyncTaskRecord.objects.all().delete()
        self.manager = ModelTrackingAsyncManager(
            config=AsyncDashboardConfig(record_model_path="sample.AsyncTaskRecord"),
        )

    def test_create_event_initialises_dashboard_record(self):
        self.manager.async_task_lifecycle(
            event="create",
            task_name="dash-create",
            user=SimpleNamespace(username="sarah"),
            affected_objects=["Book:1"],
            task_kwargs={"example": True},
            task_args=["arg1"],
            message="Task queued",
            status=AsyncTaskRecord.STATUS.PENDING,
        )

        record = AsyncTaskRecord.objects.get(task_name="dash-create")
        self.assertEqual(record.status, AsyncTaskRecord.STATUS.PENDING)
        self.assertEqual(record.user_label, "sarah")
        self.assertIn("Book:1", record.affected_objects)
        stored_kwargs = record.task_kwargs
        if isinstance(stored_kwargs, str):
            stored_kwargs = json.loads(stored_kwargs)
        self.assertEqual(stored_kwargs, {"example": True})
        self.assertEqual(record.task_args, ["arg1"])

    def test_progress_event_updates_progress_without_overwriting_message(self):
        self.manager.async_task_lifecycle(
            event="create",
            task_name="dash-progress",
            message="Queued",
            status=AsyncTaskRecord.STATUS.PENDING,
        )
        self.manager.async_task_lifecycle(
            event="progress",
            task_name="dash-progress",
            message="Working",  # should not clobber existing message
            progress_payload="50%",
        )

        record = AsyncTaskRecord.objects.get(task_name="dash-progress")
        self.assertEqual(record.status, AsyncTaskRecord.STATUS.IN_PROGRESS)
        self.assertEqual(record.progress_payload, "50%")
        self.assertEqual(record.message, "Queued")

    def test_completion_event_sets_result_and_timestamp(self):
        self.manager.async_task_lifecycle(event="create", task_name="dash-complete")
        ts = timezone.now()
        self.manager.async_task_lifecycle(
            event="complete",
            task_name="dash-complete",
            result={"count": 3},
            timestamp=ts,
        )

        record = AsyncTaskRecord.objects.get(task_name="dash-complete")
        self.assertEqual(record.status, AsyncTaskRecord.STATUS.SUCCESS)
        stored_result = record.result_payload
        if isinstance(stored_result, str):
            stored_result = json.loads(stored_result)
        self.assertEqual(stored_result, {"count": 3})
        self.assertEqual(record.completed_at, ts)

    def test_fail_event_marks_failure_and_preserves_timestamp(self):
        self.manager.async_task_lifecycle(event="create", task_name="dash-fail")
        ts = timezone.now()
        self.manager.async_task_lifecycle(
            event="fail",
            task_name="dash-fail",
            result="boom",
            message="Exploded",
            timestamp=ts,
        )

        record = AsyncTaskRecord.objects.get(task_name="dash-fail")
        self.assertEqual(record.status, AsyncTaskRecord.STATUS.FAILED)
        self.assertEqual(record.result_payload, "boom")
        self.assertEqual(record.failed_at, ts)
        self.assertEqual(record.message, "Exploded")

    def test_cleanup_event_marks_flag_without_status_regression(self):
        self.manager.async_task_lifecycle(event="create", task_name="dash-cleanup")
        self.manager.async_task_lifecycle(event="complete", task_name="dash-cleanup")
        self.manager.async_task_lifecycle(event="cleanup", task_name="dash-cleanup")

        record = AsyncTaskRecord.objects.get(task_name="dash-cleanup")
        self.assertTrue(record.cleaned_up)
        self.assertEqual(record.status, AsyncTaskRecord.STATUS.SUCCESS)

    def test_custom_formatters_are_applied(self):
        def format_user(user):
            return getattr(user, "email", "")

        def format_affected(objs):
            return "|".join(str(x) for x in objs) if objs else ""

        manager = ModelTrackingAsyncManager(
            config=AsyncDashboardConfig(
                record_model_path="sample.AsyncTaskRecord",
                format_user=format_user,
                format_affected=format_affected,
                format_payload=lambda payload: {"wrapped": payload},
            )
        )
        payload = {"key": "value"}
        manager.async_task_lifecycle(
            event="create",
            task_name="dash-format",
            user=SimpleNamespace(email="user@example.com"),
            affected_objects=["A", "B"],
            task_kwargs=payload,
        )

        record = AsyncTaskRecord.objects.get(task_name="dash-format")
        self.assertEqual(record.user_label, "user@example.com")
        self.assertEqual(record.affected_objects, "A|B")
        self.assertEqual(record.task_kwargs, {"wrapped": payload})


class DummyCustomManager(AsyncManager):
    pass


class AsyncMixinManagerResolutionTests(TestCase):
    class DummyView(AsyncMixin):
        bulk_async = True
        bulk_min_async_records = 1
        bulk_async_backend = "q2"
        bulk_async_notification = "none"
        bulk_async_conflict_checking = True
        templates_path = "sample/daisyUI"
        model = Book

    def test_direct_manager_class_attribute(self):
        view = self.DummyView()
        view.async_manager_class = SampleAsyncManager
        view.async_manager_class_path = None

        manager_cls = view.get_async_manager_class()
        self.assertIs(manager_cls, SampleAsyncManager)
        self.assertEqual(
            view.get_async_manager_class_path(),
            "sample.async_manager.SampleAsyncManager",
        )

    def test_manager_class_path_attribute(self):
        view = self.DummyView()
        view.async_manager_class = None
        view.async_manager_class_path = "powercrud.async_dashboard.ModelTrackingAsyncManager"

        manager_cls = view.get_async_manager_class()
        from powercrud.async_dashboard import ModelTrackingAsyncManager

        self.assertIs(manager_cls, ModelTrackingAsyncManager)
        self.assertEqual(
            view.get_async_manager_class_path(),
            "powercrud.async_dashboard.ModelTrackingAsyncManager",
        )

    def test_view_supplies_manager_config(self):
        view = self.DummyView()
        view.async_manager_class = None
        view.async_manager_class_path = "powercrud.async_dashboard.ModelTrackingAsyncManager"
        view.async_manager_config = {"record_model_path": "sample.AsyncTaskRecord"}

        manager = view.get_async_manager()
        self.assertIsInstance(manager, ModelTrackingAsyncManager)
        self.assertEqual(manager._config.record_model_path, "sample.AsyncTaskRecord")

    @override_settings(
        POWERCRUD_SETTINGS={
            "ASYNC_MANAGER_DEFAULT": {
                "manager_class": "sample.async_manager.SampleAsyncManager",
            }
        }
    )
    def test_settings_default_manager_class(self):
        view = self.DummyView()
        view.async_manager_class = None
        view.async_manager_class_path = None

        manager_cls = view.get_async_manager_class()
        self.assertIs(manager_cls, SampleAsyncManager)
        self.assertEqual(
            view.get_async_manager_class_path(),
            "sample.async_manager.SampleAsyncManager",
        )

    @override_settings(
        POWERCRUD_SETTINGS={
            "ASYNC_MANAGER_DEFAULT": {
                "manager_class": "powercrud.async_dashboard.ModelTrackingAsyncManager",
                "config": {"record_model_path": "sample.AsyncTaskRecord"},
            }
        }
    )
    def test_settings_default_manager_config(self):
        view = self.DummyView()
        view.async_manager_class = None
        view.async_manager_class_path = None

        manager = view.get_async_manager()
        self.assertIsInstance(manager, ModelTrackingAsyncManager)
        self.assertEqual(manager._config.record_model_path, "sample.AsyncTaskRecord")

        self.assertEqual(
            view.get_async_manager_class_path(),
            "powercrud.async_dashboard.ModelTrackingAsyncManager",
        )
