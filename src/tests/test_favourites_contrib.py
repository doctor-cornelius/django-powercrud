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
from powercrud.contrib.favourites.services import (
    build_query_string_from_state,
    get_filter_favourite_user,
    normalise_saved_state,
)
from powercrud.mixins.list_options_mixin import LIST_OPTIONS_SESSION_KEY
from sample.views import BookCRUDView

BOOK_VIEW_KEY = f"{BookCRUDView.__module__}.{BookCRUDView.__name__}"
SESSION_FAVOURITE_OWNER_USERNAME = "powercrud_filter_favourite_owner_username"


def resolve_filter_favourite_owner_from_session(request):
    """Return the saved-favourite owner named in the test session."""

    username = request.session.get(SESSION_FAVOURITE_OWNER_USERNAME)
    if not username:
        return request.user
    return get_user_model().objects.get(username=username)


def set_filter_favourite_owner_session(client, user):
    """Store the resolved saved-favourite owner username on the test session."""

    session = client.session
    session[SESSION_FAVOURITE_OWNER_USERNAME] = user.username
    session.save()


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
    view.role = Role.LIST

    filterset = view.get_filterset(view.get_queryset())
    list_column_state = view.build_list_column_state(queryset=filterset.qs)
    state = view.get_current_list_state(
        filterset,
        list_column_state=list_column_state,
    )

    assert state == {
        "filters": {
            "title": ["django"],
            "genres": ["1", "2"],
        },
        "visible_filters": ["genres"],
        "sort": "-published_date",
        "page_size": "25",
        "visible_columns": list(list_column_state.active_columns),
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
    assert 'aria-label="Saved favourites"' in response_text, (
        "Book list should render the compact icon-only saved favourites trigger when the view opts in."
    )
    assert 'data-powercrud-tooltip="semantic"' in response_text and 'data-tippy-content="Saved favourites"' in response_text, (
        "The unselected favourites trigger should use PowerCRUD Tippy metadata instead of a native title tooltip."
    )
    assert 'title="Saved favourites"' not in response_text, (
        "The unselected favourites trigger should not use browser-native title tooltips."
    )
    assert 'data-powercrud-filter-favourites-selected="false"' in response_text, (
        "Book list should render the saved favourites trigger in its unselected icon-only state by default."
    )
    assert 'data-powercrud-filter-favourites-icon-outline="true"' in response_text, (
        "Book list should render the outline heart icon for the unselected saved favourites trigger."
    )
    assert "Apply" not in response_text, (
        "The compact favourites UI should auto-apply on selection instead of rendering a separate Apply button."
    )
    assert "Favourite name" in response_text and "Reset" in response_text and "Update" in response_text and "Delete" in response_text, (
        "Authenticated users should see the inline save, update, and delete favourites controls inside the favourites panel."
    )
    assert "favourites-save-form" not in response_text, (
        "The compact favourites UI should no longer render or reference the removed modal save-form endpoint."
    )
    assert 'data-powercrud-filter-favourites-toolbar="true"' in response_text, (
        "Book list should render the filter favourites toolbar container for the opted-in list."
    )
    assert 'class="dropdown dropdown-end relative z-[60]"' in response_text, (
        "The saved favourites trigger should render as a top-level view control."
    )
    assert "Sign in to save favourites." not in response_text, (
        "Authenticated users should not see the anonymous-login helper message."
    )


@pytest.mark.django_db
def test_book_list_renders_long_selected_favourite_with_truncation_tooltip(client):
    """Long selected favourite names should keep their full text in the icon trigger metadata."""

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
    assert 'aria-label="Saved favourite: Pages set to two hundred twent"' in response_text, (
        "Long selected favourite names should keep the trigger icon-only while remaining accessible."
    )
    assert 'data-powercrud-filter-favourites-selected="true"' in response_text, (
        "Selected favourites should mark the saved favourites trigger as selected."
    )
    assert 'data-powercrud-filter-favourites-icon-filled="true"' in response_text, (
        "Selected favourites should render the filled heart icon."
    )
    assert 'text-primary' in response_text, (
        "Selected favourites should use the semantic primary color on the filled heart icon."
    )
    assert 'data-powercrud-tooltip="semantic"' in response_text, (
        "Selected favourites should enable a semantic tooltip on the icon trigger."
    )
    assert 'data-tippy-content="Pages set to two hundred twent"' in response_text, (
        "Long selected favourite names should keep the full value in the tooltip payload even when the trigger truncates it."
    )
    assert 'title="Pages set to two hundred twent"' not in response_text, (
        "Selected favourites should avoid browser-native title tooltips so placement is controlled by Tippy."
    )


@pytest.mark.django_db
def test_book_list_marks_matching_saved_favourite_on_full_page_render(client):
    """Initial list rendering should mark a saved favourite selected when state matches."""

    user = get_user_model().objects.create_user(username="fav-refresh-selected-user")
    client.force_login(user)
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Refresh survives",
        state={
            "filters": {"title": ["refresh"]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
            "visible_columns": list(BookCRUDView.default_list_fields),
        },
    )

    response = client.get(
        reverse("sample:bigbook-list"),
        {
            "title": "refresh",
            "page_size": "5",
        },
    )
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Book list should render before checking matching saved favourite selected state."
    )
    assert 'aria-label="Saved favourite: Refresh survives"' in response_text, (
        "A matching saved favourite should survive full page rendering as selected trigger state."
    )
    assert 'data-powercrud-filter-favourites-selected="true"' in response_text, (
        "A matching saved favourite should render the selected heart state on initial page load."
    )


def test_book_view_derives_favourites_key_from_view_identity():
    """The favourites scope key should be derived from the list view's Python identity."""

    view = BookCRUDView()

    assert view.get_favourites_key() == BOOK_VIEW_KEY, (
        "BookCRUDView should derive its favourites scope key from its module and class name."
    )


def test_filter_favourite_user_resolver_defaults_to_request_user():
    """The package resolver should preserve request.user as the default owner."""

    user = object()
    request = type("Request", (), {"user": user})()

    assert get_filter_favourite_user(request) is user, (
        "The saved-favourite owner resolver should default to request.user."
    )


@pytest.mark.django_db
def test_book_view_filter_favourite_user_hook_controls_initial_list_context():
    """List views should use the overridable favourite-user hook for initial context."""

    active_user = get_user_model().objects.create_user(username="fav-list-active-user")
    owner_user = get_user_model().objects.create_user(username="fav-list-owner-user")
    favourite = SavedFilterFavourite.objects.create(
        user=owner_user,
        view_key=BOOK_VIEW_KEY,
        name="Owner favourite",
        state={
            "filters": {},
            "visible_filters": [],
            "sort": "",
            "page_size": "",
            "visible_columns": list(BookCRUDView.default_list_fields),
        },
    )

    class OwnerFavouriteBookView(BookCRUDView):
        """Book view that stores favourites against a resolved owner."""

        def get_filter_favourite_user(self, request):
            """Return the owner user instead of the active request user."""

            return owner_user

    request = RequestFactory().get("/sample/bigbook/")
    request.user = active_user
    view = OwnerFavouriteBookView()
    view.request = request
    view.role = Role.LIST
    filterset = view.get_filterset(view.get_queryset())
    list_column_state = view.build_list_column_state(queryset=filterset.qs)

    context = view.get_favourites_context(
        filterset,
        list_column_state=list_column_state,
    )

    assert context["filter_favourites_can_manage"] is True, (
        "A resolved authenticated favourite owner should keep management controls enabled."
    )
    assert [item.pk for item in context["saved_filter_favourites"]] == [favourite.pk], (
        "Initial list context should load saved favourites for the resolved owner."
    )
    assert context["selected_filter_favourite_id"] == favourite.pk, (
        "Initial list context should match selected state against the resolved owner's favourites."
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
        "visible_columns": ["title", "author", "pages"],
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
    assert json.loads(response.headers["HX-Trigger-After-Swap"]) == {
        "powercrud:favourite-saved": {"favouriteId": saved.pk}
    }, (
        "Successful favourite saves should trigger browser state sync after the panel fragment has swapped."
    )


@override_settings(
    POWERCRUD_SETTINGS={
        "FILTER_FAVOURITE_USER_RESOLVER": (
            "tests.test_favourites_contrib."
            "resolve_filter_favourite_owner_from_session"
        )
    }
)
@pytest.mark.django_db
def test_favourite_save_view_uses_configured_owner_resolver(client):
    """Saving a favourite should attach ownership to the configured resolved user."""

    active_user = get_user_model().objects.create_user(username="fav-save-active-user")
    owner_user = get_user_model().objects.create_user(username="fav-save-owner-user")
    client.force_login(active_user)
    set_filter_favourite_owner_session(client, owner_user)

    state = {"filters": {}, "visible_filters": [], "sort": "", "page_size": ""}
    response = client.post(
        reverse("powercrud:favourites-save"),
        {
            "name": "Operator owned",
            "view_key": BOOK_VIEW_KEY,
            "list_view_url": reverse("sample:bigbook-list"),
            "toolbar_dom_id": "powercrud-favourites-toolbar-test",
            "current_state_json": json.dumps(state),
            "original_target": "#content",
            "state_json": json.dumps(state),
        },
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200, (
        "Saving with a configured owner resolver should still return a toolbar fragment."
    )
    assert SavedFilterFavourite.objects.filter(
        user=owner_user,
        view_key=BOOK_VIEW_KEY,
        name="Operator owned",
    ).exists(), "The saved favourite should be created for the resolved owner user."
    assert not SavedFilterFavourite.objects.filter(
        user=active_user,
        view_key=BOOK_VIEW_KEY,
        name="Operator owned",
    ).exists(), (
        "The active request user should not own the saved favourite when the "
        "resolver returns another user."
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


@override_settings(
    POWERCRUD_SETTINGS={
        "FILTER_FAVOURITE_USER_RESOLVER": (
            "tests.test_favourites_contrib."
            "resolve_filter_favourite_owner_from_session"
        )
    }
)
@pytest.mark.django_db
def test_duplicate_favourite_save_uses_configured_owner_resolver(client):
    """Duplicate-name validation should check the resolved favourite owner."""

    active_user = get_user_model().objects.create_user(username="fav-dup-active-user")
    owner_user = get_user_model().objects.create_user(username="fav-dup-owner-user")
    client.force_login(active_user)
    set_filter_favourite_owner_session(client, owner_user)
    SavedFilterFavourite.objects.create(
        user=owner_user,
        view_key=BOOK_VIEW_KEY,
        name="Existing owner favourite",
        state={"filters": {}, "visible_filters": [], "sort": "", "page_size": ""},
    )

    response = client.post(
        reverse("powercrud:favourites-save"),
        {
            "name": "Existing owner favourite",
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
        "Duplicate validation against the resolved owner should still render as a toolbar-panel response."
    )
    assert SavedFilterFavourite.objects.filter(
        user=owner_user,
        view_key=BOOK_VIEW_KEY,
    ).count() == 1, (
        "Duplicate-name validation should not create a second favourite for "
        "the resolved owner."
    )
    assert "already exists" in response.content.decode(), (
        "The resolved owner's duplicate favourite should be reported to the active user."
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


@override_settings(
    POWERCRUD_SETTINGS={
        "FILTER_FAVOURITE_USER_RESOLVER": (
            "tests.test_favourites_contrib."
            "resolve_filter_favourite_owner_from_session"
        )
    }
)
@pytest.mark.django_db
def test_favourites_toolbar_view_lists_configured_owner_favourites(client):
    """The toolbar endpoint should list saved favourites for the resolved owner."""

    active_user = get_user_model().objects.create_user(username="fav-toolbar-active-user")
    owner_user = get_user_model().objects.create_user(username="fav-toolbar-owner-user")
    client.force_login(active_user)
    set_filter_favourite_owner_session(client, owner_user)
    SavedFilterFavourite.objects.create(
        user=owner_user,
        view_key=BOOK_VIEW_KEY,
        name="Owner toolbar favourite",
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
        },
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200, (
        "The toolbar endpoint should render successfully when an owner resolver is configured."
    )
    assert "Owner toolbar favourite" in response.content.decode(), (
        "The toolbar endpoint should list saved favourites for the resolved owner."
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
            "visible_columns": ["title", "pages"],
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
    assert (
        client.session[LIST_OPTIONS_SESSION_KEY][BOOK_VIEW_KEY]
        == {"visible_columns": ["title", "pages"]}
    ), (
        "Applying a saved favourite with visible_columns should store that column state in the session."
    )


@pytest.mark.django_db
def test_favourite_apply_view_clears_columns_for_legacy_filter_only_state(client):
    """Applying a legacy filter-only favourite should return visible columns to defaults."""

    user = get_user_model().objects.create_user(username="fav-legacy-apply-user")
    favourite = SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Legacy favourite",
        state={
            "filters": {"title": ["django"]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
        },
    )
    client.force_login(user)
    session = client.session
    session[LIST_OPTIONS_SESSION_KEY] = {
        BOOK_VIEW_KEY: {"visible_columns": ["title", "pages"]}
    }
    session.save()

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
        "Applying a legacy saved favourite should still navigate successfully."
    )
    assert BOOK_VIEW_KEY not in client.session.get(LIST_OPTIONS_SESSION_KEY, {}), (
        "Legacy favourites without visible_columns should clear current column session state."
    )


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
        "visible_columns": ["title", "genres"],
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
    assert json.loads(response.headers["HX-Trigger-After-Swap"]) == {
        "powercrud:favourite-updated": {"favouriteId": favourite.pk}
    }, (
        "Successful favourite updates should trigger browser state sync after the panel fragment has swapped."
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
    favourite_id = favourite.pk
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
    assert json.loads(response.headers["HX-Trigger-After-Swap"]) == {
        "powercrud:favourite-deleted": {"favouriteId": favourite_id}
    }, (
        "Successful favourite deletes should trigger browser state sync after the panel fragment has swapped."
    )


@override_settings(
    POWERCRUD_SETTINGS={
        "FILTER_FAVOURITE_USER_RESOLVER": (
            "tests.test_favourites_contrib."
            "resolve_filter_favourite_owner_from_session"
        )
    }
)
@pytest.mark.django_db
def test_favourite_apply_update_and_delete_use_configured_owner_resolver(client):
    """Shared action endpoints should use the resolved owner for favourite lookups."""

    active_user = get_user_model().objects.create_user(username="fav-action-active-user")
    owner_user = get_user_model().objects.create_user(username="fav-action-owner-user")
    favourite = SavedFilterFavourite.objects.create(
        user=owner_user,
        view_key=BOOK_VIEW_KEY,
        name="Owner action favourite",
        state={
            "filters": {"title": ["owner"]},
            "visible_filters": [],
            "sort": "",
            "page_size": "",
        },
    )
    client.force_login(active_user)
    set_filter_favourite_owner_session(client, owner_user)

    apply_response = client.get(
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
    updated_state = {
        "filters": {"title": ["updated"]},
        "visible_filters": [],
        "sort": "",
        "page_size": "",
    }
    update_response = client.post(
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
    delete_response = client.post(
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

    assert apply_response.status_code == 200, (
        "Applying a favourite owned by the resolved user should succeed even "
        "when request.user differs."
    )
    assert "title=owner" in apply_response.headers["HX-Location"], (
        "Applying should use the resolved owner's saved favourite state."
    )
    assert update_response.status_code == 200, (
        "Updating a favourite owned by the resolved user should succeed."
    )
    assert favourite.state == updated_state, (
        "Updating should modify the resolved owner's favourite."
    )
    assert delete_response.status_code == 200, (
        "Deleting a favourite owned by the resolved user should succeed."
    )
    assert not SavedFilterFavourite.objects.filter(pk=favourite.pk).exists(), (
        "Deleting should remove the resolved owner's favourite."
    )


def test_build_query_string_from_state_serializes_multi_value_filters_in_order():
    """Saved state should round-trip back to ordered query-string parameters."""

    query_string = build_query_string_from_state(
        {
            "filters": {"title": ["django"], "genres": ["2", "5"]},
            "visible_filters": ["genres", "pages"],
            "sort": "-published_date",
            "page_size": "25",
            "visible_columns": ["title", "pages"],
        }
    )

    assert query_string == (
        "title=django&genres=2&genres=5&visible_filters=genres&visible_filters=pages&sort=-published_date&page_size=25"
    ), "Serializing saved favourites should preserve query-backed state while omitting session-backed visible columns."


def test_normalise_saved_state_preserves_optional_visible_columns():
    """Saved favourite state should preserve optional visible columns without requiring them."""

    assert normalise_saved_state(
        {
            "filters": {},
            "visible_filters": [],
            "sort": "",
            "page_size": "",
            "visible_columns": ["title", "pages", "title", ""],
        }
    )["visible_columns"] == ["title", "pages"], (
        "Visible columns should be normalized as ordered unique string values."
    )
    assert "visible_columns" not in normalise_saved_state(
        {"filters": {}, "visible_filters": [], "sort": "", "page_size": ""}
    ), (
        "Legacy saved favourites without visible_columns should remain valid filter-only payloads."
    )
