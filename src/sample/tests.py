from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.urls import reverse
from datetime import date
import uuid
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model

from powercrud.async_context import task_context
from powercrud.bulk_persistence import BulkUpdateExecutionContext

from sample.async_manager import SampleAsyncManager
from sample.backends import BookBulkUpdateBackend
from sample.forms import BookForm
from sample.models import AsyncTaskRecord, Author, Book, Genre
from sample.services import BookBulkUpdateService, BookWriteService
from sample.views import BookCRUDView


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

    def test_create_event_stores_django_user(self):
        user = get_user_model().objects.create_user(
            username="bulkuser",
            email="bulkuser@example.com",
            password="testpass123",
        )

        self.manager.async_task_lifecycle(
            event="create",
            task_name="task-django-user",
            user=user,
            affected_objects=["Book:5"],
            task_kwargs={"example": True},
            status=AsyncTaskRecord.STATUS.PENDING,
            message="Task queued",
        )

        record = AsyncTaskRecord.objects.get(task_name="task-django-user")
        self.assertEqual(record.user_label, "bulkuser")

    def test_create_event_marks_anonymous(self):
        self.manager.async_task_lifecycle(
            event="create",
            task_name="task-anon",
            user=None,
            affected_objects=["Book:9"],
            task_kwargs={},
            status=AsyncTaskRecord.STATUS.PENDING,
            message="Task queued",
        )

        record = AsyncTaskRecord.objects.get(task_name="task-anon")
        self.assertEqual(record.user_label, "Anonymous")

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
        AsyncTaskRecord.objects.create(
            task_name="task-detail", status=AsyncTaskRecord.STATUS.PENDING
        )
        response = self.client.get(
            reverse("sample:asynctaskrecord-detail", args=["task-detail"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "task-progress")


class SampleAsyncContextDemoTests(TestCase):
    def setUp(self):
        with patch("sample.models.time.sleep", return_value=None):
            self.author = Author.objects.create(
                name="Author", bio="", birth_date=date(2000, 1, 1)
            )
            self.genre = Genre.objects.create(name="Genre", description="")
            self.book = Book.objects.create(
                title="Demo Book",
                author=self.author,
                published_date=date.today(),
                bestseller=False,
                isbn=str(uuid.uuid4())[:17],
                pages=100,
            )
        self.book.genres.add(self.genre)

    def test_book_save_streams_progress_inside_context(self):
        with task_context("demo-task", "sample.async_manager.SampleAsyncManager"):
            with (
                patch("sample.models.register_descendant_conflicts") as mock_register,
                patch("sample.models.AsyncManager") as mock_manager_cls,
                patch("sample.models.time.sleep", return_value=None),
            ):
                manager_instance = mock_manager_cls.return_value
                self.book.save()

        mock_register.assert_called_once_with("sample.Genre", [self.genre.id])
        manager_instance.update_progress.assert_called()
        args, kwargs = manager_instance.update_progress.call_args
        self.assertEqual(args[0], "demo-task")
        self.assertIn("processed child", args[1])

    def test_book_save_without_context_runs_normally(self):
        with (
            patch("sample.models.register_descendant_conflicts") as mock_register,
            patch("sample.models.AsyncManager") as mock_manager_cls,
            patch("sample.models.time.sleep", return_value=None) as mock_sleep,
        ):
            self.book.save()

        mock_register.assert_not_called()
        mock_manager_cls.assert_not_called()
        mock_sleep.assert_called()


class SampleBookFormDependencyTests(TestCase):
    """Validate sample view behavior for author-dependent genre constraints."""

    def setUp(self):
        self.author_a = Author.objects.create(name="Author A")
        self.author_b = Author.objects.create(name="Author B")
        self.genre_a = Genre.objects.create(name="Genre A")
        self.genre_b = Genre.objects.create(name="Genre B")
        self.author_a.genres.add(self.genre_a)
        self.author_b.genres.add(self.genre_b)

        self.book_a = Book.objects.create(
            title="Book A",
            author=self.author_a,
            published_date=date(2024, 1, 1),
            bestseller=False,
            isbn="9788888800001",
            pages=120,
        )
        self.book_a.genres.set([self.genre_a])

        self.book_b = Book.objects.create(
            title="Book B",
            author=self.author_b,
            published_date=date(2024, 1, 2),
            bestseller=False,
            isbn="9788888800002",
            pages=130,
        )
        self.book_b.genres.set([self.genre_b])

    def _build_book_view(self, method="get"):
        request_factory = RequestFactory()
        request = getattr(request_factory, method)("/")
        view = BookCRUDView()
        view.request = request
        return view

    def test_book_view_filters_genres_from_posted_author(self):
        view = self._build_book_view(method="post")
        form = view._finalize_form(
            view.get_form_class()(
                data={
                    "title": self.book_a.title,
                    "author": str(self.author_b.pk),
                    "published_date": "2024-01-01",
                    "isbn": self.book_a.isbn,
                    "pages": str(self.book_a.pages),
                    "bestseller": "",
                },
                instance=self.book_a,
            )
        )

        genre_ids = list(form.fields["genres"].queryset.values_list("id", flat=True))
        self.assertIn(
            self.genre_b.pk,
            genre_ids,
            "BookCRUDView should include genres explicitly assigned to the posted author.",
        )
        self.assertNotIn(
            self.genre_a.pk,
            genre_ids,
            "BookCRUDView should exclude genres not assigned to the posted author.",
        )

    def test_book_view_filters_genres_from_instance_when_unbound(self):
        """Unbound forms should use instance author to scope genre choices."""
        view = self._build_book_view()
        form = view._finalize_form(view.get_form_class()(instance=self.book_a))

        genre_ids = list(form.fields["genres"].queryset.values_list("id", flat=True))
        self.assertIn(
            self.genre_a.pk,
            genre_ids,
            "Unbound BookCRUDView forms should include genres assigned to the instance author.",
        )
        self.assertNotIn(
            self.genre_b.pk,
            genre_ids,
            "Unbound BookCRUDView forms should exclude genres from other authors.",
        )

    def test_book_view_genres_field_is_optional(self):
        """Genres should be optional when author-scoped choices are empty."""
        author_without_genres = Author.objects.create(name="Author Without Genres")
        view = self._build_book_view(method="post")
        form = view._finalize_form(
            view.get_form_class()(
                data={
                    "title": "No Genres Book",
                    "author": str(author_without_genres.pk),
                    "published_date": "2024-01-03",
                    "isbn": "9788888800003",
                    "pages": "99",
                    "bestseller": "",
                }
            )
        )

        self.assertFalse(
            form.fields["genres"].required,
            "BookCRUDView forms should keep genres optional to allow save when no scoped genres exist.",
        )
        self.assertTrue(
            form.is_valid(),
            "BookCRUDView forms should validate without genres when the selected author has no available genre options.",
        )


class SamplePersistenceTutorialHelperTests(TestCase):
    """Exercise the sample helper classes used by the advanced tutorials."""

    def setUp(self):
        """Create sample book data used by the tutorial helper tests."""
        self.author = Author.objects.create(name="Tutorial Author")
        self.genre = Genre.objects.create(name="Tutorial Genre")
        self.author.genres.add(self.genre)

    def test_tutorial_helpers_can_be_imported_and_instantiated(self):
        """Sample tutorial helpers should remain importable for docs examples."""
        write_service = BookWriteService()
        bulk_service = BookBulkUpdateService()
        backend = BookBulkUpdateBackend()

        self.assertIsInstance(
            write_service,
            BookWriteService,
            "BookWriteService should be importable and instantiable for tutorial examples.",
        )
        self.assertIsInstance(
            bulk_service,
            BookBulkUpdateService,
            "BookBulkUpdateService should be importable and instantiable for tutorial examples.",
        )
        self.assertIsInstance(
            backend,
            BookBulkUpdateBackend,
            "BookBulkUpdateBackend should be importable and instantiable for tutorial examples.",
        )

    def test_book_write_service_saves_book_and_many_to_many_values(self):
        """The sample write service should persist the book and related genres."""
        form = BookForm(
            data={
                "title": "Tutorial Save",
                "author": str(self.author.pk),
                "genres": [str(self.genre.pk)],
                "published_date": "2024-01-05",
                "bestseller": "",
                "isbn": "9788888800099",
                "pages": "111",
                "description": "Saved via tutorial helper",
            }
        )

        self.assertTrue(
            form.is_valid(),
            f"BookForm should validate in the tutorial helper test. Errors: {form.errors}",
        )

        book = BookWriteService().save_book(form=form, mode="form")

        self.assertIsNotNone(
            book.pk,
            "BookWriteService.save_book should return a saved Book instance with a primary key.",
        )
        self.assertEqual(
            list(book.genres.values_list("pk", flat=True)),
            [self.genre.pk],
            "BookWriteService.save_book should call form.save_m2m() so the selected genres are persisted.",
        )

    def test_book_bulk_update_backend_delegates_to_service_with_context(self):
        """The sample backend should forward context and progress callback unchanged."""
        backend = BookBulkUpdateBackend()
        queryset = Book.objects.none()
        progress_callback = Mock()
        context = BulkUpdateExecutionContext(
            mode="async",
            task_name="tutorial-task",
            user_id=123,
        )
        expected_result = {"success": True, "success_records": 2, "errors": []}

        with patch.object(
            BookBulkUpdateService,
            "apply",
            return_value=expected_result,
        ) as mock_apply:
            result = backend.persist_bulk_update(
                queryset=queryset,
                bulk_fields=["title"],
                fields_to_update=["title"],
                field_data=[{"field_name": "title", "value": "Updated"}],
                context=context,
                progress_callback=progress_callback,
            )

        self.assertEqual(
            result,
            expected_result,
            "BookBulkUpdateBackend.persist_bulk_update should return the result from BookBulkUpdateService.apply unchanged.",
        )
        mock_apply.assert_called_once()
        _, kwargs = mock_apply.call_args
        self.assertIs(
            kwargs["context"],
            context,
            "BookBulkUpdateBackend.persist_bulk_update should forward the execution context to BookBulkUpdateService.apply.",
        )
        self.assertIs(
            kwargs["progress_callback"],
            progress_callback,
            "BookBulkUpdateBackend.persist_bulk_update should forward the progress callback to BookBulkUpdateService.apply.",
        )
