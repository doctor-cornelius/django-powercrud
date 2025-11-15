from __future__ import annotations

import json
from datetime import date
from types import SimpleNamespace

import pytest
from django import forms
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.utils import timezone

from powercrud.mixins.core_mixin import CoreMixin
from powercrud.mixins.form_mixin import FormMixin
from powercrud.mixins import InlineEditingMixin, TableMixin, HtmxMixin, CoreMixin
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


class InlineTestView(InlineEditingMixin, TableMixin, HtmxMixin, CoreMixin):
    """Minimal view harness to exercise InlineEditingMixin behaviour."""

    model = Book
    namespace = "sample"
    url_base = "bigbook"
    templates_path = "powercrud/daisyUI"
    inline_edit_enabled = True

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

    assert response.status_code == 200
    assert b"inline-field-widget" in response.content
    assert b"Save" in response.content


@pytest.mark.django_db
def test_inline_post_success_swaps_display(sample_book, sample_author):
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

    assert response.status_code == 200
    assert b"actions" in response.content
    assert payload == {"inline-row-saved": {"pk": sample_book.pk}}
    sample_book.refresh_from_db()
    assert sample_book.title == "Updated Inline Title"


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
    assert payload == {
        "inline-row-error": {
            "pk": sample_book.pk,
            "row_id": f"pc-row-{sample_book.pk}",
            "message": "This field is required.",
        }
    }
    assert b"text-error" in response.content


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

    assert response.status_code == 200
    assert b"inline-field-widget" in response.content


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
    inline_edit_enabled = True
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
def test_inline_edit_fields_default_to_form_fields():
    view = CoreHarness()
    view.inline_edit_fields = None
    fields = view.get_inline_edit_fields()
    assert fields == view.form_fields


@pytest.mark.django_db
def test_inline_field_dependencies_resolve_endpoint():
    view = CoreHarness()
    view.inline_edit_fields = ["title", "isbn", "author", "genres"]
    view.form_fields = ["title", "isbn", "author", "genres"]
    view.inline_field_dependencies = {"genres": {"depends_on": ["author"]}}
    deps = view.get_inline_field_dependencies()
    assert deps["genres"]["endpoint_url"] == "/resolved/"
    assert deps["genres"]["depends_on"] == ["author"]


@pytest.mark.django_db
def test_inline_edit_fields_intersects_form_fields(caplog):
    class InlineMismatchHarness(CoreHarness):
        inline_edit_fields = ["title", "isbn"]
        form_fields = ["title"]

    view = InlineMismatchHarness()
    with caplog.at_level("WARNING"):
        fields = view.get_inline_edit_fields()

    assert fields == ["title"]
    assert "isbn" in caplog.text


@pytest.mark.django_db
def test_inline_dependency_warns_when_child_not_inline(caplog):
    view = CoreHarness()
    view.inline_field_dependencies = {"genres": {"depends_on": ["author"]}}

    with caplog.at_level("WARNING"):
        deps = view.get_inline_field_dependencies()

    assert deps == {}
    assert "ignored because the field is not inline-editable" in caplog.text


@pytest.mark.django_db
def test_inline_dependency_filters_invalid_parents(caplog):
    view = CoreHarness()
    view.inline_edit_fields = ["title", "isbn", "author", "genres"]
    view.form_fields = ["title", "isbn", "author", "genres"]
    view.inline_field_dependencies = {
        "genres": {
            "depends_on": ["author", "missing"],
        }
    }

    with caplog.at_level("WARNING"):
        deps = view.get_inline_field_dependencies()

    assert deps["genres"]["depends_on"] == ["author"]
    assert "non-inline parent fields" in caplog.text


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
