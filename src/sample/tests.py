from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from sample.async_manager import SampleAsyncManager
from sample.models import AsyncTaskRecord


class SampleAsyncDashboardTests(TestCase):
    def setUp(self):
        self.manager = SampleAsyncManager()

    def test_create_event_persists_record(self):
        self.manager.async_task_lifecycle(
            event="create",
            task_name="task-create",
            user="alice",
            affected_objects=["Book:1", "Book:2"],
            task_kwargs={"foo": "bar"},
            status=AsyncTaskRecord.STATUS.PENDING,
            message="Task queued",
        )
        record = AsyncTaskRecord.objects.get(task_name="task-create")
        self.assertEqual(record.status, AsyncTaskRecord.STATUS.PENDING)
        self.assertEqual(record.user_label, "alice")
        self.assertIn("Book:1", record.affected_objects)
        self.assertEqual(record.task_kwargs, {"foo": "bar"})

    def test_progress_event_updates_status(self):
        self.manager.async_task_lifecycle(event="create", task_name="task-progress")
        self.manager.async_task_lifecycle(
            event="progress",
            task_name="task-progress",
            progress_payload="Working",
            message="Working",
            status=AsyncTaskRecord.STATUS.IN_PROGRESS,
        )
        record = AsyncTaskRecord.objects.get(task_name="task-progress")
        self.assertEqual(record.status, AsyncTaskRecord.STATUS.IN_PROGRESS)
        self.assertEqual(record.progress_payload, "Working")

    def test_complete_event_marks_finished(self):
        self.manager.async_task_lifecycle(event="create", task_name="task-complete")
        before = timezone.now()
        self.manager.async_task_lifecycle(
            event="complete",
            task_name="task-complete",
            result="done",
            message="All done",
            status=AsyncTaskRecord.STATUS.SUCCESS,
            timestamp=before,
        )
        record = AsyncTaskRecord.objects.get(task_name="task-complete")
        self.assertEqual(record.status, AsyncTaskRecord.STATUS.SUCCESS)
        self.assertEqual(record.result_payload, "done")
        self.assertIsNotNone(record.completed_at)

    def test_fail_event_marks_failed(self):
        self.manager.async_task_lifecycle(event="create", task_name="task-fail")
        self.manager.async_task_lifecycle(
            event="fail",
            task_name="task-fail",
            message="Boom",
            result="traceback",
            status=AsyncTaskRecord.STATUS.FAILED,
        )
        record = AsyncTaskRecord.objects.get(task_name="task-fail")
        self.assertEqual(record.status, AsyncTaskRecord.STATUS.FAILED)
        self.assertEqual(record.result_payload, "traceback")
        self.assertIsNotNone(record.failed_at)

    def test_cleanup_event_sets_flag_without_overwriting_status(self):
        self.manager.async_task_lifecycle(event="create", task_name="task-cleanup")
        self.manager.async_task_lifecycle(
            event="complete",
            task_name="task-cleanup",
            status=AsyncTaskRecord.STATUS.SUCCESS,
            result=True,
        )
        self.manager.async_task_lifecycle(
            event="cleanup",
            task_name="task-cleanup",
            status=None,
        )
        record = AsyncTaskRecord.objects.get(task_name="task-cleanup")
        self.assertTrue(record.cleaned_up)
        self.assertEqual(record.status, AsyncTaskRecord.STATUS.SUCCESS)

    def test_progress_event_preserves_existing_message(self):
        self.manager.async_task_lifecycle(
            event="create",
            task_name="task-progress-message",
            message="Initial queue",
            status=AsyncTaskRecord.STATUS.PENDING,
        )
        self.manager.async_task_lifecycle(
            event="progress",
            task_name="task-progress-message",
            progress_payload="Working",
            message="Working",
            status=AsyncTaskRecord.STATUS.IN_PROGRESS,
        )
        record = AsyncTaskRecord.objects.get(task_name="task-progress-message")
        self.assertEqual(record.status, AsyncTaskRecord.STATUS.IN_PROGRESS)
        self.assertEqual(record.message, "Initial queue")
        self.assertEqual(record.progress_payload, "Working")

    def test_async_task_detail_view_renders(self):
        AsyncTaskRecord.objects.create(task_name="task-detail", status=AsyncTaskRecord.STATUS.PENDING)
        response = self.client.get(reverse("sample:asynctaskrecord-detail", args=["task-detail"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "task-progress")
