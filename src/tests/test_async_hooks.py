from __future__ import annotations

import json
from types import SimpleNamespace


from powercrud.async_hooks import (
    _extract_manager_class_path,
    _extract_manager_config,
    _parse_task_kwargs,
    progress_update_decorator,
)


class DummyTask(SimpleNamespace):
    pass


def test_parse_task_kwargs_handles_json():
    task = DummyTask(kwargs=json.dumps({"foo": "bar"}))
    assert _parse_task_kwargs(task) == {"foo": "bar"}

    task.kwargs = "{'foo': 'bar'}"
    assert _parse_task_kwargs(task)["foo"] == "bar"

    task.kwargs = object()
    assert _parse_task_kwargs(task) == {}


def test_extract_manager_helpers():
    task = DummyTask(
        kwargs={"manager_class": "module.Manager", "manager_config": {"foo": "bar"}}
    )
    assert _extract_manager_class_path(task) == "module.Manager"
    assert _extract_manager_config(task) == {"foo": "bar"}

    task.kwargs = {"manager_config": "not-a-dict"}
    assert _extract_manager_config(task) is None


def test_progress_update_decorator(monkeypatch):
    updates = {}

    class FakeManager:
        def update_progress(self, task_name, message):
            updates.setdefault(task_name, []).append(message)

    monkeypatch.setattr(
        "powercrud.async_manager.AsyncManager", lambda: FakeManager(), raising=False
    )

    @progress_update_decorator
    def worker(data, progress_callback=None, **kwargs):
        for item in data:
            progress_callback(f"Processed {item}")
        return True

    assert worker([1, 2], task_name="task-123") is True
    assert updates["task-123"] == ["Processed 1", "Processed 2"]
