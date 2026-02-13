from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

from neapolitan.views import Role

from powercrud.mixins.form_mixin import FormMixin
from powercrud.mixins.bulk_mixin.view_mixin import ViewMixin
from powercrud.mixins.htmx_mixin import HtmxMixin
from sample.models import Author, Book


class BaseContext:
    def get_context_data(self, **kwargs):
        kwargs.setdefault("request", self.request)
        return kwargs


class DummyFormView(HtmxMixin, ViewMixin, FormMixin, BaseContext):
    model = Book
    form_fields = ["title", "author", "published_date"]
    dropdown_sort_options = {"author": "name"}
    use_crispy = None
    use_htmx = True
    bulk_fields = ["author"]
    bulk_delete = True
    role = Role.UPDATE
    templates_path = "powercrud/daisyUI"
    form_class = None
    base_template_path = "powercrud/base.html"
    namespace = "sample"
    url_base = "book"
    template_name_suffix = "_form"
    modal_id = None
    modal_target = None

    def __init__(self, request):
        self.request = request
        self._object = None
        self.kwargs = {}

    def get_object(self):
        return self._object

    def get_conflict_checking_enabled(self):
        return True

    def _check_for_conflicts(self, selected_ids):
        return True

    def list(self, request, *args, **kwargs):
        return HttpResponse("list")

    def get_original_target(self):
        return "#content"

    def get_modal_target(self):
        return "#modal"

    def get_selected_ids_from_session(self, request):
        return request.session.get("selected", [])

    def save_selected_ids_to_session(self, request, ids):
        request.session["selected"] = list(ids)

    def clear_selection_from_session(self, request):
        request.session["selected"] = []

    def get_bulk_selection_key_suffix(self):
        return "test"


def attach_session(request):
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.mark.django_db
def test_get_form_class_uses_crispy(settings):
    if "crispy_forms" not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS = tuple(settings.INSTALLED_APPS) + ("crispy_forms",)

    author = Author.objects.create(name="Ada")
    request = attach_session(RequestFactory().get("/"))
    view = DummyFormView(request)
    view.use_crispy = True
    view._object = Book.objects.create(
        title="Book",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="1234567890123",
        pages=10,
    )

    form_class = view.get_form_class()
    form = form_class()
    assert hasattr(form, "helper")
    assert form.helper.form_tag is False
    assert form.base_fields["published_date"].widget.input_type == "date"


@pytest.mark.django_db
def test_get_form_class_without_crispy(settings):
    settings.INSTALLED_APPS = tuple(
        app for app in settings.INSTALLED_APPS if app != "crispy_forms"
    )
    request = attach_session(RequestFactory().get("/"))
    view = DummyFormView(request)
    view.use_crispy = True
    form_class = view.get_form_class()
    form = form_class()
    assert not hasattr(form, "helper")


@pytest.mark.django_db
def test_show_form_conflict_returns_render(monkeypatch):
    author = Author.objects.create(name="Ada")
    book = Book.objects.create(
        title="Conflict",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="3213213210000",
        pages=5,
    )
    request = attach_session(RequestFactory().get("/"))
    request.htmx = SimpleNamespace()
    view = DummyFormView(request)
    view._object = book
    view.object = book

    captured = {}

    def fake_render(request, template_name, context):
        captured["template"] = template_name
        captured["context"] = context
        return HttpResponse("conflict")

    monkeypatch.setattr("powercrud.mixins.form_mixin.render", fake_render)

    def fake_render_response(self, context):
        return fake_render(self.request, "template", context)

    monkeypatch.setattr(DummyFormView, "render_to_response", fake_render_response)
    response = view.show_form(request)
    assert response.content == b"conflict"
    assert captured["context"]["conflict_detected"] is True


@pytest.mark.django_db
def test_form_valid_htmx_returns_list(monkeypatch):
    author = Author.objects.create(name="Ada")
    book = Book.objects.create(
        title="Async",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="5555555550000",
        pages=50,
    )
    request = attach_session(RequestFactory().post("/"))
    request.htmx = SimpleNamespace()
    view = DummyFormView(request)
    view._object = book
    view.object = book
    view.role = Role.UPDATE

    monkeypatch.setattr(
        "powercrud.mixins.form_mixin.reverse", lambda name, kwargs=None: f"/{name}"
    )

    form = view.get_form_class()(
        instance=book,
        data={"title": "Async", "author": author.pk, "published_date": "2024-01-01"},
    )
    assert form.is_valid()

    monkeypatch.setattr(view, "_check_for_conflicts", lambda selected_ids: False)
    response = view.form_valid(form)
    assert isinstance(response, HttpResponse)
    assert json.loads(response["HX-Trigger"]) == {"formSuccess": True}
    assert response["HX-Retarget"] == view.get_original_target()


@pytest.mark.django_db
def test_form_invalid_htmx_keeps_modal(monkeypatch):
    author = Author.objects.create(name="Ada")
    book = Book.objects.create(
        title="Invalid",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="4545454545000",
        pages=12,
    )
    request = attach_session(RequestFactory().post("/"))
    request.htmx = True
    view = DummyFormView(request)
    view._object = book
    view.object = book
    view.role = Role.UPDATE
    view.use_modal = True

    monkeypatch.setattr(
        "powercrud.mixins.form_mixin.render",
        lambda request, template_name, context: HttpResponse("invalid", headers={}),
    )
    monkeypatch.setattr(
        "powercrud.mixins.form_mixin.reverse", lambda name, kwargs=None: f"/{name}"
    )

    form = view.get_form_class()(instance=book, data={})
    assert not form.is_valid()

    response = view.form_invalid(form)
    assert "formError" in json.loads(response["HX-Trigger"])
    assert response["HX-Retarget"] == view.get_modal_target()
