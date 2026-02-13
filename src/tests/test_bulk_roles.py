from __future__ import annotations

import pytest
from django.views import View

from powercrud.mixins.bulk_mixin.roles import BulkActions, BulkEditRole


class DummyView(View):
    url_base = "widget"
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
    role = None


def test_bulk_edit_role_generates_url():
    role = BulkEditRole()
    pattern = role.get_url(DummyView)
    assert pattern.name == "widget-bulk-edit"
    assert getattr(pattern.pattern, "_route") == "widget/bulk-edit/"
    assert callable(pattern.callback)


@pytest.mark.parametrize(
    "action, expected_route",
    [
        (BulkActions.TOGGLE_SELECTION, "widget/toggle-selection/<int:pk>/"),
        (BulkActions.CLEAR_SELECTION, "widget/clear-selection/"),
        (BulkActions.TOGGLE_ALL_SELECTION, "widget/toggle-all-selection/"),
    ],
)
def test_bulk_actions_generate_paths(action, expected_route):
    pattern = action.get_url(DummyView)
    assert getattr(pattern.pattern, "_route") == expected_route
    assert pattern.name == f"widget-{action.value}"


def test_bulk_actions_handlers():
    assert BulkActions.TOGGLE_SELECTION.handlers() == {"post": "toggle_selection_view"}
    assert BulkActions.CLEAR_SELECTION.handlers() == {"post": "clear_selection_view"}
    assert BulkActions.TOGGLE_ALL_SELECTION.handlers() == {
        "post": "toggle_all_selection_view"
    }
