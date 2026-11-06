"""PowerCRUD-specific async consumer tests retained from the mixed module."""

import uuid
from datetime import date
from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase, override_settings

from powercrud.async_manager import AsyncManager
from powercrud.async_dashboard import ModelTrackingAsyncManager
from powercrud.mixins.async_mixin import AsyncMixin
from sample.models import Author, Book, Genre
from sample.async_manager import SampleAsyncManager


class AsyncManagerTestMixin:
    """Reset the PowerCRUD coordination cache for consumer tests."""

    def setUp(self):
        super().setUp()
        self.async_manager = AsyncManager()
        self.async_manager.cache.delete(self.async_manager.active_prefix)
        self.async_manager.cache.clear()


class DummyConflictView(AsyncMixin):
    model = Book
    templates_path = "powercrud/daisyUI"
    bulk_async = True
    bulk_async_conflict_checking = True
    bulk_min_async_records = 1
    namespace = "sample"
    pk_url_kwarg = "pk"
    bulk_async_backend = "q2"

class TestSingleRecordConflicts(AsyncManagerTestMixin, TestCase):
    """Task 6: ensure single-record operations respect async locks."""

    def setUp(self):
        super().setUp()
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
        candidate_paths = [
            "sample/book_form_conflict.html",
            "powercrud/daisyUI/partial/form_conflict.html",
        ]
        self.view.get_focused_component_template_paths = Mock(
            return_value=candidate_paths
        )
        with patch("powercrud.mixins.async_mixin.render") as render_mock:
            render_mock.return_value.status_code = 200
            render_mock.return_value.content = b"Edit Conflict Please try again later"
            response = self.view._render_conflict_response(request, book.pk, "update")

        render_context = render_mock.call_args.args[2]
        self.assertEqual(
            render_context["form_conflict_template_paths"], candidate_paths
        )
        self.view.get_focused_component_template_paths.assert_called_once_with(
            "form_conflict"
        )

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
        view.async_manager_class_path = (
            "powercrud.async_dashboard.ModelTrackingAsyncManager"
        )

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
        view.async_manager_class_path = (
            "powercrud.async_dashboard.ModelTrackingAsyncManager"
        )
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
