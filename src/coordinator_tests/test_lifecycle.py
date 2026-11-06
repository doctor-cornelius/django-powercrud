"""Relocated reusable q2 lifecycle, progress, cleanup, and tracking checks."""

import json
import uuid
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase
from django.utils import timezone

from powercrud.async_manager import AsyncManager
from powercrud.async_dashboard import AsyncDashboardConfig, ModelTrackingAsyncManager
from powercrud.async_hooks import _extract_manager_class_path, task_completion_hook
from coordinator_tests.testapp.models import AsyncTaskRecord
from coordinator_tests.workers import simple_test_worker


class AsyncManagerTestMixin:
    """Clear only the isolated coordination cache around each manager test."""

    def setUp(self):
        super().setUp()
        self.async_manager = AsyncManager()
        self.async_manager.cache.clear()


class DummyCustomManager(AsyncManager):
    """Suite-owned custom manager used to qualify manager reconstruction."""

    pass


class TestSysFunctions(AsyncManagerTestMixin, TestCase):
    def test_cache_working(self):
        (
            self.assertTrue(self.async_manager.validate_async_cache()),
            "Async cache should be valid",
        )

    def test_q2_cluster_working(self):
        (
            self.assertTrue(self.async_manager.validate_async_qcluster()),
            "Async QCluster should be valid",
        )

    def test_async_working(self):
        """Test if async functionality is working."""
        (
            self.assertTrue(self.async_manager.validate_async_system()),
            "Async system should be valid",
        )

class TestCleanupUtilities(AsyncManagerTestMixin, TestCase):
    def _prepare_active_task(self, task_name: str, conflict_ids: dict[str, set[int]]):
        self.async_manager.add_conflict_ids(task_name, conflict_ids)
        self.async_manager.add_active_task(task_name)

    def test_cleanup_completed_tasks_removes_artifacts(self):
        task_name = "cleanup-task-success"
        conflict_ids = {"coordinator_testapp.Book": {42}}
        self._prepare_active_task(task_name, conflict_ids)

        with patch("powercrud.async_manager.Task") as mock_task_model:
            mock_task_model.objects.filter.return_value.first.return_value = (
                SimpleNamespace(
                    success=True,
                    result={"ok": True},
                )
            )
            summary = self.async_manager.cleanup_completed_tasks()

        self.assertIn(task_name, summary["cleaned"])
        clean_details = summary["cleaned"][task_name]
        self.assertEqual(clean_details["conflict_lock_keys"], 1)
        self.assertEqual(clean_details["progress_entries"], 1)
        self.assertIsNone(
            self.async_manager.cache.get(
                f"{self.async_manager.conflict_model_prefix}coordinator_testapp.Book:42"
            )
        )
        self.assertNotIn(task_name, self.async_manager.get_active_tasks())

    def test_cleanup_skips_running_tasks(self):
        task_name = "cleanup-task-running"
        conflict_ids = {"coordinator_testapp.Book": {99}}
        self._prepare_active_task(task_name, conflict_ids)

        with patch("powercrud.async_manager.Task") as mock_task_model:
            mock_task_model.objects.filter.return_value.first.return_value = (
                SimpleNamespace(
                    success=None,
                    started=timezone.now(),
                )
            )
            summary = self.async_manager.cleanup_completed_tasks()

        self.assertIn(task_name, summary["skipped"])
        self.assertIn(task_name, self.async_manager.get_active_tasks())

class TestTask3LaunchPattern(AsyncManagerTestMixin, TestCase):
    """Test the Task 3 launch pattern implementation."""

    def test_launch_async_task_success_without_conflicts(self):
        """Test successful launch without conflict detection."""

        def dummy_worker(message, task_key=None, **kwargs):
            return f"Processed: {message}"

        # Launch task without conflicts
        with patch("powercrud.async_manager.async_task") as mock_async_task:
            mock_async_task.return_value = "django_q2_task_123"

            with patch.object(
                self.async_manager, "async_task_lifecycle"
            ) as mock_lifecycle:
                task_key = self.async_manager.launch_async_task(
                    func=dummy_worker, message="test message", user="test_user"
                )

            # Verify task_key is a UUID
            self.assertIsInstance(task_key, str)
            self.assertEqual(len(task_key), 36)  # UUID4 length

            # Verify async_task was called with correct parameters
            self.assertTrue(mock_async_task.called)
            call_args = mock_async_task.call_args

            # Check function and args
            self.assertEqual(call_args[0][0], dummy_worker)
            self.assertEqual(call_args[1]["message"], "test message")

            # Check hook and task_name
            self.assertEqual(
                call_args[1]["hook"], "powercrud.async_hooks.task_completion_hook"
            )
            self.assertEqual(call_args[1]["task_name"], task_key)

            # Check task_key passed to worker
            self.assertEqual(call_args[1]["task_key"], task_key)

            mock_lifecycle.assert_called()
            lifecycle_kwargs = mock_lifecycle.call_args.kwargs
            self.assertEqual(lifecycle_kwargs["event"], "create")
            self.assertEqual(lifecycle_kwargs["task_name"], task_key)
            self.assertEqual(
                lifecycle_kwargs["status"], self.async_manager.STATUSES.PENDING
            )
            self.assertEqual(lifecycle_kwargs["message"], "Task queued")

    def test_launch_async_task_with_conflict_ids_success(self):
        """Test successful launch with conflict reservation."""

        def dummy_worker():
            return "success"

        conflict_ids = {"myapp.Book": {1, 2, 3}}

        with patch("powercrud.async_manager.async_task") as mock_async_task:
            mock_async_task.return_value = "django_q2_task_456"

            task_key = self.async_manager.launch_async_task(
                func=dummy_worker,
                conflict_ids=conflict_ids,
                user="test_user",
                affected_objects=["Book:1", "Book:2", "Book:3"],
            )

            # Verify conflict locks were created
            lock_1 = self.async_manager.cache.get(
                "powercrud:conflict:model:myapp.Book:1"
            )
            lock_2 = self.async_manager.cache.get(
                "powercrud:conflict:model:myapp.Book:2"
            )
            lock_3 = self.async_manager.cache.get(
                "powercrud:conflict:model:myapp.Book:3"
            )

            self.assertEqual(lock_1, task_key)
            self.assertEqual(lock_2, task_key)
            self.assertEqual(lock_3, task_key)

            # Verify tracking set was created
            tracking_set = self.async_manager.cache.get(
                f"powercrud:async:conflict:{task_key}"
            )
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
        self.async_manager.add_conflict_ids(existing_task, {"myapp.Book": {2, 3}})

        # Test: Try to launch with overlapping conflict
        conflict_ids = {"myapp.Book": {1, 2, 4}}  # 2 conflicts with existing

        with patch("powercrud.async_manager.async_task") as mock_async_task:
            with self.assertRaises(Exception) as cm:
                self.async_manager.launch_async_task(
                    func=dummy_worker, conflict_ids=conflict_ids
                )

            # Verify exception message
            self.assertIn("conflicts detected", str(cm.exception))

            # Verify async_task was NOT called (no enqueuing)
            self.assertFalse(mock_async_task.called)

            # Verify no locks were created for the failed task
            lock_1 = self.async_manager.cache.get(
                "powercrud:conflict:model:myapp.Book:1"
            )
            lock_4 = self.async_manager.cache.get(
                "powercrud:conflict:model:myapp.Book:4"
            )
            self.assertIsNone(lock_1)
            self.assertIsNone(lock_4)

            # Verify existing lock is unchanged
            lock_2 = self.async_manager.cache.get(
                "powercrud:conflict:model:myapp.Book:2"
            )
            self.assertEqual(lock_2, existing_task)

    def test_resolve_manager_from_path(self):
        path = f"{DummyCustomManager.__module__}.{DummyCustomManager.__name__}"
        instance = AsyncManager.resolve_manager(path)
        self.assertIsInstance(instance, DummyCustomManager)

    def test_resolve_manager_with_config(self):
        path = "powercrud.async_dashboard.ModelTrackingAsyncManager"
        instance = AsyncManager.resolve_manager(
            path,
            config={"record_model_path": "coordinator_testapp.AsyncTaskRecord"},
        )
        self.assertIsInstance(instance, ModelTrackingAsyncManager)

    def test_resolve_manager_fallback(self):
        instance = AsyncManager.resolve_manager("non.existent.Manager")
        self.assertIsInstance(instance, AsyncManager)

    def test_launch_rollback_on_enqueue_failure(self):
        """Test cleanup when async_task() fails or returns falsy."""

        def dummy_worker():
            return "should not run"

        conflict_ids = {"myapp.Book": {10, 11}}

        # Test 1: async_task raises exception
        with patch("powercrud.async_manager.async_task") as mock_async_task:
            mock_async_task.side_effect = Exception("Enqueue failed!")

            with self.assertRaises(Exception) as cm:
                self.async_manager.launch_async_task(
                    func=dummy_worker, conflict_ids=conflict_ids
                )

            self.assertIn("Failed to enqueue async task", str(cm.exception))

            # Verify rollback: no conflict locks
            lock_10 = self.async_manager.cache.get(
                "powercrud:conflict:model:myapp.Book:10"
            )
            lock_11 = self.async_manager.cache.get(
                "powercrud:conflict:model:myapp.Book:11"
            )
            self.assertIsNone(lock_10)
            self.assertIsNone(lock_11)

        # Test 2: async_task returns falsy
        with patch("powercrud.async_manager.async_task") as mock_async_task:
            mock_async_task.return_value = None  # Falsy return

            with self.assertRaises(Exception) as cm:
                self.async_manager.launch_async_task(
                    func=dummy_worker, conflict_ids=conflict_ids
                )

            self.assertIn("returned falsy task_id", str(cm.exception))

    def test_task_key_consistency(self):
        """Test task_key flows consistently through all phases."""

        def dummy_worker(data, task_key=None, **kwargs):
            return f"Received task_key: {task_key}"

        with patch("powercrud.async_manager.async_task") as mock_async_task:
            mock_async_task.return_value = "django_q2_task_789"

            returned_task_key = self.async_manager.launch_async_task(
                func=dummy_worker, data="test"
            )

            # Verify the same task_key was used for task_name
            call_args = mock_async_task.call_args
            task_name_arg = call_args[1]["task_name"]
            task_key_kwarg = call_args[1]["task_key"]

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

        with patch("powercrud.async_manager.async_task") as mock_async_task:
            mock_async_task.return_value = "task_id_hook_test"

            self.async_manager.launch_async_task(func=dummy_worker)

            # Verify hook parameter was passed correctly
            call_args = mock_async_task.call_args
            hook_arg = call_args[1]["hook"]

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
        mock_task = type(
            "MockTask",
            (),
            {"name": "test_task_key_123", "id": "mock_task_id", "success": True},
        )()

        custom_manager = CustomAsyncManager()
        custom_manager.handle_task_completion(mock_task, "test_task_key_123")

        # Verify custom method was called
        self.assertTrue(custom_manager.completion_called)
        self.assertEqual(custom_manager.completion_task_key, "test_task_key_123")

    def test_lifecycle_events_fired(self):
        """Test that 'create' event is fired with correct metadata."""

        class LifecycleTrackingManager(AsyncManager):
            def __init__(self):
                super().__init__()
                self.lifecycle_events = []

            def async_task_lifecycle(self, event, task_name=None, **kwargs):
                self.lifecycle_events.append(
                    {"event": event, "task_id": task_name, "kwargs": kwargs}
                )

        manager = LifecycleTrackingManager()

        with patch("powercrud.async_manager.async_task") as mock_async_task:
            mock_async_task.return_value = "lifecycle_test_task"

            task_key = manager.launch_async_task(
                func=lambda: "test", user="test_user", affected_objects=["obj1", "obj2"]
            )

            # Verify 'create' event was fired
            self.assertEqual(len(manager.lifecycle_events), 1)

            event = manager.lifecycle_events[0]
            self.assertEqual(event["event"], "create")
            self.assertEqual(event["task_id"], task_key)
            self.assertEqual(event["kwargs"]["user"], "test_user")
            self.assertEqual(event["kwargs"]["affected_objects"], ["obj1", "obj2"])
            self.assertEqual(
                event["kwargs"]["django_q2_task_id"], "lifecycle_test_task"
            )

    def test_handle_task_completion_emits_events(self):
        class TrackingManager(AsyncManager):
            def __init__(self):
                super().__init__()
                self.events = []

            def async_task_lifecycle(self, event, task_name, **kwargs):
                self.events.append((event, task_name, kwargs))

        manager = TrackingManager()
        mock_task = type("MockTask", (), {"success": True, "result": "ok"})()

        with patch.object(manager, "remove_active_task", return_value=True):
            manager.handle_task_completion(mock_task, "task-123")

        event_names = [call[0] for call in manager.events]
        self.assertIn("complete", event_names)
        self.assertIn("cleanup", event_names)
        complete_kwargs = next(
            kwargs for event, _, kwargs in manager.events if event == "complete"
        )
        self.assertEqual(complete_kwargs["status"], manager.STATUSES.SUCCESS)
        self.assertEqual(complete_kwargs["message"], "Task completed successfully")

    def test_handle_task_completion_failure_event(self):
        class TrackingManager(AsyncManager):
            def __init__(self):
                super().__init__()
                self.events = []

            def async_task_lifecycle(self, event, task_name, **kwargs):
                self.events.append((event, task_name, kwargs))

        manager = TrackingManager()
        mock_task = type("MockTask", (), {"success": False, "result": "boom"})()

        with patch.object(manager, "remove_active_task", return_value=True):
            manager.handle_task_completion(mock_task, "task-456")

        event_names = [call[0] for call in manager.events]
        self.assertIn("fail", event_names)
        fail_kwargs = next(
            kwargs for event, _, kwargs in manager.events if event == "fail"
        )
        self.assertEqual(fail_kwargs["status"], manager.STATUSES.FAILED)
        self.assertIn("boom", fail_kwargs["message"])

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

        with patch.object(self.async_manager, "async_task_lifecycle") as mock_lifecycle:
            self.async_manager.update_progress(task_key, "50% complete")

        mock_lifecycle.assert_called()
        kwargs = mock_lifecycle.call_args.kwargs
        self.assertEqual(kwargs["event"], "progress")
        self.assertEqual(kwargs["task_name"], task_key)
        self.assertEqual(kwargs["status"], self.async_manager.STATUSES.IN_PROGRESS)
        self.assertEqual(kwargs["message"], "50% complete")

    def test_worker_receives_task_key(self):
        """Test that worker functions receive task_key in kwargs."""
        received_kwargs = {}

        def capturing_worker(**kwargs):
            received_kwargs.update(kwargs)
            return "captured"

        with patch("powercrud.async_manager.async_task") as mock_async_task:
            mock_async_task.return_value = "worker_kwargs_test"

            task_key = self.async_manager.launch_async_task(
                func=capturing_worker, test_param="test_value"
            )

            # Check that task_key was added to kwargs passed to async_task
            call_args = mock_async_task.call_args
            passed_kwargs = call_args[1]

            self.assertEqual(passed_kwargs["task_key"], task_key)
            self.assertEqual(passed_kwargs["test_param"], "test_value")

class TestTask3StatusMethods(AsyncManagerTestMixin, TestCase):
    """Test both blocking and non-blocking status methods."""

    def test_status_methods_behavior(self):
        """Test both blocking and non-blocking status methods."""
        task_id = "status_test_task"

        # Mock successful task
        mock_success_task = type("MockTask", (), {"success": True, "id": task_id})()

        # Mock running task
        mock_running_task = type("MockTask", (), {"success": None, "id": task_id})()

        # Test blocking method with successful task
        with patch("powercrud.async_manager.fetch") as mock_fetch:
            mock_fetch.return_value = mock_success_task

            status = self.async_manager.get_task_status(task_id)
            self.assertEqual(status, "success")

            # Verify it was called with wait=300 (blocking)
            mock_fetch.assert_called_with(task_id, wait=300)

        # Test non-blocking method with running task
        with patch("powercrud.async_manager.fetch") as mock_fetch:
            mock_fetch.return_value = mock_running_task

            status = self.async_manager.get_task_status_nowait(task_id)
            self.assertEqual(status, "in_progress")

            # Verify it was called with wait=0 (non-blocking)
            mock_fetch.assert_called_with(task_id, wait=0)

        # Test no task found
        with patch("powercrud.async_manager.fetch") as mock_fetch:
            mock_fetch.return_value = None

            status_blocking = self.async_manager.get_task_status(task_id)
            status_nowait = self.async_manager.get_task_status_nowait(task_id)

            self.assertIsNone(status_blocking)
            self.assertIsNone(status_nowait)

class TestTask3EndToEndIntegration(AsyncManagerTestMixin, TestCase):
    """Test the inline launch path while preserving its mocked execution assertions."""

    def test_e2e_launch_execute_cleanup_cycle(self):
        """Test launch registration and progress capture with mocked inline execution."""
        # Execute worker synchronously by patching async_task call
        progress_messages = []

        def run_sync(func, *args, **kwargs):
            func(*args, **kwargs)
            progress_messages.append(
                self.async_manager.get_progress(kwargs["task_key"])
            )
            return "mock_django_q_task_id"

        with patch("powercrud.async_manager.async_task", side_effect=run_sync):
            task_key = self.async_manager.launch_async_task(
                func=simple_test_worker,
                message="E2E Test Message",
                user="e2e_test_user",
            )

        # Verify task_key was returned
        self.assertIsInstance(task_key, str)
        self.assertEqual(len(task_key), 36)  # UUID length

        # Verify task is in active set
        active_tasks = self.async_manager.get_active_tasks()
        self.assertIn(task_key, active_tasks)

        # The synchronous worker run should have produced progress updates
        self.assertTrue(
            progress_messages, "Worker should update progress synchronously"
        )
        final_progress = progress_messages[-1]
        self.assertIn("Processing completed", final_progress)

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
        request = self.factory.get("/progress/")
        response = view(request)

        self.assertEqual(response.status_code, 400)
        # JsonResponse doesn't have .json() method, need to parse content
        import json

        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response_data, {"error": "task_name required"})

    def test_as_view_with_progress_data(self):
        """Test as_view returns progress when available."""
        # Setup progress data
        manager = AsyncManager()
        manager.update_progress(self.task_name, self.progress_data)

        view = AsyncManager.as_view()
        request = self.factory.get(f"/progress/?task_name={self.task_name}")
        response = view(request)

        self.assertEqual(response.status_code, 200)
        import json

        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["status"], "in_progress")
        self.assertEqual(data["progress"], self.progress_data)
        self.assertNotIn("poll_interval", data)

    def test_as_view_no_progress_fallback_status(self):
        """Test as_view falls back to task status when no progress."""
        # Mock get_task_status_nowait to return 'success'
        with patch.object(
            AsyncManager, "get_task_status_nowait", return_value="success"
        ):
            view = AsyncManager.as_view()
            request = self.factory.get(f"/progress/?task_name={self.task_name}")
            response = view(request)

        self.assertEqual(response.status_code, 286)
        import json

        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["progress"], "Completed successfully!")
        self.assertNotIn("poll_interval", data)

    def test_as_view_unknown_status(self):
        """When cache indicates completion but status lookup returns None, treat as success."""
        with patch.object(AsyncManager, "get_task_status_nowait", return_value=None):
            view = AsyncManager.as_view()
            request = self.factory.get(f"/progress/?task_name={self.task_name}")
            response = view(request)

        self.assertEqual(response.status_code, 286)
        import json

        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["progress"], "Completed successfully!")



    def test_as_view_error_handling(self):
        """Test as_view handles internal errors gracefully."""
        # Mock the get_progress method on the AsyncManager class
        with patch.object(
            AsyncManager, "get_progress", side_effect=Exception("Test error")
        ):
            view = AsyncManager.as_view()
            request = self.factory.get(f"/progress/?task_name={self.task_name}")
            response = view(request)

        self.assertEqual(response.status_code, 500)
        import json

        response_data = json.loads(response.content.decode("utf-8"))
        self.assertIn("error", response_data)

    def test_progress_polling_with_manual_data(self):
        """Test end-to-end polling flow with real progress update."""

        # Launch a mock task to get task_id
        def dummy_worker(task_key, **kwargs):
            manager = AsyncManager()
            manager.update_progress(task_key, self.progress_data)
            return "done"

        with patch("powercrud.async_manager.async_task") as mock_async:
            mock_async.return_value = "mock_task_id"
            task_id = self.async_manager.launch_async_task(func=dummy_worker)

        # Since we're mocking async_task, the dummy_worker doesn't actually run
        # So we need to manually set the progress data for this test
        self.async_manager.update_progress(task_id, self.progress_data)

        # Now test the view with this task_id
        view = AsyncManager.as_view()
        request = self.factory.get(f"/progress/?task_name={task_id}")
        response = view(request)

        self.assertEqual(response.status_code, 200)
        import json

        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["status"], "in_progress")
        self.assertEqual(data["progress"], self.progress_data)

    def test_as_view_post_method(self):
        """Test as_view works with POST requests (for hx-vals)."""
        manager = AsyncManager()
        manager.update_progress(self.task_name, self.progress_data)
        view = AsyncManager.as_view()
        request = self.factory.post("/progress/", {"task_name": self.task_name})
        response = view(request)

        self.assertEqual(response.status_code, 200)  # Should work with POST data
        import json

        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response_data["task_name"], self.task_name)

    def test_poll_interval_adaptive(self):
        """Test adaptive poll_interval based on status."""
        # Test in_progress (1000ms)
        manager = AsyncManager()
        manager.update_progress(self.task_name, self.progress_data)
        view = AsyncManager.as_view()
        request = self.factory.get(f"/progress/?task_name={self.task_name}")
        response = view(request)
        import json

        response_data = json.loads(response.content.decode("utf-8"))
        self.assertNotIn("poll_interval", response_data)

        # Test pending state (should continue polling)
        manager.remove_progress_key(self.task_name)
        manager.create_progress_key(self.task_name)
        request = self.factory.get(f"/progress/?task_name={self.task_name}")
        response = view(request)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response_data["status"], "unknown")
        self.assertIn("poll_interval", response_data)
        self.assertEqual(response_data["poll_interval"], 1000)

        # Test success (terminal state)
        manager.remove_progress_key(self.task_name)
        with patch.object(
            AsyncManager, "get_task_status_nowait", return_value="success"
        ):
            response = view(request)
            response_data = json.loads(response.content.decode("utf-8"))
            self.assertEqual(response_data["status"], "success")
            self.assertEqual(response.status_code, 286)
            self.assertNotIn("poll_interval", response_data)

        # Test unknown (1000ms) - progress data still cleared
        with patch.object(AsyncManager, "get_task_status_nowait", return_value=None):
            response = view(request)
            response_data = json.loads(response.content.decode("utf-8"))
            self.assertNotIn("poll_interval", response_data)

class TestAsyncHookHelpers(TestCase):
    def test_extract_manager_class_from_dict_kwargs(self):
        task = SimpleNamespace(
            name="dummy",
            kwargs={"manager_class": "coordinator_tests.managers.CoordinatorAsyncManager"},
        )
        path = _extract_manager_class_path(task)
        self.assertEqual(path, "coordinator_tests.managers.CoordinatorAsyncManager")

    def test_extract_manager_class_from_serialized_kwargs(self):
        json_payload = '{"manager_class": "coordinator_tests.managers.CoordinatorAsyncManager"}'
        task = SimpleNamespace(name="dummy", kwargs=json_payload)
        path = _extract_manager_class_path(task)
        self.assertEqual(path, "coordinator_tests.managers.CoordinatorAsyncManager")

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
            kwargs={"manager_class": "coordinator_tests.managers.CoordinatorAsyncManager"},
        )

        task_completion_hook(task)

        mock_async_manager.resolve_manager.assert_called_once_with(
            "coordinator_tests.managers.CoordinatorAsyncManager", config=None
        )
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

        cfg = {"record_model_path": "coordinator_testapp.AsyncTaskRecord"}
        task = SimpleNamespace(
            name="task789",
            kwargs={
                "manager_class": "powercrud.async_dashboard.ModelTrackingAsyncManager",
                "manager_config": cfg,
            },
        )

        task_completion_hook(task)

        mock_async_manager.resolve_manager.assert_called_once_with(
            "powercrud.async_dashboard.ModelTrackingAsyncManager",
            config=cfg,
        )
        mock_manager.handle_task_completion.assert_called_once_with(task, "task789")

class TestModelTrackingAsyncManager(AsyncManagerTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        AsyncTaskRecord.objects.all().delete()
        self.manager = ModelTrackingAsyncManager(
            config=AsyncDashboardConfig(record_model_path="coordinator_testapp.AsyncTaskRecord"),
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
                record_model_path="coordinator_testapp.AsyncTaskRecord",
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
