from __future__ import annotations

from copy import deepcopy
import json
from datetime import date
from types import SimpleNamespace

import pytest
from django import forms
from django.contrib.sessions.middleware import SessionMiddleware
from django.conf import settings
from django.test import RequestFactory, override_settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from powercrud.mixins.form_mixin import FormMixin
from powercrud.mixins import (
    CoreMixin,
    FilteringMixin,
    HtmxMixin,
    InlineEditingMixin,
    TableMixin,
)
from sample.models import Author, Book, Genre


def attach_session(request):
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.fixture(autouse=True)
def fast_book_save(monkeypatch):
    """Speed up Book.save() by skipping the deliberate sleep."""
    monkeypatch.setattr("sample.models.time.sleep", lambda *_args, **_kwargs: None)


@pytest.fixture(autouse=True)
def enable_crispy(settings):
    """Ensure crispy_forms is available for template rendering."""
    if "crispy_forms" not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS = tuple(settings.INSTALLED_APPS) + ("crispy_forms",)


@pytest.fixture
def sample_author(db):
    return Author.objects.create(name="Inline Author")


@pytest.fixture
def sample_genre(db):
    return Genre.objects.create(name="Inline Genre")


@pytest.fixture
def sample_book(sample_author, sample_genre):
    book = Book.objects.create(
        title="Original Title",
        author=sample_author,
        published_date=date(2024, 1, 1),
        bestseller=False,
        isbn="9780000000001",
        pages=321,
    )
    book.genres.add(sample_genre)
    return book


class InlineTestForm(forms.ModelForm):
    def clean(self):
        cleaned = super().clean()
        if cleaned.get("title") == "non-field-error":
            self.add_error(None, "Custom non-field problem")
        return cleaned

    class Meta:
        model = Book
        fields = ["title", "author", "published_date", "isbn", "pages", "bestseller"]


class InlineOptionalFieldForm(forms.ModelForm):
    """Inline test form that exposes an optional field omitted from the row UI."""

    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "published_date",
            "isbn",
            "pages",
            "bestseller",
            "description",
        ]


class InlineTestView(InlineEditingMixin, TableMixin, HtmxMixin, CoreMixin):
    """Minimal view harness to exercise InlineEditingMixin behaviour."""

    model = Book
    namespace = "sample"
    url_base = "bigbook"
    templates_path = "powercrud/daisyUI"

    def __init__(self, request, obj):
        self.request = request
        self.kwargs = {"pk": obj.pk}
        self.object = obj

    # ------------------------------------------------------------------
    # Minimal hooks used by the mixin
    # ------------------------------------------------------------------
    def get_object(self):
        return self.object

    def get_inline_editing(self) -> bool:
        return True

    def get_inline_context(self):
        return {
            "enabled": True,
            "fields": ["title"],
            "dependencies": {},
            "row_id_prefix": "pc-row-",
            "row_endpoint_name": "sample:bigbook-inline-row",
            "dependency_endpoint_name": "sample:bigbook-inline-dependency",
            "dependency_endpoint_url": "/sample/bigbook/inline-dependency/",
        }

    def get_bulk_edit_enabled(self):
        return False

    def _get_selected_ids(self):
        return []

    def get_use_htmx(self):
        return True

    def get_original_target(self):
        return "#content"

    def get_htmx_target(self):
        return "content"

    def build_inline_form(self, *, instance, data=None, files=None):
        return InlineTestForm(data=data, files=files, instance=instance)

    def _build_inline_row_payload(self, obj):
        return {
            "row_id": f"pc-row-{obj.pk}",
            "id": str(obj.pk),
            "inline_url": self._get_inline_row_url(obj),
            "inline_allowed": True,
            "inline_blocked_reason": None,
            "inline_blocked_label": None,
            "inline_blocked_meta": {},
            "cells": [
                {
                    "name": "title",
                    "value": obj.title,
                    "is_inline_editable": True,
                    "dependency": None,
                },
                {
                    "name": "isbn",
                    "value": obj.isbn,
                    "is_inline_editable": False,
                    "dependency": None,
                },
                {
                    "name": "pages",
                    "value": obj.pages,
                    "is_inline_editable": True,
                    "dependency": None,
                },
            ],
            "actions": "<div>actions</div>",
        }

    def safe_reverse(self, viewname, kwargs=None):
        if viewname.endswith("inline-row") and kwargs:
            return f"/sample/bigbook/{kwargs['pk']}/inline/"
        if viewname.endswith("inline-dependency"):
            return "/sample/bigbook/inline-dependency/"
        if viewname.endswith("bigbook-list"):
            return "/sample/bigbook/"
        return f"/{viewname}/"

    def get_inline_row_endpoint_name(self):
        return "sample:bigbook-inline-row"

    def get_inline_dependency_endpoint_name(self):
        return "sample:bigbook-inline-dependency"

    def get_inline_row_id(self, obj):
        return f"pc-row-{obj.pk}"

    # ------------------------------------------------------------------
    # Convenience helpers mirroring TableMixin/CoreMixin defaults
    # ------------------------------------------------------------------
    def get_table_pixel_height_other_page_elements(self):
        return "0px"

    def get_table_max_height(self):
        return 70

    def get_table_classes(self):
        return ""


class InlineMissingFieldView(InlineTestView):
    inline_edit_fields = ["title", "author", "published_date", "isbn", "bestseller"]


class InlineGeneratedOptionalFieldView(FormMixin, InlineTestView):
    """Exercise inline saves through FormMixin's generated ModelForm path."""

    form_fields = [
        "title",
        "author",
        "published_date",
        "isbn",
        "pages",
        "bestseller",
        "description",
    ]
    inline_edit_fields = ["title", "pages"]

    def build_inline_form(self, *, instance, data=None, files=None):
        """Delegate inline form construction to FormMixin for regression coverage."""
        return FormMixin.build_inline_form(
            self,
            instance=instance,
            data=data,
            files=files,
        )


class InlineCustomOptionalFieldView(FormMixin, InlineTestView):
    """Exercise inline saves through FormMixin with a custom form_class."""

    form_class = InlineOptionalFieldForm
    inline_edit_fields = ["title", "pages"]

    def build_inline_form(self, *, instance, data=None, files=None):
        """Delegate inline form construction to FormMixin for regression coverage."""
        return FormMixin.build_inline_form(
            self,
            instance=instance,
            data=data,
            files=files,
        )


class InlineDependencyCaptureView(InlineTestView):
    """Capture inline dependency inputs to assert context propagation."""

    def __init__(self, request, obj):
        super().__init__(request, obj)
        self.captured_instance_pk = None
        self.captured_author = None

    def build_inline_form(self, *, instance, data=None, files=None):
        self.captured_instance_pk = getattr(instance, "pk", None)
        self.captured_author = data.get("author") if data is not None else None
        return super().build_inline_form(instance=instance, data=data, files=files)


class InlineDependencyMetadataView(InlineTestView):
    """Expose one inline dependency to verify dependency widget metadata."""

    def get_inline_field_dependencies(self):
        return {
            "title": {
                "depends_on": ["author"],
                "endpoint_url": "/sample/bigbook/inline-dependency/",
            }
        }


class InlineFilterAwareView(FilteringMixin, InlineTestView):
    """Exercise inline-save refresh policy against the active filterset."""

    filterset_fields = ["title"]


class InlineKeepPageView(InlineFilterAwareView):
    """Force inline saves to preserve the current page during refresh."""

    inline_save_refresh_policy = "keep_page"


class InlineResetPageView(InlineFilterAwareView):
    """Force inline saves to reset pagination during refresh."""

    inline_save_refresh_policy = "reset_page"


class InlinePowerUpdateDeniedView(InlineTestView):
    """Block all row updates through the built-in update permission hook."""

    def has_power_update_permission(self, request, obj):
        """Deny update permission for the current test row."""
        return False


class InlineUpdateGuardView(InlineTestView):
    """Block all row updates through the row-state update guard hooks."""

    def can_update_object(self, obj, request):
        """Disable updates for the current test row."""
        return False

    def get_update_disabled_reason(self, obj, request):
        """Return the reason shown when update guard hooks block the row."""
        return "Editing locked by policy."


class InlineOnlyRestrictionView(InlineTestView):
    """Keep update allowed while adding an inline-only row restriction."""

    inline_edit_allowed = staticmethod(lambda obj, request: False)


def _make_request(method="get", path="/inline/", data=None):
    rf = RequestFactory()
    request = getattr(rf, method)(path, data=data or {})
    request.htmx = SimpleNamespace()
    attach_session(request)
    return request


@pytest.mark.django_db
def test_inline_get_renders_form_html(sample_book):
    request = _make_request("get")
    view = InlineTestView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)

    assert response.status_code == 200, "Expected inline row GET to render successfully."
    assert (
        b"inline-field-widget" in response.content
    ), "Expected inline row GET response to include editable inline field markup."
    assert b"Save" in response.content, "Expected inline row GET response to include Save action."
    assert (
        b"pc-inline-actions-cell" in response.content
    ), "Expected inline row GET response to reserve width for Save and Cancel controls."
    assert (
        b"pc-inline-actions-controls" in response.content
    ), "Expected inline row GET response to wrap Save and Cancel in the dedicated inline actions container."
    assert (
        b'data-inline-actions="true"' in response.content
    ), "Expected active inline row actions to keep the inline-actions marker used by keyboard guards."
    assert (
        b"> -->" not in response.content
    ), "Inline row form should not render stray HTML comment artifacts near actions."
    assert (
        b"pc-inline-editable" not in response.content
    ), "Active inline form rows should not reuse the display-state editable marker class."
    assert b'name="pk"' in response.content and b'name="csrfmiddlewaretoken"' in response.content, (
        "Inline form rows should retain object identity and CSRF fields."
    )
    assert b"data-inline-save" in response.content and b"data-inline-cancel" in response.content, (
        "Inline form rows should retain Save and Cancel runtime hooks."
    )
    assert b'hx-post="/sample/bigbook/' in response.content and b'hx-include="#pc-row-' in response.content, (
        "Save should retain the row endpoint and include every named row field."
    )
    assert b'hx-vals=\'{"inline_display": true}\'' in response.content and b'hx-swap="outerHTML"' in response.content, (
        "Cancel should retain display-mode and outer-row swap semantics."
    )


@pytest.mark.django_db
def test_inline_form_response_uses_focused_model_row_for_get_and_invalid_post(
    sample_book, sample_author, tmp_path
):
    """Entry and invalid save responses should select the same model form row."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "book_inline_row_form.html").write_text(
        '<tr id="{{ row.row_id }}" data-inline-row="true" data-inline-active="true" data-custom-inline-form>'
        '<td>{{ form.title }}{% if form.title.errors %}{{ form.title.errors|join:", " }}{% endif %}</td>'
        '<td data-hidden-count="{{ inline_hidden_fields|length }}">{{ action_button_classes }} {{ inline_save_url }} {{ inline_cancel_url }}</td>'
        "</tr>"
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    def focused_paths(component):
        if component == "inline_row_form":
            return [
                "sample/book_inline_row_form.html",
                "powercrud/daisyUI/partial/inline_row_form.html",
            ]
        return [f"powercrud/daisyUI/partial/{component}.html"]

    get_request = _make_request("get")
    get_view = InlineTestView(get_request, sample_book)
    get_view.get_focused_component_template_paths = focused_paths
    invalid_request = _make_request(
        "post",
        data={
            "title": "",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000011",
            "pages": "123",
            "bestseller": "",
        },
    )
    invalid_view = InlineTestView(invalid_request, sample_book)
    invalid_view.get_focused_component_template_paths = focused_paths

    with override_settings(TEMPLATES=template_settings):
        get_response = get_view._dispatch_inline_row(get_request, pk=sample_book.pk)
        invalid_response = invalid_view._dispatch_inline_row(
            invalid_request, pk=sample_book.pk
        )

    assert b"data-custom-inline-form" in get_response.content and b"Original Title" in get_response.content, (
        "Ordinary entry should select the model form row with the bound instance."
    )
    assert b"data-hidden-count=" in get_response.content and b"/sample/bigbook/" in get_response.content, (
        "The model form row should receive hidden fields, classes, and save/cancel URLs."
    )
    assert b"data-custom-inline-form" in invalid_response.content and b"This field is required" in invalid_response.content, (
        "Invalid saves should retain the same model override and bound validation state."
    )
    assert b"<script" not in get_response.content + invalid_response.content, (
        "A focused inline form row should not need copied PowerCRUD JavaScript."
    )


@pytest.mark.django_db
def test_inline_form_row_preserves_disabled_selection_column(sample_book):
    """Active editing should retain one disabled selection cell when enabled."""
    request = _make_request("get")
    view = InlineTestView(request, sample_book)
    view.get_selection_controls_enabled = lambda: True

    response = view._dispatch_inline_row(request, pk=sample_book.pk)

    assert response.content.count(b"row-select-checkbox") == 1, (
        "The active form row should retain exactly one selection-column placeholder."
    )
    assert b'data-id="' + str(sample_book.pk).encode() + b'"' in response.content and b"disabled" in response.content, (
        "The selection placeholder should retain the row ID and remain disabled while editing."
    )


@pytest.mark.django_db
def test_inline_display_response_uses_focused_model_row(sample_book, tmp_path):
    """Cancel/display requests should render the model-first canonical display row."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "book_inline_row_display.html").write_text(
        '<tr id="{{ row.row_id }}" data-inline-row="true" data-custom-inline-display><td>{{ row.cells.0.value }}</td></tr>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]
    request = _make_request("get", path="/inline/?inline_display=true")
    view = InlineTestView(request, sample_book)

    def focused_paths(component):
        if component == "inline_row_display":
            return [
                "sample/book_inline_row_display.html",
                "powercrud/daisyUI/partial/inline_row_display.html",
            ]
        return [f"powercrud/daisyUI/partial/{component}.html"]

    view.get_focused_component_template_paths = focused_paths
    with override_settings(TEMPLATES=template_settings):
        response = view._dispatch_inline_row(request, pk=sample_book.pk)

    assert response.status_code == 200, (
        "An inline display request should return a replacement row."
    )
    assert b"data-custom-inline-display" in response.content and sample_book.title.encode() in response.content, (
        "The direct response should select the model display row with row payload context."
    )
    assert b'data-inline-active="true"' not in response.content and b"<script" not in response.content, (
        "Display responses should remain non-active and require no copied JavaScript."
    )


@pytest.mark.django_db
def test_inline_post_success_triggers_list_refresh(sample_book, sample_author):
    request = _make_request(
        "post",
        data={
            "title": "Updated Inline Title",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000011",
            "pages": "123",
            "bestseller": "",
        },
    )
    view = InlineTestView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 204, (
        "Successful inline saves should return 204 so the existing list can refresh without swapping the active row markup directly."
    )
    assert response.content == b"", (
        "Successful inline saves should not return row HTML once refreshTable drives the visible list update."
    )
    assert payload == {
        "inline-row-saved": {"pk": sample_book.pk},
        "refreshTable": {"reset_page": False},
    }, (
        "Successful inline saves without active filters should keep the current page while triggering a list refresh."
    )
    sample_book.refresh_from_db()
    assert sample_book.title == "Updated Inline Title", "Successful inline saves should persist the submitted field changes."


@pytest.mark.django_db
def test_inline_post_uses_persist_single_object_hook(sample_book, sample_author, monkeypatch):
    request = _make_request(
        "post",
        data={
            "title": "Saved Via Inline Hook",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000011",
            "pages": "123",
            "bestseller": "",
        },
    )
    view = InlineTestView(request, sample_book)
    captured = {}
    original_persist = view.persist_single_object

    def fake_persist_single_object(*, form, mode, instance=None):
        captured["mode"] = mode
        captured["instance"] = instance
        return original_persist(form=form, mode=mode, instance=instance)

    monkeypatch.setattr(view, "persist_single_object", fake_persist_single_object)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 204, (
        "Inline saves routed through persist_single_object should still succeed."
    )
    assert payload["inline-row-saved"] == {"pk": sample_book.pk}, (
        "Inline saves routed through persist_single_object should still emit the inline-row-saved event."
    )
    assert captured["mode"] == "inline", (
        "Inline row saves should call persist_single_object with mode='inline'."
    )
    assert captured["instance"] is sample_book, (
        "Inline row saves should pass the current object through to persist_single_object."
    )
    sample_book.refresh_from_db()
    assert sample_book.title == "Saved Via Inline Hook", (
        "Inline row saves should persist through the object returned by persist_single_object."
    )


@pytest.mark.django_db
def test_inline_post_missing_required_field_is_preserved(sample_book, sample_author):
    request = _make_request(
        "post",
        data={
            "title": "Updated Inline Title",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000011",
            "bestseller": "",
        },
    )
    view = InlineMissingFieldView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 204
    assert payload == {
        "inline-row-saved": {"pk": sample_book.pk},
        "refreshTable": {"reset_page": False},
    }
    sample_book.refresh_from_db()
    assert sample_book.pages == 321


@pytest.mark.django_db
def test_inline_post_preserved_fields_ignore_manual_input(sample_book, sample_author):
    request = _make_request(
        "post",
        data={
            "title": "Updated Inline Title",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000011",
            "pages": "1",
            "bestseller": "",
        },
    )
    view = InlineMissingFieldView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 204
    assert payload == {
        "inline-row-saved": {"pk": sample_book.pk},
        "refreshTable": {"reset_page": False},
    }
    sample_book.refresh_from_db()
    assert sample_book.pages == 321


@pytest.mark.django_db
def test_inline_get_renders_hidden_optional_field_for_generated_form(
    sample_book, sample_author
):
    """Inline rows should emit hidden inputs for non-rendered form fields."""
    sample_book.description = "Preserve generated form description"
    sample_book.save(update_fields=["description"])

    request = _make_request("get")
    view = InlineGeneratedOptionalFieldView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)

    assert (
        response.status_code == 200
    ), "Inline row GETs built from form_fields should render successfully when emitting hidden reposted fields."
    assert (
        b'type="hidden" name="description" value="Preserve generated form description"'
        in response.content
    ), (
        "Inline rows built from form_fields should include hidden inputs for optional form fields that are not rendered visibly in the row."
    )


@pytest.mark.django_db
def test_inline_post_preserves_optional_field_when_reposted_for_generated_form(
    sample_book, sample_author
):
    """Inline save should preserve optional values when the row reposts them."""
    sample_book.description = "Preserve generated form description"
    sample_book.save(update_fields=["description"])

    request = _make_request(
        "post",
        data={
            "title": "Updated Inline Title",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000011",
            "pages": "321",
            "bestseller": "",
            "description": "Preserve generated form description",
        },
    )
    view = InlineGeneratedOptionalFieldView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert (
        response.status_code == 204
    ), "Inline saves built from form_fields should succeed when the row reposts hidden non-rendered fields."
    assert payload == {
        "inline-row-saved": {"pk": sample_book.pk},
        "refreshTable": {"reset_page": False},
    }, (
        "Inline saves built from form_fields should refresh the list after reposting hidden non-rendered fields."
    )
    sample_book.refresh_from_db()
    assert sample_book.description == "Preserve generated form description", (
        "Inline saves built from form_fields should preserve optional instance values when the row reposts hidden non-rendered fields."
    )


@pytest.mark.django_db
def test_inline_get_renders_hidden_optional_field_for_custom_form(
    sample_book, sample_author
):
    """Custom inline forms should also emit hidden inputs for non-rendered fields."""
    sample_book.description = "Preserve custom form description"
    sample_book.save(update_fields=["description"])

    request = _make_request("get")
    view = InlineCustomOptionalFieldView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)

    assert (
        response.status_code == 200
    ), "Inline row GETs built from form_class should render successfully when emitting hidden reposted fields."
    assert (
        b'type="hidden" name="description" value="Preserve custom form description"'
        in response.content
    ), (
        "Inline rows built from form_class should include hidden inputs for optional form fields that are not rendered visibly in the row."
    )


@pytest.mark.django_db
def test_inline_post_preserves_optional_field_when_reposted_for_custom_form(
    sample_book, sample_author
):
    """Custom inline forms should preserve optional values when the row reposts them."""
    sample_book.description = "Preserve custom form description"
    sample_book.save(update_fields=["description"])

    request = _make_request(
        "post",
        data={
            "title": "Updated Inline Title",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000011",
            "pages": "321",
            "bestseller": "",
            "description": "Preserve custom form description",
        },
    )
    view = InlineCustomOptionalFieldView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert (
        response.status_code == 204
    ), "Inline saves built from form_class should succeed when the row reposts hidden non-rendered fields."
    assert payload == {
        "inline-row-saved": {"pk": sample_book.pk},
        "refreshTable": {"reset_page": False},
    }, (
        "Inline saves built from form_class should refresh the list after reposting hidden non-rendered fields."
    )
    sample_book.refresh_from_db()
    assert sample_book.description == "Preserve custom form description", (
        "Inline saves built from form_class should preserve optional instance values when the row reposts hidden non-rendered fields."
    )


@pytest.mark.django_db
def test_inline_post_resets_page_when_saved_row_falls_out_of_active_filters(
    sample_book, sample_author
):
    request = _make_request(
        "post",
        path="/inline/?title=Original&page=3&page_size=50&sort=title",
        data={
            "title": "Updated Inline Title",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000011",
            "pages": "123",
            "bestseller": "",
        },
    )
    view = InlineFilterAwareView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 204, (
        "Inline saves should still complete successfully when the saved row falls out of the active filters."
    )
    assert payload["refreshTable"] == {"reset_page": True}, (
        "Inline saves should reset pagination when the saved row no longer belongs to the active filtered queryset."
    )


@pytest.mark.django_db
def test_inline_post_keeps_page_when_saved_row_stays_in_active_filters(
    sample_book, sample_author
):
    request = _make_request(
        "post",
        path="/inline/?title=Original&page=3&page_size=50&sort=title",
        data={
            "title": "Original Title",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000011",
            "pages": "999",
            "bestseller": "",
        },
    )
    view = InlineFilterAwareView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 204, (
        "Inline saves should still complete successfully when the saved row remains in the active filters."
    )
    assert payload["refreshTable"] == {"reset_page": False}, (
        "Inline saves should preserve the current page when the saved row still belongs to the active filtered queryset."
    )


@pytest.mark.django_db
def test_inline_post_keep_page_policy_overrides_filter_membership(
    sample_book, sample_author
):
    request = _make_request(
        "post",
        path="/inline/?title=Original&page=3",
        data={
            "title": "Updated Inline Title",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000011",
            "pages": "123",
            "bestseller": "",
        },
    )
    view = InlineKeepPageView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert payload["refreshTable"] == {"reset_page": False}, (
        "Explicit keep_page policy should preserve the current page even when the saved row falls out of the active filters."
    )


@pytest.mark.django_db
def test_inline_post_reset_page_policy_overrides_filter_membership(
    sample_book, sample_author
):
    request = _make_request(
        "post",
        path="/inline/?title=Original&page=3",
        data={
            "title": "Original Title",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000011",
            "pages": "123",
            "bestseller": "",
        },
    )
    view = InlineResetPageView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert payload["refreshTable"] == {"reset_page": True}, (
        "Explicit reset_page policy should drop the current page even when the saved row remains inside the active filters."
    )


@pytest.mark.django_db
def test_inline_post_preserve_toggle_restores_validation(sample_book, sample_author):
    class InlineMissingFieldNoPreserveView(InlineMissingFieldView):
        inline_preserve_required_fields = False

    request = _make_request(
        "post",
        data={
            "title": "Updated Inline Title",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000011",
            "bestseller": "",
        },
    )
    view = InlineMissingFieldNoPreserveView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 200
    assert payload["inline-row-error"]["message"] == "This field is required."


@pytest.mark.django_db
def test_inline_post_validation_error_returns_inline_form(sample_book, sample_author):
    request = _make_request(
        "post",
        data={
            "title": "",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000033",
            "pages": "33",
            "bestseller": "",
        },
    )
    view = InlineTestView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 200
    assert payload["inline-row-error"]["pk"] == sample_book.pk
    assert payload["inline-row-error"]["row_id"] == f"pc-row-{sample_book.pk}"
    assert payload["inline-row-error"]["message"] == "This field is required."
    assert payload["inline-row-error"]["field_errors"] == [
        {
            "field": "title",
            "label": "Title",
            "message": "This field is required.",
        }
    ]
    assert payload["inline-row-error"]["non_field_errors"] == []
    assert b"text-error" in response.content
    assert b'data-inline-field-error="true"' in response.content
    assert b'data-inline-error-field="title"' in response.content
    assert b'aria-invalid="true"' in response.content
    assert b'id_title_inline_error' in response.content


@pytest.mark.django_db
def test_inline_post_non_field_error_renders_alert(sample_book, sample_author):
    request = _make_request(
        "post",
        data={
            "title": "non-field-error",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000044",
            "pages": "33",
            "bestseller": "",
        },
    )
    view = InlineTestView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 200
    assert payload["inline-row-error"]["message"] == "Custom non-field problem"
    assert payload["inline-row-error"]["field_errors"] == []
    assert payload["inline-row-error"]["non_field_errors"] == [
        {"message": "Custom non-field problem"}
    ]
    assert response.content.count(b"alert alert-error") >= 1


@pytest.mark.django_db
def test_inline_numeric_error_preserves_value(sample_book, sample_author):
    request = _make_request(
        "post",
        data={
            "title": sample_book.title,
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000055",
            "pages": "aa",
            "bestseller": "",
        },
    )
    view = InlineTestView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 200
    assert b'value="aa"' in response.content
    assert b"Enter a whole number" in response.content
    assert payload["inline-row-error"]["message"] == "Enter a whole number."


@pytest.mark.django_db
def test_inline_guard_blocks_locked_state(sample_book, monkeypatch):
    request = _make_request("get")
    view = InlineTestView(request, sample_book)

    def always_locked(self, obj, req):
        return {"status": "locked", "message": "Row locked", "lock": {"label": "Busy"}}

    monkeypatch.setattr(InlineTestView, "_evaluate_inline_state", always_locked)
    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 423
    assert payload["inline-row-locked"]["message"] == "Row locked"
    assert payload["inline-row-locked"]["lock"]["label"] == "Busy"
    assert b'data-inline-status="locked"' in response.content, (
        "Locked responses should return display-row status metadata."
    )
    assert b'aria-disabled="true"' in response.content and b"pc-inline-editable" not in response.content, (
        "Locked rows should show a disabled affordance rather than an editable trigger."
    )


@pytest.mark.django_db
def test_inline_guard_blocks_get_when_update_guard_denies_row(sample_book):
    request = _make_request("get")
    view = InlineUpdateGuardView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 403, (
        "Inline GET should reject rows blocked by can_update_object before rendering an editable form."
    )
    assert payload["inline-row-forbidden"]["message"] == "Editing locked by policy.", (
        "Inline GET should reuse the configured update-guard reason when blocking the row."
    )
    assert b'data-inline-status="forbidden"' in response.content and b'aria-disabled="true"' in response.content, (
        "Forbidden responses should return a disabled display row with status metadata."
    )


@pytest.mark.django_db
def test_inline_guard_blocks_post_when_update_guard_denies_row(sample_book, sample_author):
    request = _make_request(
        "post",
        data={
            "title": "Blocked Inline Title",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000022",
            "pages": "123",
            "bestseller": "",
        },
    )
    view = InlineUpdateGuardView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 403, (
        "Inline POST should reject rows blocked by can_update_object instead of saving them."
    )
    assert payload["inline-row-forbidden"]["message"] == "Editing locked by policy.", (
        "Inline POST should reuse the configured update-guard reason when blocking the row."
    )
    sample_book.refresh_from_db()
    assert sample_book.title == "Original Title", (
        "Inline POST should not persist changes when can_update_object blocks the row."
    )


@pytest.mark.django_db
def test_inline_guard_blocks_get_when_power_update_permission_denies_row(sample_book):
    """Inline GET should reject rows denied by the built-in update permission hook."""
    request = _make_request("get")
    view = InlinePowerUpdateDeniedView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 403, (
        "Inline GET should reject rows blocked by has_power_update_permission before rendering an editable form."
    )
    assert payload["inline-row-forbidden"]["message"] == "Editing not permitted for this row.", (
        "Inline GET should use the generic forbidden message when permission, not row state, blocks editing."
    )


@pytest.mark.django_db
def test_inline_guard_blocks_post_when_power_update_permission_denies_row(
    sample_book,
    sample_author,
):
    """Inline POST should reject rows denied by the built-in update permission hook."""
    request = _make_request(
        "post",
        data={
            "title": "Permission Denied Inline Title",
            "author": str(sample_author.pk),
            "published_date": "2024-01-01",
            "isbn": "9780000000022",
            "pages": "123",
            "bestseller": "",
        },
    )
    view = InlinePowerUpdateDeniedView(request, sample_book)

    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert response.status_code == 403, (
        "Inline POST should reject rows blocked by has_power_update_permission instead of saving them."
    )
    assert payload["inline-row-forbidden"]["message"] == "Editing not permitted for this row.", (
        "Inline POST should use the generic forbidden message when permission, not row state, blocks editing."
    )
    sample_book.refresh_from_db()
    assert sample_book.title == "Original Title", (
        "Inline POST should not persist changes when has_power_update_permission blocks the row."
    )


@pytest.mark.django_db
def test_can_inline_edit_requires_update_guard_and_inline_only_policy(sample_book):
    request = _make_request("get")

    guarded_view = InlineUpdateGuardView(request, sample_book)
    inline_only_view = InlineOnlyRestrictionView(request, sample_book)

    assert guarded_view.can_inline_edit(sample_book, request) is False, (
        "Inline editing should be blocked when the new update guard hook denies the row."
    )
    assert inline_only_view.can_inline_edit(sample_book, request) is False, (
        "Inline editing should also remain blockable through the existing inline-only policy hook."
    )


@pytest.mark.django_db
def test_inline_guard_serializes_lazy_translation_messages(sample_book, monkeypatch):
    request = _make_request("get")
    view = InlineTestView(request, sample_book)

    def always_locked(self, obj, req):
        return {
            "status": "locked",
            "message": _("Inline editing blocked – record is locked."),
            "lock": {"label": _("Busy")},
        }

    monkeypatch.setattr(InlineTestView, "_evaluate_inline_state", always_locked)
    response = view._dispatch_inline_row(request, pk=sample_book.pk)
    payload = json.loads(response["HX-Trigger"])

    assert (
        response.status_code == 423
    ), "Locked inline rows should still return the guard response status."
    assert (
        payload["inline-row-locked"]["message"]
        == "Inline editing blocked \u2013 record is locked."
    ), "Lazy translation messages should be normalized into JSON-safe strings in HX-Trigger payloads."
    assert (
        payload["inline-row-locked"]["lock"]["label"] == "Busy"
    ), "Nested lazy translation values should also be normalized into JSON-safe strings."


@pytest.mark.django_db
def test_inline_dependency_endpoint_renders_widget(sample_book):
    request = _make_request(
        "post",
        path="/inline-dependency/",
        data={
            "field": "title",
            "title": sample_book.title,
            "author": str(sample_book.author_id),
            "published_date": "2024-01-01",
            "isbn": sample_book.isbn,
            "pages": str(sample_book.pages),
            "bestseller": "",
        },
    )
    view = InlineTestView(request, sample_book)

    response = view._dispatch_inline_dependency(request, pk=sample_book.pk)

    assert response.status_code == 200, "Dependency endpoint should return refreshed widget HTML."
    assert (
        b'inline-field-widget w-full' in response.content
    ), "Dependency widget response should include the expected wrapper class."
    assert (
        b'data-inline-field="title"' in response.content
    ), "Dependency widget response should preserve the inline field marker after swap."


@pytest.mark.django_db
def test_inline_dependency_prefers_model_inline_field_override(sample_book, tmp_path):
    """Dependency responses should select the model field component with isolated context."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "book_inline_field.html").write_text(
        '<div data-custom-inline-field data-name="{{ field_name }}" '
        'data-endpoint="{{ field_dependency.endpoint_url|default:dependency_endpoint_url }}">{{ field }}</div>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]
    request = _make_request(
        "post",
        path="/inline-dependency/",
        data={
            "field": "title",
            "title": sample_book.title,
            "author": str(sample_book.author_id),
            "published_date": "2024-01-01",
            "isbn": sample_book.isbn,
            "pages": str(sample_book.pages),
            "bestseller": "",
        },
    )
    view = InlineDependencyMetadataView(request, sample_book)

    def focused_paths(component):
        assert component == "inline_field", (
            "The dependency endpoint should resolve only the inline-field component."
        )
        return [
            "sample/book_inline_field.html",
            "powercrud/daisyUI/partial/inline_field.html",
        ]

    view.get_focused_component_template_paths = focused_paths
    with override_settings(TEMPLATES=template_settings):
        response = view._dispatch_inline_dependency(request, pk=sample_book.pk)

    assert b"data-custom-inline-field" in response.content and b'data-name="title"' in response.content, (
        "The model override should receive the bound field and field name."
    )
    assert b'data-endpoint="/sample/bigbook/inline-dependency/"' in response.content, (
        "The model override should receive resolved dependency metadata and fallback context."
    )
    assert sample_book.title.encode() in response.content and b"<script" not in response.content, (
        "The model override should render the bound value without copied JavaScript."
    )


@pytest.mark.django_db
def test_inline_dependency_uses_url_pk_fallback_when_post_pk_missing(sample_book):
    request = _make_request(
        "post",
        path="/inline-dependency/",
        data={
            "field": "title",
            "author": str(sample_book.author_id),
            "title": sample_book.title,
        },
    )
    view = InlineDependencyCaptureView(request, sample_book)

    response = view._dispatch_inline_dependency(request, pk=sample_book.pk)

    assert response.status_code == 200, "Dependency refresh should succeed when URL pk is provided."
    assert (
        view.captured_instance_pk == sample_book.pk
    ), "Dependency refresh should resolve row instance from URL kwargs when POST pk is absent."


@pytest.mark.django_db
def test_inline_dependency_preserves_parent_values_from_post(sample_book):
    request = _make_request(
        "post",
        path="/inline-dependency/",
        data={
            "field": "title",
            "pk": str(sample_book.pk),
            "author": str(sample_book.author_id),
            "title": sample_book.title,
        },
    )
    view = InlineDependencyCaptureView(request, sample_book)

    response = view._dispatch_inline_dependency(request, pk=sample_book.pk)

    assert response.status_code == 200, "Dependency refresh should return the refreshed widget."
    assert (
        view.captured_author == str(sample_book.author_id)
    ), "Dependency refresh should pass posted parent field values into the rebuilt inline form."


@pytest.mark.django_db
def test_inline_dependency_preserves_dependency_metadata_on_widget_swap(sample_book):
    request = _make_request(
        "post",
        path="/inline-dependency/",
        data={
            "field": "title",
            "pk": str(sample_book.pk),
            "author": str(sample_book.author_id),
            "title": sample_book.title,
        },
    )
    view = InlineDependencyMetadataView(request, sample_book)

    response = view._dispatch_inline_dependency(request, pk=sample_book.pk)

    assert response.status_code == 200, "Dependency refresh should return widget HTML for dependent fields."
    assert (
        b'data-inline-dependent="true"' in response.content
    ), "Dependent widget swaps should preserve dependency markers for future refresh wiring."
    assert (
        b'data-inline-depends-on="author"' in response.content
    ), "Dependent widget swaps should include parent field dependency metadata."
    assert (
        b'data-inline-endpoint="/sample/bigbook/inline-dependency/"' in response.content
    ), "Dependent widget swaps should preserve the dependency endpoint URL."


@pytest.mark.django_db
def test_inline_dependency_rejects_unknown_field(sample_book):
    request = _make_request(
        "post",
        path="/inline-dependency/",
        data={"field": "not_a_field"},
    )
    view = InlineTestView(request, sample_book)

    response = view._dispatch_inline_dependency(request, pk=sample_book.pk)
    assert response.status_code == 400


@pytest.mark.django_db
def test_inline_dependency_requires_field_param(sample_book):
    request = _make_request("post", path="/inline-dependency/")
    view = InlineTestView(request, sample_book)

    response = view._dispatch_inline_dependency(request, pk=sample_book.pk)
    assert response.status_code == 400


class CoreHarness(FormMixin, InlineEditingMixin, CoreMixin):
    """Lightweight CoreMixin harness to exercise inline helpers."""

    model = Book
    fields = ["title", "author", "isbn", "published_date"]
    form_fields = ["title", "isbn"]
    inline_edit_fields = ["title", "isbn"]
    namespace = "sample"
    url_base = "bigbook"

    def __init__(self):
        self.use_htmx = True
        super().__init__()

    def get_use_htmx(self):
        return self.use_htmx

    def safe_reverse(self, name, kwargs=None):
        return "/resolved/"

    def get_inline_dependency_endpoint_name(self):
        return "sample:bigbook-inline-dependency"


@pytest.mark.django_db
def test_inline_editing_requires_htmx():
    view = CoreHarness()
    view.use_htmx = False
    assert view.get_inline_editing() is False


@pytest.mark.django_db
def test_inline_edit_fields_none_disables_inline_editing():
    view = CoreHarness()
    view.inline_edit_fields = None
    fields = view.get_inline_edit_fields()
    assert fields == []
    assert view.get_inline_editing() is False


@pytest.mark.django_db
def test_legacy_inline_edit_enabled_true_defaults_to_form_fields():
    class LegacyInlineHarness(CoreHarness):
        inline_edit_enabled = True
        inline_edit_fields = None

    with pytest.warns(
        FutureWarning,
        match="temporarily falling back to resolved form_fields",
    ):
        view = LegacyInlineHarness()

    assert (
        view.get_inline_edit_fields() == ["title", "isbn"]
    ), "Legacy inline_edit_enabled=True should temporarily fall back to resolved form_fields."
    assert (
        view.get_inline_editing() is True
    ), "Legacy inline_edit_enabled=True should still activate inline editing during the compatibility window."


@pytest.mark.django_db
def test_legacy_inline_edit_enabled_true_respects_explicit_inline_fields():
    class LegacyInlineHarness(CoreHarness):
        inline_edit_enabled = True
        inline_edit_fields = ["title"]

    with pytest.warns(FutureWarning, match="inline_edit_enabled is deprecated"):
        view = LegacyInlineHarness()

    assert (
        view.get_inline_edit_fields() == ["title"]
    ), "Explicit inline_edit_fields should still win when legacy inline_edit_enabled=True is present."


@pytest.mark.django_db
def test_legacy_inline_edit_enabled_false_disables_inline_editing():
    class LegacyInlineHarness(CoreHarness):
        inline_edit_enabled = False
        inline_edit_fields = ["title"]

    with pytest.warns(FutureWarning, match="inline_edit_enabled is deprecated"):
        view = LegacyInlineHarness()

    assert (
        view.get_inline_edit_fields() == []
    ), "Legacy inline_edit_enabled=False should keep inline editing disabled even if inline_edit_fields is set."
    assert (
        view.get_inline_editing() is False
    ), "Legacy inline_edit_enabled=False should keep inline editing turned off during the compatibility window."


@pytest.mark.django_db
def test_inline_field_dependencies_resolve_endpoint():
    view = CoreHarness()
    view.inline_edit_fields = ["title", "isbn", "author", "genres"]
    view.form_fields = ["title", "isbn", "author", "genres"]
    view.field_queryset_dependencies = {
        "genres": {
            "depends_on": ["author"],
            "filter_by": {"authors": "author"},
        }
    }
    deps = view.get_inline_field_dependencies()
    assert deps["genres"]["endpoint_url"] == "/resolved/"
    assert deps["genres"]["depends_on"] == ["author"]


@pytest.mark.django_db
def test_inline_field_dependencies_derive_from_queryset_dependencies():
    view = CoreHarness()
    view.inline_edit_fields = ["title", "isbn", "author", "genres"]
    view.form_fields = ["title", "isbn", "author", "genres"]
    view.field_queryset_dependencies = {
        "genres": {
            "depends_on": ["author"],
            "filter_by": {"authors": "author"},
        }
    }

    deps = view.get_inline_field_dependencies()

    assert (
        deps["genres"]["depends_on"] == ["author"]
    ), "Inline dependencies should be derived automatically from field_queryset_dependencies."
    assert (
        deps["genres"]["endpoint_url"] == "/resolved/"
    ), "Derived inline dependencies should still resolve the default dependency endpoint."


@pytest.mark.django_db
def test_inline_field_dependencies_dedupe_parent_names():
    """Duplicate dependency parents should be collapsed to one ordered entry."""
    view = CoreHarness()
    view.inline_edit_fields = ["title", "isbn", "author", "genres"]
    view.form_fields = ["title", "isbn", "author", "genres"]
    view.field_queryset_dependencies = {
        "genres": {
            "depends_on": ["author", "author"],
            "filter_by": {"authors": "author"},
        }
    }

    deps = view.get_inline_field_dependencies()

    assert deps["genres"]["depends_on"] == ["author"], (
        "field_queryset_dependencies[*].depends_on should quietly drop later duplicates so inline wiring does not repeat parent bindings."
    )


@pytest.mark.django_db
def test_inline_field_dependencies_setting_is_ignored_when_present():
    view = CoreHarness()
    view.inline_edit_fields = ["title", "isbn", "author", "genres"]
    view.form_fields = ["title", "isbn", "author", "genres"]
    view.field_queryset_dependencies = {
        "genres": {
            "depends_on": ["author"],
            "filter_by": {"authors": "author"},
        }
    }
    view.inline_field_dependencies = {
        "genres": {
            "depends_on": ["title"],
            "endpoint_name": "sample:custom-inline-dependency",
        }
    }

    deps = view.get_inline_field_dependencies()

    assert (
        deps["genres"]["depends_on"] == ["author"]
    ), "inline_field_dependencies should be ignored in favour of derived field_queryset_dependencies metadata."
    assert (
        deps["genres"]["endpoint_name"] == "sample:bigbook-inline-dependency"
    ), "Ignoring inline_field_dependencies should preserve the default inline dependency endpoint name."
    assert (
        deps["genres"]["endpoint_url"] == "/resolved/"
    ), "Ignoring inline_field_dependencies should still resolve the default endpoint URL."


@pytest.mark.django_db
def test_inline_edit_fields_intersects_form_fields():
    class InlineMismatchHarness(CoreHarness):
        inline_edit_fields = ["title", "isbn"]
        form_fields = ["title"]

    view = InlineMismatchHarness()
    fields = view.get_inline_edit_fields()

    assert (
        fields == ["title"]
    ), "Inline edit fields should be intersected with the actual form fields exposed by the form class."


def test_inline_edit_fields_rejects_non_editable_model_fields():
    class InlineInvalidHarness(CoreHarness):
        inline_edit_fields = ["title", "uneditable_field"]

    with pytest.raises(ValueError, match="inline_edit_fields"):
        InlineInvalidHarness()


@pytest.mark.django_db
def test_inline_dependency_ignores_child_when_not_inline():
    view = CoreHarness()
    view.field_queryset_dependencies = {
        "genres": {
            "depends_on": ["author"],
            "filter_by": {"authors": "author"},
        }
    }

    deps = view.get_inline_field_dependencies()

    assert deps == {}


@pytest.mark.django_db
def test_inline_dependency_filters_invalid_parents():
    view = CoreHarness()
    view.inline_edit_fields = ["title", "isbn", "author", "genres"]
    view.form_fields = ["title", "isbn", "author", "genres"]
    view.field_queryset_dependencies = {
        "genres": {
            "depends_on": ["author", "missing"],
            "filter_by": {"authors": "author"},
        }
    }

    deps = view.get_inline_field_dependencies()

    assert deps["genres"]["depends_on"] == ["author"]


class DummyCache(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class DummyQueryset:
    def __init__(self, record):
        self.record = record

    def filter(self, **kwargs):
        self.kwargs = kwargs
        return self

    def first(self):
        return self.record


class DummyRecordModel:
    def __init__(self, record):
        self.objects = DummyQueryset(record)


class DummyAsyncManager:
    def __init__(self, record, lock_key):
        self.cache = DummyCache({lock_key: "task-123"})
        self.conflict_model_prefix = "pc-lock:"
        self._record_model = DummyRecordModel(record)

    def _field(self, logical_name, default):
        mapping = {
            "task_name": "task_name",
            "user": "user",
            "user_label": "user",
        }
        return mapping.get(logical_name, default)


class LockMetadataView(InlineEditingMixin):
    model = Book

    def __init__(self, manager):
        self._manager = manager

    def get_async_manager(self):
        return self._manager


@pytest.mark.django_db
def test_inline_lock_metadata_includes_user_and_label(sample_book):
    lock_key = f"pc-lock:sample.book:{sample_book.pk}"
    record = SimpleNamespace(
        task_name="task-123",
        status="running",
        message="Processing",
        created_at=timezone.now(),
        updated_at=timezone.now(),
        user="Casey",
    )
    manager = DummyAsyncManager(record, lock_key)
    view = LockMetadataView(manager)

    metadata = view._get_inline_lock_metadata(sample_book)

    assert metadata["task"] == "task-123"
    assert metadata["lock_key"] == lock_key
    assert "Casey" in metadata["label"]
