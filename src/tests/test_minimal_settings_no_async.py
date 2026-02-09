import importlib
import json
import sys
from types import SimpleNamespace

import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory
from neapolitan.views import Role

from sample.models import Author, Book


def _reload_powercrud_mixins():
    """
    Remove cached mixin modules so imports see the current settings.
    """
    for name in list(sys.modules.keys()):
        if name == "powercrud.mixins" or name.startswith("powercrud.mixins."):
            sys.modules.pop(name, None)
    return importlib.import_module("powercrud.mixins")


def test_powercrud_mixin_imports_without_async_stack():
    """
    Smoke-test that importing PowerCRUDMixin does not require async dependencies
    such as django_q or POWERCRUD_SETTINGS. When run under tests.settings_minimal
    this simulates a minimal project that has not enabled async at all.
    """
    mixins_module = _reload_powercrud_mixins()
    assert hasattr(mixins_module, "PowerCRUDMixin")


def _attach_session(request):
    SessionMiddleware(lambda req: None).process_request(request)
    request.session.save()
    return request


def _build_non_async_view_class():
    from powercrud.mixins import PowerCRUDMixin

    class _ShowFormTerminal:
        def show_form(self, request, *args, **kwargs):
            return HttpResponse("show-form-ok")

    class NonAsyncPowerCRUDView(PowerCRUDMixin, _ShowFormTerminal):
        model = Book
        fields = ["id", "title", "author", "published_date"]
        form_fields = ["title", "author", "published_date"]
        bulk_fields = ["author"]
        bulk_delete = True
        use_htmx = True
        use_modal = True
        templates_path = "powercrud/daisyUI"
        base_template_path = "powercrud/base.html"
        namespace = "sample"
        url_base = "book"
        template_name_suffix = "_form"
        role = Role.UPDATE

        def __init__(self, request):
            self.request = request
            self.kwargs = {}
            self._object = None

        def get_object(self):
            return self._object

    return NonAsyncPowerCRUDView


@pytest.mark.django_db
def test_show_form_sync_view_does_not_require_async_conflict_hooks():
    author = Author.objects.create(name="No Async")
    book = Book.objects.create(
        title="Sync Edit",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="8888888888888",
        pages=11,
    )
    request = _attach_session(RequestFactory().get("/"))
    request.htmx = SimpleNamespace(target=None)

    view_cls = _build_non_async_view_class()
    view = view_cls(request)
    view._object = book

    response = view.show_form(request)
    assert response.content == b"show-form-ok"


@pytest.mark.django_db
def test_bulk_delete_sync_view_does_not_require_async_processing_hooks():
    author = Author.objects.create(name="No Async")
    book = Book.objects.create(
        title="Sync Bulk",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9999999999999",
        pages=12,
    )
    request = _attach_session(
        RequestFactory().post(
            "/",
            {"bulk_submit": "1", "delete_selected": "1", "selected_ids[]": [book.pk]},
        )
    )
    request.htmx = SimpleNamespace(target=None)

    view_cls = _build_non_async_view_class()
    view = view_cls(request)

    response = view.bulk_edit(request)
    assert json.loads(response["HX-Trigger"]) == {
        "bulkEditSuccess": True,
        "refreshTable": True,
    }
