"""Shared server-side behaviour matrix for selectable template packs."""

import json
from datetime import date

import pytest
from crispy_forms.helper import FormHelper
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.urls import reverse

from powercrud.contrib.favourites.models import SavedFilterFavourite
from powercrud.mixins.list_options_mixin import LIST_OPTIONS_SESSION_KEY
from powercrud.template_packs import get_configured_template_pack
from sample.models import Author, Book
from sample.urls import urlpatterns
from sample.views import BookCRUDView


BOOTSTRAP_SELECTOR = "powercrud.contrib.bootstrap5:template_pack"
BOOK_VIEW_KEY = f"{BookCRUDView.__module__}.{BookCRUDView.__name__}"


def _create_shared_books() -> tuple[Author, list[Book]]:
    """Create enough sample records to exercise list and mutation scenarios."""
    author = Author.objects.create(name="Shared Matrix Author")
    books = [
        Book.objects.create(
            title=f"Shared Matrix Book {number}",
            author=author,
            published_date=date(2024, 1, number + 1),
            bestseller=False,
            isbn=f"9780000006{number:03d}",
            pages=200 + number,
        )
        for number in range(7)
    ]
    return author, books


def _login_manager(client) -> None:
    """Establish the sample role that may use the shared mutation routes."""
    response = client.post(reverse("sample:demo-login", args=["manager"]))
    assert response.status_code == 302, (
        "The shared sample manager role should authenticate before matrix mutation checks."
    )


@pytest.mark.django_db
def test_shared_catalogue_and_selected_pack_matrix():
    """Both presentations should exercise the one sample catalogue and selected pack."""
    route_names = {pattern.name for pattern in urlpatterns if pattern.name}
    assert {
        "bigbook-list",
        "bigbook-create",
        "bigbook-detail",
        "bigbook-delete",
        "bigbook-bulk-edit",
        "bigbook-inline-row",
        "bigbook-inline-dependency",
        "bigbook-columns",
    } <= route_names, "The shared sample URL catalogue must retain every matrix route."

    template_pack = get_configured_template_pack()
    active_selector = settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK")
    if active_selector == BOOTSTRAP_SELECTOR:
        assert template_pack.identity == "bootstrap5", (
            "Bootstrap settings must select the optional Bootstrap pack for the shared matrix."
        )
    else:
        assert active_selector is None, (
            "The shared matrix should run only under implicit DaisyUI or explicit Bootstrap settings."
        )
        assert template_pack.identity == "daisyui", (
            "Default settings must retain the compatible DaisyUI pack for the shared matrix."
        )


@pytest.mark.django_db
def test_shared_list_htmx_columns_and_favourites_matrix(client):
    """Every selectable pack should preserve list and fragment transport semantics."""
    _create_shared_books()
    list_url = reverse("sample:bigbook-list")

    full_response = client.get(f"{list_url}?page_size=5&sort=title")
    htmx_response = client.get(
        f"{list_url}?page_size=5&sort=title", HTTP_HX_REQUEST="true"
    )
    csrf_response = client.get(
        list_url,
        {"title": "Shared Matrix", "csrfmiddlewaretoken": "leaked-token"},
        HTTP_HX_REQUEST="true",
        HTTP_HX_TARGET="content",
    )

    for response, response_name in (
        (full_response, "full-page"),
        (htmx_response, "HTMX"),
    ):
        response_text = response.content.decode()
        assert response.status_code == 200, (
            f"The {response_name} shared Book list should render for the selected pack."
        )
        assert "Shared Matrix Book 0" in response_text, (
            f"The {response_name} shared Book list should retain the seeded catalogue."
        )
        assert 'id="filtered_results"' in response_text, (
            f"The {response_name} list should retain the stable HTMX swap target."
        )
        assert 'data-powercrud-pagination="true"' in response_text, (
            f"The {response_name} list should retain pagination lifecycle semantics."
        )
        assert 'data-powercrud-list-columns-trigger="true"' in response_text, (
            f"The {response_name} list should retain the column chooser integration."
        )

    assert "csrfmiddlewaretoken" not in csrf_response["HX-Push-Url"], (
        "HTMX list navigation must never reflect CSRF tokens in its pushed URL."
    )
    assert "title=Shared+Matrix" in csrf_response["HX-Push-Url"], (
        "HTMX list navigation must retain legitimate filter state in its pushed URL."
    )

    columns_response = client.post(
        reverse("sample:bigbook-columns"),
        {
            "list_view_url": list_url,
            "visible_columns": ["title", "pages"],
            "list_columns_action": "apply",
        },
    )
    assert columns_response.status_code == 302, (
        "The shared column chooser must preserve its ordinary form submission path."
    )
    assert client.session[LIST_OPTIONS_SESSION_KEY][BOOK_VIEW_KEY] == {
        "visible_columns": ["title", "pages"]
    }, "The column chooser must persist the selected column state."

    user = get_user_model().objects.create_user(username="matrix-favourite-user")
    favourite = SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Shared matrix favourite",
        state={
            "filters": {"title": ["Shared Matrix"]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
            "visible_columns": ["title", "pages"],
        },
    )
    client.force_login(user)
    favourite_response = client.get(
        reverse("powercrud:favourites-apply"),
        {
            "favourite_id": favourite.pk,
            "view_key": BOOK_VIEW_KEY,
            "list_view_url": list_url,
            "toolbar_dom_id": "shared-matrix-favourites",
            "current_state_json": "{}",
            "original_target": "#content",
        },
        HTTP_HX_REQUEST="true",
    )
    assert favourite_response.status_code == 200, (
        "The shared favourite application route should retain HTMX navigation."
    )
    assert json.loads(favourite_response["HX-Location"])["target"] == "#content", (
        "A shared favourite must refresh the original shared list target."
    )
    assert client.session[LIST_OPTIONS_SESSION_KEY][BOOK_VIEW_KEY] == {
        "visible_columns": ["title", "pages"]
    }, "A shared favourite must restore its saved visible columns."


@pytest.mark.django_db
def test_shared_form_matrix_covers_native_and_crispy_rendering(client):
    """Every selected pack should retain native and declared crispy form outcomes."""

    class RequiredNameForm(forms.Form):
        """Expose required-field feedback in both supported form renderers."""

        name = forms.CharField(label="Display name")

    template_pack = get_configured_template_pack()
    form = RequiredNameForm(data={"name": ""})
    form.helper = FormHelper()
    form.helper.form_tag = False
    form.helper.disable_csrf = True
    assert not form.is_valid(), "The matrix form fixture should expose required-field validation."

    native = render_to_string(
        f"{template_pack.template_namespace}/partial/form_fields.html",
        {"form": form, "use_crispy": False},
    )
    crispy = render_to_string(
        f"{template_pack.template_namespace}/partial/form_fields.html",
        {
            "form": form,
            "use_crispy": True,
            "framework_template_path": template_pack.template_namespace,
        },
    )

    for rendered, renderer_name in ((native, "native"), (crispy, "crispy")):
        assert 'name="name"' in rendered and "Display name" in rendered, (
            f"The {renderer_name} selected-pack form should retain the bound field and label."
        )
        assert "This field is required" in rendered, (
            f"The {renderer_name} selected-pack form should retain validation feedback."
        )
    assert "<form" not in crispy, (
        "The reusable crispy fields fragment must not introduce a nested form element."
    )

    _login_manager(client)
    response = client.get(reverse("sample:bigbook-create"))
    assert response.status_code == 200, "The shared create route should render for every pack."
    assert 'data-powercrud-form="object"' in response.content.decode(), (
        "The shared create route should retain its object-form runtime hook."
    )


@pytest.mark.django_db
def test_shared_detail_delete_and_modal_matrix(client):
    """Detail and delete routes should retain full-page and modal fragment responses."""
    _author, books = _create_shared_books()
    _login_manager(client)
    book = books[0]

    route_checks = (
        ("detail", reverse("sample:bigbook-detail", args=[book.pk])),
        ("delete", reverse("sample:bigbook-delete", args=[book.pk])),
    )
    for route_name, route_url in route_checks:
        full_response = client.get(route_url)
        htmx_response = client.get(route_url, HTTP_HX_REQUEST="true")
        for response, response_name in ((full_response, "full-page"), (htmx_response, "HTMX")):
            assert response.status_code == 200, (
                f"The {response_name} shared Book {route_name} route should render for every pack."
            )
            assert "Shared Matrix Book 0" in response.content.decode(), (
                f"The {response_name} Book {route_name} response should retain the selected object."
            )


@pytest.mark.django_db
def test_shared_bulk_async_and_inline_matrix(client):
    """Declared bulk, async, and inline capabilities should remain selected-pack usable."""
    _author, books = _create_shared_books()
    _login_manager(client)
    list_url = reverse("sample:bigbook-list")
    inline_url = reverse("sample:bigbook-inline-row", args=[books[0].pk])
    dependency_url = reverse("sample:bigbook-inline-dependency", args=[books[0].pk])
    bulk_url = reverse("sample:bigbook-bulk-edit")

    list_response = client.get(list_url)
    inline_response = client.get(inline_url, HTTP_HX_REQUEST="true")
    dependency_response = client.post(
        dependency_url,
        {"field": "genres", "pk": books[0].pk, "author": books[0].author_id},
        HTTP_HX_REQUEST="true",
    )
    bulk_response = client.get(
        bulk_url,
        {"selected_ids[]": [book.pk for book in books[:2]]},
        HTTP_HX_REQUEST="true",
    )

    assert list_response.status_code == 200, "The shared list should expose bulk and inline entry points."
    list_text = list_response.content.decode()
    assert 'data-powercrud-row-select="true"' in list_text, (
        "The selected pack should expose shared bulk-selection controls."
    )
    assert 'data-inline-row="true"' in list_text, (
        "The selected pack should expose shared inline-edit display rows."
    )
    assert inline_response.status_code == 200, (
        "The shared inline endpoint should render a selected-pack editable row."
    )
    inline_text = inline_response.content.decode()
    assert 'data-inline-row="true"' in inline_text and 'data-inline-save' in inline_text, (
        "The selected pack inline response should retain its row and save semantics."
    )
    assert dependency_response.status_code == 200, (
        "The shared inline dependency endpoint should render a selected-pack field."
    )
    assert 'data-inline-dependent="true"' in dependency_response.content.decode(), (
        "The selected pack dependency response should retain inline dependency metadata."
    )
    assert bulk_response.status_code == 200, (
        "The shared bulk endpoint should render for a selected pack with selected records."
    )
    bulk_text = bulk_response.content.decode()
    assert 'data-powercrud-form="bulk"' in bulk_text, (
        "The selected pack bulk response should retain its shared bulk-form runtime hook."
    )
    async_outcome = render_to_string(
        f"{get_configured_template_pack().template_namespace}/bulk_edit_form.html#async_queue_success",
        {"bulk_outcomes_template_paths": []},
    )
    assert 'data-powercrud-bulk-outcome="queued"' in async_outcome, (
        "The selected pack should retain the declared asynchronous bulk outcome fragment."
    )
