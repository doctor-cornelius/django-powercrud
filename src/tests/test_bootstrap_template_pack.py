"""Focused Phase 7.1 contract tests for the optional Bootstrap 5 pack."""

from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from crispy_forms.helper import FormHelper
from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import get_template, render_to_string
from django.test import RequestFactory
from django.urls import reverse

from powercrud.template_pack_validation import validate_template_pack
from powercrud.modal_presentation import modal_presentation_attributes
from powercrud.template_packs import (
    TEMPLATE_PACK_CONTRACT_VERSION,
    TemplatePack,
    get_configured_template_pack,
    get_selected_template_pack,
    resolve_template_pack,
)
from sample.models import Author, Book


BOOTSTRAP_SELECTOR = "powercrud.contrib.bootstrap5:template_pack"
BOOTSTRAP_NAMESPACE = "powercrud/packs/bootstrap5"
BOOTSTRAP_TEMPLATE_PATHS = frozenset(
    {
        "bulk_edit_form.html",
        "crispy_partials.html",
        "layout/inline_field.html",
        "object_confirm_delete.html",
        "object_detail.html",
        "object_form.html",
        "object_list.html",
        "partial/bulk_edit_errors.html",
        "partial/bulk_fields.html",
        "partial/bulk_form.html",
        "partial/bulk_outcomes.html",
        "partial/bulk_selection_controls.html",
        "partial/bulk_selection_status.html",
        "partial/delete_actions.html",
        "partial/delete_conflict.html",
        "partial/delete_content.html",
        "partial/delete_shell.html",
        "partial/detail.html",
        "partial/detail_content.html",
        "partial/detail_shell.html",
        "partial/extra_buttons.html",
        "partial/filter_form.html",
        "partial/filter_favourites.html",
        "partial/filter_favourites_panel.html",
        "partial/filter_panel_actions.html",
        "partial/filter_trigger.html",
        "partial/form_actions.html",
        "partial/form_conflict.html",
        "partial/form_fields.html",
        "partial/form_shell.html",
        "partial/inline_field.html",
        "partial/inline_row_display.html",
        "partial/inline_row_form.html",
        "partial/list.html",
        "partial/list_actions.html",
        "partial/list_columns.html",
        "partial/modal.html",
        "partial/modal_content.html",
        "partial/modal_shell.html",
        "partial/page_size_selector.html",
        "partial/pagination.html",
        "partial/row_actions.html",
        "partial/table_header.html",
        "partial/table_row.html",
        "partial/table_shell.html",
    }
)


pytestmark = pytest.mark.skipif(
    settings.SETTINGS_MODULE != "tests.settings_bootstrap",
    reason="Bootstrap pack tests require the optional Bootstrap settings overlay.",
)


def test_bootstrap_declaration_is_opt_in_with_completed_modal_lifecycle():
    """The Bootstrap declaration should advertise only completed capabilities."""
    template_pack = resolve_template_pack(BOOTSTRAP_SELECTOR)

    assert template_pack == TemplatePack(
        identity="bootstrap5",
        contract_version=TEMPLATE_PACK_CONTRACT_VERSION,
        template_namespace=BOOTSTRAP_NAMESPACE,
        template_package="powercrud",
        template_resource_root="contrib/bootstrap5/templates/powercrud/packs/bootstrap5",
        legacy_copy_destination=None,
        framework_adapter="bootstrap5",
        variant_adapter=None,
        capabilities=frozenset(
            {"list", "form", "detail", "delete", "filters", "modal", "bulk", "async", "inline", "favourites"}
        ),
        supports_native_forms=True,
        crispy_template_packs=frozenset({"bootstrap5"}),
        django_app="powercrud.contrib.bootstrap5",
        manual_assets=(
            "powercrud/contrib/bootstrap5/css/bootstrap5.css",
            "powercrud/contrib/bootstrap5/js/bootstrap5.js",
        ),
        vite_assets=("config/static/js/bootstrap5.js",),
        unsupported_presentation_options=frozenset(),
    ), "The selected Bootstrap declaration should describe every completed Bootstrap presentation capability."

    with pytest.raises(ImproperlyConfigured, match="Unknown PowerCRUD template pack"):
        resolve_template_pack("bootstrap5")


def test_bootstrap_selected_namespace_and_validation_are_available():
    """The installed overlay must select a valid pack without altering its declaration."""
    selected = get_selected_template_pack()
    configured = get_configured_template_pack()

    assert selected.identity == "bootstrap5", "Bootstrap settings should select the optional pack."
    assert configured is not None and configured.template_namespace == BOOTSTRAP_NAMESPACE, (
        "Configured Bootstrap settings should resolve the package-owned Bootstrap namespace."
    )
    validate_template_pack(selected)


def test_bootstrap_namespace_contains_only_pack_owned_baseline_templates():
    """The selectable baseline must not delegate presentation back to DaisyUI."""
    root = (
        Path(settings.BASE_DIR)
        / "powercrud"
        / "contrib"
        / "bootstrap5"
        / "templates"
        / "powercrud"
        / "packs"
        / "bootstrap5"
    )
    discovered = {path.relative_to(root).as_posix() for path in root.rglob("*.html")}

    assert discovered == BOOTSTRAP_TEMPLATE_PATHS, (
        "Bootstrap Phase 7.1 should ship its exact baseline inventory and no accidental "
        "DaisyUI facade tree."
    )
    for relative_path in discovered:
        source = (root / relative_path).read_text(encoding="utf-8")
        assert "powercrud/packs/daisyui" not in source, (
            f"Bootstrap baseline template {relative_path} must own its presentation markup."
        )
        if relative_path != "bulk_edit_form.html":
            assert "<script" not in source, (
                f"Bootstrap template {relative_path} must not duplicate PowerCRUD runtime code."
            )


def test_bootstrap_roots_and_required_fragments_compile():
    """The validator's baseline resources must resolve through Django's app loader."""
    for relative_path in BOOTSTRAP_TEMPLATE_PATHS:
        assert get_template(f"{BOOTSTRAP_NAMESPACE}/{relative_path}") is not None, (
            f"Bootstrap template {relative_path} should compile through the selected namespace."
        )

    for fragment_name in (
        "object_list.html#pcrud_content",
        "object_list.html#filtered_results",
        "object_list.html#pagination",
        "object_form.html#pcrud_content",
        "object_form.html#conflict_detected",
        "object_form.html#normal_content",
        "object_detail.html#pcrud_content",
        "object_confirm_delete.html#pcrud_content",
        "object_confirm_delete.html#conflict_detected",
        "object_confirm_delete.html#normal_content",
        "object_list.html#bulk_selection_status",
        "object_list.html#list_columns",
        "bulk_edit_form.html#full_form",
        "bulk_edit_form.html#async_queue_success",
        "partial/bulk_edit_errors.html#bulk_edit_error",
        "partial/bulk_edit_errors.html#bulk_edit_conflict",
        "partial/list.html#inline_row_display",
        "partial/list.html#inline_row_form",
        "crispy_partials.html#load_tags",
        "crispy_partials.html#crispy_form",
    ):
        assert get_template(f"{BOOTSTRAP_NAMESPACE}/{fragment_name}") is not None, (
            f"Bootstrap baseline should retain direct fragment {fragment_name}."
        )


def test_bootstrap_optional_components_preserve_shared_semantic_hooks():
    """Bootstrap optional components should keep the server and adapter contracts intact."""
    request = RequestFactory().get("/books/?title=Power")
    bulk_status = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/partial/bulk_selection_status.html",
        {
            "list_view_url": "/books/",
            "selected_count": 2,
            "enable_bulk_edit": True,
            "modal_target": "powercrudModalContent",
            "view": SimpleNamespace(get_extra_button_classes=""),
        },
        request=request,
    )
    columns = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/partial/list_columns.html",
        {
            "request": request,
            "list_options_url": "/books/options/",
            "list_view_url": "/books/",
            "original_target": "#content",
            "use_htmx": True,
            "view": SimpleNamespace(get_extra_button_classes=""),
            "list_column_state": {
                "active_columns": ["title"],
                "allowed_columns": ["title", "author"],
                "choices": [
                    {"name": "title", "label": "Title", "is_default": True, "is_active": True},
                    {"name": "author", "label": "Author", "is_default": False, "is_active": False},
                ],
            },
        },
        request=request,
    )
    field = forms.CharField().get_bound_field(forms.Form(), "genre")
    inline_field = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/partial/inline_field.html",
        {
            "field": field,
            "field_name": "genre",
            "field_dependency": {"depends_on": ["author"], "endpoint_url": "/books/dependency/"},
            "dependency_endpoint_url": "/books/dependency/",
        },
    )
    favourites = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/partial/filter_favourites.html",
        {
            "filter_favourites_toolbar_dom_id": "book-favourites",
            "filter_favourites_view_key": "sample.bigbook",
            "current_list_state_json": "{}",
            "selected_filter_favourite_name": "",
            "framework_template_path": BOOTSTRAP_NAMESPACE,
            "view": SimpleNamespace(get_extra_button_classes=""),
        },
    )
    row_actions = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/partial/row_actions.html",
        {
            "row_actions": SimpleNamespace(
                standard_actions=[],
                show_extra_dropdown=True,
                dropdown_trigger_class="",
                row_action_states_url="/books/7/action-states/",
                extra_actions=[
                    SimpleNamespace(
                        href="/books/7/archive/",
                        class_name="",
                        tooltip_text="Archive this book",
                        style="",
                        use_htmx=True,
                        hx_post=True,
                        target="#book-row-7",
                        use_history=False,
                        modal_attrs="",
                        modal_box_classes="",
                        refresh_list_on_modal_close=False,
                        disable=False,
                        lazy_row_action_state=True,
                        action_index=0,
                        lazy_hidden_if=False,
                        inline_action="archive",
                        text="Archive",
                    )
                ],
            )
        },
    )

    assert 'data-powercrud-bulk-actions="true"' in bulk_status and 'data-powercrud-modal-trigger="true"' in bulk_status, (
        "Bootstrap bulk status should preserve selection refresh and modal-loading hooks."
    )
    assert '<details class="dropdown"' in columns and 'data-powercrud-list-columns-panel="true"' in columns, (
        "Bootstrap columns should retain the native details/summary and adapter panel contracts."
    )
    assert 'name="visible_columns"' in columns and 'hx-post="/books/options/"' in columns, (
        "Bootstrap columns should retain selection fields and HTMX list-options transport."
    )
    assert 'data-inline-field="genre"' in inline_field and 'data-inline-depends-on="author"' in inline_field, (
        "Bootstrap inline fields should preserve dependency metadata for the shared adapter."
    )
    assert 'data-powercrud-filter-favourites-trigger="true"' in favourites and 'data-powercrud-filter-favourites-template="true"' in favourites, (
        "Bootstrap favourites should retain the private toolbar and deferred-panel hooks."
    )
    assert '<li><a href="/books/7/archive/"' in row_actions and 'data-powercrud-row-action-state-mode="lazy"' in row_actions, (
        "Bootstrap row-action menus should preserve list-item semantics and lazy action-state metadata."
    )


def test_bootstrap_table_alignment_and_dropdown_button_classes_use_portable_values():
    """Bootstrap must translate semantic alignment and preserve shared dropdown classes."""
    table_header = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/partial/table_header.html",
        {
            "enable_selection_controls": False,
            "headers": [
                {"field_name": "title", "align": "left", "is_sortable": False},
                {"field_name": "pages", "align": "right", "is_sortable": False},
            ],
            "has_row_actions": False,
        },
    )
    dropdown = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/partial/extra_buttons.html",
        {
            "extra_buttons_mode": "dropdown",
            "extra_button_classes": "shared-extra-class",
            "extra_buttons": [
                {
                    "href": "/books/export/",
                    "extra_class_attrs": "",
                    "button_class": "btn-primary",
                    "disabled": False,
                    "link_attrs": "",
                    "disabled_attrs": "",
                    "selection_attrs": "",
                    "disabled_reason": "",
                    "text": "Export",
                }
            ],
        },
    )

    assert 'class="pc-table-column-width text-start"' in table_header, (
        "The public left alignment must map to Bootstrap's text-start utility."
    )
    assert 'class="pc-table-column-width text-end"' in table_header, (
        "The public right alignment must map to Bootstrap's text-end utility."
    )
    assert "shared-extra-class btn-primary" in dropdown, (
        "Dropdown entries must receive the same configured extra-button classes as button mode."
    )
    assert "dropdown-menu show" not in dropdown, (
        "Bootstrap extra-button menus must remain closed until their details control opens."
    )


def test_bootstrap_modal_templates_preserve_portable_presentation_attributes():
    """The Bootstrap markup must pass semantic modal settings to its lifecycle adapter."""
    presentation_attrs = modal_presentation_attributes(
        {
            "size": "wide",
            "max_width": "60rem",
            "max_height": "75dvh",
            "scroll": "modal",
            "fullscreen": False,
            "vertical_alignment": "top",
        }
    )
    shell = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/partial/modal_shell.html",
        {
            "modal_id": "portableModal",
            "modal_target": "portableModalContent",
            "modal_classes": "modal",
            "modal_box_classes": "modal-dialog modal-dialog-scrollable",
            "modal_body_classes": "",
            "modal_presentation_attrs": presentation_attrs,
            "bulk_modal_presentation_attrs": presentation_attrs,
            "modal_uses_legacy_classes": False,
            "modal_content_template_paths": [
                f"{BOOTSTRAP_NAMESPACE}/partial/modal_content.html"
            ],
        },
    )
    bulk = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/partial/bulk_selection_status.html",
        {
            "list_view_url": "/books/",
            "selected_count": 2,
            "enable_bulk_edit": True,
            "modal_target": "portableModalContent",
            "bulk_modal_presentation_attrs": presentation_attrs,
            "modal_uses_legacy_classes": False,
            "view": SimpleNamespace(get_extra_button_classes=""),
        },
    )

    for attribute in (
        'data-powercrud-modal-size="wide"',
        'data-powercrud-modal-max-width="60rem"',
        'data-powercrud-modal-max-height="75dvh"',
        'data-powercrud-modal-scroll="modal"',
        'data-powercrud-modal-fullscreen="false"',
        'data-powercrud-modal-vertical-alignment="top"',
    ):
        assert attribute in shell and attribute in bulk, (
            "Bootstrap modal and bulk triggers must retain each portable presentation field."
        )


def test_bootstrap_form_fields_render_native_and_crispy_validation():
    """Both Bootstrap field renderers should preserve accessible bound-form feedback."""

    class RequiredNameForm(forms.Form):
        """Small bound form that exposes native and crispy validation output."""

        name = forms.CharField(label="Display name", help_text="Shown to collaborators")

    form = RequiredNameForm(data={"name": ""})
    form.helper = FormHelper()
    form.helper.form_tag = False
    form.helper.disable_csrf = True
    assert not form.is_valid(), "The Bootstrap form fixture should contain a required-field error."

    native = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/partial/form_fields.html",
        {"form": form, "use_crispy": False},
    )
    crispy = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/partial/form_fields.html",
        {
            "form": form,
            "use_crispy": True,
            "framework_template_path": BOOTSTRAP_NAMESPACE,
        },
    )

    for rendered, renderer_name in ((native, "native"), (crispy, "crispy")):
        assert 'name="name"' in rendered and "Display name" in rendered, (
            f"The Bootstrap {renderer_name} renderer should preserve the bound input and label."
        )
        assert "This field is required" in rendered, (
            f"The Bootstrap {renderer_name} renderer should preserve validation feedback."
        )
    assert 'class="form-control is-invalid"' in native, (
        "The native Bootstrap renderer should apply the pack-owned control and invalid classes."
    )
    assert 'aria-describedby="id_name_help id_name_errors"' in native, (
        "The native Bootstrap renderer should relate help and error feedback to the invalid control."
    )
    assert 'aria-describedby="id_name_help id_name_errors"' in native, (
        "The native Bootstrap renderer should relate the control to help and error text."
    )
    assert "Shown to collaborators" in native, (
        "The native Bootstrap renderer should preserve help text."
    )
    assert "<form" not in native and "<form" not in crispy, (
        "Reusable Bootstrap field fragments must not introduce nested forms."
    )


def test_bootstrap_form_delete_and_conflict_fragments_preserve_transport_contract():
    """Bootstrap CRUD leaves must retain the shared transport and return semantics."""

    class UploadForm(forms.Form):
        """Minimal multipart form used to prove shell ownership."""

        attachment = forms.FileField(required=False)

    request = RequestFactory().get(
        "/books/new/?status=open&status=review&page=3&csrfmiddlewaretoken=leaked"
    )
    form_context = {
        "request": request,
        "form": UploadForm(),
        "object": None,
        "object_verbose_name": "book",
        "form_display_items": [],
        "create_view_url": "/books/new/",
        "use_htmx": True,
        "use_modal": True,
        "original_target": "#powercrudModalContent",
        "use_crispy": False,
        "csrf_token": "bootstrap-token",
        "framework_template_path": BOOTSTRAP_NAMESPACE,
        "form_shell_template_paths": [f"{BOOTSTRAP_NAMESPACE}/partial/form_shell.html"],
    }
    form_rendered = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/object_form.html#normal_content",
        form_context,
        request=request,
    )
    assert 'method="post"' in form_rendered and 'action="/books/new/"' in form_rendered, (
        "The Bootstrap form shell should own the POST transport action."
    )
    assert 'enctype="multipart/form-data"' in form_rendered and 'data-powercrud-form="object"' in form_rendered, (
        "The Bootstrap form shell should retain multipart and runtime form hooks."
    )
    assert 'hx-post="/books/new/"' in form_rendered and 'hx-target="#powercrudModalContent"' in form_rendered, (
        "The Bootstrap form shell should retain modal-compatible HTMX transport."
    )
    assert 'hx-push-url="false"' in form_rendered and "X-Redisplay-Object-List" in form_rendered, (
        "The Bootstrap form shell should retain modal history and list redisplay semantics."
    )
    assert form_rendered.count('name="_powercrud_filter_status"') == 2, (
        "The Bootstrap form shell should retain repeated non-page query values."
    )
    assert "_powercrud_filter_page" not in form_rendered and "_powercrud_filter_csrfmiddlewaretoken" not in form_rendered, (
        "The Bootstrap form shell should exclude page and CSRF query values from retained state."
    )
    assert form_rendered.count("<form") == 1, (
        "The Bootstrap form shell and fields must not create nested forms."
    )

    delete_context = {
        "request": request,
        "object": "Ada",
        "object_verbose_name": "author",
        "delete_errors": ["Protected relationship"],
        "delete_view_url": "/authors/7/delete/",
        "use_htmx": True,
        "original_target": "#author-list",
        "csrf_token": "bootstrap-token",
        "framework_template_path": BOOTSTRAP_NAMESPACE,
        "delete_content_template_paths": [f"{BOOTSTRAP_NAMESPACE}/partial/delete_content.html"],
    }
    delete_rendered = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/object_confirm_delete.html#normal_content",
        delete_context,
        request=request,
    )
    assert "Protected relationship" in delete_rendered and 'action="/authors/7/delete/"' in delete_rendered, (
        "The Bootstrap delete content should retain errors and its POST action."
    )
    assert 'hx-post="/authors/7/delete/"' in delete_rendered and 'hx-target="#author-list"' in delete_rendered, (
        "The Bootstrap delete content should retain its HTMX target and post URL."
    )
    assert 'hx-push-url="false"' in delete_rendered and "X-Redisplay-Object-List" in delete_rendered, (
        "The Bootstrap delete content should retain list-redisplay semantics."
    )

    conflict_context = {
        "request": RequestFactory().get("/authors/7/edit/?page_size=25"),
        "conflict_message": "An update is running",
        "object": "Ada",
        "list_view_url": "/authors/",
        "filter_params": "status=open",
        "original_target": "#author-list",
    }
    conflict_rendered = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/partial/form_conflict.html",
        {**conflict_context, "use_htmx": True, "use_modal": False},
    )
    modal_conflict_rendered = render_to_string(
        f"{BOOTSTRAP_NAMESPACE}/partial/form_conflict.html",
        {**conflict_context, "use_htmx": True, "use_modal": True},
    )
    assert 'hx-get="/authors/?page_size=25&status=open"' in conflict_rendered, (
        "The Bootstrap form conflict should retain its current HTMX list URL."
    )
    assert 'hx-target="#author-list"' in conflict_rendered and 'hx-push-url="true"' in conflict_rendered, (
        "The Bootstrap form conflict should retain its HTMX target and history behavior."
    )
    assert "Return to List" not in modal_conflict_rendered, (
        "The Bootstrap form conflict should suppress the list return in a modal context."
    )


@pytest.mark.django_db
def test_bootstrap_native_baseline_renders_the_shared_crud_routes(client):
    """The declared baseline must render list, form, detail, and delete without optional features."""
    author = Author.objects.create(name="Bootstrap baseline author")
    book = Book.objects.create(
        title="Bootstrap baseline book",
        author=author,
        published_date=date(2024, 1, 1),
        isbn="9780000007001",
        pages=240,
    )

    list_response = client.get(reverse("sample:bigbook-list"))
    assert list_response.status_code == 200, "The Bootstrap baseline list route should render."
    assert "Bootstrap baseline book" in list_response.content.decode(), (
        "The Bootstrap baseline list should render shared sample data."
    )
    assert 'data-powercrud-object-list="true"' in list_response.content.decode(), (
        "The Bootstrap baseline list should retain the stable lifecycle root hook."
    )

    login_response = client.post(reverse("sample:demo-login", args=["manager"]))
    assert login_response.status_code == 302, "The sample manager role should authenticate for CRUD routes."
    for route_name, route_url in (
        ("create", reverse("sample:bigbook-create")),
        ("detail", reverse("sample:bigbook-detail", args=[book.pk])),
        ("delete", reverse("sample:bigbook-delete", args=[book.pk])),
    ):
        response = client.get(route_url)
        assert response.status_code == 200, f"The Bootstrap baseline {route_name} route should render."
        assert "Bootstrap baseline book" in response.content.decode() or route_name == "create", (
            f"The Bootstrap baseline {route_name} route should retain shared object context."
        )


@pytest.mark.django_db
def test_bootstrap_list_filters_sort_pagination_and_htmx_contract(client):
    """Bootstrap owns list navigation through the shared semantic server contract."""
    author = Author.objects.create(name="Bootstrap list author")
    for number in range(6):
        Book.objects.create(
            title=f"Bootstrap list book {number}",
            author=author,
            published_date=date(2024, 1, number + 1),
            isbn=f"97800000071{number:02d}",
            pages=200 + number,
        )

    list_url = reverse("sample:bigbook-list")
    full_response = client.get(f"{list_url}?page_size=5&sort=title")
    htmx_response = client.get(
        f"{list_url}?page_size=5&sort=title", HTTP_HX_REQUEST="true"
    )
    filtered_response = client.get(
        f"{list_url}?title=Bootstrap+list+book+1&page_size=5&sort=title",
        HTTP_HX_REQUEST="true",
        HTTP_HX_TARGET="content",
    )

    for response, response_name in ((full_response, "full-page"), (htmx_response, "HTMX")):
        response_text = response.content.decode()
        assert response.status_code == 200, f"The Bootstrap {response_name} list should render."
        assert 'id="filtered_results"' in response_text, (
            "The Bootstrap list should retain the stable HTMX swap target."
        )
        assert 'data-powercrud-pagination="true"' in response_text, (
            "The Bootstrap list should retain shared pagination lifecycle semantics."
        )
        assert 'id="filterToggleBtn"' in response_text and 'id="filter-form"' in response_text, (
            "The Bootstrap list should render the complete filter controls."
        )
        assert 'data-powercrud-page-size-select="true"' in response_text, (
            "The Bootstrap list should retain the shared page-size hook."
        )
        assert 'data-powercrud-list-columns-trigger="true"' in response_text, (
            "The completed Bootstrap list should expose its column chooser."
        )
        assert 'data-inline-row="true"' in response_text, (
            "The completed Bootstrap list should render its inline-capable row contract."
        )

    bootstrap_template_root = (
        Path(settings.BASE_DIR)
        / "powercrud"
        / "contrib"
        / "bootstrap5"
        / "templates"
        / "powercrud"
        / "packs"
        / "bootstrap5"
    )
    bootstrap_list_markup = "\n".join(
        (bootstrap_template_root / relative_path).read_text(encoding="utf-8")
        for relative_path in ("object_list.html", "partial/list_actions.html", "partial/table_row.html", "partial/row_actions.html")
    )
    assert 'data-powercrud-modal-trigger="true"' in bootstrap_list_markup, (
        "The Bootstrap-owned 7.4 list should expose the selected private modal trigger."
    )

    filtered_text = filtered_response.content.decode()
    assert "Bootstrap list book 1" in filtered_text, (
        "Bootstrap filtering should preserve shared server filtering results."
    )
    assert "Bootstrap list book 0" not in filtered_text, (
        "Bootstrap filtering should exclude non-matching shared records."
    )
    assert "title=Bootstrap+list+book+1" in filtered_response["HX-Push-Url"], (
        "Bootstrap HTMX filtering should retain legitimate query state."
    )


@pytest.mark.django_db
def test_bootstrap_modal_shell_and_create_transport_preserve_shared_hooks(client):
    """Bootstrap should own the modal shell while retaining existing modal transport IDs."""
    login_response = client.post(reverse("sample:demo-login", args=["manager"]))
    assert login_response.status_code == 302, "The sample manager should authenticate for the create action."
    response = client.get(reverse("sample:bigbook-list"))
    rendered = response.content.decode()

    assert response.status_code == 200, "The Bootstrap list with its modal host should render."
    assert 'id="powercrudBaseModal"' in rendered and 'data-powercrud-modal' in rendered, (
        "The Bootstrap list should retain the shared modal root ID and lifecycle marker."
    )
    assert 'id="powercrudModalContent"' in rendered and 'data-powercrud-modal-content' in rendered, (
        "The Bootstrap shell should retain the shared HTMX modal content target."
    )
    assert 'class="modal fade"' in rendered and 'data-bs-dismiss="modal"' in rendered, (
        "The Bootstrap modal host should use Bootstrap component markup rather than a native dialog."
    )
    create_url = reverse("sample:bigbook-create")
    assert f'hx-get="{create_url}"' in rendered and 'hx-target="#powercrudModalContent"' in rendered, (
        "The Bootstrap create action should retain modal-compatible HTMX transport."
    )
