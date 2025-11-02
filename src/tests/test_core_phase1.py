from types import SimpleNamespace

import pytest
from django.test import RequestFactory

from neapolitan.views import Role

from powercrud.mixins.core_mixin import CoreMixin
from powercrud.mixins.table_mixin import TableMixin
from powercrud.mixins.paginate_mixin import PaginateMixin
from powercrud.mixins.url_mixin import UrlMixin

from sample.models import Author, Book


@pytest.mark.django_db
def test_core_mixin_expands_fields_and_properties():
    class AuthorView(CoreMixin):
        model = Author
        fields = "__all__"
        properties = "__all__"
        detail_fields = "__fields__"
        detail_properties = "__all__"

    view = AuthorView()

    assert "name" in view.fields
    assert "bio" in view.fields
    # reverse relations should be removed
    assert "books" not in view.fields

    # detail fields default to processed fields list
    assert view.detail_fields == view.fields

    # properties populated and filtered
    assert "has_bio" in view.properties
    assert "property_birth_date" in view.properties


@pytest.mark.django_db
def test_core_mixin_respects_excludes_and_form_fields():
    class BookView(CoreMixin):
        model = Book
        fields = "__all__"
        exclude = ["description"]
        properties = "__all__"
        properties_exclude = ["isbn_empty"]

    view = BookView()

    assert "description" not in view.fields
    assert "isbn_empty" not in view.properties
    # uneditable field should never appear in form_fields
    assert "uneditable_field" not in view.form_fields
    # ensure editable fields are still present
    assert "title" in view.form_fields


@pytest.mark.django_db
def test_core_mixin_all_fields_and_excludes():
    class AllFieldsView(CoreMixin):
        model = Author
        fields = "__all__"
        properties = "__all__"
        properties_exclude = ["has_bio"]
        detail_fields = "__all__"
        detail_properties = "__properties__"
        detail_properties_exclude = ["has_bio"]
        bulk_fields = ["name"]

    view = AllFieldsView()
    assert "books" not in view.fields
    assert "has_bio" not in view.properties
    assert "has_bio" not in view.detail_properties


def test_core_mixin_invalid_property_raises():
    class InvalidPropertyView(CoreMixin):
        model = Author
        fields = ["name"]
        properties = ["missing"]

    with pytest.raises(ValueError):
        InvalidPropertyView()


def test_core_mixin_invalid_fields_raise_value_error():
    class BrokenView(CoreMixin):
        model = Author
        fields = ["nonexistent"]

    with pytest.raises(ValueError):
        BrokenView()


class DummyPaginateParent:
    def __init__(self):
        self.parent_called = False

    def paginate_queryset(self, queryset, page_size):
        self.parent_called = True
        return "parent-result"


def test_paginate_mixin_get_paginate_by_handles_query_params():
    rf = RequestFactory()

    class PaginateView(PaginateMixin):
        paginate_by = 25

    view = PaginateView()

    view.request = rf.get("/?page_size=10")
    assert view.get_paginate_by() == 10

    view.request = rf.get("/?page_size=all")
    assert view.get_paginate_by() is None

    view.request = rf.get("/?page_size=invalid")
    assert view.get_paginate_by() == 25


def test_paginate_mixin_page_size_options_are_strings_without_duplicates():
    class PaginateView(PaginateMixin):
        paginate_by = 12

    view = PaginateView()

    options = view.get_page_size_options()
    assert all(isinstance(option, str) for option in options)
    assert options.count("12") == 1


def test_paginate_queryset_resets_page_when_flagged(monkeypatch):
    rf = RequestFactory()

    class PaginateView(PaginateMixin, DummyPaginateParent):
        paginate_by = 10

    view = PaginateView()
    DummyPaginateParent.__init__(view)

    view.request = rf.get("/?page=5")
    original_querydict = view.request.GET.copy()
    view._reset_pagination = True

    result = view.paginate_queryset([], 10)

    assert result == "parent-result"
    assert view.parent_called is True
    # original QueryDict restored after pagination
    assert view.request.GET == original_querydict


def test_table_mixin_returns_expected_css_values():
    class TableView(TableMixin):
        table_pixel_height_other_page_elements = 120
        table_max_height = 70
        table_max_col_width = 32
        table_header_min_wrap_width = 20
        table_classes = "table-zebra"
        action_button_classes = "btn-xs"
        extra_button_classes = "btn-sm"

    view = TableView()

    assert view.get_table_pixel_height_other_page_elements() == "120px"
    assert view.get_table_max_height() == 70
    assert view.get_table_max_col_width() == "32ch"
    assert view.get_table_header_min_wrap_width() == "20ch"
    assert view.get_table_classes() == "table-zebra"
    assert view.get_action_button_classes() == "btn-xs"
    assert view.get_extra_button_classes() == "btn-sm"


def test_table_header_wrap_never_exceeds_max_width():
    class TableView(TableMixin):
        table_max_col_width = 15
        table_header_min_wrap_width = 25

    view = TableView()
    assert view.get_table_header_min_wrap_width() == "15ch"


def test_url_mixin_get_prefix_handles_namespace():
    class UrlView(UrlMixin):
        namespace = "sample"
        url_base = "book"

    view = UrlView()
    assert view.get_prefix() == "sample:book"

    view.namespace = None
    assert view.get_prefix() == "book"


def test_url_mixin_get_template_names_uses_model_meta():
    class UrlView(UrlMixin):
        model = Author
        template_name_suffix = "_list"
        templates_path = "powercrud/daisyUI"
        template_name = None

    view = UrlView()
    expected = [
        "sample/author_list.html",
        "powercrud/daisyUI/object_list.html",
    ]
    assert view.get_template_names() == expected


def test_safe_reverse_handles_no_reverse_match(monkeypatch):
    from django.urls import NoReverseMatch
    from powercrud.mixins import url_mixin as url_module

    class UrlView(UrlMixin):
        namespace = None
        url_base = "book"

    view = UrlView()

    def fake_reverse(name, kwargs=None):
        raise NoReverseMatch()

    monkeypatch.setattr(url_module, "reverse", fake_reverse)
    assert view.safe_reverse("missing") is None


def test_url_reverse_builds_names_for_roles(monkeypatch):
    from powercrud.mixins import url_mixin as url_module

    calls = []

    def fake_reverse(name, kwargs=None):
        calls.append((name, kwargs))
        return f"/{name}"

    monkeypatch.setattr(url_module, "reverse", fake_reverse)

    class UrlView(UrlMixin):
        namespace = None
        url_base = "book"
        lookup_field = "pk"
        lookup_url_kwarg = "pk"

    view = UrlView()

    assert view.reverse(Role.LIST, view) == "/book-list"
    assert view.reverse(Role.CREATE, view) == "/book-create"

    obj = SimpleNamespace(pk=5)
    assert view.reverse(Role.DETAIL, view, obj) == "/book-detail"
    assert calls[-1] == ("book-detail", {"pk": 5})

    with pytest.raises(ValueError):
        view.reverse(Role.DETAIL, view)


def test_get_success_url_uses_role_and_namespace(monkeypatch):
    from powercrud.mixins import url_mixin as url_module

    results = []

    def fake_reverse(name, kwargs=None):
        results.append((name, kwargs))
        return f"/{name}"

    monkeypatch.setattr(url_module, "reverse", fake_reverse)

    class UrlView(UrlMixin):
        model = Author
        namespace = "sample"
        url_base = "author"
        lookup_field = "pk"
        lookup_url_kwarg = "pk"

    view = UrlView()
    view.role = Role.CREATE
    view.object = SimpleNamespace(pk=7)

    assert view.get_success_url() == "/sample:author-list"
    assert results[-1][0] == "sample:author-list"

    view.role = Role.DETAIL
    assert view.get_success_url() == "/sample:author-detail"
    assert results[-1] == ("sample:author-detail", {"pk": 7})
