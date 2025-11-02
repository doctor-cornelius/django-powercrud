from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory

from powercrud.mixins.async_mixin import AsyncMixin
from powercrud.mixins.bulk_mixin.metadata_mixin import MetadataMixin
from powercrud.mixins.bulk_mixin.operation_mixin import OperationMixin
from powercrud.mixins.bulk_mixin.selection_mixin import SelectionMixin
from powercrud.mixins.bulk_mixin.view_mixin import ViewMixin
from powercrud.mixins.htmx_mixin import HtmxMixin
from sample.models import Author, Book


class DummyResponse(HttpResponse):
    def __init__(self, template_name, context):
        super().__init__(content=b"")
        self.template_name = template_name
        self.context_data = context


def make_htmx_request(rf: RequestFactory, method: str = "get", data=None):
    handler = getattr(rf, method.lower())
    request = handler("/", data or {})
    SessionMiddleware(lambda req: None).process_request(request)
    request.session.save()
    if method.lower() == "post":
        request._dont_enforce_csrf_checks = True
    request.htmx = SimpleNamespace(target=None)
    return request


class HarnessView(
    HtmxMixin,
    AsyncMixin,
    SelectionMixin,
    MetadataMixin,
    OperationMixin,
    ViewMixin,
):
    model = Book
    lookup_url_kwarg = "pk"
    templates_path = "powercrud/daisyUI"
    bulk_fields = ["author"]
    bulk_delete = True
    use_modal = True
    use_htmx = True
    modal_id = "bulkModal"
    modal_target = "bulkContent"
    default_htmx_target = "#content"
    dropdown_sort_options = {"author": "name"}
    bulk_async = False
    bulk_async_conflict_checking = False

    def __init__(self, request):
        self.request = request


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def fake_render(monkeypatch):
    def _render(request, template_name, context):
        return DummyResponse(template_name, context)

    monkeypatch.setattr(
        "powercrud.mixins.bulk_mixin.view_mixin.render",
        _render,
    )


def test_bulk_edit_requires_htmx(rf):
    request = rf.get("/")
    request.session = {}
    view = HarnessView(request)

    response = view.bulk_edit(request)
    assert response.status_code == 400


@pytest.mark.django_db
def test_bulk_edit_returns_error_without_ids(rf, fake_render):
    request = make_htmx_request(rf)
    view = HarnessView(request)

    response = view.bulk_edit(request)

    assert response.template_name.endswith("#bulk_edit_error")
    assert response.context_data["error"] == "No items selected for bulk edit."


@pytest.mark.django_db
def test_bulk_edit_detects_conflicts(rf, fake_render):
    author = Author.objects.create(name="Alpha")
    book = Book.objects.create(
        title="Example",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="3333333333333",
        pages=9,
    )

    request = make_htmx_request(rf, data={"selected_ids[]": [book.pk]})
    view = HarnessView(request)
    view.get_conflict_checking_enabled = lambda: True
    view._check_for_conflicts = lambda ids: True

    response = view.bulk_edit(request)

    assert response.template_name.endswith("#bulk_edit_conflict")
    assert response.context_data["conflict_detected"] is True
    assert response.context_data["selected_count"] == 1


@pytest.mark.django_db
def test_bulk_edit_handles_missing_bulk_fields(rf, fake_render):
    author = Author.objects.create(name="Alpha")
    book = Book.objects.create(
        title="Example",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="4444444444444",
        pages=12,
    )

    request = make_htmx_request(rf, data={"selected_ids[]": [book.pk]})
    view = HarnessView(request)
    view.bulk_fields = []
    view.bulk_delete = False

    response = view.bulk_edit(request)
    assert response.context_data["error"] == "No fields configured for bulk editing."


@pytest.mark.django_db
def test_bulk_edit_process_post_delete_success(rf):
    author = Author.objects.create(name="Alpha")
    book = Book.objects.create(
        title="DeleteMe",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="5555555555555",
        pages=20,
    )

    request = make_htmx_request(
        rf,
        method="post",
        data={
            "bulk_submit": "1",
            "delete_selected": "1",
            "selected_ids[]": [book.pk],
        },
    )
    view = HarnessView(request)
    view._perform_bulk_delete = lambda queryset: {
        "success": True,
        "success_records": queryset.count(),
        "errors": [],
    }

    response = view.bulk_edit(request)
    assert isinstance(response, HttpResponse)
    assert json.loads(response["HX-Trigger"]) == {
        "bulkEditSuccess": True,
        "refreshTable": True,
    }


@pytest.mark.django_db
def test_bulk_edit_process_post_async(rf, monkeypatch):
    author = Author.objects.create(name="Ada")
    book = Book.objects.create(
        title="Async",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="7777777777777",
        pages=20,
    )

    request = make_htmx_request(
        rf,
        method="post",
        data={
            "bulk_submit": "1",
            "selected_ids[]": [book.pk],
            "fields_to_update": ["author"],
            "author": str(author.pk),
        },
    )
    view = HarnessView(request)

    monkeypatch.setattr(view, "should_process_async", lambda count: True)
    called = {"invoked": False}

    def fake_handle(*args, **kwargs):
        called["invoked"] = True
        return "async"

    monkeypatch.setattr(view, "_handle_async_bulk_operation", fake_handle)

    response = view.bulk_edit(request)
    assert called["invoked"] is True
    assert response == "async"


@pytest.mark.django_db
def test_bulk_edit_process_post_update_error(rf, fake_render):
    author = Author.objects.create(name="Alpha")
    book = Book.objects.create(
        title="Needs Update",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="6666666666666",
        pages=22,
    )

    request = make_htmx_request(
        rf,
        method="post",
        data={
            "bulk_submit": "1",
            "selected_ids[]": [book.pk],
            "fields_to_update": ["author"],
            "author": str(author.pk),
        },
    )
    view = HarnessView(request)
    view._perform_bulk_update = lambda *args, **kwargs: {
        "success": False,
        "errors": [("author", ["bad value"])],
        "success_records": 0,
    }

    response = view.bulk_edit(request)

    assert response.template_name.endswith("bulk_edit_form.html")
    trigger = json.loads(response["HX-Trigger"])
    assert trigger["formError"] is True
    assert response["HX-Retarget"] == view.get_modal_target()
