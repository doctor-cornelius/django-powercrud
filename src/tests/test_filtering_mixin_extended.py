from __future__ import annotations

from datetime import date

import pytest
from django_filters import FilterSet
from django.test import RequestFactory

from powercrud.mixins.filtering_mixin import (
    FilteringMixin,
    HTMXFilterSetMixin,
    NULL_FILTER_SENTINEL,
    NullableModelChoiceFilter,
)
from powercrud.mixins.form_mixin import FormMixin
from powercrud.mixins.htmx_mixin import HtmxMixin
from sample.models import Author, Book, Genre, Profile


class BaseFilterHarness(HtmxMixin, FormMixin, FilteringMixin):
    """Shared harness for isolated filtering mixin tests."""

    use_htmx = True
    use_modal = False
    templates_path = "powercrud/daisyUI"
    bulk_fields = []
    bulk_delete = False
    modal_id = None
    modal_target = None

    def __init__(self, request):
        self.request = request
        self.use_crispy = False
        self.form_class = None


class FilterHarness(BaseFilterHarness):
    """Harness for book filter generation tests."""

    model = Book
    filterset_fields = ["author", "genres", "bestseller"]
    dropdown_sort_options = {"author": "name"}

    def __init__(self, request):
        super().__init__(request)
        self.m2m_filter_and_logic = True


class AuthorNullFilterHarness(BaseFilterHarness):
    """Harness for nullable scalar filter generation tests."""

    model = Author
    filterset_fields = ["name", "birth_date"]


class DuplicateFilterHarness(BaseFilterHarness):
    """Harness proving duplicate filterset_fields are normalized quietly."""

    model = Book
    filterset_fields = ["author", "author", "genres"]


class AuthorNullFilterExcludeHarness(AuthorNullFilterHarness):
    """Harness for opt-out coverage on nullable scalar fields."""

    filter_null_fields_exclude = ["birth_date"]


class ProfileNullFilterHarness(BaseFilterHarness):
    """Harness for merged nullable relation filter generation tests."""

    model = Profile
    filterset_fields = ["author", "favorite_genre"]


class ProfileNullFilterExcludeHarness(ProfileNullFilterHarness):
    """Harness for opt-out coverage on nullable relation fields."""

    filter_null_fields_exclude = ["favorite_genre"]


class PassiveHTMXBookFilterSet(HTMXFilterSetMixin, FilterSet):
    """Custom filterset that relies on PowerCRUD to call `setup_htmx_attrs()`."""

    class Meta:
        model = Book
        fields = ["author", "title"]


class PlainBookFilterSet(FilterSet):
    """Custom filterset without HTMX helper support."""

    class Meta:
        model = Book
        fields = ["author"]


class CustomBookFilterHarness(BaseFilterHarness):
    """Harness for custom filterset precedence and shared runtime behavior."""

    model = Book
    filterset_class = PassiveHTMXBookFilterSet
    filterset_fields = ["pages"]
    filter_queryset_options = {"author": {"name": "Alan"}}


class CustomBookFilterNoHtmxHarness(CustomBookFilterHarness):
    """Harness for custom filterset behavior when HTMX is disabled."""

    use_htmx = False


class PlainCustomBookFilterHarness(BaseFilterHarness):
    """Harness for custom filtersets that do not expose HTMX setup helpers."""

    model = Book
    filterset_class = PlainBookFilterSet


@pytest.mark.django_db
def test_filterset_builds_choices():
    """Build dropdown choices and M2M filters for the standard book harness."""
    author_a = Author.objects.create(name="Alan")
    genre = Genre.objects.create(name="Sci-Fi")
    book = Book.objects.create(
        title="Sample",
        author=author_a,
        published_date=date(2024, 1, 1),
        bestseller=True,
        isbn="1234567890123",
        pages=100,
    )
    book.genres.add(genre)

    request = RequestFactory().get("/", {"author": author_a.pk})
    view = FilterHarness(request)
    filterset = view.get_filterset(Book.objects.all())
    assert filterset is not None, "Expected a filterset for configured book filters."
    assert list(
        filterset.form.fields["author"].queryset.values_list("name", flat=True)
    ) == ["Alan"], "Author filter queryset should be scoped to the available author."
    assert "genres" in filterset.filters, "Genres filter should be generated."
    assert (
        filterset.filters["genres"].extra["queryset"].count() == 1
    ), "Genre filter queryset should be limited to the available related genre."
    assert (
        filterset.form.fields["author"].label == "Author"
    ), "Non-text auto-generated filter labels should continue to use the plain field label."


@pytest.mark.django_db
def test_filterset_dedupes_configured_fields():
    """Duplicate filterset_fields entries should collapse to first occurrence."""
    request = RequestFactory().get("/")
    view = DuplicateFilterHarness(request)

    filterset = view.get_filterset(Book.objects.all())

    assert list(filterset.filters.keys()) == ["author", "genres"], (
        "filterset_fields should quietly drop later duplicates while preserving first-occurrence order."
    )


@pytest.mark.django_db
def test_nullable_scalar_fields_get_companion_null_filter():
    """Add a companion null filter for nullable scalar auto-filters."""
    Author.objects.create(name="Alan", birth_date=date(1980, 1, 1))
    Author.objects.create(name="Betty", birth_date=None)

    request = RequestFactory().get("/", {"birth_date__isnull": "true"})
    view = AuthorNullFilterHarness(request)
    filterset = view.get_filterset(Author.objects.all())

    assert (
        filterset is not None
    ), "Expected an auto-generated filterset for nullable scalar field coverage."
    assert (
        "birth_date__isnull" in filterset.filters
    ), "Nullable scalar fields should gain a companion __isnull filter."
    assert (
        filterset.form.fields["birth_date__isnull"].label == "Birth date is empty"
    ), "Companion null filter label should describe the underlying field clearly."
    assert (
        "data-powercrud-searchable-select"
        not in filterset.form.fields["birth_date__isnull"].widget.attrs
    ), "Companion null filters should remain native boolean selects, not searchable selects."
    assert list(filterset.qs.values_list("name", flat=True)) == [
        "Betty"
    ], "Companion null filter should return only rows where the scalar field is null."
    assert (
        filterset.form.fields["name"].label == "Name"
    ), "Auto-generated text filters should keep the plain field label instead of appending the lookup name."


@pytest.mark.django_db
def test_nullable_scalar_companion_null_filter_stays_next_to_parent_field():
    """Keep companion null filters adjacent to their parent field in the form."""
    request = RequestFactory().get("/")
    view = AuthorNullFilterHarness(request)
    filterset = view.get_filterset(Author.objects.all())

    assert (
        filterset is not None
    ), "Expected an auto-generated filterset when checking companion filter ordering."
    assert list(filterset.form.fields.keys()) == [
        "name",
        "birth_date",
        "birth_date__isnull",
    ], "Companion null filters should render immediately after their parent field."


@pytest.mark.django_db
def test_nullable_scalar_companion_null_filter_false_returns_non_null_records():
    """Interpret `false` on a companion null filter as `isnull=False`."""
    Author.objects.create(name="Alan", birth_date=date(1980, 1, 1))
    Author.objects.create(name="Betty", birth_date=None)

    request = RequestFactory().get("/", {"birth_date__isnull": "false"})
    view = AuthorNullFilterHarness(request)
    filterset = view.get_filterset(Author.objects.all())

    assert (
        filterset is not None
    ), "Expected a filterset when testing nullable scalar false filtering."
    assert list(filterset.qs.values_list("name", flat=True)) == [
        "Alan"
    ], "A false companion null filter should keep only rows where the scalar field is not null."


@pytest.mark.django_db
def test_nullable_relation_fields_merge_empty_only_option_and_filter_nulls():
    """Merge an `Empty only` option into nullable relation filter selects."""
    author_one = Author.objects.create(name="Alan")
    author_two = Author.objects.create(name="Betty")
    genre = Genre.objects.create(name="Sci-Fi")
    Profile.objects.create(
        author=author_one,
        nickname="Has Genre",
        favorite_genre=genre,
    )
    Profile.objects.create(
        author=author_two,
        nickname="Missing Genre",
        favorite_genre=None,
    )

    request = RequestFactory().get("/", {"favorite_genre": NULL_FILTER_SENTINEL})
    view = ProfileNullFilterHarness(request)
    filterset = view.get_filterset(Profile.objects.all())

    assert (
        filterset is not None
    ), "Expected a filterset when testing merged nullable relation filtering."
    assert isinstance(
        filterset.filters["favorite_genre"], NullableModelChoiceFilter
    ), "Nullable relation filters should use the merged NullableModelChoiceFilter."
    relation_choices = list(filterset.form.fields["favorite_genre"].choices)
    assert (
        relation_choices[1] == (NULL_FILTER_SENTINEL, "Empty only")
    ), "Merged nullable relation filters should expose an 'Empty only' option after the blank choice."
    assert list(filterset.qs.values_list("nickname", flat=True)) == [
        "Missing Genre"
    ], "Selecting the merged null sentinel should return only rows where the relation is null."


@pytest.mark.django_db
def test_filter_null_fields_exclude_disables_scalar_null_companion_filter():
    """Respect scalar opt-outs for automatic companion null filters."""
    Author.objects.create(name="Alan", birth_date=None)

    request = RequestFactory().get("/")
    view = AuthorNullFilterExcludeHarness(request)
    filterset = view.get_filterset(Author.objects.all())

    assert (
        filterset is not None
    ), "Expected a filterset when testing scalar null-filter opt-out."
    assert (
        "birth_date__isnull" not in filterset.filters
    ), "Excluded scalar fields should not receive companion null filters."


@pytest.mark.django_db
def test_filter_null_fields_exclude_disables_relation_empty_only_option():
    """Respect relation opt-outs for merged null-only select options."""
    author_one = Author.objects.create(name="Alan")
    author_two = Author.objects.create(name="Betty")
    genre = Genre.objects.create(name="Sci-Fi")
    Profile.objects.create(
        author=author_one,
        nickname="Has Genre",
        favorite_genre=genre,
    )
    Profile.objects.create(
        author=author_two,
        nickname="Missing Genre",
        favorite_genre=None,
    )

    request = RequestFactory().get("/")
    view = ProfileNullFilterExcludeHarness(request)
    filterset = view.get_filterset(Profile.objects.all())

    assert (
        filterset is not None
    ), "Expected a filterset when testing relation null-filter opt-out."
    relation_choices = list(filterset.form.fields["favorite_genre"].choices)
    assert (
        (NULL_FILTER_SENTINEL, "Empty only") not in relation_choices
    ), "Excluded nullable relation fields should not expose the merged 'Empty only' option."


@pytest.mark.django_db
def test_custom_filterset_class_preserves_htmx_and_searchable_selects():
    """Custom filtersets should keep HTMX and shared select enhancement behavior."""
    Author.objects.create(name="Alan")
    Author.objects.create(name="Betty")

    request = RequestFactory().get("/")
    view = CustomBookFilterHarness(request)
    filterset = view.get_filterset(Book.objects.all())

    assert (
        filterset is not None
    ), "Expected a filterset instance when a custom filterset_class is configured."
    assert list(filterset.form.fields.keys()) == [
        "author",
        "title",
    ], "A custom filterset_class should define the filter fields even when filterset_fields is also present."
    assert list(
        filterset.form.fields["author"].queryset.values_list("name", flat=True)
    ) == [
        "Alan",
        "Betty",
    ], "filter_queryset_options should not be auto-applied to a fully custom filterset_class."
    assert (
        filterset.form.fields["title"].widget.attrs.get("hx-get") == ""
    ), "Custom filtersets exposing setup_htmx_attrs() should receive HTMX widget attrs automatically when use_htmx=True."
    assert (
        "data-powercrud-searchable-select"
        in filterset.form.fields["author"].widget.attrs
    ), "Shared searchable-select enhancement should still apply to eligible custom filterset select widgets."


@pytest.mark.django_db
def test_custom_filterset_class_skips_auto_htmx_attrs_when_htmx_disabled():
    """Do not inject HTMX attrs into custom filtersets when HTMX is disabled."""
    Author.objects.create(name="Alan")

    request = RequestFactory().get("/")
    view = CustomBookFilterNoHtmxHarness(request)
    filterset = view.get_filterset(Book.objects.all())

    assert (
        filterset is not None
    ), "Expected a filterset instance when checking HTMX-disabled custom filterset behavior."
    assert (
        "hx-get" not in filterset.form.fields["title"].widget.attrs
    ), "Custom filtersets should not receive HTMX widget attrs when use_htmx=False."


@pytest.mark.django_db
def test_plain_custom_filterset_class_without_htmx_helper_still_works():
    """Leave plain custom filtersets alone when they do not expose HTMX helpers."""
    Author.objects.create(name="Alan")

    request = RequestFactory().get("/")
    view = PlainCustomBookFilterHarness(request)
    filterset = view.get_filterset(Book.objects.all())

    assert (
        filterset is not None
    ), "Expected a plain custom filterset instance to build successfully."
    assert (
        "hx-get" not in filterset.form.fields["author"].widget.attrs
    ), "Custom filtersets without setup_htmx_attrs() should keep their existing widget attrs unchanged."
