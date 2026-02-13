from powercrud import async_context


def test_task_context_sets_and_resets():
    assert async_context.get_current_task() is None
    with async_context.task_context("task-123", "module.Manager"):
        current = async_context.get_current_task()
        assert current.task_name == "task-123"
        assert current.manager_class_path == "module.Manager"
        assert async_context.skip_nested_async() is True
    assert async_context.get_current_task() is None
    assert async_context.skip_nested_async() is False


def test_register_descendant_conflicts_without_context(monkeypatch):
    called = []

    class DummyManager:
        def add_conflict_ids(self, *args, **kwargs):
            called.append((args, kwargs))

    monkeypatch.setattr("powercrud.async_manager.AsyncManager", lambda: DummyManager())
    async_context.register_descendant_conflicts("sample.Book", [1, 2])
    assert called == []


def test_register_descendant_conflicts_invokes_manager(monkeypatch):
    added = {}

    class DummyManager:
        def add_conflict_ids(self, task_name, payload):
            added["task"] = task_name
            added["payload"] = payload

    monkeypatch.setattr("powercrud.async_manager.AsyncManager", lambda: DummyManager())

    with async_context.task_context("task-abc"):
        async_context.register_descendant_conflicts("sample.Book", [1, "2", None])

    assert added["task"] == "task-abc"
    assert added["payload"] == {"sample.book": {1, 2}}
