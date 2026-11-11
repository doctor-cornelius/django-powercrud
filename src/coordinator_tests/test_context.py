"""Tests for reusable task context and factory-bound descendant locks."""

from powercrud._coordinator.context import (
    get_current_task,
    register_descendant_conflicts,
    skip_nested_async,
    task_context,
)
from powercrud._coordinator.exceptions import DescendantConflictError


def test_task_context_sets_and_resets():
    assert get_current_task() is None, "No task context should exist before entry"
    with task_context("task-123", "module.Manager"):
        current = get_current_task()
        assert current.task_name == "task-123", "Context should expose the current task name"
        assert current.manager_class_path == "module.Manager", "Context should preserve manager identity"
        assert skip_nested_async() is True, "Nested async work should be suppressed in context"
    assert get_current_task() is None, "Context should reset after leaving its block"
    assert skip_nested_async() is False, "Nested async work should resume outside its block"


def test_nested_task_context_restores_parent_context():
    """A nested scope restores the original manager and task metadata."""
    parent_manager = object()
    child_manager = object()
    with task_context("parent", manager=parent_manager):
        with task_context("child", manager=child_manager):
            assert get_current_task().manager is child_manager
        assert get_current_task().task_name == "parent"
        assert get_current_task().manager is parent_manager
    assert get_current_task() is None


def test_register_descendant_conflicts_without_context():
    called = []

    class DummyManager:
        def add_conflict_ids(self, *args, **kwargs):
            called.append((args, kwargs))

    register_descendant_conflicts(
        "coordinator_testapp.Book", [1, 2], manager_factory=lambda: DummyManager()
    )
    assert called == [], "Descendant registration should be a no-op without task context"


def test_register_descendant_conflicts_invokes_manager():
    added = {}

    class DummyManager:
        def add_conflict_ids(self, task_name, payload):
            added["task"] = task_name
            added["payload"] = payload

    with task_context("task-abc"):
        register_descendant_conflicts(
            "coordinator_testapp.Book",
            [1, "2", None],
            manager_factory=lambda: DummyManager(),
        )
    assert added["task"] == "task-abc", "Descendant locks should use the active task key"
    assert added["payload"] == {"coordinator_testapp.book": {1, "2"}}, "Descendant IDs should retain their original Python types"


def test_failed_descendant_acquisition_stops_before_following_work():
    """A failed descendant reservation is visible to the protected caller."""
    class RejectingManager:
        """Represent a conflict backend that rejects a new protected object."""

        def add_conflict_ids(self, task_name, payload):
            """Reject acquisition while recording the attempted typed values."""
            return False

    with task_context("parent"):
        try:
            register_descendant_conflicts(
                "coordinator_testapp.Book", ["uuid-pk"],
                manager_factory=RejectingManager,
            )
        except DescendantConflictError:
            reached_following_work = False
        else:
            reached_following_work = True
    assert not reached_following_work, "Rejected descendant acquisition must prevent protected work"
