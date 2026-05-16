"""Tests for PowerCRUD list-column options."""

from __future__ import annotations

import pytest
from django.test import RequestFactory
from django.urls import reverse
from neapolitan.views import Role

from powercrud.mixins import PowerCRUDMixin
from powercrud.mixins.list_options_mixin import LIST_OPTIONS_SESSION_KEY
from sample.models import Book
from sample.views import BookCRUDView


BOOK_VIEW_KEY = f"{BookCRUDView.__module__}.{BookCRUDView.__name__}"


@pytest.mark.django_db
def test_book_list_renders_column_chooser_for_anonymous_user(client):
    """The opted-in sample book list should expose the column chooser."""

    response = client.get(reverse("sample:bigbook-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, "Book list should render successfully."
    assert "Cols 9/12" in response_text, (
        "Users should see the list-column chooser with active/allowed counts."
    )
    assert 'data-powercrud-list-columns-trigger="true"' in response_text and 'data-tippy-content="Choose visible columns"' in response_text, (
        "The list-column chooser trigger should expose a PowerCRUD tooltip."
    )
    assert 'name="visible_columns"' in response_text, (
        "The chooser should render checkbox inputs for selectable columns."
    )
    assert 'name="list_columns_action"' in response_text and 'value="reset"' in response_text, (
        "The chooser should render a reset action for returning to default columns."
    )
    assert 'class="btn btn-outline btn-sm"' in response_text, (
        "The list-column reset action should render as a proper outlined button."
    )
    assert 'data-field-name="uneditable_field"' not in response_text, (
        "BookCRUDView should hide at least one allowed data column by default for the sample demo."
    )
    assert 'value="uneditable_field"' in response_text, (
        "Hidden-by-default columns should still be available in the chooser."
    )


@pytest.mark.django_db
def test_list_column_apply_persists_preference_and_clears_hidden_sort(client):
    """Applying columns should persist session state and clear hidden-column sort."""

    response = client.post(
        reverse("sample:bigbook-columns"),
        {
            "list_view_url": reverse("sample:bigbook-list"),
            "visible_columns": ["title", "pages"],
            "sort": "isbn",
            "page": "3",
            "page_size": "5",
            "list_columns_action": "apply",
        },
    )

    assert response.status_code == 302, (
        "A non-HTMX column apply should redirect back to the list."
    )
    assert response["Location"] == f"{reverse('sample:bigbook-list')}?page_size=5", (
        "Applying columns should reset page and clear sort if the sorted column is hidden."
    )
    assert (
        client.session[LIST_OPTIONS_SESSION_KEY][BOOK_VIEW_KEY]
        == {"visible_columns": ["title", "pages"]}
    ), (
        "List column session state should store the normalized active visible columns."
    )


@pytest.mark.django_db
def test_list_column_reset_deletes_preference(client):
    """Resetting list columns should remove the saved session state."""

    session = client.session
    session[LIST_OPTIONS_SESSION_KEY] = {
        BOOK_VIEW_KEY: {"visible_columns": ["title", "pages"]}
    }
    session.save()

    response = client.post(
        reverse("sample:bigbook-columns"),
        {
            "list_view_url": reverse("sample:bigbook-list"),
            "list_columns_action": "reset",
            "page": "2",
            "page_size": "10",
        },
    )

    assert response.status_code == 302, "Reset should redirect back to the list."
    assert response["Location"] == f"{reverse('sample:bigbook-list')}?page_size=10", (
        "Reset should preserve page size and reset pagination."
    )
    assert BOOK_VIEW_KEY not in client.session.get(LIST_OPTIONS_SESSION_KEY, {}), (
        "Reset should delete the saved list-column state from the session."
    )


@pytest.mark.django_db
def test_list_column_apply_rejects_empty_selection(client):
    """The RC should reject user-selected zero-data-column tables."""

    response = client.post(
        reverse("sample:bigbook-columns"),
        {
            "list_view_url": reverse("sample:bigbook-list"),
            "list_columns_action": "apply",
        },
    )

    assert response.status_code == 400, (
        "Applying an empty visible-column set should fail instead of saving it."
    )
    assert LIST_OPTIONS_SESSION_KEY not in client.session, (
        "Invalid empty column state should not create session state."
    )


@pytest.mark.django_db
def test_list_column_apply_accepts_single_visible_column(client):
    """The RC allows any non-empty active data-column set."""

    response = client.post(
        reverse("sample:bigbook-columns"),
        {
            "list_view_url": reverse("sample:bigbook-list"),
            "visible_columns": ["title"],
            "list_columns_action": "apply",
        },
    )

    assert response.status_code == 302, (
        "Applying one visible data column should be accepted because only zero columns are invalid."
    )
    assert (
        client.session[LIST_OPTIONS_SESSION_KEY][BOOK_VIEW_KEY]
        == {"visible_columns": ["title"]}
    ), (
        "A single-column visible state should persist in the session unchanged."
    )


@pytest.mark.django_db
def test_list_column_state_defaults_without_session():
    """A GET should render defaults when no session state is available."""

    class BookListView(PowerCRUDMixin):
        model = Book
        role = Role.LIST
        fields = ["title", "author", "isbn"]
        default_list_fields = ["title", "author"]

    request = RequestFactory().get("/")
    view = BookListView()
    view.request = request

    assert view.get_active_list_columns() == ["title", "author"], (
        "Missing session state should fall back to default columns on GET."
    )


@pytest.mark.django_db
def test_list_options_enabled_uses_all_allowed_columns_by_default():
    """list_options_enabled should opt into the chooser without narrowing defaults."""

    class BookListView(PowerCRUDMixin):
        model = Book
        role = Role.LIST
        fields = ["title", "author", "isbn"]
        list_options_enabled = True

    request = RequestFactory().get("/")
    view = BookListView()
    view.request = request

    assert BookListView.has_list_options_urls() is True, (
        "list_options_enabled=True should register the list-column endpoint even without default_list_fields."
    )
    assert view.get_list_options_enabled() is True, (
        "list_options_enabled=True should opt list views into selectable columns."
    )
    assert view.get_default_list_columns() == ["title", "author", "isbn"], (
        "Without default_list_fields, the reset/default state should include every allowed column."
    )
    assert view.get_active_list_columns() == ["title", "author", "isbn"], (
        "Missing session state should use all allowed columns when only list_options_enabled is set."
    )


@pytest.mark.django_db
def test_list_options_enabled_false_disables_default_list_fields():
    """An explicit false opt-out should disable list options even if defaults exist."""

    class BookListView(PowerCRUDMixin):
        model = Book
        role = Role.LIST
        fields = ["title", "author", "isbn"]
        list_options_enabled = False
        default_list_fields = ["title"]

    request = RequestFactory().get("/")
    view = BookListView()
    view.request = request

    assert BookListView.has_list_options_urls() is False, (
        "list_options_enabled=False should suppress the list-column endpoint."
    )
    assert view.get_list_options_enabled() is False, (
        "list_options_enabled=False should disable the chooser even when default_list_fields is declared."
    )
    assert view.get_active_list_columns() == ["title", "author", "isbn"], (
        "Disabled list options should render every allowed column."
    )


@pytest.mark.django_db
def test_list_column_state_drops_stale_session_columns():
    """Session state should drop stale columns and fall back to defaults if empty."""

    class BookListView(PowerCRUDMixin):
        model = Book
        role = Role.LIST
        fields = ["title", "author", "isbn"]
        default_list_fields = ["title", "author"]

    request = RequestFactory().get("/")
    view = BookListView()
    view.request = request
    view_key = view.get_list_options_key()

    request.session = {
        LIST_OPTIONS_SESSION_KEY: {
            view_key: {"visible_columns": ["missing", "isbn"]},
        }
    }

    assert view.get_active_list_columns() == ["isbn"], (
        "Stale session column names should be dropped while valid names remain active."
    )

    request.session = {
        LIST_OPTIONS_SESSION_KEY: {
            view_key: {"visible_columns": ["missing"]},
        }
    }

    assert view.get_active_list_columns() == ["title", "author"], (
        "Entirely stale session column state should fall back to default columns."
    )
