"""Compatibility checks for public PowerCRUD async paths and wrappers."""

from unittest.mock import patch

from django.test import TestCase
from django.urls import URLPattern, URLResolver

from powercrud.async_manager import AsyncManager


class TestAsyncCompatibility(TestCase):
    """Keep established URL and completion-hook imports observable."""

    def test_get_url_returns_path(self):
        """Test get_url returns proper path object."""
        path_obj = AsyncManager.get_url()
        self.assertIsInstance(path_obj, URLPattern)
        self.assertEqual(str(path_obj.pattern), "powercrud/async/progress/")
        self.assertEqual(path_obj.name, "powercrud_async_progress")
        self.assertTrue(callable(path_obj.callback))

    def test_get_urlpatterns_returns_resolver(self):
        """Ensure get_urlpatterns provides a namespaced include."""
        resolver = AsyncManager.get_urlpatterns()
        self.assertIsInstance(resolver, URLResolver)
        self.assertEqual(str(resolver.pattern), "powercrud/")
        self.assertEqual(resolver.namespace, "powercrud")

    def test_hook_import_path_works(self):
        """Test that the completion hook import path remains callable."""
        from powercrud.async_hooks import task_completion_hook

        self.assertTrue(callable(task_completion_hook))
        mock_task = type(
            "MockTask", (), {"name": "test_hook_task", "id": "mock_id", "success": True}
        )()
        with patch("powercrud.async_manager.Task"):
            try:
                task_completion_hook(mock_task)
                hook_callable = True
            except Exception as exc:
                hook_callable = False
                self.fail(f"Completion hook raised unexpectedly: {exc}")
        self.assertTrue(hook_callable, "Completion hook should be callable without errors")
