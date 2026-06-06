import re
from pathlib import Path
from types import SimpleNamespace
from datetime import date

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db.models import BooleanField, Case, Value, When
from django.template import Context, Template
from django.urls import NoReverseMatch, reverse
from django.test import RequestFactory

from neapolitan.views import Role

from powercrud.actions import PowerAction, PowerButton
from powercrud.mixins.core_mixin import CoreMixin
from powercrud.mixins.list_options_mixin import ListOptionsMixin
from powercrud.mixins.table_mixin import TableMixin
from powercrud.mixins.paginate_mixin import PaginateMixin
from powercrud.mixins.url_mixin import UrlMixin

from sample.models import Author, Book, Genre, Profile
from sample import views as sample_views


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
    class BookView(ListOptionsMixin, CoreMixin):
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
    class BookView(ListOptionsMixin, CoreMixin):
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
        default_list_fields = ["title", "isbn_empty", "title"]
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
    assert view.default_list_fields == ["title", "isbn_empty"], (
        "default_list_fields should quietly drop later duplicates while keeping first-occurrence order."
    )


@pytest.mark.django_db
def test_core_mixin_resolves_default_list_fields_against_fields_and_properties():
    """default_list_fields should opt into a subset of the rendered column allow-list."""

    class BookView(ListOptionsMixin, CoreMixin):
        model = Book
        role = Role.LIST
        fields = ["title", "author", "pages"]
        properties = ["isbn_empty"]
        default_list_fields = ["title", "isbn_empty"]

    view = BookView()

    assert view.get_allowed_list_columns() == ["title", "author", "pages", "isbn_empty"], (
        "Allowed list columns should be resolved from fields followed by properties."
    )
    assert view.get_default_list_columns() == ["title", "isbn_empty"], (
        "default_list_fields should preserve allowed-column order and include properties."
    )
    assert view.get_active_list_columns() == ["title", "isbn_empty"], (
        "Views with no session state should render their default visible columns."
    )


def test_core_mixin_rejects_empty_default_list_fields():
    """Empty default visible columns are intentionally invalid for v1."""

    class BrokenView(CoreMixin):
        model = Book
        fields = ["title"]
        default_list_fields = []

    with pytest.raises(ImproperlyConfigured, match="default_list_fields cannot be empty"):
        BrokenView()


def test_core_mixin_rejects_unknown_default_list_fields():
    """default_list_fields should fail clearly when it names an unavailable column."""

    class BrokenView(CoreMixin):
        model = Book
        fields = ["title"]
        default_list_fields = ["missing"]

    with pytest.raises(ValueError, match="default_list_fields"):
        BrokenView()


@pytest.mark.django_db
def test_core_mixin_normalises_saved_visible_columns_to_allowed_order():
    """Saved column state should drop stale names and keep the configured column order."""

    class BookView(ListOptionsMixin, CoreMixin):
        model = Book
        role = Role.LIST
        fields = ["title", "author", "pages"]
        properties = ["isbn_empty"]
        default_list_fields = ["title"]

    view = BookView()

    assert view.normalise_visible_list_columns(["pages", "missing", "author"]) == [
        "author",
        "pages",
    ], "Visible column state should drop stale names and render in the allow-list order."
    assert view.normalise_visible_list_columns(["missing"]) == ["title"], (
        "Invalid or empty visible column state should fall back to default_list_fields."
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


@pytest.mark.django_db
def test_core_mixin_accepts_static_queryset_annotation_fields():
    class AnnotatedBookView(CoreMixin):
        model = Book
        queryset = Book.objects.annotate(
            long_book=Case(
                When(pages__gte=400, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        fields = ["title", "long_book", "pages"]
        detail_fields = "__fields__"

    view = AnnotatedBookView()

    assert view.fields == ["title", "long_book", "pages"], (
        "fields should preserve explicitly ordered queryset annotation columns."
    )
    assert view.detail_fields == ["title", "pages"], (
        "detail_fields inherited from __fields__ should stay model-field-only."
    )


@pytest.mark.parametrize(
    ("config_name", "config_value"),
    [
        ("bulk_fields", ["long_book"]),
        ("inline_edit_fields", ["long_book"]),
        ("form_fields", ["long_book"]),
    ],
)
def test_core_mixin_rejects_queryset_annotations_on_editable_surfaces(
    config_name,
    config_value,
):
    class BrokenView(CoreMixin):
        model = Book
        queryset = Book.objects.annotate(
            long_book=Case(
                When(pages__gte=400, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        fields = ["title", "long_book"]

    setattr(BrokenView, config_name, config_value)

    with pytest.raises(ValueError, match=config_name):
        BrokenView()


def test_core_mixin_rejects_explicit_queryset_annotation_detail_fields():
    class BrokenView(CoreMixin):
        model = Book
        queryset = Book.objects.annotate(
            long_book=Case(
                When(pages__gte=400, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        fields = ["title", "long_book"]
        detail_fields = ["long_book"]

    with pytest.raises(ValueError, match="detail_field"):
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
def test_core_mixin_sorts_request_time_queryset_annotation_fields():
    short_book = Book.objects.create(
        title="Short Book",
        author=Author.objects.create(name="Short Author"),
        published_date=date(2024, 1, 1),
        bestseller=False,
        isbn="9781000000041",
        pages=120,
    )
    long_book = Book.objects.create(
        title="Long Book",
        author=Author.objects.create(name="Long Author"),
        published_date=date(2024, 1, 2),
        bestseller=False,
        isbn="9781000000042",
        pages=600,
    )

    rf = RequestFactory()

    class AnnotatedBookSortView(CoreMixin, DummyQuerysetParent):
        model = Book
        fields = ["title", "long_book"]

        def get_queryset(self):
            """Annotate the operational column after the parent queryset exists."""
            return super().get_queryset().annotate(
                long_book=Case(
                    When(pages__gte=400, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )

    view = AnnotatedBookSortView()
    view.request = rf.get("/?sort=-long_book")

    queryset = view._apply_queryset_sorting(view.get_queryset())
    view.validate_list_fields_against_queryset(view.fields, queryset)
    ordered_pks = list(queryset.values_list("pk", flat=True))

    assert ordered_pks == [long_book.pk, short_book.pk], (
        "Request-time queryset annotations should sort after the effective queryset exposes the annotation."
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
        extra_buttons_mode = "dropdown"
        extra_actions_mode = "dropdown"

    view = TableView()

    assert view.get_table_pixel_height_other_page_elements() == "120px"
    assert view.get_table_max_height() == 70
    assert view.get_table_max_col_width() == "32ch"
    assert view.get_table_header_min_wrap_width() == "20ch"
    assert view.get_table_classes() == "table-zebra"
    assert view.get_action_button_classes() == "btn-xs"
    assert view.get_extra_button_classes() == "btn-sm"
    assert view.get_extra_buttons_mode() == "dropdown"
    assert view.get_extra_actions_mode() == "dropdown"


def test_table_header_wrap_never_exceeds_max_width():
    class TableView(TableMixin):
        table_max_col_width = 15
        table_header_min_wrap_width = 25

    view = TableView()
    assert view.get_table_header_min_wrap_width() == "15ch"


@pytest.mark.django_db
def test_core_mixin_rejects_invalid_extra_buttons_mode():
    class BrokenView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_buttons_mode = "auto"

    with pytest.raises(ImproperlyConfigured):
        BrokenView()


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
def test_core_mixin_does_not_warn_for_plain_powerbutton_defaults(caplog):
    class ButtonView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_buttons = [
            PowerButton(
                text="Approvals Queue",
                url_name="sample:bigbook-list",
                button_class="btn-outline",
                display_modal=False,
                htmx_target="content",
            )
        ]

    with caplog.at_level("WARNING", logger="powercrud"):
        view = ButtonView()

    assert view.extra_buttons[0]["uses_selection"] is False, (
        "Plain PowerButton toolbar buttons should remain non-selection buttons."
    )
    assert "selection_min_* settings without uses_selection=True" not in caplog.text, (
        "Generated PowerButton defaults should not trigger the explicit-threshold warning."
    )


@pytest.mark.django_db
def test_core_mixin_normalizes_extra_button_modal_close_refresh_flag():
    class ButtonRefreshView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_buttons = [
            {
                "url_name": "sample:bigbook-list",
                "text": "Reload",
            },
            {
                "url_name": "sample:bigbook-selected-summary",
                "text": "Selected Summary",
                "display_modal": True,
                "refresh_list_on_modal_close": True,
            },
        ]

    view = ButtonRefreshView()

    assert view.extra_buttons[0]["refresh_list_on_modal_close"] is False, (
        "Extra buttons should default refresh_list_on_modal_close to False when omitted."
    )
    assert view.extra_buttons[1]["refresh_list_on_modal_close"] is True, (
        "Extra buttons should preserve an explicit True modal-close refresh flag."
    )


@pytest.mark.django_db
def test_core_mixin_rejects_non_bool_extra_button_modal_close_refresh_flag():
    class BrokenView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_buttons = [
            {
                "url_name": "sample:bigbook-selected-summary",
                "text": "Selected Summary",
                "refresh_list_on_modal_close": "yes",
            }
        ]

    with pytest.raises(
        ImproperlyConfigured,
        match="extra_buttons\\[0\\]\\.refresh_list_on_modal_close",
    ):
        BrokenView()


@pytest.mark.django_db
def test_core_mixin_accepts_powerbutton_in_extra_buttons():
    class ButtonView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_buttons = [
            PowerButton(
                text="Selected Summary",
                url_name="sample:bigbook-selected-summary",
                display_modal=True,
                uses_selection=True,
                selection_min_count=1,
                selection_min_behavior="disable",
            ),
            {
                "url_name": "sample:bigbook-list",
                "text": "Reload",
            },
        ]

    view = ButtonView()

    assert view.extra_buttons[0]["uses_selection"] is True, (
        "PowerButton declarations should normalize into primitive extra_buttons dictionaries."
    )
    assert view.extra_buttons[1]["text"] == "Reload", (
        "Primitive extra_buttons dictionaries should still work beside PowerButton declarations."
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
def test_core_mixin_rejects_unknown_extra_action_disabled_state_hook():
    class BrokenView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_actions = [
            {
                "url_name": "sample:bigbook-description-preview",
                "text": "Description Preview",
                "disabled_state": "missing_disabled_state",
            }
        ]

    with pytest.raises(ImproperlyConfigured):
        BrokenView()


@pytest.mark.django_db
def test_core_mixin_rejects_unknown_extra_action_hidden_hook():
    """Reject primitive hidden_if declarations that reference no view method."""
    class BrokenView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_actions = [
            {
                "url_name": "sample:bigbook-description-preview",
                "text": "Description Preview",
                "hidden_if": "missing_hidden_hook",
            }
        ]

    with pytest.raises(ImproperlyConfigured, match="hidden_if"):
        BrokenView()


@pytest.mark.django_db
def test_core_mixin_rejects_mixed_extra_action_disabled_styles():
    class BrokenView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_actions = [
            {
                "url_name": "sample:bigbook-description-preview",
                "text": "Description Preview",
                "disabled_state": "get_description_disabled_state",
                "disabled_if": "is_description_disabled",
            }
        ]

        def get_description_disabled_state(self, obj, request):
            """Unused test helper."""
            return None

        def is_description_disabled(self, obj, request):
            """Unused test helper."""
            return False

    with pytest.raises(ImproperlyConfigured, match="disabled_state"):
        BrokenView()


@pytest.mark.django_db
def test_core_mixin_accepts_extra_action_disabled_state_hook():
    class ActionView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_actions = [
            {
                "url_name": "sample:bigbook-description-preview",
                "text": "Description Preview",
                "disabled_state": "get_description_disabled_state",
            }
        ]

        def get_description_disabled_state(self, obj, request):
            """Return no disabled state for config validation."""
            return None

    view = ActionView()

    assert view.extra_actions[0]["disabled_state"] == "get_description_disabled_state", (
        "Primitive extra_actions should accept the single disabled_state hook."
    )
    assert view.extra_actions[0]["disabled_if"] is None, (
        "disabled_state should not require the legacy disabled_if hook."
    )


@pytest.mark.django_db
def test_core_mixin_accepts_extra_action_hidden_hook_with_disabled_state():
    """Accept primitive hidden_if declarations alongside disabled_state hooks."""
    class ActionView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_actions = [
            {
                "url_name": "sample:bigbook-description-preview",
                "text": "Description Preview",
                "hidden_if": "should_hide_description_preview",
                "disabled_state": "get_description_disabled_state",
            }
        ]

        def should_hide_description_preview(self, obj, request):
            """Return no hidden state for config validation."""
            return False

        def get_description_disabled_state(self, obj, request):
            """Return no disabled state for config validation."""
            return None

    view = ActionView()

    assert view.extra_actions[0]["hidden_if"] == "should_hide_description_preview", (
        "Primitive extra_actions should accept a hidden_if hook alongside disabled_state."
    )
    assert view.extra_actions[0]["disabled_state"] == "get_description_disabled_state", (
        "Primitive extra_actions should preserve the disabled_state hook when hidden_if is configured."
    )


@pytest.mark.django_db
def test_core_mixin_accepts_poweraction_in_extra_actions():
    class ActionView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_actions = [
            PowerAction(
                text="Description Preview",
                url_name="sample:bigbook-description-preview",
                display_modal=True,
                hidden_if="should_hide_description_preview",
                disabled_state="get_description_disabled_state",
            ),
            {
                "url_name": "sample:bigbook-update",
                "text": "Normal Edit",
            },
        ]

        def get_description_disabled_state(self, obj, request):
            """Return no disabled state for config validation."""
            return None

        def should_hide_description_preview(self, obj, request):
            """Return no hidden state for config validation."""
            return False

    view = ActionView()

    assert view.extra_actions[0]["hidden_if"] == "should_hide_description_preview", (
        "PowerAction declarations should normalize hidden_if into primitive extra_actions dictionaries."
    )
    assert view.extra_actions[0]["disabled_state"] == "get_description_disabled_state", (
        "PowerAction declarations should normalize into primitive extra_actions dictionaries."
    )
    assert view.extra_actions[1]["text"] == "Normal Edit", (
        "Primitive extra_actions dictionaries should still work beside PowerAction declarations."
    )


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


@pytest.mark.django_db
def test_core_mixin_normalizes_extra_action_modal_close_refresh_flag():
    class ActionRefreshView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_actions = [
            {
                "url_name": "sample:bigbook-description-preview",
                "text": "Description Preview",
            },
            {
                "url_name": "sample:bigbook-update",
                "text": "Normal Edit",
                "display_modal": True,
                "refresh_list_on_modal_close": True,
            },
        ]

    view = ActionRefreshView()

    assert view.extra_actions[0]["refresh_list_on_modal_close"] is False, (
        "Extra actions should default refresh_list_on_modal_close to False when omitted."
    )
    assert view.extra_actions[1]["refresh_list_on_modal_close"] is True, (
        "Extra actions should preserve an explicit True modal-close refresh flag."
    )


@pytest.mark.django_db
def test_core_mixin_rejects_non_bool_extra_action_modal_close_refresh_flag():
    class BrokenView(CoreMixin):
        model = Book
        fields = "__all__"
        base_template_path = "sample/base.html"
        extra_actions = [
            {
                "url_name": "sample:bigbook-description-preview",
                "text": "Description Preview",
                "refresh_list_on_modal_close": "yes",
            }
        ]

    with pytest.raises(
        ImproperlyConfigured,
        match="extra_actions\\[0\\]\\.refresh_list_on_modal_close",
    ):
        BrokenView()


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


def test_table_mixin_get_view_help_defaults_to_empty_mapping():
    class TableView(TableMixin):
        model = Author

    view = TableView()

    assert view.get_view_help() == {}, (
        "Collapsed view help should default to an empty mapping when no help is configured."
    )
    assert view.get_view_help_detail_paragraphs() == [], (
        "Collapsed view help should not produce paragraphs when no help is configured."
    )


def test_table_mixin_get_view_help_prefers_configured_mapping():
    class TableView(TableMixin):
        model = Author
        view_help_default_color = "info"
        view_help_min_width = "42rem"
        view_help = {
            "summary": "About this screen",
            "details": "First paragraph.\n\nSecond paragraph.",
            "default_open": True,
        }

    view = TableView()
    help_config = view.get_view_help()

    assert help_config["summary"] == "About this screen", (
        "Collapsed view help should expose the configured summary."
    )
    assert help_config["details"] == "First paragraph.\n\nSecond paragraph.", (
        "Collapsed view help should expose the configured details."
    )
    assert help_config["default_open"] is True, (
        "Collapsed view help should expose the configured default-open state."
    )
    assert help_config["color"] == "info", (
        "Collapsed view help should use the view-level default color when no local color is set."
    )
    assert help_config["min_width"] == "42rem", (
        "Collapsed view help should use the view-level minimum width when no local override is set."
    )
    assert "var(--color-info)" in help_config["style"], (
        "Collapsed view help should map semantic colors to daisyUI CSS variables."
    )
    assert view.get_view_help_detail_paragraphs() == [
        "First paragraph.",
        "Second paragraph.",
    ], "Collapsed view help should split blank-line-separated details into paragraphs."


def test_table_mixin_get_view_help_prefers_local_color_and_width_overrides():
    class TableView(TableMixin):
        model = Author
        view_help_default_color = "base"
        view_help_min_width = "40rem"
        view_help = {
            "summary": "About this screen",
            "details": "Helpful guidance.",
            "color": "#abc",
            "min_width": "30rem",
        }

    view = TableView()
    help_config = view.get_view_help()

    assert help_config["color"] == "#abc", (
        "Collapsed view help should use the local color override when provided."
    )
    assert help_config["min_width"] == "30rem", (
        "Collapsed view help should use the local minimum-width override when provided."
    )
    assert "#aabbcc" in help_config["style"], (
        "Collapsed view help should expand short hex colors before rendering style variables."
    )
    assert "--pc-view-help-summary-fg" in help_config["style"], (
        "Collapsed view help should provide a readable summary foreground variable for hex themes."
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


def test_table_mixin_get_column_alignments_defaults_to_empty_mapping():
    class TableView(TableMixin):
        model = Author

    view = TableView()

    assert view.get_column_alignments() == {}, (
        "Column alignment overrides should default to an empty mapping when no per-column alignment is configured."
    )


def test_table_mixin_get_column_alignments_prefers_configured_mapping():
    class TableView(TableMixin):
        model = Author
        column_alignments = {"name": "center"}

    view = TableView()

    assert view.get_column_alignments() == {"name": "center"}, (
        "Column alignment overrides should use the configured mapping when provided."
    )


def test_table_mixin_get_list_cell_tooltip_fields_defaults_to_empty_mapping():
    class TableView(TableMixin):
        model = Author

    view = TableView()

    assert view.get_list_cell_tooltip_fields() == {}, (
        "List cell tooltip fields should default to an empty mapping when no semantic cell tooltips are configured."
    )


def test_table_mixin_get_list_cell_tooltip_fields_prefers_configured_list():
    class TableView(TableMixin):
        model = Author
        list_cell_tooltip_fields = ["name", "has_bio"]

    view = TableView()

    assert view.get_list_cell_tooltip_fields() == ["name", "has_bio"], (
        "List cell tooltip fields should use the configured ordered list when provided."
    )


def test_table_mixin_get_list_cell_tooltip_fields_prefers_configured_mapping():
    class TableView(TableMixin):
        model = Author
        list_cell_tooltip_fields = {"name": "get_name_tooltip"}

    view = TableView()

    assert view.get_list_cell_tooltip_fields() == {"name": "get_name_tooltip"}, (
        "List cell tooltip fields should use the configured hook mapping when provided."
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


def test_table_mixin_get_link_fields_defaults_to_empty_mapping():
    class TableView(TableMixin):
        model = Author

    view = TableView()

    assert view.get_link_fields() == {}, (
        "Declarative list-cell links should default to an empty mapping when no link_fields config is provided."
    )


def test_table_mixin_get_link_fields_prefers_configured_mapping():
    class TableView(TableMixin):
        model = Author
        link_fields = {"name": {"view_name": "sample:author-detail", "open_in": "current"}}

    view = TableView()

    assert view.get_link_fields() == {
        "name": {"view_name": "sample:author-detail", "open_in": "current"}
    }, "TableMixin should expose the configured narrow link_fields mapping unchanged."


def test_table_mixin_get_list_cell_link_defaults_to_none():
    class TableView(TableMixin):
        model = Author

    author = Author(name="Link Default")
    view = TableView()

    assert (
        view.get_list_cell_link(
            author,
            "name",
            author.name,
            is_property=False,
            request=None,
        )
        is None
    ), "The default list-cell link hook should return None so declarative config remains the only link source unless overridden."


def test_core_mixin_rejects_unknown_column_alignment_keys():
    class BrokenView(CoreMixin):
        model = Author
        fields = "__all__"
        column_alignments = {"missing_field": "center"}

    with pytest.raises(ValueError, match="column_alignments"):
        BrokenView()


def test_core_mixin_rejects_invalid_column_alignment_values():
    class BrokenView(CoreMixin):
        model = Author
        fields = "__all__"
        column_alignments = {"name": "middle"}

    with pytest.raises(ImproperlyConfigured, match="column_alignments"):
        BrokenView()


@pytest.mark.django_db
def test_core_mixin_normalizes_string_and_dict_link_fields():
    class LinkedView(CoreMixin):
        model = Book
        fields = "__all__"
        link_fields = {
            "author": "sample:author-detail",
            "title": {
                "view_name": "sample:bigbook-detail",
                "pk_attr": "pk",
                "open_in": "modal",
                "modal_box_classes": "modal-box w-11/12 max-w-6xl",
            },
            "a_really_long_property_header_for_title": {
                "url": "https://example.test/books",
                "open_in": "new",
            },
        }

    view = LinkedView()

    assert view.link_fields == {
        "author": {"view_name": "sample:author-detail", "open_in": "new"},
        "title": {
            "view_name": "sample:bigbook-detail",
            "pk_attr": "pk",
            "open_in": "modal",
            "modal_box_classes": "modal-box w-11/12 max-w-6xl",
        },
        "a_really_long_property_header_for_title": {
            "url": "https://example.test/books",
            "open_in": "new",
        },
    }, "link_fields should normalize shorthand, view-name dicts, and static-url dicts into one internal mapping shape."


@pytest.mark.django_db
def test_core_mixin_uses_view_default_for_omitted_link_field_open_in():
    class LinkedView(CoreMixin):
        model = Book
        fields = "__all__"
        list_cell_link_default_open_in = "modal"
        link_fields = {
            "author": "sample:author-detail",
            "title": {
                "view_name": "sample:bigbook-detail",
                "modal_box_classes": "modal-box w-11/12 max-w-6xl",
            },
            "a_really_long_property_header_for_title": {
                "url": "https://example.test/books",
                "open_in": "new",
            },
        }

    view = LinkedView()

    assert view.link_fields["author"]["open_in"] == "modal", (
        "String shorthand link_fields should use the view-wide default opening mode."
    )
    assert view.link_fields["title"] == {
        "view_name": "sample:bigbook-detail",
        "open_in": "modal",
        "modal_box_classes": "modal-box w-11/12 max-w-6xl",
    }, (
        "Dict link_fields without open_in should use the view-wide default and still allow modal sizing."
    )
    assert view.link_fields[
        "a_really_long_property_header_for_title"
    ]["open_in"] == "new", (
        "Explicit per-link open_in should override the view-wide default opening mode."
    )


def test_core_mixin_defaults_omitted_list_cell_link_open_in_to_new():
    class LinkedView(CoreMixin):
        model = Book
        fields = "__all__"
        link_fields = {
            "author": "sample:author-detail",
            "title": {
                "view_name": "sample:bigbook-detail",
            },
        }

    view = LinkedView()

    assert view.list_cell_link_default_open_in == "new", (
        "The view-wide list-cell link opening default should assume a new browser context when omitted."
    )
    assert view.link_fields["author"]["open_in"] == "new", (
        "String shorthand link_fields should use the package default when no view default is configured."
    )
    assert view.link_fields["title"]["open_in"] == "new", (
        "Dict link_fields without open_in should use the package default when no view default is configured."
    )


def test_core_mixin_rejects_invalid_list_cell_link_default_open_in():
    class BrokenView(CoreMixin):
        model = Author
        fields = "__all__"
        list_cell_link_default_open_in = "popup"

    with pytest.raises(ImproperlyConfigured, match="list_cell_link_default_open_in"):
        BrokenView()


def test_core_mixin_rejects_unknown_link_field_keys():
    class BrokenView(CoreMixin):
        model = Author
        fields = "__all__"
        link_fields = {"missing_field": "sample:author-detail"}

    with pytest.raises(ValueError, match="link_fields"):
        BrokenView()


def test_core_mixin_rejects_invalid_link_field_shapes():
    class BrokenView(CoreMixin):
        model = Author
        fields = "__all__"
        link_fields = {"name": {"label": "Author"}}

    with pytest.raises(ImproperlyConfigured, match="link_fields"):
        BrokenView()


def test_core_mixin_rejects_legacy_link_field_use_modal():
    class BrokenView(CoreMixin):
        model = Author
        fields = "__all__"
        link_fields = {"name": {"view_name": "sample:author-detail", "use_modal": True}}

    with pytest.raises(ImproperlyConfigured, match="link_fields"):
        BrokenView()


def test_core_mixin_rejects_invalid_link_field_open_in():
    class BrokenView(CoreMixin):
        model = Author
        fields = "__all__"
        link_fields = {"name": {"view_name": "sample:author-detail", "open_in": "popup"}}

    with pytest.raises(ImproperlyConfigured, match="link_fields"):
        BrokenView()


@pytest.mark.parametrize("open_in", ["current", "new"])
def test_core_mixin_rejects_link_field_modal_box_classes_without_modal(open_in):
    class BrokenView(CoreMixin):
        model = Author
        fields = "__all__"
        link_fields = {
            "name": {
                "view_name": "sample:author-detail",
                "open_in": open_in,
                "modal_box_classes": "modal-box w-11/12 max-w-6xl",
            }
        }

    with pytest.raises(ImproperlyConfigured, match="link_fields"):
        BrokenView()


def test_core_mixin_rejects_blank_link_field_modal_box_classes():
    class BrokenView(CoreMixin):
        model = Author
        fields = "__all__"
        link_fields = {
            "name": {
                "view_name": "sample:author-detail",
                "open_in": "modal",
                "modal_box_classes": " ",
            }
        }

    with pytest.raises(ImproperlyConfigured, match="link_fields"):
        BrokenView()


def test_core_mixin_rejects_ambiguous_link_field_url_source():
    class BrokenView(CoreMixin):
        model = Author
        fields = "__all__"
        link_fields = {
            "name": {
                "view_name": "sample:author-detail",
                "url": "https://example.test/authors",
            }
        }

    with pytest.raises(ImproperlyConfigured, match="link_fields"):
        BrokenView()


def test_core_mixin_rejects_link_field_pk_attr_with_static_url():
    class BrokenView(CoreMixin):
        model = Author
        fields = "__all__"
        link_fields = {
            "name": {
                "url": "https://example.test/authors",
                "pk_attr": "pk",
            }
        }

    with pytest.raises(ImproperlyConfigured, match="link_fields"):
        BrokenView()


@pytest.mark.django_db
def test_core_mixin_warns_when_link_fields_overlap_inline_edit_fields(caplog):
    class OverlapView(CoreMixin):
        model = Book
        fields = "__all__"
        inline_edit_fields = ["title"]
        link_fields = {"title": "sample:bigbook-detail"}

    with caplog.at_level("WARNING"):
        OverlapView()

    assert "overlap inline_edit_fields" in caplog.text, (
        "Config validation should log a warning when link_fields target cells that inline editing will always make non-linkable."
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


def test_list_cell_tooltip_fields_blank_value_raises():
    class BrokenView(CoreMixin):
        model = Author
        fields = ["name"]
        list_cell_tooltip_fields = ["name", "   "]

    with pytest.raises(ImproperlyConfigured):
        BrokenView()


def test_list_cell_tooltip_fields_mapping_blank_value_raises():
    class BrokenView(CoreMixin):
        model = Author
        fields = ["name"]
        list_cell_tooltip_fields = {"name": "   "}

    with pytest.raises(ImproperlyConfigured):
        BrokenView()


def test_list_cell_tooltip_fields_mixed_style_raises():
    class BrokenView(CoreMixin):
        model = Author
        fields = ["name"]
        list_cell_tooltip_fields = ["name", {"has_bio": "get_has_bio_tooltip"}]

    with pytest.raises(ImproperlyConfigured):
        BrokenView()


def test_list_cell_tooltip_fields_legacy_list_warns():
    class LegacyView(CoreMixin):
        model = Author
        fields = ["name"]
        list_cell_tooltip_fields = ["name"]

    with pytest.warns(FutureWarning, match="list_cell_tooltip_fields as a list"):
        LegacyView()


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
def test_author_list_omits_view_help_when_unset(client):
    """Keep the list heading compact when collapsed view help is not configured."""
    Author.objects.create(name="Alice Jones")

    response = client.get(reverse("sample:author-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Author list view should render successfully without view_help configured."
    )
    assert '<details class="collapse collapse-arrow mt-3 border"' not in response_text, (
        "List view should not render the collapsed help container when view_help is unset."
    )


@pytest.mark.django_db
def test_author_list_renders_collapsed_view_help_before_toolbar(client, monkeypatch):
    """Render collapsed screen help below instructions and above the list toolbar."""
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.view_instructions",
        "Helpful author guidance",
        raising=False,
    )
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.view_help",
        {
            "summary": "About authors",
            "details": "First paragraph.\n\nSecond paragraph.",
            "color": "info",
            "min_width": "34rem",
        },
        raising=False,
    )

    Author.objects.create(name="Alice Jones")

    response = client.get(reverse("sample:author-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Author list view should render successfully when view_help is configured."
    )
    view_help_index = response_text.index(
        '<details class="collapse collapse-arrow mt-3 border"'
    )

    assert 'data-powercrud-view-help="true"' in response_text[view_help_index:], (
        "List view should render the collapsed help container when view_help is configured."
    )
    assert response_text.index("Helpful author guidance") < view_help_index, (
        "Collapsed view help should render below view_instructions."
    )
    assert view_help_index < response_text.index(
        'data-powercrud-list-toolbar="true"'
    ), "Collapsed view help should render above the list toolbar."
    assert "<summary" in response_text and "About authors" in response_text, (
        "Collapsed view help should render the configured one-line summary."
    )
    assert 'data-powercrud-view-help-min-width="34rem"' in response_text, (
        "Collapsed view help should expose its minimum width for table-width syncing."
    )
    assert (
        "--pc-view-help-summary-bg: color-mix(in srgb, var(--color-info) 18%"
        in response_text
    ), (
        "Collapsed view help should render semantic color variables as a tinted summary bar."
    )
    assert "padding-block: 0.75rem;" in response_text, (
        "Collapsed view help should use compact summary-bar vertical padding."
    )
    assert "padding-top: 0.75rem;" in response_text, (
        "Collapsed view help should add top padding to expanded content."
    )
    assert 'data-powercrud-view-help-content="true"' in response_text, (
        "Collapsed view help should mark the content area separately for content coloring."
    )
    assert "<p>First paragraph.</p>" in response_text, (
        "Collapsed view help should render the first details paragraph."
    )
    assert "<p>Second paragraph.</p>" in response_text, (
        "Collapsed view help should render blank-line-separated paragraphs separately."
    )
    assert not re.search(
        r'<details[^>]*data-powercrud-view-help="true"[^>]*open',
        response_text,
    ), "Collapsed view help should start closed when default_open is omitted."


@pytest.mark.django_db
def test_author_list_escapes_view_help_html(client, monkeypatch):
    """Escape HTML-like summary and detail text so view_help remains plain text only."""
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.view_help",
        {
            "summary": "<strong>Unsafe summary</strong>",
            "details": "<em>Unsafe details</em>",
        },
        raising=False,
    )

    Author.objects.create(name="Alice Jones")

    response = client.get(reverse("sample:author-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Author list view should render successfully when HTML-like view_help text is configured."
    )
    assert "&lt;strong&gt;Unsafe summary&lt;/strong&gt;" in response_text, (
        "List view should escape HTML-like view_help summary text."
    )
    assert "&lt;em&gt;Unsafe details&lt;/em&gt;" in response_text, (
        "List view should escape HTML-like view_help details text."
    )
    assert "<strong>Unsafe summary</strong>" not in response_text, (
        "List view should not render raw HTML from view_help summary."
    )
    assert "<em>Unsafe details</em>" not in response_text, (
        "List view should not render raw HTML from view_help details."
    )


@pytest.mark.django_db
def test_author_list_renders_hex_view_help_color(client, monkeypatch):
    """Render a safe inline style variable set for hex-coloured view help."""
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.view_help",
        {
            "summary": "About authors",
            "details": "Use this screen to review authors.",
            "color": "#abc",
        },
        raising=False,
    )

    Author.objects.create(name="Alice Jones")

    response = client.get(reverse("sample:author-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Author list view should render successfully when hex view_help color is configured."
    )
    assert (
        "--pc-view-help-summary-bg: color-mix(in srgb, #aabbcc 18%"
        in response_text
    ), "Collapsed view help should render an expanded hex summary tint variable."
    assert (
        "--pc-view-help-content-bg: color-mix(in srgb, #aabbcc 8%"
        in response_text
    ), "Collapsed view help should render a quieter content tint for hex themes."


@pytest.mark.django_db
def test_author_list_renders_open_view_help_when_configured(client, monkeypatch):
    """Respect the view_help default_open flag through the native details attribute."""
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.view_help",
        {
            "summary": "About authors",
            "details": "Use this screen to review authors.",
            "default_open": True,
        },
        raising=False,
    )

    Author.objects.create(name="Alice Jones")

    response = client.get(reverse("sample:author-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Author list view should render successfully when open view_help is configured."
    )
    assert re.search(
        r'<details[^>]*data-powercrud-view-help="true"[^>]*open',
        response_text,
    ), "Collapsed view help should render open when default_open is True."


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
    assert "text-right" in template_text, (
        "List template should include explicit right-alignment branches so column_alignments can render right-aligned cells."
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
    assert 'data-tippy-content="Page count: 412"' in response_text, (
        "Configured sample pages cells should render semantic tooltip text on a visible non-inline model field."
    )
    assert 'data-tippy-content="ISBN: 978-1-4028-9462-1"' in response_text, (
        "Configured sample property cells should render semantic list-cell tooltip text, even when the displayed value is an icon."
    )
    assert 'data-powercrud-tooltip="semantic-cell"' in response_text, (
        "Configured sample list cells should use the dedicated semantic-cell tooltip channel rather than the generic semantic or overflow channels."
    )


@pytest.mark.django_db
def test_profile_list_renders_centered_categorical_columns(client, monkeypatch):
    """Profile sample list should center the categorical alignment-demo columns."""
    monkeypatch.setattr(
        "sample.views.ProfileCRUDView.column_alignments",
        {
            "status": "center",
            "priority_band": "center",
        },
        raising=False,
    )
    author = Author.objects.create(name="Profile Alignment Author")
    Profile.objects.create(
        author=author,
        nickname="Centered Profile",
        status=Profile.Status.REVIEW,
        priority_band=Profile.PriorityBand.HIGH,
    )

    response = client.get(reverse("sample:profile-list"))
    response_text = response.content.decode()

    assert response.status_code == 200, (
        "Profile list should render successfully so the centered alignment demo columns can be inspected."
    )
    assert 'data-field-name="status"' in response_text, (
        "Profile list should render the sample status column used for the alignment demo."
    )
    assert 'data-field-name="priority_band"' in response_text, (
        "Profile list should render the sample priority band column used for the alignment demo."
    )
    assert "Review" in response_text and "High" in response_text, (
        "Profile list should render the categorical sample values that demonstrate centered alignment."
    )
    assert response_text.count("pc-inline-editable w-full px-0 pc-inline-align-center flex justify-center text-center") >= 2, (
        "Profile list should render centered inline-display button markup for the configured categorical alignment demo columns."
    )
    assert reverse("sample:profile-inline-row", args=[author.profile.pk]) in response_text, (
        "Profile list should keep inline editing enabled while demonstrating the reduced row-action set."
    )
    assert '<span class="text-center block w-full h-full">Actions</span>' in response_text, (
        "Profile list should show the actions header when the sample has one row action."
    )
    assert ">View<" not in response_text, (
        "Profile list should omit the built-in View action for the one-row-action demo."
    )
    assert response_text.count(">Edit<") == 1, (
        "Profile list should demonstrate the one-row-action case."
    )
    assert ">Delete<" not in response_text, (
        "Profile list should omit the built-in Delete action for the one-row-action demo."
    )
    with pytest.raises(NoReverseMatch):
        reverse("sample:profile-detail", args=[author.profile.pk])
    assert reverse("sample:profile-update", args=[author.profile.pk]) in response_text, (
        "Profile list should render the restored Edit row action."
    )
    with pytest.raises(NoReverseMatch):
        reverse("sample:profile-delete", args=[author.profile.pk])


@pytest.mark.django_db
def test_book_list_escapes_semantic_list_cell_tooltip_html(client, monkeypatch):
    """Escape HTML-like semantic cell tooltip text so list-cell tooltips remain plain text only."""
    monkeypatch.setattr(
        "sample.views.BookCRUDView.get_title_tooltip",
        lambda self, obj, request=None: "<strong>Unsafe</strong>",
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
    assert 'class="grid gap-x-2 gap-y-0"' in response_text, (
        "Book list filter form should keep compact grid spacing without fixed breakpoint column classes."
    )
    assert "grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));" in response_text, (
        "Book list filter form should auto-fit readable filter columns instead of hard-capping at three columns."
    )
    assert "max-width: calc((20rem * 4) + (0.5rem * 3));" in response_text, (
        "Book list filter form should cap the filter grid at four readable columns even when the table is very wide."
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
    assert "max-width: 78rem;" not in response_text, (
        "The filter panel shell should no longer cap below the synced table width."
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
        "Book list view should wrap the Add filter control in a dedicated container inside the filter panel."
    )
    assert 'data-powercrud-filter-toolbar' in response_text, (
        "Book list view should render a distinct filter-toolbar cluster to visually separate filter actions from other page actions."
    )
    assert 'data-powercrud-filter-label="true"' not in response_text, (
        "The compact filter trigger should be icon-only so it does not widen the view-control toolbar."
    )
    assert 'aria-label="Show filters"' in response_text, (
        "The icon-only filter trigger should keep an accessible label for screen-reader and tooltip use."
    )
    assert 'data-powercrud-filter-toggle id="filterToggleBtn" aria-controls="filterCollapse" aria-expanded="false" aria-label="Show filters" data-powercrud-tooltip="semantic" data-tippy-content="Show filters"' in response_text, (
        "The filter trigger should use PowerCRUD Tippy metadata instead of a native title tooltip."
    )
    filter_panel_index = response_text.index('id="filterCollapse"')
    assert filter_panel_index < response_text.index(
        'data-powercrud-add-filter-container',
        filter_panel_index,
    ), (
        "The Add filter control should sit inside the collapsible filter panel rather than widening the top toolbar."
    )
    assert 'class="hidden border-b border-base-200 px-3 py-2" data-powercrud-add-filter-container' in response_text, (
        "Book list view should hide the Add filter control by default until the user opens the filter panel."
    )
    assert "bg-base-200" in response_text and "border-base-content/20" in response_text, (
        "Add filter should use a neutral panel-control surface instead of matching active filter inputs."
    )
    assert "[data-powercrud-add-filter-container]:not(.hidden)" in response_text and "justify-content: flex-end;" in response_text, (
        "Visible Add filter controls should align to the top-right of the filter panel on desktop."
    )
    assert 'data-powercrud-filter-panel-action data-powercrud-filter-reset' in response_text, (
        "Reset filters should live in the top filter control row rather than a separate footer."
    )
    assert 'class="btn btn-outline btn-sm' in response_text and "Reset filters" in response_text, (
        "Reset filters should render as a visible button beside Add filter."
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
    assert 'id="page-size-select"' in response_text and 'name="page_size"' in response_text and 'data-powercrud-page-size-select="true"' in response_text, (
        "Page-size changes should use the dedicated PowerCRUD page-size selector hook rather than a broad form-level include."
    )
    assert 'data-tippy-content="Rows per page"' in response_text, (
        "Page-size control should expose a PowerCRUD tooltip."
    )
    assert 'class="cursor-pointer" name="page_size"' in response_text, (
        "The page-size select should use a pointer cursor to match clickable toolbar controls."
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
    assert 'data-powercrud-modal' in response_text, (
        "The shared PowerCRUD modal should expose a stable frontend hook."
    )
    assert 'data-powercrud-modal-box' in response_text, (
        "The shared PowerCRUD modal box should expose a stable frontend hook for sizing."
    )
    assert 'class="modal-box flex max-h-[calc(100dvh-2rem)] flex-col"' in response_text, (
        "The default modal box should be bounded to the viewport."
    )
    assert 'class="min-h-0 flex-1 overflow-y-auto py-4"' in response_text, (
        "The default modal body should scroll when modal content exceeds the viewport."
    )


@pytest.mark.django_db
def test_book_list_renders_custom_modal_context(client, monkeypatch):
    """Render configured modal IDs, targets, and class hooks in the shared modal shell."""
    author = Author.objects.create(name="Large Modal Link Author")
    Book.objects.create(
        title="Large Modal Link Book",
        author=author,
        published_date=date(2024, 11, 1),
        bestseller=False,
        isbn="9876543210777",
        pages=88,
        description="List-cell modal sizing coverage",
    )

    monkeypatch.setattr(sample_views.BookCRUDView, "modal_id", "customBookModal")
    monkeypatch.setattr(sample_views.BookCRUDView, "modal_target", "customBookModalContent")
    monkeypatch.setattr(sample_views.BookCRUDView, "modal_classes", "modal modal-bottom sm:modal-middle")
    monkeypatch.setattr(
        sample_views.BookCRUDView,
        "modal_box_classes",
        "modal-box w-11/12 max-w-4xl",
    )
    monkeypatch.setattr(sample_views.BookCRUDView, "modal_body_classes", "py-6")
    monkeypatch.setattr(
        sample_views.BookCRUDView,
        "bulk_modal_box_classes",
        "modal-box w-11/12 max-w-6xl",
    )

    response = client.get(reverse("sample:bigbook-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Book list view should render successfully with customized modal settings."
    )
    assert 'id="customBookModal"' in response_text, (
        "The modal shell should use the configured modal_id."
    )
    assert 'id="customBookModalContent"' in response_text, (
        "The modal shell should use the configured modal_target."
    )
    assert 'class="modal modal-bottom sm:modal-middle"' in response_text, (
        "The modal shell should render configured dialog classes."
    )
    assert 'class="modal-box w-11/12 max-w-4xl"' in response_text, (
        "The modal box should render configured default classes."
    )
    assert 'class="py-6"' in response_text, (
        "The modal content target should render configured body classes."
    )
    assert 'hx-target="#customBookModalContent"' in response_text, (
        "Modal triggers should target the configured modal content element."
    )
    assert 'data-powercrud-modal-box-classes="modal-box w-11/12 max-w-6xl"' in response_text, (
        "The built-in bulk edit trigger should expose configured bulk modal box classes."
    )
    assert (
        'data-powercrud-modal-box-classes="modal-box flex max-h-[calc(100dvh-2rem)] '
        'w-11/12 max-w-6xl flex-col"'
    ) in response_text, (
        "The sample modal list-cell link should expose its larger per-cell modal box classes."
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
    assert "data-powercrud-extra-buttons-dropdown='true'" in response_text, (
        "Sample book list should render configured extra buttons in the top toolbar overflow menu."
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
    selected_summary_index = response_text.find("Selected Summary")
    selected_summary_anchor_start = response_text.rfind("<a ", 0, selected_summary_index)
    selected_summary_anchor_end = response_text.find(">", selected_summary_anchor_start)
    selected_summary_link = response_text[
        selected_summary_anchor_start:selected_summary_anchor_end
    ]
    assert selected_summary_anchor_start != -1 and selected_summary_anchor_end != -1, (
        "Sample book list should render Selected Summary as a modal header action."
    )
    assert "selected-summary" in selected_summary_link, (
        "Selected Summary should point at the sample selected-summary endpoint."
    )
    assert "data-powercrud-modal-box-classes" not in selected_summary_link, (
        "Selected Summary should use the view default modal width rather than a per-button override."
    )
    assert "Home in Modal!" in response_text, (
        "Sample book list should keep a separate modal header button for per-button sizing."
    )
    assert (
        'data-powercrud-modal-box-classes="modal-box flex max-h-[calc(100dvh-2rem)] '
        'w-11/12 max-w-3xl flex-col"'
    ) in response_text, (
        "Home in Modal should demonstrate per-button modal sizing without changing Selected Summary."
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
    assert (
        "data-powercrud-modal-box-classes='modal-box flex max-h-[calc(100dvh-2rem)] "
        "w-11/12 max-w-5xl flex-col'"
    ) in response_text, (
        "Sample modal extra action should demonstrate per-action modal sizing."
    )


@pytest.mark.django_db
def test_book_list_hides_primitive_extra_action_when_hidden_hook_matches(client):
    """Hide primitive row actions from the base book sample when hidden_if matches."""
    author = Author.objects.create(name="Primitive Hidden Action Author")
    Book.objects.create(
        title="Hidden Preview Primitive",
        author=author,
        published_date=date(2024, 10, 2),
        bestseller=False,
        isbn="9876543210668",
        pages=41,
        description="This row would otherwise have a preview.",
    )

    response = client.get(reverse("sample:bigbook-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "Book list view should render successfully so primitive hidden_if behavior can be inspected."
    )
    assert "Description Preview" not in response_text, (
        "Base BookCRUDView should hide the primitive description-preview action when hidden_if matches."
    )
    assert ">More<" in response_text, (
        "The row should keep More visible because the Normal Edit extra action still applies."
    )


@pytest.mark.django_db
def test_powerfield_book_list_hides_poweraction_when_hidden_hook_matches(client):
    """Hide PowerAction row actions from the PowerField book sample when hidden_if matches."""
    author = Author.objects.create(name="PowerAction Hidden Action Author")
    Book.objects.create(
        title="Hidden Preview PowerAction",
        author=author,
        published_date=date(2024, 10, 3),
        bestseller=False,
        isbn="9876543210669",
        pages=42,
        description="This row would otherwise have a preview.",
    )

    response = client.get(reverse("sample:powerfield-book-list"))
    response_text = " ".join(response.content.decode().split())

    assert response.status_code == 200, (
        "PowerField book list view should render successfully so PowerAction hidden_if behavior can be inspected."
    )
    assert "Description Preview" not in response_text, (
        "PowerFieldBookCRUDView should hide the PowerAction description-preview action when hidden_if matches."
    )
    assert ">More<" in response_text, (
        "The row should keep More visible because the Normal Edit PowerAction still applies."
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
    assert "data-powercrud-row-actions-trigger" not in response_text, (
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
    assert "data-powercrud-row-actions-template='true'" in response_text, (
        "Sample book list should render the floating row-actions menu template when dropdown mode is enabled."
    )
    assert ">More<" in response_text, (
        "Sample book list should include the More trigger for overflow extra row actions."
    )
    assert "Description Preview" in response_text, (
        "Sample book list should keep the configured extra action labels inside the dropdown markup."
    )
