from __future__ import annotations

from types import SimpleNamespace

import pytest
from django.test import RequestFactory
from django.views import View

from neapolitan.views import Role

from powercrud.mixins.config_mixin import resolve_class_config
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
    inline_edit_fields = ["title"]
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

    def get_bulk_update_enabled(self):
        return True

    def get_bulk_delete_enabled(self):
        return True

    def get_storage_key(self):
        return "storage-key"

    def get_original_target(self):
        return "#content"

    def get_htmx_target(self):
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


class CreateDeniedUrlViewHarness(UrlViewHarness):
    """URL context harness that denies PowerCRUD-owned create permission."""

    def has_power_create_permission(self, request):
        """Deny create permission for context-level create URL tests."""
        return False


class LegacyInlineUrlViewHarness(UrlMixin, ContextBase, View):
    namespace = "sample"
    url_base = "legacy-book"
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
    template_name = None
    template_name_suffix = "_detail"
    templates_path = "powercrud/daisyUI"
    base_template_path = "powercrud/base.html"
    path_converter = "int"
    model = Book
    inline_edit_enabled = True


class SelectionButtonUrlHarness(UrlMixin, ContextBase, View):
    namespace = "sample"
    url_base = "selection-book"
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
    template_name = None
    template_name_suffix = "_detail"
    templates_path = "powercrud/daisyUI"
    base_template_path = "powercrud/base.html"
    path_converter = "int"
    model = Book
    use_htmx = True
    use_modal = True
    bulk_fields = []
    bulk_delete = False
    extra_buttons = [
        {
            "url_name": "sample:bigbook-selected-summary",
            "text": "Selected Summary",
            "uses_selection": True,
        }
    ]


class SelectionButtonOptOutUrlHarness(SelectionButtonUrlHarness):
    url_base = "selection-opt-out-book"
    extra_button_selection_controls_disabled = True


class LazyRowActionUrlHarness(UrlMixin, ContextBase, View):
    """URL harness with one lazy dropdown row action."""

    namespace = "sample"
    url_base = "lazy-book"
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
    template_name = None
    template_name_suffix = "_detail"
    templates_path = "powercrud/daisyUI"
    base_template_path = "powercrud/base.html"
    path_converter = "int"
    model = Book
    extra_actions_mode = "dropdown"
    extra_actions = [
        {
            "url_name": "sample:book-detail",
            "text": "Preview",
            "disabled_state": "get_preview_disabled_state",
            "disabled_state_mode": "lazy",
        }
    ]


class LazyHiddenRowActionUrlHarness(UrlMixin, ContextBase, View):
    """URL harness with one lazy-hidden dropdown row action."""

    namespace = "sample"
    url_base = "lazy-hidden-book"
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
    template_name = None
    template_name_suffix = "_detail"
    templates_path = "powercrud/daisyUI"
    base_template_path = "powercrud/base.html"
    path_converter = "int"
    model = Book
    extra_actions_mode = "dropdown"
    extra_actions = [
        {
            "url_name": "sample:book-detail",
            "text": "Preview",
            "hidden_if": "should_hide_preview",
            "hidden_if_mode": "lazy",
        }
    ]


class LazyCellTooltipUrlHarness(UrlMixin, ContextBase, View):
    """URL harness with one lazy list-cell tooltip."""

    namespace = "sample"
    url_base = "lazy-tooltip-book"
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
    template_name = None
    template_name_suffix = "_detail"
    templates_path = "powercrud/daisyUI"
    base_template_path = "powercrud/base.html"
    path_converter = "int"
    model = Book
    fields = ["title"]
    list_cell_tooltip_fields = {
        "title": {"hook": "get_title_tooltip", "mode": "lazy"}
    }


def test_resolve_class_config_copies_mutable_values():
    cfg = resolve_class_config(UrlViewHarness)

    assert cfg.bulk_fields == ["author"], (
        "Class-level config snapshots should expose primitive list values."
    )
    assert cfg.bulk_fields is not UrlViewHarness.bulk_fields, (
        "Class-level config snapshots should copy mutable list values so callers cannot mutate class config accidentally."
    )


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
        lambda name, kwargs=None: (
            f"/{name}" if kwargs is None else f"/{name}/{kwargs['pk']}"
        ),
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


def test_get_context_data_hides_create_url_when_create_permission_denied(monkeypatch):
    """Denied create permission should clear create_view_url at context level."""
    request = RequestFactory().get("/")
    request.session = {"selected": []}
    view = CreateDeniedUrlViewHarness(request, None, role=Role.LIST)

    monkeypatch.setattr(
        url_module,
        "reverse",
        lambda name, kwargs=None: f"/{name}",
    )

    context = view.get_context_data()

    assert context["create_view_url"] is None, (
        "Denied create permission should hide Create before template rendering, even when the create route reverses."
    )
    assert context["list_view_url"] == "/sample:book-list", (
        "The harness should still resolve the list URL so the test proves create permission, not URL reversal, hid Create."
    )


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
    assert "book-inline-row" in names
    assert "book-inline-dependency" in names


def test_get_urls_generates_selection_endpoints_for_selection_extra_buttons(monkeypatch):
    def fake_as_view(cls, **kwargs):
        return lambda request, *args, **kw: None

    monkeypatch.setattr(
        SelectionButtonUrlHarness,
        "as_view",
        classmethod(fake_as_view),
    )

    patterns = SelectionButtonUrlHarness.get_urls()
    names = {pattern.name for pattern in patterns}
    assert "selection-book-bulk-edit" not in names, (
        "Selection-aware extra buttons should not register the built-in bulk edit modal route."
    )
    assert "selection-book-toggle-selection" in names, (
        "Selection-aware extra buttons should register row-selection toggle URLs."
    )
    assert "selection-book-clear-selection" in names, (
        "Selection-aware extra buttons should register clear-selection URLs."
    )
    assert "selection-book-toggle-all-selection" in names, (
        "Selection-aware extra buttons should register page-level selection URLs."
    )
    assert "selection-book-select-all-matching" in names, (
        "Selection-aware extra buttons should register filtered-selection metadata URLs."
    )


def test_get_urls_respects_extra_button_selection_controls_opt_out(monkeypatch):
    def fake_as_view(cls, **kwargs):
        return lambda request, *args, **kw: None

    monkeypatch.setattr(
        SelectionButtonOptOutUrlHarness,
        "as_view",
        classmethod(fake_as_view),
    )

    patterns = SelectionButtonOptOutUrlHarness.get_urls()
    names = {pattern.name for pattern in patterns}
    assert "selection-opt-out-book-bulk-edit" not in names, (
        "Opt-out selection-only views should not register the built-in bulk edit modal route."
    )
    assert "selection-opt-out-book-toggle-selection" not in names, (
        "Opt-out selection-only views should not register row-selection endpoints."
    )
    assert "selection-opt-out-book-clear-selection" not in names, (
        "Opt-out selection-only views should not register clear-selection endpoints."
    )


def test_get_urls_generates_lazy_row_action_state_endpoint(monkeypatch):
    """Lazy row actions should register the per-row state endpoint."""

    recorded = []

    def fake_as_view(cls, **kwargs):
        recorded.append(kwargs)
        return lambda request, *args, **kw: None

    monkeypatch.setattr(
        LazyRowActionUrlHarness,
        "as_view",
        classmethod(fake_as_view),
    )

    patterns = LazyRowActionUrlHarness.get_urls()
    names = {pattern.name for pattern in patterns}

    assert "lazy-book-row-action-states" in names, (
        "Views with lazy row actions should expose a row-action state URL."
    )
    assert any(
        kwargs.get("role") == Role.LIST
        and kwargs.get("row_action_state_action") == "states"
        for kwargs in recorded
    ), "The lazy row-action state URL should route to the list role state handler."


def test_get_urls_generates_lazy_hidden_row_action_state_endpoint(monkeypatch):
    """Lazy-hidden row actions should register the per-row state endpoint."""

    recorded = []

    def fake_as_view(cls, **kwargs):
        recorded.append(kwargs)
        return lambda request, *args, **kw: None

    monkeypatch.setattr(
        LazyHiddenRowActionUrlHarness,
        "as_view",
        classmethod(fake_as_view),
    )

    patterns = LazyHiddenRowActionUrlHarness.get_urls()
    names = {pattern.name for pattern in patterns}

    assert "lazy-hidden-book-row-action-states" in names, (
        "Views with lazy hidden row actions should expose a row-action state URL."
    )
    assert any(
        kwargs.get("role") == Role.LIST
        and kwargs.get("row_action_state_action") == "states"
        for kwargs in recorded
    ), "The lazy hidden row-action state URL should route to the list role state handler."


def test_get_urls_generates_lazy_cell_tooltip_endpoint(monkeypatch):
    """Lazy list-cell tooltips should register the per-cell content endpoint."""

    recorded = []

    def fake_as_view(cls, **kwargs):
        recorded.append(kwargs)
        return lambda request, *args, **kw: None

    monkeypatch.setattr(
        LazyCellTooltipUrlHarness,
        "as_view",
        classmethod(fake_as_view),
    )

    patterns = LazyCellTooltipUrlHarness.get_urls()
    names = {pattern.name for pattern in patterns}

    assert "lazy-tooltip-book-cell-tooltip" in names, (
        "Views with lazy list-cell tooltips should expose a cell-tooltip URL."
    )
    assert any(
        kwargs.get("role") == Role.LIST
        and kwargs.get("cell_tooltip_action") == "content"
        for kwargs in recorded
    ), "The lazy cell-tooltip URL should route to the list role content handler."


def test_legacy_inline_edit_enabled_still_generates_inline_urls(monkeypatch):
    def fake_as_view(cls, **kwargs):
        return lambda request, *args, **kw: None

    monkeypatch.setattr(LegacyInlineUrlViewHarness, "as_view", classmethod(fake_as_view))

    patterns = LegacyInlineUrlViewHarness.get_urls()
    names = {pattern.name for pattern in patterns}
    assert (
        "legacy-book-inline-row" in names
    ), "Legacy inline_edit_enabled=True should still register inline row URLs during the compatibility window."
    assert (
        "legacy-book-inline-dependency" in names
    ), "Legacy inline_edit_enabled=True should still register inline dependency URLs during the compatibility window."
