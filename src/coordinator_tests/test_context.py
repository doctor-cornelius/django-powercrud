from powercrud import async_context


def test_task_context_sets_and_resets():
    assert async_context.get_current_task() is None, "No task context should exist before entry"
    with async_context.task_context("task-123", "module.Manager"):
        current = async_context.get_current_task()
        assert current.task_name == "task-123", "Context should expose the current task name"
        assert current.manager_class_path == "module.Manager", "Context should preserve manager identity"
        assert async_context.skip_nested_async() is True, "Nested async work should be suppressed in context"
    assert async_context.get_current_task() is None, "Context should reset after leaving its block"
    assert async_context.skip_nested_async() is False, "Nested async work should resume outside context"


def test_register_descendant_conflicts_without_context(monkeypatch):
    called = []

    class DummyManager:
        def add_conflict_ids(self, *args, **kwargs):
            called.append((args, kwargs))

    monkeypatch.setattr("powercrud.async_manager.AsyncManager", lambda: DummyManager())
    async_context.register_descendant_conflicts("coordinator_testapp.Book", [1, 2])
    assert called == [], "Descendant registration should be a no-op without task context"


def test_register_descendant_conflicts_invokes_manager(monkeypatch):
    added = {}

    class DummyManager:
        def add_conflict_ids(self, task_name, payload):
            added["task"] = task_name
            added["payload"] = payload

    monkeypatch.setattr("powercrud.async_manager.AsyncManager", lambda: DummyManager())

    with async_context.task_context("task-abc"):
        async_context.register_descendant_conflicts("coordinator_testapp.Book", [1, "2", None])

    assert added["task"] == "task-abc", "Descendant locks should use the active task key"
    assert added["payload"] == {"coordinator_testapp.book": {1, 2}}, "Descendant IDs should be normalized and registered"
