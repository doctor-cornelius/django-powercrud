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
    assert 'class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4"' in response_text, (
        "Book list filter form should use the responsive grid classes for a structured layout."
    )
    assert "filter-field form-control w-full min-w-0" in response_text, (
        "Book list filter fields should use the compact wrapper class within the grid layout."
    )
    assert "sm:col-span-2" not in response_text, (
        "Filter multiselects should not automatically span two columns in the compact grid layout."
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
def test_author_list_renders_extra_actions_in_dropdown(client):
    """Render row extra actions in the sample author overflow dropdown."""
    Author.objects.create(name="Dropdown Author")

    response = client.get(reverse("sample:author-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Author list view should render successfully so dropdown row actions can be inspected."
    )
    assert "dropdown-content menu" in response_text, (
        "Sample author list should render extra row actions inside the dropdown menu when dropdown mode is enabled."
    )
    assert ">More<" in response_text, (
        "Sample author list should include the More trigger for overflow extra row actions."
    )
    assert "View Again" in response_text, (
        "Sample author list should keep the configured extra action labels inside the dropdown markup."
    )
