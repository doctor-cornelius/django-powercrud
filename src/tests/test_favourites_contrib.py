"""Tests for the optional PowerCRUD favourites contrib app."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.checks import run_checks
from django.test import RequestFactory
from django.test.utils import override_settings
from django.urls import NoReverseMatch, reverse
from neapolitan.views import Role

from powercrud.contrib.favourites.models import SavedFilterFavourite
from powercrud.contrib.favourites.services import build_query_string_from_state
from sample.views import BookCRUDView

BOOK_VIEW_KEY = f"{BookCRUDView.__module__}.{BookCRUDView.__name__}"


@pytest.mark.django_db
def test_book_view_current_list_state_includes_expected_fields():
    """Current list state should include filters, visible filters, sort, and page size."""

    request = RequestFactory().get(
        "/sample/bigbook/",
        {
            "title": "django",
            "genres": ["1", "2"],
            "visible_filters": ["genres"],
            "sort": "-published_date",
            "page_size": "25",
            "page": "3",
        },
    )
    view = BookCRUDView()
    view.request = request

    filterset = view.get_filterset(view.get_queryset())
    state = view.get_current_list_state(filterset)

    assert state == {
        "filters": {
            "title": ["django"],
            "genres": ["1", "2"],
        },
        "visible_filters": ["genres"],
        "sort": "-published_date",
        "page_size": "25",
    }, "Saved list state should preserve active filter values plus visible_filters, sort, and page_size while excluding page."


@pytest.mark.django_db
def test_book_list_renders_favourites_toolbar_for_authenticated_user(client):
    """Authenticated users should see active favourites controls on the opted-in list."""

    user = get_user_model().objects.create_user(username="fav-toolbar-user")
    client.force_login(user)

    response = client.get(reverse("sample:bigbook-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Book list should still render successfully when the optional favourites contrib app is enabled."
    )
    assert "Favourites" in response_text, (
        "Book list should render the compact filter favourites trigger when the view opts in."
    )
    assert "Apply" not in response_text, (
        "The compact favourites UI should auto-apply on selection instead of rendering a separate Apply button."
    )
    assert "Favourite name" in response_text and "Update selected" in response_text and "Delete selected" in response_text, (
        "Authenticated users should see the inline save, update, and delete favourites controls inside the favourites panel."
    )
    assert "favourites-save-form" not in response_text, (
        "The compact favourites UI should no longer render or reference the removed modal save-form endpoint."
    )
    assert 'data-powercrud-filter-favourites-toolbar="true"' in response_text, (
        "Book list should render the filter favourites toolbar container for the opted-in list."
    )
    assert 'class="dropdown dropdown-start relative z-[60] hidden -ml-px"' in response_text, (
        "The filter favourites trigger should stay hidden until the user opens the filter panel."
    )
    assert "Sign in to save favourites." not in response_text, (
        "Authenticated users should not see the anonymous-login helper message."
    )


@pytest.mark.django_db
def test_book_list_renders_long_selected_favourite_with_truncation_tooltip(client):
    """Long selected favourite names should truncate in the trigger and keep the full tooltip text."""

    user = get_user_model().objects.create_user(username="fav-long-label-user")
    client.force_login(user)
    favourite = SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Pages set to two hundred twent",
        state={"filters": {}, "visible_filters": [], "sort": "", "page_size": ""},
    )

    response = client.get(
        reverse("powercrud:favourites-toolbar"),
        {
            "view_key": BOOK_VIEW_KEY,
            "list_view_url": reverse("sample:bigbook-list"),
            "toolbar_dom_id": "powercrud-favourites-toolbar-test",
            "current_state_json": "{}",
            "original_target": "#content",
            "selected_favourite_id": str(favourite.pk),
        },
        HTTP_HX_REQUEST="true",
    )
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Rendering the favourites toolbar with a selected favourite should succeed."
    )
    assert 'max-w-[15ch] overflow-hidden text-ellipsis whitespace-nowrap' in response_text, (
        "Long selected favourite names should use the constrained trigger-label wrapper so the toolbar stays compact."
    )
    assert 'data-powercrud-tooltip="overflow"' in response_text, (
        "Long selected favourite names should enable the existing overflow tooltip hook on the trigger label."
    )
    assert 'data-tippy-content="Pages set to two hundred twent"' in response_text, (
        "Long selected favourite names should keep the full value in the tooltip payload even when the trigger truncates it."
    )


def test_book_view_derives_favourites_key_from_view_identity():
    """The favourites scope key should be derived from the list view's Python identity."""

    view = BookCRUDView()

    assert view.get_favourites_key() == BOOK_VIEW_KEY, (
        "BookCRUDView should derive its favourites scope key from its module and class name."
    )


def test_book_view_silently_disables_favourites_when_contrib_app_is_unavailable():
    """Opting into favourites should degrade cleanly when the optional contrib app is not installed."""

    request = RequestFactory().get("/sample/bigbook/")
    view = BookCRUDView()
    view.request = request
    view.role = Role.LIST

    with patch.object(view, "get_favourites_contrib_installed", return_value=False):
        assert view.get_favourites_enabled() is False, (
            "Views should silently disable favourites when the optional contrib app is unavailable."
        )
        assert view.get_favourites_context() == {
            "filter_favourites_enabled": False,
            "saved_filter_favourites": [],
        }, (
            "Views should expose the disabled favourites context instead of raising when the contrib app is unavailable."
        )


@override_settings(ROOT_URLCONF="tests.urls_without_powercrud")
@pytest.mark.django_db
def test_book_view_silently_disables_favourites_when_shared_routes_are_unavailable(client):
    """Opted-in views should not render favourites when the shared URLs are missing."""

    user = get_user_model().objects.create_user(username="fav-missing-routes-user")
    client.force_login(user)

    response = client.get(reverse("sample:bigbook-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Book list should still render successfully even when the shared favourites routes are not mounted."
    )
    assert 'data-powercrud-filter-favourites-toolbar="true"' not in response_text, (
        "Book list should hide the favourites toolbar entirely when the shared favourites routes are unavailable."
    )
    assert 'hx-get="None"' not in response_text and 'hx-post="None"' not in response_text, (
        "Book list should never render literal None HTMX URLs when favourites are unavailable."
    )
    assert 'data-powercrud-favourite-save-url="None"' not in response_text, (
        "Book list should not expose a broken save URL payload when the shared favourites routes are unavailable."
    )


@override_settings(ROOT_URLCONF="tests.urls_without_powercrud")
def test_favourites_system_check_warns_when_shared_routes_are_unavailable():
    """Installing favourites without mounting the shared PowerCRUD URLs should emit a warning."""

    favourites_warnings = [
        check
        for check in run_checks()
        if check.id == "powercrud.W001"
    ]

    assert len(favourites_warnings) == 1, (
        "Expected exactly one favourites configuration warning when the shared PowerCRUD routes are unavailable."
    )
    warning = favourites_warnings[0]
    assert "shared URLs are not mounted" in warning.msg, (
        "The favourites configuration warning should explain that the shared URLs are missing."
    )
    assert "include('powercrud.urls', namespace='powercrud')" in warning.hint, (
        "The favourites configuration warning should tell projects how to mount the required shared URLs."
    )


def test_favourites_system_check_is_clean_when_shared_routes_are_available():
    """The favourites configuration warning should disappear when the shared routes are mounted."""

    favourites_warnings = [
        check
        for check in run_checks()
        if check.id == "powercrud.W001"
    ]

    assert favourites_warnings == [], (
        "Expected no favourites configuration warning when the shared PowerCRUD routes are mounted."
    )


@pytest.mark.django_db
def test_duplicate_favourite_save_rerenders_form_errors_for_htmx(client):
    """Duplicate favourite names should rerender validation errors into the toolbar panel."""

    user = get_user_model().objects.create_user(username="fav-duplicate-save-user")
    client.force_login(user)
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Existing favourite",
        state={"filters": {}, "visible_filters": [], "sort": "", "page_size": ""},
    )

    response = client.post(
        reverse("powercrud:favourites-save"),
        {
            "view_key": BOOK_VIEW_KEY,
            "list_view_url": reverse("sample:bigbook-list"),
            "toolbar_dom_id": "powercrud-favourites-toolbar-test",
            "current_state_json": json.dumps(
                {"filters": {}, "visible_filters": [], "sort": "", "page_size": ""}
            ),
            "state_json": json.dumps(
                {"filters": {}, "visible_filters": [], "sort": "", "page_size": ""}
            ),
            "original_target": "#content",
            "name": "Existing favourite",
        },
        HTTP_HX_REQUEST="true",
    )
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Duplicate favourites should return a normal HTMX swap response so validation errors render inline."
    )
    assert "already exists for this list" in response_text, (
        "Duplicate favourite saves should render the validation error back into the toolbar panel."
    )


@pytest.mark.django_db
def test_author_list_does_not_render_favourites_toolbar_when_view_not_enabled(client):
    """Views that do not opt in should not render favourites controls."""

    response = client.get(reverse("sample:author-list"))
    response_text = response.content.decode()

    assert "Save current" not in response_text, (
        "Author list should not render favourites controls when filter_favourites_enabled is unset."
    )


@pytest.mark.django_db
def test_favourite_save_view_persists_state_and_returns_toolbar_fragment(client):
    """Saving a favourite should persist it and retarget the toolbar fragment."""

    user = get_user_model().objects.create_user(username="fav-save-user")
    client.force_login(user)

    state = {
        "filters": {"title": ["django"]},
        "visible_filters": ["genres"],
        "sort": "-published_date",
        "page_size": "25",
    }
    response = client.post(
        reverse("powercrud:favourites-save"),
        {
            "name": "Recent Django",
            "view_key": BOOK_VIEW_KEY,
            "list_view_url": reverse("sample:bigbook-list"),
            "toolbar_dom_id": "powercrud-favourites-toolbar-test",
            "current_state_json": json.dumps(state),
            "original_target": "#content",
            "state_json": json.dumps(state),
        },
        HTTP_HX_REQUEST="true",
    )

    saved = SavedFilterFavourite.objects.get(user=user, view_key=BOOK_VIEW_KEY)

    assert response.status_code == 200, (
        "Saving a valid favourite should return a toolbar fragment response."
    )
    assert saved.name == "Recent Django", (
        "Saving a favourite should persist the submitted favourite name."
    )
    assert saved.state == state, (
        "Saving a favourite should persist the normalized list-state payload."
    )
    assert 'data-powercrud-filter-favourites-panel="true"' not in response.content.decode(), (
        "Successful favourite saves should return the inner dropdown panel content rather than the entire toolbar wrapper."
    )
    assert "Recent Django" in response.content.decode(), (
        "Successful favourite saves should refresh the toolbar with the new option visible."
    )
    assert 'selected' in response.content.decode(), (
        "Successful favourite saves should mark the new favourite as selected in the refreshed panel."
    )


@pytest.mark.django_db
def test_favourite_save_view_rejects_duplicate_names_per_user_and_view(client):
    """Duplicate favourite names should validate instead of creating a second row."""

    user = get_user_model().objects.create_user(username="fav-dup-user")
    client.force_login(user)
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Recent Django",
        state={"filters": {}, "visible_filters": [], "sort": "", "page_size": ""},
    )

    response = client.post(
        reverse("powercrud:favourites-save"),
        {
            "name": "Recent Django",
            "view_key": BOOK_VIEW_KEY,
            "list_view_url": reverse("sample:bigbook-list"),
            "toolbar_dom_id": "powercrud-favourites-toolbar-test",
            "current_state_json": "{}",
            "original_target": "#content",
            "state_json": "{}",
        },
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200, (
        "Duplicate favourite saves should return an HTMX-swappable validation response instead of surfacing a transport error."
    )
    assert SavedFilterFavourite.objects.filter(user=user, view_key=BOOK_VIEW_KEY).count() == 1, (
        "Duplicate favourite saves should not create an additional database row."
    )
    assert "already exists" in response.content.decode(), (
        "Duplicate favourite saves should explain the uniqueness failure to the user."
    )
    assert "Favourite name" in response.content.decode(), (
        "Duplicate favourite saves should re-render the inline save form so the user can correct the name in place."
    )


@pytest.mark.django_db
def test_favourite_save_view_rejects_names_longer_than_thirty_chars(client):
    """Favourite names longer than the supported maximum should fail validation."""

    user = get_user_model().objects.create_user(username="fav-long-name-user")
    client.force_login(user)

    response = client.post(
        reverse("powercrud:favourites-save"),
        {
            "name": "1234567890123456789012345678901",
            "view_key": BOOK_VIEW_KEY,
            "list_view_url": reverse("sample:bigbook-list"),
            "toolbar_dom_id": "powercrud-favourites-toolbar-test",
            "current_state_json": "{}",
            "original_target": "#content",
            "state_json": "{}",
        },
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200, (
        "Overlong favourite names should return an HTMX-swappable validation response so the inline form can show the error."
    )
    assert (
        SavedFilterFavourite.objects.filter(user=user, view_key=BOOK_VIEW_KEY).count() == 0
    ), "Overlong favourite names should not create a saved favourite row."
    assert "Ensure this value has at most 30 characters" in response.content.decode(), (
        "Overlong favourite names should explain the thirty-character validation limit in the inline form."
    )


@pytest.mark.django_db
def test_favourites_toolbar_view_can_expand_inline_save_form(client):
    """The toolbar endpoint should render an inline save form when requested."""

    user = get_user_model().objects.create_user(username="fav-toolbar-expand-user")
    client.force_login(user)

    response = client.get(
        reverse("powercrud:favourites-toolbar"),
        {
            "view_key": BOOK_VIEW_KEY,
            "list_view_url": reverse("sample:bigbook-list"),
            "toolbar_dom_id": "powercrud-favourites-toolbar-test",
            "current_state_json": "{}",
            "original_target": "#content",
            "show_save_form": "1",
        },
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200, (
        "Requesting the expanded favourites toolbar state should render successfully."
    )
    assert "Favourite name" in response.content.decode(), (
        "Requesting inline save mode should render the favourite name field inside the dropdown panel."
    )


def test_favourites_save_form_route_has_been_removed():
    """The old modal-only favourites save-form route should no longer exist."""

    with pytest.raises(NoReverseMatch):
        reverse("powercrud:favourites-save-form")


@pytest.mark.django_db
def test_favourite_apply_view_returns_hx_location_for_saved_state(client):
    """Applying a favourite over HTMX should return an HX-Location payload for partial navigation."""

    user = get_user_model().objects.create_user(username="fav-apply-user")
    favourite = SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Recent Django",
        state={
            "filters": {"title": ["django"], "genres": ["1", "2"]},
            "visible_filters": ["genres"],
            "sort": "-published_date",
            "page_size": "25",
        },
    )
    client.force_login(user)

    response = client.get(
        reverse("powercrud:favourites-apply"),
        {
            "favourite_id": favourite.pk,
            "view_key": BOOK_VIEW_KEY,
            "list_view_url": reverse("sample:bigbook-list"),
            "toolbar_dom_id": "powercrud-favourites-toolbar-test",
            "current_state_json": "{}",
            "original_target": "#content",
        },
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200, (
        "Applying a saved favourite over HTMX should return a successful navigation response."
    )
    assert json.loads(response.headers["HX-Location"]) == {
        "path": "/sample/bigbook/?title=django&genres=1&genres=2&visible_filters=genres&sort=-published_date&page_size=25",
        "push": "/sample/bigbook/?title=django&genres=1&genres=2&visible_filters=genres&sort=-published_date&page_size=25",
        "target": "#content",
        "swap": "innerHTML",
    }, "Applying a favourite over HTMX should instruct the browser to refresh the list shell at the original target with the saved list URL."


@pytest.mark.django_db
def test_favourite_update_view_overwrites_saved_state_and_refreshes_toolbar(client):
    """Updating a favourite should replace its saved state and refresh the toolbar fragment."""

    user = get_user_model().objects.create_user(username="fav-update-user")
    favourite = SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Recent Django",
        state={"filters": {"title": ["old"]}, "visible_filters": [], "sort": "", "page_size": ""},
    )
    client.force_login(user)

    updated_state = {
        "filters": {"title": ["django"], "genres": ["9"]},
        "visible_filters": ["genres"],
        "sort": "-published_date",
        "page_size": "25",
    }
    response = client.post(
        reverse("powercrud:favourites-update"),
        {
            "favourite_id": favourite.pk,
            "view_key": BOOK_VIEW_KEY,
            "list_view_url": reverse("sample:bigbook-list"),
            "toolbar_dom_id": "powercrud-favourites-toolbar-test",
            "current_state_json": json.dumps(updated_state),
            "state_json": json.dumps(updated_state),
            "original_target": "#content",
        },
        HTTP_HX_REQUEST="true",
    )

    favourite.refresh_from_db()

    assert response.status_code == 200, (
        "Updating an owned favourite should return an updated toolbar fragment."
    )
    assert favourite.state == updated_state, (
        "Updating a favourite should overwrite the stored list state with the submitted normalized payload."
    )
    assert "Recent Django" in response.content.decode(), (
        "Updating a favourite should refresh the toolbar with the existing favourite still present."
    )
    assert 'data-powercrud-favourite-query-string="title=django&amp;genres=9&amp;visible_filters=genres&amp;sort=-published_date&amp;page_size=25"' in response.content.decode(), (
        "Updating a favourite should refresh the selected option metadata so later applies use the newly saved query-string state."
    )


@pytest.mark.django_db
def test_favourite_delete_view_removes_only_the_current_users_favourite(client):
    """Deleting a favourite should only affect the owner's matching row."""

    user = get_user_model().objects.create_user(username="fav-delete-user")
    other_user = get_user_model().objects.create_user(username="fav-other-user")
    favourite = SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Mine",
        state={"filters": {}, "visible_filters": [], "sort": "", "page_size": ""},
    )
    SavedFilterFavourite.objects.create(
        user=other_user,
        view_key=BOOK_VIEW_KEY,
        name="Theirs",
        state={"filters": {}, "visible_filters": [], "sort": "", "page_size": ""},
    )
    client.force_login(user)

    response = client.post(
        reverse("powercrud:favourites-delete"),
        {
            "favourite_id": favourite.pk,
            "view_key": BOOK_VIEW_KEY,
            "list_view_url": reverse("sample:bigbook-list"),
            "toolbar_dom_id": "powercrud-favourites-toolbar-test",
            "current_state_json": "{}",
            "original_target": "#content",
        },
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200, (
        "Deleting an owned favourite should return an updated toolbar fragment."
    )
    assert not SavedFilterFavourite.objects.filter(pk=favourite.pk).exists(), (
        "Deleting a favourite should remove the owner's selected favourite row."
    )
    assert SavedFilterFavourite.objects.filter(user=other_user, name="Theirs").exists(), (
        "Deleting one user's favourite should not affect another user's saved favourites."
    )


def test_build_query_string_from_state_serializes_multi_value_filters_in_order():
    """Saved state should round-trip back to ordered query-string parameters."""

    query_string = build_query_string_from_state(
        {
            "filters": {"title": ["django"], "genres": ["2", "5"]},
            "visible_filters": ["genres", "pages"],
            "sort": "-published_date",
            "page_size": "25",
        }
    )

    assert query_string == (
        "title=django&genres=2&genres=5&visible_filters=genres&visible_filters=pages&sort=-published_date&page_size=25"
    ), "Serializing saved favourites should preserve multi-value filters and visible filter order."
