from __future__ import annotations

from types import SimpleNamespace

import pytest
from django.test import RequestFactory
from django.views import View

from neapolitan.views import Role

from powercrud.mixins import url_mixin as url_module
from powercrud.mixins.url_mixin import UrlMixin
from sample.models import Author, Book


class ContextBase:
    def get_context_data(self, **kwargs):
        kwargs.setdefault("request", getattr(self, "request", None))
        return kwargs


class UrlViewHarness(UrlMixin, ContextBase, View):
    namespace = "sample"
    url_base = "book"
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
    template_name = None
    template_name_suffix = "_detail"
    templates_path = "powercrud/daisyUI"
    base_template_path = "powercrud/base.html"
    path_converter = "int"
    model = Book
    bulk_fields = ["author"]
    bulk_delete = True
    paginate_by = 25

    def __init__(self, request, obj, role=Role.DETAIL):
        self.request = request
        self.object = obj
        self.role = role

    # mixin hooks
    def get_use_crispy(self):
        return False

    def get_use_htmx(self):
        return True

    def get_use_modal(self):
        return True

    def get_bulk_edit_enabled(self):
        return True

    def get_bulk_delete_enabled(self):
        return True

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

    def get_page_size_options(self):
        return ["10", "25"]

    def get_selected_ids_from_session(self, request):
        return request.session.get("selected", [])


@pytest.mark.django_db
def test_get_template_names_and_prefix(monkeypatch):
    author = Author.objects.create(name="Ada")
    book = Book.objects.create(
        title="Signal",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="1234567890123",
        pages=10,
    )
    request = RequestFactory().get("/?sort=title")
    request.session = {"selected": [str(book.pk)]}

    view = UrlViewHarness(request, book)
    monkeypatch.setattr(
        url_module,
        "reverse",
        lambda name, kwargs=None: f"/{name}" if kwargs is None else f"/{name}/{kwargs['pk']}",
        raising=False,
    )

    templates = view.get_template_names()
    assert templates[0] == "sample/book_detail.html"
    assert view.get_prefix() == "sample:book"

    from django.urls import NoReverseMatch

    def raise_no_reverse(*args, **kwargs):
        raise NoReverseMatch()

    monkeypatch.setattr(url_module, "reverse", raise_no_reverse, raising=False)
    assert view.safe_reverse("missing") is None


def test_get_success_url_uses_role(monkeypatch):
    request = RequestFactory().get("/")
    request.session = {"selected": []}
    dummy_obj = SimpleNamespace(pk=5)
    view = UrlViewHarness(request, dummy_obj, role=Role.CREATE)
    monkeypatch.setattr(url_module, "reverse", lambda name, kwargs=None: f"/{name}")
    assert view.get_success_url() == "/sample:book-list"

    view.role = Role.DETAIL
    monkeypatch.setattr(
        url_module,
        "reverse",
        lambda name, kwargs=None: f"/{name}/{kwargs['pk']}" if kwargs else f"/{name}",
    )
    assert view.get_success_url() == "/sample:book-detail/5"


def test_safe_reverse_handles_failure(monkeypatch):
    view = UrlViewHarness(RequestFactory().get("/"), SimpleNamespace(pk=1))

    def boom(*args, **kwargs):
        from django.urls import NoReverseMatch
        raise NoReverseMatch()

    monkeypatch.setattr(url_module, "reverse", boom)
    assert view.safe_reverse("missing") is None


def test_get_urls_generates_patterns(monkeypatch):
    recorded = []

    def fake_as_view(cls, **kwargs):
        recorded.append(kwargs.get("role"))
        return lambda request, *args, **kw: None

    monkeypatch.setattr(UrlViewHarness, "as_view", classmethod(fake_as_view))

    patterns = UrlViewHarness.get_urls()
    names = {pattern.name for pattern in patterns}
    assert "book-list" in names
    assert "book-bulk-edit" in names
