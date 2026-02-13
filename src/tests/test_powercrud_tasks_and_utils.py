from __future__ import annotations

import contextlib
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings

from powercrud import schedules, tasks, urls


class DummyAsyncManager:
    def __init__(self):
        self.progress_updates = []

    def update_progress(self, task_name, message):
        self.progress_updates.append((task_name, message))


class DummyManagerConfig(DummyAsyncManager):
    def __init__(self, config=None):
        super().__init__()
        self.config = config

    def cleanup_completed_tasks(self):
        return {"cleaned": {"foo": {"reason": "done"}}}


class DummyQueryset(list):
    def count(self):
        return len(self)

    # emulate QuerySet.values_list used by bulk_edit_process_post
    def values_list(self, field_name, flat=False):
        return [getattr(obj, field_name) for obj in self]


class DummyModelManager:
    def __init__(self, items):
        self._items = items

    def filter(self, **kwargs):
        return DummyQueryset(self._items)


class DummyModel:
    def __init__(self, items):
        self.objects = DummyModelManager(items)


@pytest.fixture(autouse=True)
def no_transaction_atomic(monkeypatch):
    """
    OperationMixin wraps work in transaction.atomic(); this fixture makes it a no-op
    so the tests can run without touching the real database transaction machinery.
    """

    monkeypatch.setattr(
        "powercrud.mixins.bulk_mixin.operation_mixin.transaction.atomic",
        lambda: contextlib.nullcontext(),
    )


def test_bulk_delete_task_happy_path(monkeypatch):
    dummy_manager = DummyAsyncManager()

    monkeypatch.setattr(
        tasks.AsyncManager,
        "resolve_manager",
        classmethod(lambda cls, manager_class_path=None, config=None: dummy_manager),
    )

    items = [SimpleNamespace(pk=1, delete=lambda: None)]
    dummy_model = DummyModel(items)
    monkeypatch.setattr(
        tasks, "apps", SimpleNamespace(get_model=lambda path: dummy_model)
    )

    class DummyBulkMixin:
        def _perform_bulk_delete(self, queryset, progress_callback=None):
            for idx, _ in enumerate(queryset, start=1):
                progress_callback(idx, len(queryset))
            return {"success": True, "success_records": len(queryset), "errors": []}

    monkeypatch.setattr(tasks, "BulkMixin", DummyBulkMixin)

    result = tasks.bulk_delete_task(
        model_path="sample.Book",
        selected_ids=[1],
        user_id=99,
        task_key="task-123",
    )

    assert result is True
    assert ("task-123", "starting delete") in dummy_manager.progress_updates
    assert ("task-123", "deleting: 1/1") in dummy_manager.progress_updates
    assert (
        "task-123",
        "completed delete: 1 processed",
    ) in dummy_manager.progress_updates


def test_bulk_delete_task_handles_errors(monkeypatch):
    dummy_manager = DummyAsyncManager()

    monkeypatch.setattr(
        tasks.AsyncManager,
        "resolve_manager",
        classmethod(lambda cls, manager_class_path=None, config=None: dummy_manager),
    )

    def failing_delete():
        raise RuntimeError("boom")

    items = [SimpleNamespace(pk=1, delete=failing_delete)]
    dummy_model = DummyModel(items)
    monkeypatch.setattr(
        tasks, "apps", SimpleNamespace(get_model=lambda path: dummy_model)
    )

    class FailingBulkMixin:
        def _perform_bulk_delete(self, queryset, progress_callback=None):
            raise RuntimeError("delete failed")

    monkeypatch.setattr(tasks, "BulkMixin", FailingBulkMixin)

    result = tasks.bulk_delete_task(
        model_path="sample.Book",
        selected_ids=[1],
        user_id=99,
        task_name="human-friendly",
    )
    assert result is False
    # Failure path still reports the error to the manager
    assert any(
        "failed delete" in message for _, message in dummy_manager.progress_updates
    )


def test_bulk_update_task_success(monkeypatch):
    dummy_manager = DummyAsyncManager()
    monkeypatch.setattr(
        tasks.AsyncManager,
        "resolve_manager",
        classmethod(lambda cls, manager_class_path=None, config=None: dummy_manager),
    )

    items = [SimpleNamespace(pk=1)]
    dummy_model = DummyModel(items)
    monkeypatch.setattr(
        tasks, "apps", SimpleNamespace(get_model=lambda path: dummy_model)
    )

    class DummyBulkMixin:
        def _perform_bulk_update(
            self,
            queryset,
            bulk_fields,
            fields_to_update,
            field_data,
            progress_callback=None,
        ):
            for idx, _ in enumerate(queryset, start=1):
                if progress_callback:
                    progress_callback(idx, len(queryset))
            return {"success": True, "success_records": len(queryset), "errors": []}

    monkeypatch.setattr(tasks, "BulkMixin", DummyBulkMixin)

    result = tasks.bulk_update_task(
        "sample.Book",
        selected_ids=[1],
        user_id=10,
        bulk_fields=["title"],
        fields_to_update=["title"],
        field_data=[{"field": "title", "value": "New", "info": {}}],
        task_key="task-789",
    )

    assert result is True
    assert ("task-789", "updating: 1/1") in dummy_manager.progress_updates
    assert (
        "task-789",
        "completed update: 1 processed",
    ) in dummy_manager.progress_updates


def test_bulk_update_task_reports_failure(monkeypatch):
    dummy_manager = DummyAsyncManager()
    monkeypatch.setattr(
        tasks.AsyncManager,
        "resolve_manager",
        classmethod(lambda cls, manager_class_path=None, config=None: dummy_manager),
    )

    dummy_model = DummyModel([SimpleNamespace(pk=1)])
    monkeypatch.setattr(
        tasks, "apps", SimpleNamespace(get_model=lambda path: dummy_model)
    )

    class FailingBulkMixin:
        def _perform_bulk_update(
            self,
            queryset,
            bulk_fields,
            fields_to_update,
            field_data,
            progress_callback=None,
        ):
            raise ValidationError("invalid data")

    monkeypatch.setattr(tasks, "BulkMixin", FailingBulkMixin)

    assert (
        tasks.bulk_update_task(
            "sample.Book",
            selected_ids=[1],
            user_id=1,
            bulk_fields=["title"],
            fields_to_update=["title"],
            field_data=[],
            task_name="named-task",
        )
        is False
    )

    assert any(
        "failed update" in message for _, message in dummy_manager.progress_updates
    )


@override_settings(POWERCRUD_SETTINGS={"ASYNC_ENABLED": False})
def test_cleanup_async_artifacts_skips_when_disabled(monkeypatch, caplog):
    caplog.set_level("DEBUG")
    schedules.cleanup_async_artifacts()
    assert "Skipping scheduled cleanup" in caplog.text


@override_settings(POWERCRUD_SETTINGS={"ASYNC_ENABLED": True})
def test_cleanup_async_artifacts_runs_manager(monkeypatch, caplog):
    dummy = DummyManagerConfig(config={"foo": "bar"})

    class DummyAsyncModule:
        def __call__(self):
            return DummyManagerConfig(config={"foo": "bar"})

    monkeypatch.setattr(
        "powercrud.async_manager.AsyncManager",
        lambda: dummy,
    )

    caplog.set_level("INFO")
    schedules.cleanup_async_artifacts()
    assert ("Scheduled cleanup removed 1 task(s)") in caplog.text


def test_pcrud_help_command_success(monkeypatch, capsys):
    from powercrud.management.commands import pcrud_help

    opened = {}

    monkeypatch.setattr(
        pcrud_help.webbrowser, "open", lambda url: opened.setdefault("url", url)
    )

    command = pcrud_help.Command()
    command.handle()

    assert opened["url"] == "https://doctor-cornelius.github.io/django-powercrud/"
    out = capsys.readouterr().out
    assert "Opening powercrud documentation" in out


def test_pcrud_help_command_failure(monkeypatch, capsys):
    from powercrud.management.commands import pcrud_help

    def boom(url):
        raise RuntimeError("browser missing")

    monkeypatch.setattr(pcrud_help.webbrowser, "open", boom)

    command = pcrud_help.Command()
    command.handle()

    out = capsys.readouterr().out
    assert "Failed to open browser" in out
    assert "Please manually visit" in out


def test_urlpatterns_include_async_progress():
    pattern = urls.urlpatterns[0]
    assert pattern.name == "async_progress"
    assert "AsyncManager.as_view" in pattern.callback.__qualname__
    assert getattr(pattern.pattern, "_route", "") == "powercrud/async/progress/"
