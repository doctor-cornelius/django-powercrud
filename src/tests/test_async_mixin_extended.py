from __future__ import annotations

from types import SimpleNamespace

import pytest
from django.test import RequestFactory

from powercrud.mixins.async_mixin import AsyncMixin
from sample.models import Book


class CustomManager:
    def __init__(self, config=None):
        self.config = config

    def enqueue_bulk_task(self, *args, **kwargs):
        return "queued"

    def generate_task_name(self):
        return "task-id"

    def launch_async_task(self, *args, **kwargs):
        return "queued"


class DummyAsyncView(AsyncMixin):

    bulk_async = True
    bulk_async_backend = "q2"
    bulk_async_conflict_checking = True
    bulk_min_async_records = 3
    async_manager_class_path = None
    async_manager_class = CustomManager
    templates_path = "powercrud/daisyUI"
    bulk_async_allow_anonymous = True
    model = Book

    def __init__(self):
        self.request = RequestFactory().post("/")
        self.async_manager_config = None

    def get_async_queryset(self, selected_ids):
        return selected_ids


def test_should_process_async_respects_flags():
    view = DummyAsyncView()
    assert view.should_process_async(5) is True
    assert view.should_process_async(2) is False

    view.bulk_async = False
    assert view.should_process_async(5) is False


def test_handle_async_bulk_operation_enqueues(monkeypatch):
    captured = {}

    class Manager(CustomManager):
        def launch_async_task(self, *args, **kwargs):
            captured["kwargs"] = kwargs
            return "queued"

    view = DummyAsyncView()
    view.async_manager_class = Manager
    monkeypatch.setattr(view, "_check_for_conflicts", lambda ids: False)
    monkeypatch.setattr(view, "clear_selection_from_session", lambda request: None, raising=False)
    monkeypatch.setattr(view, "async_queue_success", lambda request, task_name, ids: "queued")

    result = view._handle_async_bulk_operation(
        SimpleNamespace(user=SimpleNamespace(is_anonymous=False, id=1)),
        [1, 2, 3],
        delete_selected=True,
        bulk_fields=["author"],
        fields_to_update=[],
        field_data=[],
    )
    assert result == "queued"
    assert "conflict_ids" in captured["kwargs"]


def test_get_async_manager_uses_settings(monkeypatch):
    view = DummyAsyncView()
    mgr = view.get_async_manager()
    assert isinstance(mgr, CustomManager)

    view.async_manager_class = None
    view.async_manager_class_path = "tests.test_async_mixin_extended.CustomManager"
    view.async_manager_config = {"foo": "bar"}

    monkeypatch.setattr(
        "powercrud.mixins.async_mixin.AsyncManager.resolve_manager",
        classmethod(lambda cls, path, config=None: CustomManager(config=config)),
    )
    mgr = view.get_async_manager()
    assert mgr.config == {"foo": "bar"}


def test_handle_async_bulk_operation_failure(monkeypatch):
    view = DummyAsyncView()
    view.async_manager_class = CustomManager
    monkeypatch.setattr(view, "_check_for_conflicts", lambda ids: False)
    def raise_error():
        raise RuntimeError("boom")

    monkeypatch.setattr(view, "get_async_manager", raise_error)

    result = view._handle_async_bulk_operation(
        SimpleNamespace(user=SimpleNamespace(is_anonymous=False, id=1)),
        [1, 2, 3],
        delete_selected=False,
        bulk_fields=["author"],
        fields_to_update=["author"],
        field_data=[{"field": "author"}],
    )
    assert result.status_code == 500
