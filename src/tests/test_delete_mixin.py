from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.test import RequestFactory
from neapolitan.views import Role

from powercrud.mixins import PowerCRUDAsyncMixin, PowerCRUDMixin
from powercrud.mixins import async_mixin as async_module
from powercrud.mixins import delete_mixin as delete_module
from sample.models import Book


class DummyResponse(HttpResponse):
    """Lightweight response double that exposes rendered template context."""

    def __init__(self, template_name, context, rendered_get=None):
        super().__init__(content=b"")
        self.template_name = template_name
        self.context_data = context
        self.rendered_get = rendered_get


class ContextBase:
    """Provide a terminal get_context_data implementation for mixin harnesses."""

    def get_context_data(self, **kwargs):
        kwargs.setdefault("request", getattr(self, "request", None))
        return kwargs


class DeleteHarness(PowerCRUDMixin, ContextBase):
    """Concrete view harness for unit-testing DeleteMixin behavior."""

    namespace = "sample"
    url_base = "book"
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
    template_name = None
    template_name_suffix = "_confirm_delete"
    templates_path = "powercrud/daisyUI"
    base_template_path = "powercrud/base.html"
    default_htmx_target = "#content"
    use_htmx = True
    use_modal = True
    modal_id = "powercrudBaseModal"
    modal_target = "powercrudModalContent"
    path_converter = "int"
    model = Book
    role = Role.DELETE
    fields = ["title"]

    def __init__(self, request, obj):
        self.request = request
        self.object = None
        self._object = obj
        self.kwargs = {"pk": getattr(obj, "pk", 1)}
        super().__init__()

    def get_object(self):
        return self._object

    def get_use_crispy(self):
        return False

    def get_bulk_edit_enabled(self):
        return False

    def get_bulk_delete_enabled(self):
        return False

    def get_storage_key(self):
        return "storage-key"

    def get_original_target(self):
        return "#content"

    def get_table_pixel_height_other_page_elements(self):
        return "0px"

    def get_table_max_height(self):
        return 70

    def get_table_max_col_width(self):
        return "20ch"

    def get_table_header_min_wrap_width(self):
        return "12ch"

    def get_table_classes(self):
        return "table-zebra"

    def get_success_url(self):
        return "/books/"


class AsyncDeleteHarness(PowerCRUDAsyncMixin, ContextBase):
    """Harness that layers async conflict checks over the shared delete path."""

    namespace = "sample"
    url_base = "book"
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
    template_name = None
    template_name_suffix = "_confirm_delete"
    templates_path = "powercrud/daisyUI"
    base_template_path = "powercrud/base.html"
    default_htmx_target = "#content"
    use_htmx = True
    use_modal = True
    modal_id = "powercrudBaseModal"
    modal_target = "powercrudModalContent"
    path_converter = "int"
    model = Book
    role = Role.DELETE
    fields = ["title"]
    bulk_async = False
    bulk_async_conflict_checking = False

    def __init__(self, request, obj):
        self.request = request
        self.object = None
        self._object = obj
        self.kwargs = {"pk": getattr(obj, "pk", 1)}
        super().__init__()

    def get_object(self):
        return self._object

    def get_use_crispy(self):
        return False

    def get_bulk_edit_enabled(self):
        return False

    def get_bulk_delete_enabled(self):
        return False

    def get_storage_key(self):
        return "storage-key"

    def get_original_target(self):
        return "#content"

    def get_table_pixel_height_other_page_elements(self):
        return "0px"

    def get_table_max_height(self):
        return 70

    def get_table_max_col_width(self):
        return "20ch"

    def get_table_header_min_wrap_width(self):
        return "12ch"

    def get_table_classes(self):
        return "table-zebra"

    def get_success_url(self):
        return "/books/"


def attach_session(request):
    """Attach a usable Django session to a RequestFactory request."""
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    return request


def make_htmx_post(rf: RequestFactory, data=None):
    """Build a POST request flagged as HTMX for modal-flow tests."""
    request = attach_session(rf.post("/sample/book/1/delete/", data or {}))
    request.htmx = SimpleNamespace(target=None)
    request._dont_enforce_csrf_checks = True
    return request


@pytest.fixture
def fake_delete_render(monkeypatch):
    """Capture delete-error render calls without relying on a full template stack."""

    def _render(request, template_name, context):
        return DummyResponse(template_name, context, request.GET.copy())

    monkeypatch.setattr(delete_module, "render", _render)


@pytest.fixture
def fake_async_render(monkeypatch):
    """Capture async conflict render calls without rendering real templates."""

    def _render(request, template_name, context):
        return DummyResponse(template_name, context, request.GET.copy())

    monkeypatch.setattr(async_module, "render", _render)


@pytest.fixture(autouse=True)
def fake_reverse(monkeypatch):
    """Keep delete view context deterministic without depending on URLConf wiring."""

    def _reverse(name, kwargs=None):
        if kwargs:
            return f"/{name}/{kwargs['pk']}"
        return f"/{name}"

    monkeypatch.setattr("powercrud.mixins.url_mixin.reverse", _reverse)


class RefusingDelete:
    """Delete target that raises ValidationError with a configurable payload."""

    def __init__(self, message):
        self.pk = 1
        self.message = message
        self.delete_calls = 0

    def delete(self):
        self.delete_calls += 1
        raise ValidationError(self.message)

    def __str__(self):
        return "Blocked Book"


class ExplodingDelete:
    """Delete target that raises an unexpected exception."""

    def __init__(self):
        self.pk = 1

    def delete(self):
        raise RuntimeError("boom")

    def __str__(self):
        return "Exploding Book"


class SuccessfulDelete:
    """Delete target that records successful delete calls."""

    def __init__(self):
        self.pk = 1
        self.delete_calls = 0

    def delete(self):
        self.delete_calls += 1

    def __str__(self):
        return "Deleted Book"


def test_delete_process_htmx_validation_error_keeps_modal(rf, fake_delete_render):
    request = make_htmx_post(
        rf,
        data={
            "_powercrud_filter_status": "active",
            "_powercrud_filter_owner": "7",
        },
    )
    obj = RefusingDelete("Canonical rows cannot be deleted.")
    view = DeleteHarness(request, obj)

    response = view.process_deletion(request, pk=obj.pk)

    assert response.status_code == 200, (
        "Handled HTMX delete refusals should return a normal 200 response so HTMX can swap the modal content."
    )
    assert response.template_name.endswith("object_confirm_delete.html#pcrud_content"), (
        "Handled HTMX delete refusals should re-render the delete confirmation partial rather than falling through to a list response."
    )
    assert response.context_data["delete_errors"] == [
        "Canonical rows cannot be deleted."
    ], "Delete refusal handling should expose the flattened validation messages to the template."
    assert response.rendered_get.get("status") == "active", (
        "Delete refusal redisplay should restore posted filter parameters so the template can preserve list context."
    )
    assert response.rendered_get.get("owner") == "7", (
        "Delete refusal redisplay should preserve every posted filter parameter, not just the first one."
    )
    assert response["HX-Retarget"] == view.get_modal_target(), (
        "Handled HTMX delete refusals should retarget the response back into the modal content container."
    )
    trigger = json.loads(response["HX-Trigger"])
    assert trigger["formError"] is True, (
        "Handled HTMX delete refusals should mark the response as a user-facing form-style error."
    )
    assert trigger["showModal"] == "powercrudBaseModal", (
        "Handled HTMX delete refusals should explicitly keep the delete modal open."
    )


def test_delete_process_non_htmx_validation_error_rerenders_confirmation(
    rf, fake_delete_render
):
    request = attach_session(rf.post("/sample/book/1/delete/"))
    obj = RefusingDelete(["Cannot remove this book.", "Still referenced elsewhere."])
    view = DeleteHarness(request, obj)

    response = view.process_deletion(request, pk=obj.pk)

    assert response.status_code == 200, (
        "Handled non-HTMX delete refusals should re-render the confirmation page instead of redirecting or failing."
    )
    assert response.template_name.endswith("object_confirm_delete.html"), (
        "Handled non-HTMX delete refusals should render the full delete confirmation template."
    )
    assert response.context_data["delete_errors"] == [
        "Cannot remove this book.",
        "Still referenced elsewhere.",
    ], "Delete refusal handling should preserve all ValidationError messages for non-HTMX responses."
    assert "HX-Retarget" not in response, (
        "Non-HTMX delete refusal responses should not add modal-only HTMX headers."
    )


def test_delete_process_flattens_validation_error_dicts(rf, fake_delete_render):
    request = make_htmx_post(rf)
    obj = RefusingDelete(
        {
            "title": ["bad state"],
            "__all__": ["general rule"],
        }
    )
    view = DeleteHarness(request, obj)

    response = view.process_deletion(request, pk=obj.pk)

    assert response.context_data["delete_errors"] == [
        "title: bad state",
        "general rule",
    ], (
        "Dict-shaped delete ValidationErrors should be flattened into user-displayable messages while preserving field context where possible."
    )


def test_delete_process_success_still_redirects(rf):
    request = attach_session(rf.post("/sample/book/1/delete/"))
    obj = SuccessfulDelete()
    view = DeleteHarness(request, obj)

    response = view.process_deletion(request, pk=obj.pk)

    assert response.status_code == 302, (
        "Successful single deletes should preserve the existing redirect-based success contract in phase 1."
    )
    assert response["Location"] == "/books/", (
        "Successful single deletes should still redirect to the configured success URL."
    )
    assert obj.delete_calls == 1, (
        "Successful single deletes should still call delete() exactly once."
    )


def test_delete_process_unexpected_exceptions_still_bubble(rf):
    request = attach_session(rf.post("/sample/book/1/delete/"))
    view = DeleteHarness(request, ExplodingDelete())

    with pytest.raises(RuntimeError, match="boom"):
        view.process_deletion(request, pk=1)


def test_async_delete_conflict_short_circuits_before_delete(rf, fake_async_render):
    request = make_htmx_post(rf)
    obj = SuccessfulDelete()
    view = AsyncDeleteHarness(request, obj)
    view.get_conflict_checking_enabled = lambda: True
    view._check_for_conflicts = lambda selected_ids: True

    response = view.process_deletion(request, pk=obj.pk)

    assert response.template_name.endswith("#conflict_detected"), (
        "Async delete conflicts should keep using the existing conflict response template."
    )
    assert obj.delete_calls == 0, (
        "Async delete conflict detection should short-circuit before the shared delete path attempts to delete the object."
    )
