import re
from pathlib import Path
from types import SimpleNamespace
from datetime import date

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.urls import reverse
from django.test import RequestFactory

from neapolitan.views import Role

from powercrud.mixins.core_mixin import CoreMixin
from powercrud.mixins.table_mixin import TableMixin
from powercrud.mixins.paginate_mixin import PaginateMixin
from powercrud.mixins.url_mixin import UrlMixin

from sample.models import Author, Book, Genre


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
def test_core_mixin_accepts_non_editable_model_fields_for_form_display_fields():
    class BookView(CoreMixin):
        model = Book
        fields = "__all__"
        form_display_fields = ["uneditable_field", "author"]

    view = BookView()

    assert view.form_display_fields == ["uneditable_field", "author"], (
        "form_display_fields should accept model fields used for display-only context, including editable=False fields."
    )


def test_core_mixin_invalid_form_display_field_raises_value_error():
    class BrokenView(CoreMixin):
        model = Book
        fields = "__all__"
        form_display_fields = ["missing_field"]

    with pytest.raises(ValueError, match="form_display_fields"):
        BrokenView()


@pytest.mark.django_db
def test_core_mixin_dedupes_applicable_string_lists():
    """Configured list-style options should quietly keep first occurrence only."""

    class DedupedView(CoreMixin):
        model = Book
        fields = ["title", "author", "title", "published_date"]
        properties = ["isbn_empty", "isbn_empty"]
        exclude = ["published_date", "published_date"]
        detail_fields = ["author", "title", "author"]
        detail_exclude = ["author", "author"]
        detail_properties = ["isbn_empty", "isbn_empty"]
        detail_properties_exclude = []
        form_fields = ["title", "author", "title"]
        form_fields_exclude = ["author", "author"]
        form_display_fields = ["author", "author"]
        form_disabled_fields = ["title", "title"]
        bulk_fields = ["author", "author"]
        inline_edit_fields = ["title", "title"]

    view = DedupedView()

    assert view.fields == ["title", "author"], (
        "fields should quietly drop later duplicates while keeping first-occurrence order after excludes are applied."
    )
    assert view.properties == ["isbn_empty"], (
        "properties should quietly drop later duplicates while keeping first-occurrence order."
    )
    assert view.exclude == ["published_date"], (
        "exclude should be normalized to a unique ordered list even though duplicate exclusions are already harmless."
    )
    assert view.detail_fields == ["title"], (
        "detail_fields should quietly drop later duplicates, then apply detail_exclude once."
    )
    assert view.detail_exclude == ["author"], (
        "detail_exclude should be normalized to a unique ordered list."
    )
    assert view.detail_properties == ["isbn_empty"], (
        "detail_properties should quietly drop later duplicates while preserving first occurrence."
    )
    assert view.form_fields == ["title"], (
        "form_fields should quietly drop later duplicates, then apply form_fields_exclude once."
    )
    assert view.form_fields_exclude == ["author"], (
        "form_fields_exclude should be normalized to a unique ordered list."
    )
    assert view.form_display_fields == ["author"], (
        "form_display_fields should quietly drop later duplicates so display-only context does not repeat rows."
    )
    assert view.form_disabled_fields == ["title"], (
        "form_disabled_fields should quietly drop later duplicates before forms are finalized."
    )
    assert view.bulk_fields == ["author"], (
        "bulk_fields should quietly drop later duplicates before bulk metadata is built."
    )
    assert view.inline_edit_fields == ["title"], (
        "inline_edit_fields should quietly drop later duplicates before inline-edit validation runs."
    )


def test_core_mixin_rejects_non_editable_bulk_fields():
    class BrokenView(CoreMixin):
        model = Book
        fields = "__all__"
        bulk_fields = ["uneditable_field"]

    with pytest.raises(ValueError, match="bulk_fields"):
        BrokenView()


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


class DummyQuerysetParent:
    def get_queryset(self):
        return self.model.objects.all()


@pytest.mark.django_db
def test_core_mixin_relation_sort_defaults_to_related_name_field():
    alpha_author = Author.objects.create(name="Alpha Author")
    zulu_author = Author.objects.create(name="Zulu Author")
    zulu_book = Book.objects.create(
        title="Zulu First By Id",
        author=zulu_author,
        published_date=date(2024, 1, 1),
        bestseller=False,
        isbn="9781000000001",
        pages=100,
    )
    alpha_book = Book.objects.create(
        title="Alpha Second By Id",
        author=alpha_author,
        published_date=date(2024, 1, 2),
        bestseller=False,
        isbn="9781000000002",
        pages=100,
    )

    rf = RequestFactory()

    class BookSortView(CoreMixin, DummyQuerysetParent):
        model = Book
        fields = ["title", "author"]

    view = BookSortView()
    view.request = rf.get("/?sort=author")

    ordered_pks = list(view.get_queryset().values_list("pk", flat=True))

    assert ordered_pks == [alpha_book.pk, zulu_book.pk], (
        "Sorting by a relation column should default to the related model's concrete name field when one exists."
    )


@pytest.mark.django_db
def test_core_mixin_relation_sort_descending_uses_related_name_field():
    alpha_author = Author.objects.create(name="Alpha Author")
    zulu_author = Author.objects.create(name="Zulu Author")
    alpha_book = Book.objects.create(
        title="Alpha First By Id",
        author=alpha_author,
        published_date=date(2024, 1, 1),
        bestseller=False,
        isbn="9781000000011",
        pages=100,
    )
    zulu_book = Book.objects.create(
        title="Zulu Second By Id",
        author=zulu_author,
        published_date=date(2024, 1, 2),
        bestseller=False,
        isbn="9781000000012",
        pages=100,
    )

    rf = RequestFactory()

    class BookSortView(CoreMixin, DummyQuerysetParent):
        model = Book
        fields = ["title", "author"]

    view = BookSortView()
    view.request = rf.get("/?sort=-author")

    ordered_pks = list(view.get_queryset().values_list("pk", flat=True))

    assert ordered_pks == [zulu_book.pk, alpha_book.pk], (
        "Descending relation sorting should use the related model's name field before applying the descending flag."
    )


@pytest.mark.django_db
def test_core_mixin_column_sort_fields_override_wins_over_relation_name_heuristic():
    zulu_author = Author.objects.create(name="Zulu Author")
    alpha_author = Author.objects.create(name="Alpha Author")
    zulu_book = Book.objects.create(
        title="Zulu First By Id",
        author=zulu_author,
        published_date=date(2024, 1, 1),
        bestseller=False,
        isbn="9781000000021",
        pages=100,
    )
    alpha_book = Book.objects.create(
        title="Alpha Second By Id",
        author=alpha_author,
        published_date=date(2024, 1, 2),
        bestseller=False,
        isbn="9781000000022",
        pages=100,
    )

    rf = RequestFactory()

    class BookSortView(CoreMixin, DummyQuerysetParent):
        model = Book
        fields = ["title", "author"]
        column_sort_fields_override = {"author": "author"}

    view = BookSortView()
    view.request = rf.get("/?sort=author")

    ordered_pks = list(view.get_queryset().values_list("pk", flat=True))

    assert ordered_pks == [zulu_book.pk, alpha_book.pk], (
        "Explicit column_sort_fields_override entries should take precedence over the default related-name sorting heuristic."
    )


@pytest.mark.django_db
def test_book_list_sorts_author_column_by_visible_author_name(client):
    zulu_author = Author.objects.create(name="Zulu Author")
    alpha_author = Author.objects.create(name="Alpha Author")
    Book.objects.create(
        title="Zulu Author Book",
        author=zulu_author,
        published_date=date(2024, 1, 1),
        bestseller=False,
        isbn="9781000000031",
        pages=100,
    )
    Book.objects.create(
        title="Alpha Author Book",
        author=alpha_author,
        published_date=date(2024, 1, 2),
        bestseller=False,
        isbn="9781000000032",
        pages=100,
    )

    response = client.get(
        reverse("sample:bigbook-list"),
        {"sort": "author", "page_size": "all"},
    )
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Book list view should render successfully when sorting by a relation column."
    )
    assert response_text.index("Alpha Author Book") < response_text.index(
        "Zulu Author Book"
    ), (
        "Sorting the visible author column should order rows alphabetically by displayed author name rather than by foreign-key id."
    )


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
        extra_actions_mode = "dropdown"

    view = TableView()

    assert view.get_table_pixel_height_other_page_elements() == "120px"
    assert view.get_table_max_height() == 70
    assert view.get_table_max_col_width() == "32ch"
    assert view.get_table_header_min_wrap_width() == "20ch"
    assert view.get_table_classes() == "table-zebra"
    assert view.get_action_button_classes() == "btn-xs"
    assert view.get_extra_button_classes() == "btn-sm"
    assert view.get_extra_actions_mode() == "dropdown"


def test_table_header_wrap_never_exceeds_max_width():
    class TableView(TableMixin):
        table_max_col_width = 15
        table_header_min_wrap_width = 25

    view = TableView()
    assert view.get_table_header_min_wrap_width() == "15ch"


@pytest.mark.django_db
def test_core_mixin_rejects_invalid_extra_button_selection_behavior():
    class BrokenView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_buttons = [
            {
                "url_name": "sample:bigbook-selected-summary",
                "text": "Selected Summary",
                "uses_selection": True,
                "selection_min_behavior": "mystery",
            }
        ]

    with pytest.raises(ImproperlyConfigured):
        BrokenView()


@pytest.mark.django_db
def test_core_mixin_warns_when_selection_thresholds_without_uses_selection(caplog):
    class WarningView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_buttons = [
            {
                "url_name": "sample:bigbook-list",
                "text": "Reload",
                "selection_min_count": 2,
            }
        ]

    with caplog.at_level("WARNING", logger="powercrud"):
        view = WarningView()

    assert view.extra_buttons[0]["uses_selection"] is False, (
        "Extra buttons should default uses_selection to False when the setting is omitted."
    )
    assert "selection_min_* settings without uses_selection=True" in caplog.text, (
        "PowerCRUD should warn when selection threshold settings are declared on buttons that are not selection-aware."
    )


@pytest.mark.django_db
def test_core_mixin_rejects_unknown_extra_action_disabled_hook():
    class BrokenView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_actions = [
            {
                "url_name": "sample:bigbook-description-preview",
                "text": "Description Preview",
                "disabled_if": "missing_disabled_hook",
            }
        ]

    with pytest.raises(ImproperlyConfigured):
        BrokenView()


@pytest.mark.django_db
def test_core_mixin_warns_when_disabled_reason_without_disabled_if(caplog):
    class WarningView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_actions = [
            {
                "url_name": "sample:bigbook-description-preview",
                "text": "Description Preview",
                "disabled_reason": "description_reason",
            }
        ]

        def description_reason(self, obj, request):
            """Unused test helper."""
            return "unused"

    with caplog.at_level("WARNING", logger="powercrud"):
        view = WarningView()

    assert view.extra_actions[0]["disabled_reason"] is None, (
        "PowerCRUD should ignore disabled_reason hooks that are declared without disabled_if."
    )
    assert "disabled_reason without disabled_if" in caplog.text, (
        "PowerCRUD should warn when disabled_reason is configured without the corresponding disabled_if hook."
    )


def test_table_mixin_get_view_title_falls_back_to_model_verbose_name_plural():
    class TableView(TableMixin):
        model = Author

    view = TableView()

    assert view.get_view_title() == "The Author Persons", (
        "List heading should default to the model plural verbose name when no override is configured."
    )


def test_table_mixin_get_view_title_prefers_configured_override():
    class TableView(TableMixin):
        model = Author
        view_title = "Custom Author Heading"

    view = TableView()

    assert view.get_view_title() == "Custom Author Heading", (
        "List heading should use view_title when the override is configured on the view."
    )


def test_table_mixin_get_view_instructions_defaults_to_empty_string():
    class TableView(TableMixin):
        model = Author

    view = TableView()

    assert view.get_view_instructions() == "", (
        "List helper instructions should default to an empty string when no override is configured."
    )


def test_table_mixin_get_view_instructions_prefers_configured_override():
    class TableView(TableMixin):
        model = Author
        view_instructions = "Helpful author guidance"

    view = TableView()

    assert view.get_view_instructions() == "Helpful author guidance", (
        "List helper instructions should use the configured view_instructions text when provided."
    )


def test_table_mixin_get_column_help_text_defaults_to_empty_mapping():
    class TableView(TableMixin):
        model = Author

    view = TableView()

    assert view.get_column_help_text() == {}, (
        "Column header help should default to an empty mapping when no help text is configured."
    )


def test_table_mixin_get_column_help_text_prefers_configured_mapping():
    class TableView(TableMixin):
        model = Author
        column_help_text = {"name": "Primary display name"}

    view = TableView()

    assert view.get_column_help_text() == {"name": "Primary display name"}, (
        "Column header help should use the configured column_help_text mapping when provided."
    )


def test_table_mixin_get_list_cell_tooltip_fields_defaults_to_empty_list():
    class TableView(TableMixin):
        model = Author

    view = TableView()

    assert view.get_list_cell_tooltip_fields() == [], (
        "List cell tooltip fields should default to an empty list when no semantic cell tooltips are configured."
    )


def test_table_mixin_get_list_cell_tooltip_fields_prefers_configured_list():
    class TableView(TableMixin):
        model = Author
        list_cell_tooltip_fields = ["name", "has_bio"]

    view = TableView()

    assert view.get_list_cell_tooltip_fields() == ["name", "has_bio"], (
        "List cell tooltip fields should use the configured ordered list when provided."
    )


def test_table_mixin_get_list_cell_tooltip_defaults_to_none():
    class TableView(TableMixin):
        model = Author

    author = Author(name="Tooltip Default")
    view = TableView()

    assert (
        view.get_list_cell_tooltip(
            author,
            "name",
            is_property=False,
            request=None,
        )
        is None
    ), "The default list cell tooltip hook should return None so unconfigured cells keep existing behavior."


def test_table_mixin_inline_edit_highlight_defaults_match_current_teal_styles():
    class TableView(TableMixin):
        pass

    view = TableView()
    palette = view.get_inline_edit_highlight_palette()

    assert view.get_inline_edit_always_visible() is True, (
        "Inline-edit highlights should be always visible by default to preserve the current behavior."
    )
    assert view.get_inline_edit_highlight_accent() == "#14b8a6", (
        "Default inline-edit highlight accent should use the teal package default."
    )
    assert palette == {
        "rest_bg": "rgba(20, 184, 166, 0.06)",
        "rest_border": "rgba(20, 184, 166, 0.18)",
        "hover_bg": "rgba(20, 184, 166, 0.15)",
        "hover_border": "rgba(20, 184, 166, 0.35)",
        "active_row_outline": "rgba(20, 184, 166, 0.85)",
        "active_row_bg": "rgba(20, 184, 166, 0.12)",
        "active_row_overlay": "rgba(20, 184, 166, 0.05)",
        "active_widget_bg": "rgba(20, 184, 166, 0.15)",
        "active_widget_border": "rgba(20, 184, 166, 0.35)",
    }, "Default inline-edit palette should preserve the current teal-derived styling tokens."


def test_table_mixin_inline_edit_highlight_palette_uses_custom_hex_accent():
    class TableView(TableMixin):
        inline_edit_highlight_accent = "#3b82f6"
        inline_edit_always_visible = False

    view = TableView()
    palette = view.get_inline_edit_highlight_palette()

    assert view.get_inline_edit_always_visible() is False, (
        "Views should be able to disable the always-visible resting highlight."
    )
    assert palette["rest_bg"] == "rgba(59, 130, 246, 0.06)", (
        "Custom inline-edit accent should drive the derived resting background color."
    )
    assert palette["hover_border"] == "rgba(59, 130, 246, 0.35)", (
        "Custom inline-edit accent should drive the stronger hover/focus border color."
    )


def test_table_mixin_invalid_inline_edit_highlight_accent_raises():
    class BrokenView(CoreMixin):
        model = Author
        fields = ["name"]
        inline_edit_highlight_accent = "rgb(251, 191, 36)"

    with pytest.raises(ImproperlyConfigured):
        BrokenView()


def test_view_instructions_blank_string_raises():
    class BrokenView(CoreMixin):
        model = Author
        fields = ["name"]
        view_instructions = "   "

    with pytest.raises(ImproperlyConfigured):
        BrokenView()


def test_column_help_text_blank_value_raises():
    class BrokenView(CoreMixin):
        model = Author
        fields = ["name"]
        column_help_text = {"name": "   "}

    with pytest.raises(ImproperlyConfigured):
        BrokenView()


def test_list_cell_tooltip_fields_blank_value_raises():
    class BrokenView(CoreMixin):
        model = Author
        fields = ["name"]
        list_cell_tooltip_fields = ["name", "   "]

    with pytest.raises(ImproperlyConfigured):
        BrokenView()


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


@pytest.mark.django_db
def test_author_list_displays_total_record_count_when_enabled(client, monkeypatch):
    """Render total record count text when the option is enabled."""
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.show_record_count",
        True,
        raising=False,
    )

    Author.objects.create(name="Alice Jones")
    Author.objects.create(name="Bob Smith")

    response = client.get(reverse("sample:author-list"), {"sort": "name"})
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Author list view should render successfully when record-count display is enabled."
    )
    assert "2 total records" in response_text, (
        "List view should show the total record count when no filters are active."
    )


@pytest.mark.django_db
def test_author_list_displays_filtered_paginated_record_count(client, monkeypatch):
    """Render filtered page-range metadata when the option is enabled."""
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.show_record_count",
        True,
        raising=False,
    )
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.paginate_by",
        1,
        raising=False,
    )

    Author.objects.create(name="Alice Jones")
    Author.objects.create(name="Alicia Stone")
    Author.objects.create(name="Bob Smith")

    response = client.get(reverse("sample:author-list"), {"name": "Ali"})
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Filtered author list view should render successfully when record-count display is enabled."
    )
    assert "Showing 1-1 of 2 matching records" in response_text, (
        "Filtered paginated list view should show the current page slice and total matching count."
    )


@pytest.mark.django_db
def test_author_list_uses_view_title_override_without_changing_create_label(
    client, monkeypatch
):
    """Render a custom list heading while leaving singular object copy unchanged."""
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.view_title",
        "Custom Author Heading",
        raising=False,
    )

    Author.objects.create(name="Alice Jones")

    response = client.get(reverse("sample:author-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Author list view should render successfully when a custom view_title is configured."
    )
    assert "Custom Author Heading" in response_text, (
        "List view should render the configured view_title as the visible heading."
    )
    assert "Create The Author Person" in response_text, (
        "The create button label should continue to use the singular model verbose name."
    )


@pytest.mark.django_db
def test_author_list_renders_view_instructions_when_configured(client, monkeypatch):
    """Render plain-text helper instructions beneath the list heading when configured."""
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.view_instructions",
        "Helpful author guidance",
        raising=False,
    )

    Author.objects.create(name="Alice Jones")

    response = client.get(reverse("sample:author-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Author list view should render successfully when view_instructions is configured."
    )
    assert "Helpful author guidance" in response_text, (
        "List view should render the configured view_instructions beneath the heading."
    )


@pytest.mark.django_db
def test_author_list_escapes_view_instructions_html(client, monkeypatch):
    """Escape HTML-like instructions text so view_instructions remains plain text only."""
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.view_instructions",
        "<strong>Unsafe</strong>",
        raising=False,
    )

    Author.objects.create(name="Alice Jones")

    response = client.get(reverse("sample:author-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Author list view should render successfully when HTML-like view_instructions text is configured."
    )
    assert "&lt;strong&gt;Unsafe&lt;/strong&gt;" in response_text, (
        "List view should escape HTML-like view_instructions content rather than rendering it as markup."
    )
    assert "<strong>Unsafe</strong>" not in response_text, (
        "List view should not render raw HTML from view_instructions."
    )


@pytest.mark.django_db
def test_author_list_renders_column_help_icon_and_text(client, monkeypatch):
    """Render the header help icon and tooltip text for configured columns."""
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.column_help_text",
        {
            "name": "Primary display name",
            "has_bio": "Whether the author currently has bio text.",
        },
        raising=False,
    )

    Author.objects.create(name="Alice Jones")

    response = client.get(reverse("sample:author-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Author list view should render successfully when column_help_text is configured."
    )
    assert 'aria-label="Help for Name"' in response_text, (
        "Configured field help should render a dedicated focusable header help trigger."
    )
    assert 'aria-label="Help for Has Bio"' in response_text, (
        "Configured property help should render a dedicated help trigger for property headers too."
    )
    assert 'data-tippy-content="Primary display name"' in response_text, (
        "Configured field help should be emitted as tooltip content on the header help trigger."
    )
    assert 'data-tippy-content="Whether the author currently has bio text."' in response_text, (
        "Configured property help should be emitted as tooltip content on the header help trigger."
    )
    assert 'data-powercrud-tooltip="semantic"' in response_text, (
        "Header help triggers should keep the generic semantic tooltip marker."
    )
    assert 'data-powercrud-tooltip="semantic-cell"' not in response_text, (
        "Header help triggers should not use the semantic list-cell marker reserved for hook-backed cell tooltips."
    )


@pytest.mark.django_db
def test_author_list_escapes_column_help_text_html(client, monkeypatch):
    """Escape HTML-like header help text so column_help_text remains plain text only."""
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.column_help_text",
        {"name": "<strong>Unsafe</strong>"},
        raising=False,
    )

    Author.objects.create(name="Alice Jones")

    response = client.get(reverse("sample:author-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Author list view should render successfully when HTML-like column help text is configured."
    )
    assert 'data-tippy-content="&lt;strong&gt;Unsafe&lt;/strong&gt;"' in response_text, (
        "Column header help text should be escaped in tooltip attributes rather than rendered as HTML."
    )
    assert 'data-tippy-content="<strong>Unsafe</strong>"' not in response_text, (
        "Column header help should not expose raw HTML in the rendered tooltip attribute."
    )


@pytest.mark.django_db
def test_book_update_form_renders_display_only_context_and_disabled_field(client):
    """Render the sample update form with display-only context and a disabled input."""
    author = Author.objects.create(name="Context Author")
    book = Book.objects.create(
        title="Context Book",
        author=author,
        published_date=date(2026, 1, 30),
        bestseller=False,
        isbn="978-1-4028-9462-7",
        pages=321,
    )

    response = client.get(reverse("sample:bigbook-update", args=[book.pk]))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Book update form should render successfully so the new display-only context block can be inspected."
    )
    assert "Context" in response_text, (
        "Book update form should render the display-only context section when form_display_fields are configured."
    )
    assert "Uneditable Field" in response_text, (
        "Book update form should render the configured display-only field label above the editable inputs."
    )
    assert "This field is uneditable" in response_text, (
        "Book update form should render the current persisted value for configured form_display_fields."
    )
    assert re.search(r'name="isbn"[^>]*disabled', response_text), (
        "Book update form should render configured form_disabled_fields with the disabled attribute."
    )


@pytest.mark.django_db
def test_book_create_form_hides_display_only_context_block(client):
    """Create forms should not render display-only context before an object exists."""
    response = client.get(reverse("sample:bigbook-create"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Book create form should render successfully so the absence of display-only context can be inspected."
    )
    assert "Uneditable Field" not in response_text, (
        "Book create form should hide form_display_fields because there is no persisted object yet."
    )
    assert not re.search(r'name="isbn"[^>]*disabled', response_text), (
        "Book create form should keep configured form_disabled_fields editable so required values can still be entered."
    )


def _create_book_inline_edit_fixture() -> Book:
    """Create a minimal persisted book record suitable for list partial rendering tests."""
    author = Author.objects.create(name="Inline Edit Author")
    genre = Genre.objects.create(name="Inline Edit Genre")
    book = Book.objects.create(
        title="Inline Editable Book",
        author=author,
        published_date=date(2026, 1, 30),
        bestseller=False,
        isbn="978-1-4028-9462-6",
        pages=320,
    )
    book.genres.add(genre)
    return book


def _render_book_list_partial() -> str:
    """Render the DaisyUI object-list inclusion tag for the sample book CRUD view."""
    from sample.views import BookCRUDView

    book = _create_book_inline_edit_fixture()
    request = RequestFactory().get(reverse("sample:bigbook-list"))
    request.session = {}
    view = BookCRUDView()
    view.request = request

    template = Template("{% load powercrud %}{% object_list objects view %}")
    context = Context(
        {
            "objects": Book.objects.filter(pk=book.pk),
            "view": view,
            "request": request,
            "inline_edit": view.get_inline_context(),
        }
    )
    return template.render(context)


def _render_default_inline_edit_list_partial() -> str:
    """Render the object-list partial with a test-only view that relies on package defaults."""
    from sample.views import SampleCRUDMixin

    class DefaultInlineBookView(SampleCRUDMixin):
        """Minimal test harness for default inline-edit highlight rendering."""

        model = Book
        base_template_path = "sample/base.html"
        fields = ["title", "author", "published_date", "bestseller", "isbn", "genres"]
        properties = []
        table_classes = ""
        table_pixel_height_other_page_elements = 0
        table_max_height = 70
        inline_edit_fields = ["title", "author", "published_date", "bestseller", "isbn", "genres"]
        url_base = "bigbook"
        namespace = "sample"

    book = _create_book_inline_edit_fixture()
    request = RequestFactory().get(reverse("sample:bigbook-list"))
    request.session = {}
    view = DefaultInlineBookView()
    view.request = request

    template = Template("{% load powercrud %}{% object_list objects view %}")
    context = Context(
        {
            "objects": Book.objects.filter(pk=book.pk),
            "view": view,
            "request": request,
            "inline_edit": view.get_inline_context(),
        }
    )
    return template.render(context)


def _extract_inline_css_variable(rendered_html: str, variable_name: str) -> str | None:
    """Extract a CSS custom property value from rendered HTML for stable assertions."""
    match = re.search(rf"{re.escape(variable_name)}:\s*([^;]+);", rendered_html)
    if not match:
        return None
    return match.group(1).strip()


@pytest.mark.django_db
def test_book_list_renders_default_inline_edit_highlight_css_variables():
    """Emit the current default teal inline-edit CSS variables in the list template."""
    response_text = _render_default_inline_edit_list_partial()

    assert (
        _extract_inline_css_variable(response_text, "--pc-inline-rest-bg")
        == "rgba(20, 184, 166, 0.06)"
    ), "Default inline-edit rest background variable should preserve the current teal-derived color."
    assert (
        _extract_inline_css_variable(response_text, "--pc-inline-hover-bg")
        == "rgba(20, 184, 166, 0.15)"
    ), "Default inline-edit hover background variable should preserve the current stronger teal-derived color."


@pytest.mark.django_db
def test_book_list_renders_custom_inline_edit_highlight_css_variables(
    monkeypatch,
):
    """Emit derived CSS variables for a custom hex accent and disabled resting highlight."""
    monkeypatch.setattr(
        "sample.views.BookCRUDView.inline_edit_highlight_accent",
        "#3b82f6",
        raising=False,
    )
    monkeypatch.setattr(
        "sample.views.BookCRUDView.inline_edit_always_visible",
        False,
        raising=False,
    )
    response_text = _render_book_list_partial()

    assert (
        _extract_inline_css_variable(response_text, "--pc-inline-rest-bg")
        == "transparent"
    ), "Disabling always-visible inline-edit highlighting should neutralize the resting background variable."
    assert (
        _extract_inline_css_variable(response_text, "--pc-inline-hover-bg")
        == "rgba(59, 130, 246, 0.15)"
    ), "Custom inline-edit accent should drive the stronger hover background variable."
    assert (
        _extract_inline_css_variable(response_text, "--pc-inline-active-row-outline")
        == "rgba(59, 130, 246, 0.85)"
    ), "Custom inline-edit accent should drive the active-row outline variable."


@pytest.mark.django_db
def test_book_list_inline_edit_display_uses_truncating_label_wrapper():
    """Keep the truncating wrapper and tooltip hook in the inline list template."""
    template_text = (
        Path(__file__).resolve().parents[1]
        / "powercrud"
        / "templates"
        / "powercrud"
        / "daisyUI"
        / "partial"
        / "list.html"
    ).read_text(encoding="utf-8")

    assert ".pc-inline-display-label" in template_text, (
        "Inline-edit list markup should define the dedicated truncation wrapper styles."
    )
    assert 'class="pc-inline-display-label' in template_text, (
        "Display-state inline edit cells should render the truncating label wrapper around their text."
    )
    assert 'data-powercrud-tooltip="overflow"' in template_text, (
        "Inline display labels should keep the overflow-tooltip hook on the truncating wrapper."
    )


@pytest.mark.django_db
def test_book_list_renders_sample_semantic_list_cell_tooltips(client):
    """Render the sample semantic list-cell tooltip markup for configured fields and properties."""
    author = Author.objects.create(name="Semantic Tooltip Author")
    Book.objects.create(
        title="Semantic Tooltip Book",
        author=author,
        published_date=date(2024, 9, 20),
        bestseller=False,
        isbn="978-1-4028-9462-1",
        pages=412,
        description="Semantic tooltip sample",
    )

    response = client.get(reverse("sample:bigbook-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Book list view should render successfully so semantic list-cell tooltip markup can be inspected."
    )
    assert 'data-tippy-content="Semantic Tooltip Author\n412 pages"' in response_text, (
        "Configured sample title cells should preserve newline-separated semantic tooltip text from the shared hook."
    )
    assert 'data-tippy-content="ISBN: 978-1-4028-9462-1"' in response_text, (
        "Configured sample property cells should render semantic list-cell tooltip text, even when the displayed value is an icon."
    )
    assert 'data-powercrud-tooltip="semantic-cell"' in response_text, (
        "Configured sample list cells should use the dedicated semantic-cell tooltip channel rather than the generic semantic or overflow channels."
    )


@pytest.mark.django_db
def test_book_list_escapes_semantic_list_cell_tooltip_html(client, monkeypatch):
    """Escape HTML-like semantic cell tooltip text so list-cell tooltips remain plain text only."""
    monkeypatch.setattr(
        "sample.views.BookCRUDView.get_list_cell_tooltip",
        lambda self, obj, field_name, *, is_property, request=None: (
            "<strong>Unsafe</strong>" if field_name == "title" else None
        ),
        raising=False,
    )

    author = Author.objects.create(name="Escaped Tooltip Author")
    Book.objects.create(
        title="Escaped Tooltip Book",
        author=author,
        published_date=date(2024, 9, 21),
        bestseller=False,
        isbn="978-1-4028-9462-2",
        pages=250,
        description="Escaped tooltip sample",
    )

    response = client.get(reverse("sample:bigbook-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Book list view should render successfully when HTML-like semantic list-cell tooltip text is configured."
    )
    assert 'data-tippy-content="&lt;strong&gt;Unsafe&lt;/strong&gt;"' in response_text, (
        "Semantic list-cell tooltip text should be escaped in rendered attributes rather than interpreted as HTML."
    )
    assert 'data-tippy-content="<strong>Unsafe</strong>"' not in response_text, (
        "Semantic list-cell tooltips should not expose raw HTML in rendered tooltip attributes."
    )


@pytest.mark.django_db
def test_book_list_filter_form_uses_compact_grid_layout(client):
    """Render the books filter form with the compact grid layout classes."""
    response = client.get(reverse("sample:bigbook-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Book list view should render successfully so the filter layout can be inspected."
    )
    assert 'id="filter-form"' in response_text, (
        "Book list view should render the filter form when filterset_fields are configured."
    )
    assert 'class="grid gap-x-2 gap-y-0 sm:grid-cols-2 xl:grid-cols-3"' in response_text, (
        "Book list filter form should cap itself at three columns and remove extra row gap so the panel feels compact rather than sprawling."
    )
    assert "filter-field form-control w-full min-w-0" in response_text, (
        "Book list filter fields should use the compact wrapper class within the grid layout."
    )
    assert "filter-field-shell" in response_text and "padding: 0 0.25rem;" in response_text, (
        "Book list filter fields should keep only a small amount of inline padding so the rows stay dense without collapsing into each other."
    )
    assert 'text-xs font-medium text-base-content/80' in response_text, (
        "Book list filter labels should use lighter compact label styling rather than loud heading-style labels."
    )
    assert "text-align: right;" in response_text and "justify-self: end;" in response_text, (
        "Desktop filter labels should align tightly against their controls so the compact rows read as paired label-input units."
    )
    assert "grid-template-columns: minmax(5.25rem, 6.75rem) minmax(0, 1fr) auto;" in response_text, (
        "Book list filter rows should keep a compact label column while leaving enough width for wrapped labels to stay readable."
    )
    assert "--pc-filter-control-height: 2rem;" in response_text, (
        "Book list filters should use shorter controls so the compact panel does not feel like a full data-entry form."
    )
    assert "max-width: 78rem;" in response_text, (
        "The filter panel should cap its width so it feels like a deliberate query workspace rather than spanning indefinitely."
    )
    assert "column-gap: 0.375rem;" in response_text, (
        "Book list filter rows should tighten label-to-control spacing to reduce the sense of bloat."
    )
    assert "white-space: normal;" in response_text and "overflow-wrap: anywhere;" in response_text, (
        "Book list filter labels should be allowed to wrap rather than forcing truncation or collisions with their controls."
    )
    assert "rounded-box border border-base-300 bg-base-300" in response_text, (
        "The filter panel should use a semantic base background tint so it does not disappear into a white page background."
    )
    assert "sm:col-span-2" not in response_text, (
        "Filter multiselects should not automatically span two columns in the compact grid layout."
    )


@pytest.mark.django_db
def test_book_list_shows_add_filter_control_and_hides_optional_filters_by_default(client):
    """Book list should expose optional filters through the Add filter control only."""
    response = client.get(reverse("sample:bigbook-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Book list view should render successfully so default-visible and optional filter controls can be inspected."
    )
    assert 'data-powercrud-add-filter-select' in response_text, (
        "Book list view should render the Add filter control markup when some allowed filters are optional."
    )
    assert 'data-powercrud-add-filter-container' in response_text, (
        "Book list view should wrap the Add filter control in a dedicated top-row container beside the filter actions."
    )
    assert 'data-powercrud-filter-toolbar' in response_text, (
        "Book list view should render a distinct filter-toolbar cluster to visually separate filter actions from other page actions."
    )
    assert response_text.index('data-powercrud-add-filter-container') < response_text.index('id="filterCollapse"'), (
        "The Add filter control should sit on the top action row rather than inside the collapsible filter panel."
    )
    assert '<div class="hidden" data-powercrud-add-filter-container>' in response_text, (
        "Book list view should hide the Add filter control by default until the user opens the filter panel."
    )
    assert 'id="filterCollapse"' in response_text and 'class="hidden py-2"' in response_text, (
        "Book list view should render the filter panel collapsed by default on the initial response."
    )
    assert '<option value="isbn">Isbn</option>' in response_text, (
        "Optional Book filters should appear in the Add filter control by label when they are hidden by default."
    )
    assert 'name="description"' not in response_text, (
        "Hidden optional filters should not render input controls before the user adds them."
    )


@pytest.mark.django_db
def test_book_list_page_size_form_includes_only_page_size_and_filter_form(client):
    """Book list page-size HTMX wiring should not sweep up unrelated toolbar controls."""

    response = client.get(reverse("sample:bigbook-list"))
    response_text = " ".join(response.content.decode().split())

    assert 'id="page-size-form"' in response_text, (
        "Book list should render the dedicated page-size form markup."
    )
    assert 'id="page-size-select" name="page_size" data-powercrud-page-size-select="true"' in response_text, (
        "Page-size changes should use the dedicated PowerCRUD page-size selector hook rather than a broad form-level include."
    )


@pytest.mark.django_db
def test_book_list_renders_visible_optional_filter_from_url_state(client):
    """Book list should reveal optional filters requested via URL-backed visibility state."""
    response = client.get(
        reverse("sample:bigbook-list"),
        {"visible_filters": ["description"]},
    )
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Book list view should render successfully when an optional filter is requested via visible_filters."
    )
    assert 'name="description"' in response_text, (
        "Requested optional filters should render their input controls even when they are not default-visible."
    )
    assert 'data-powercrud-remove-filter="description"' in response_text, (
        "Visible optional filters should render a remove control so users can hide them explicitly."
    )
    assert 'aria-label="Remove Description filter"' in response_text, (
        "Visible optional filters should expose an icon-only remove action with an accessible label."
    )
    assert 'name="visible_filters" value="description"' in response_text, (
        "Visible optional filters should persist their visibility state through hidden visible_filters inputs."
    )
    assert '> Remove <' not in response_text and '>Remove<' not in response_text, (
        "Optional filter remove actions should render as icon buttons rather than visible 'Remove' text."
    )
    assert 'class="hidden py-2"' in response_text, (
        "Book list view should still render the filter panel closed on the server response even when optional filters are visible."
    )


@pytest.mark.django_db
def test_book_list_keeps_filter_panel_closed_on_server_when_filter_value_is_active(client):
    """Book list should keep the server-rendered filter panel closed even with active filters."""
    response = client.get(
        reverse("sample:bigbook-list"),
        {"title": "PowerCRUD"},
    )
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Book list view should render successfully when a filter value is active in the query string."
    )
    assert 'class="hidden py-2"' in response_text, (
        "Book list view should leave panel-open decisions to client-side session state instead of auto-opening from active filter values."
    )


@pytest.mark.django_db
def test_book_list_filter_labels_do_not_append_contains(client):
    """Render plain field labels for text filters even when icontains is used."""
    response = client.get(reverse("sample:bigbook-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Book list view should render successfully so filter labels can be inspected."
    )
    assert "Title contains" not in response_text, (
        "Text filter labels should not append 'contains' when the auto-generated lookup uses icontains."
    )
    assert "Isbn contains" not in response_text, (
        "Text filter labels should keep the plain field name instead of displaying the lookup suffix."
    )
    assert "Description contains" not in response_text, (
        "Long text filter labels should also avoid the lookup suffix in the rendered filter form."
    )
    assert "Title" in response_text, (
        "The title filter should still render with its plain field label."
    )
    assert "Isbn" in response_text, (
        "The ISBN filter should still render with its plain field label."
    )
    assert "Description" in response_text, (
        "The description filter should still render with its plain field label."
    )


@pytest.mark.django_db
def test_book_list_renders_modal_with_explicit_close_button(client):
    """Render the shared DaisyUI modal with both explicit and backdrop close affordances."""
    response = client.get(reverse("sample:bigbook-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Book list view should render successfully so the shared modal chrome can be inspected."
    )
    assert 'id="powercrudBaseModal"' in response_text, (
        "Book list view should include the shared PowerCRUD dialog container when modal support is enabled."
    )
    assert 'aria-label="Close modal"' in response_text, (
        "The shared PowerCRUD modal should render an explicit close button so dismissal is visually obvious."
    )
    assert "btn btn-sm btn-circle btn-ghost absolute right-2 top-2" in response_text, (
        "The shared PowerCRUD modal should use the standard DaisyUI circular ghost close button styling."
    )
    assert 'class="modal-backdrop"' in response_text, (
        "The shared PowerCRUD modal should continue to render the backdrop close affordance."
    )


@pytest.mark.django_db
def test_book_list_renders_selection_aware_extra_button(client):
    """Render selection-aware extra button metadata on the sample book list."""
    author = Author.objects.create(name="Selection Button Author")
    selected_book = Book.objects.create(
        title="Selected Summary Book",
        author=author,
        published_date=date(2024, 9, 1),
        bestseller=False,
        isbn="9876543210555",
        pages=101,
        description="Included in summary",
    )
    session = client.session
    session["powercrud_selections"] = {"powercrud_bulk_book_": [str(selected_book.pk)]}
    session.save()

    response = client.get(reverse("sample:bigbook-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Book list view should render successfully so selection-aware extra buttons can be inspected."
    )
    assert 'data-powercrud-selection-aware="true"' in response_text, (
        "Sample book list should mark selection-aware extra buttons with frontend metadata."
    )
    assert 'data-powercrud-selection-min-count="1"' in response_text, (
        "Sample book list should expose the configured minimum selection count for the demo extra button."
    )
    assert "Selected Summary" in response_text, (
        "Sample book list should render the configured selection-aware extra button label."
    )


@pytest.mark.django_db
def test_book_list_renders_disabled_extra_action_with_reason(client):
    """Render disabled row action state for books lacking a description."""
    author = Author.objects.create(name="Descriptionless Author")
    Book.objects.create(
        title="No Description Yet",
        author=author,
        published_date=date(2024, 10, 1),
        bestseller=False,
        isbn="9876543210667",
        pages=40,
        description="",
    )

    response = client.get(reverse("sample:bigbook-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Book list view should render successfully so disabled row action state can be inspected."
    )
    assert "Description Preview" in response_text, (
        "Sample book list should include the description-preview extra action label."
    )
    assert "This book does not have a description yet." in response_text, (
        "Sample book list should expose the custom disabled reason for rows that fail the extra-action rule."
    )
    assert "btn-disabled opacity-50 pointer-events-none" in response_text, (
        "Sample book list should render disabled styling for custom-disabled extra actions."
    )


@pytest.mark.django_db
def test_book_selected_summary_uses_persisted_selection(client):
    """Render selected book details from the persisted bulk selection."""
    author = Author.objects.create(name="Summary Author")
    selected_book = Book.objects.create(
        title="Summary Target",
        author=author,
        published_date=date(2024, 11, 1),
        bestseller=True,
        isbn="9876543210888",
        pages=88,
        description="Included in selected summary",
    )
    session = client.session
    session["powercrud_selections"] = {"powercrud_bulk_book_": [str(selected_book.pk)]}
    session.save()

    response = client.get(
        reverse("sample:bigbook-selected-summary"),
        HTTP_HX_REQUEST="true",
    )
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Selected-summary endpoint should render successfully for the persisted sample selection."
    )
    assert "Selected Book Summary" in response_text, (
        "Selected-summary endpoint should render the sample modal heading."
    )
    assert selected_book.title in response_text, (
        "Selected-summary endpoint should include titles from the persisted selection."
    )


@pytest.mark.django_db
def test_book_description_preview_reports_missing_description(client):
    """Render the sample description-preview fallback message when content is blank."""
    author = Author.objects.create(name="Preview Fallback Author")
    book = Book.objects.create(
        title="Blank Description",
        author=author,
        published_date=date(2024, 12, 1),
        bestseller=False,
        isbn="9876543210999",
        pages=27,
        description="",
    )

    response = client.get(
        reverse("sample:bigbook-description-preview", args=[book.pk]),
        HTTP_HX_REQUEST="true",
    )
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Description-preview endpoint should still render a friendly fallback when a book has no description."
    )
    assert "This book does not have a description yet." in response_text, (
        "Description-preview endpoint should explain why the sample modal cannot show book description content."
    )


@pytest.mark.django_db
def test_author_list_centers_boolean_icon_cells(client):
    """Render centered wrappers for boolean icon cells in the list view."""
    Author.objects.create(
        name="Centered Icon Author",
        bio="Has biography",
        birth_date=date(1985, 6, 1),
    )

    response = client.get(reverse("sample:author-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Author list view should render successfully so centered boolean icon cells can be inspected."
    )
    assert "flex justify-center items-center w-full" in response_text, (
        "Boolean icon cells should render inside a flex wrapper that centers them horizontally."
    )


@pytest.mark.django_db
def test_author_list_renders_extra_actions_as_buttons_by_default(client):
    """Render author extra actions as visible buttons when dropdown mode is unset."""
    Author.objects.create(name="Author Buttons")

    response = client.get(reverse("sample:author-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Author list view should render successfully so default row action buttons can be inspected."
    )
    assert "View Again" in response_text, (
        "Sample author list should still render the configured extra action label."
    )
    assert "dropdown-content menu" not in response_text, (
        "Sample author list should fall back to the default visible-button row action mode when dropdown mode is unset."
    )


@pytest.mark.django_db
def test_book_list_renders_extra_actions_in_dropdown(client):
    """Render row extra actions in the sample book overflow dropdown."""
    author = Author.objects.create(name="Dropdown Author")
    Book.objects.create(
        title="Dropdown Book",
        author=author,
        published_date=date(2025, 1, 1),
        bestseller=False,
        isbn="9876543211111",
        pages=64,
        description="Dropdown description",
    )

    response = client.get(reverse("sample:bigbook-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Book list view should render successfully so dropdown row actions can be inspected."
    )
    assert "dropdown-content menu" in response_text, (
        "Sample book list should render extra row actions inside the dropdown menu when dropdown mode is enabled."
    )
    assert ">More<" in response_text, (
        "Sample book list should include the More trigger for overflow extra row actions."
    )
    assert "Description Preview" in response_text, (
        "Sample book list should keep the configured extra action labels inside the dropdown markup."
    )
