from __future__ import annotations

import re
from datetime import date

import pytest
from django.test import Client
from django.test import RequestFactory
from django.urls import reverse

from powercrud.mixins.filtering_mixin import NULL_FILTER_SENTINEL
from powercrud.templatetags import powercrud as powercrud_tags
from sample import views as sample_views
from sample.models import Author, Book, Genre, Profile


@pytest.mark.django_db
def test_author_sample_view_exposes_nullable_scalar_companion_filter():
    """Author sample view should expose the nullable birth-date companion filter."""
    Author.objects.create(name="Alan", birth_date=None)

    view = sample_views.AuthorCRUDView()
    view.request = RequestFactory().get("/")
    filterset = view.get_filterset(Author.objects.all())

    assert (
        filterset is not None
    ), "Expected AuthorCRUDView to generate a filterset for the sample app."
    assert (
        "birth_date__isnull" in filterset.filters
    ), "AuthorCRUDView should expose the nullable birth_date companion filter in the sample app."


@pytest.mark.django_db
def test_author_sample_view_keeps_nullable_scalar_companion_optional_by_default():
    """Author sample view should allow the birth-date null companion without showing it by default."""
    Author.objects.create(name="Alan", birth_date=None)

    view = sample_views.AuthorCRUDView()
    view.request = RequestFactory().get("/")
    filterset = view.get_filterset(Author.objects.all())
    context = view.get_filter_visibility_context(filterset)

    assert [field.name for field in context["visible_filter_fields"]] == [
        "name",
        "birth_date",
        "genres",
    ], "AuthorCRUDView should keep its main filters visible by default without auto-showing the nullable companion control."
    assert [choice["name"] for choice in context["addable_filter_choices"]] == [
        "birth_date__isnull",
    ], "AuthorCRUDView should still allow the nullable birth-date companion control to be added on demand."


@pytest.mark.django_db
def test_profile_sample_view_exposes_nullable_relation_empty_only_option():
    """Profile sample view should expose the merged null-only relation option."""
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

    view = sample_views.ProfileCRUDView()
    view.request = RequestFactory().get("/")
    filterset = view.get_filterset(Profile.objects.all())

    assert (
        filterset is not None
    ), "Expected ProfileCRUDView to generate a filterset for the sample app."
    relation_choices = list(filterset.form.fields["favorite_genre"].choices)
    assert (
        (NULL_FILTER_SENTINEL, "Empty only") in relation_choices
    ), "ProfileCRUDView should expose the merged 'Empty only' option for nullable favorite_genre filtering."


@pytest.mark.django_db
def test_profile_sample_view_applies_static_queryset_filters_to_forms_and_bulk():
    """Profile sample view should demonstrate static queryset rules across surfaces."""
    author = Author.objects.create(name="Static Profile Author")
    sci_fi = Genre.objects.create(name="Sci-Fi")
    fantasy = Genre.objects.create(name="Fantasy")
    profile = Profile.objects.create(
        author=author,
        nickname="Static Demo",
        favorite_genre=sci_fi,
    )

    view = sample_views.ProfileCRUDView()
    view.request = RequestFactory().get("/")

    form = view._finalize_form(view.get_form_class()(instance=profile))
    inline_form = view.build_inline_form(instance=profile)
    bulk_qs = view.get_bulk_choices_for_field(
        "favorite_genre",
        Profile._meta.get_field("favorite_genre"),
    )

    form_genre_names = list(
        form.fields["favorite_genre"].queryset.values_list("name", flat=True)
    )
    inline_genre_names = list(
        inline_form.fields["favorite_genre"].queryset.values_list("name", flat=True)
    )
    bulk_genre_names = list(bulk_qs.values_list("name", flat=True))

    assert form_genre_names == [
        "Sci-Fi"
    ], "ProfileCRUDView should restrict regular form genre choices using a static field_queryset_dependencies rule."
    assert inline_genre_names == [
        "Sci-Fi"
    ], "ProfileCRUDView should reuse the same static field queryset restriction during inline editing."
    assert bulk_genre_names == [
        "Sci-Fi"
    ], "ProfileCRUDView should reuse the same static field queryset restriction for bulk edit choices."
    assert (
        fantasy.name not in bulk_genre_names
    ), "ProfileCRUDView bulk choices should exclude genres that fail the sample static queryset rule."


@pytest.mark.django_db
def test_profile_sample_view_exposes_centered_alignment_overrides():
    """Profile sample view should expose the current mixed alignment demo."""
    view = sample_views.ProfileCRUDView()

    assert view.get_column_alignments() == {
        "status": "center",
        "priority_band": "right",
        "favorite_genre": "left",
    }, "ProfileCRUDView should expose the current sample alignment overrides for its categorical and text demo columns."


@pytest.mark.django_db
def test_book_sample_view_scopes_genres_queryset_for_regular_forms():
    """Book sample view should scope genres from the selected author in regular forms."""
    author_a = Author.objects.create(name="Author A")
    author_b = Author.objects.create(name="Author B")
    genre_a = Genre.objects.create(name="Genre A")
    genre_b = Genre.objects.create(name="Genre B")
    author_a.genres.add(genre_a)
    author_b.genres.add(genre_b)
    book = Book.objects.create(
        title="Scoped Sample Book",
        author=author_a,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9781234500001",
        pages=88,
    )

    view = sample_views.BookCRUDView()
    view.request = RequestFactory().post("/")
    form = view._finalize_form(
        view.get_form_class()(
            instance=book,
            data={
                "title": book.title,
                "author": str(author_b.pk),
                "published_date": "2024-01-01",
                "isbn": book.isbn,
                "pages": str(book.pages),
                "bestseller": "",
            },
        )
    )

    genre_ids = list(form.fields["genres"].queryset.values_list("id", flat=True))
    assert genre_ids == [
        genre_b.pk
    ], "BookCRUDView should scope genre choices to the selected author in the sample form."
    assert (
        form.fields["genres"].required is False
    ), "The sample BookForm should still keep genres optional while PowerCRUD scopes the queryset."


@pytest.mark.django_db
def test_book_sample_view_derives_inline_dependencies_from_queryset_config():
    """Book sample view should expose inline dependency metadata without duplicating config."""
    view = sample_views.BookCRUDView()
    view.request = RequestFactory().get("/")

    deps = view.get_inline_field_dependencies()

    assert (
        deps["genres"]["depends_on"] == ["author"]
    ), "BookCRUDView should derive inline dependency metadata from field_queryset_dependencies."


@pytest.mark.django_db
def test_book_sample_view_exposes_default_and_optional_filter_visibility():
    """Book sample view should demonstrate default-visible and optional filters."""
    Author.objects.create(name="Filter Demo Author")

    view = sample_views.BookCRUDView()
    view.request = RequestFactory().get("/", {"visible_filters": ["isbn"]})
    filterset = view.get_filterset(Book.objects.all())
    context = view.get_filter_visibility_context(filterset)

    assert [field.name for field in context["visible_filter_fields"]] == [
        "author",
        "title",
        "published_date",
        "isbn",
        "bestseller",
    ], "BookCRUDView should keep its configured default filters visible and allow optional filters to be revealed from the URL-backed visibility state."
    assert context["persisted_optional_filter_names"] == [
        "isbn"
    ], "BookCRUDView should persist revealed optional filters separately from its default-visible filter set."
    assert [choice["name"] for choice in context["addable_filter_choices"]] == [
        "pages",
        "description",
        "genres",
    ], "BookCRUDView should leave only the remaining hidden filters available in the Add filter menu."


@pytest.mark.django_db
def test_book_sample_view_demonstrates_property_link_fields():
    """Book sample view should expose a real list-cell link demo on a non-inline property column."""
    author = Author.objects.create(name="Link Demo Author")
    book = Book.objects.create(
        title="Linked Sample Book",
        author=author,
        published_date=date(2024, 1, 1),
        bestseller=False,
        isbn="9781234500099",
        pages=321,
    )

    view = sample_views.BookCRUDView()
    request = RequestFactory().get("/")
    request.session = {}
    view.request = request

    row = powercrud_tags.object_list({"request": request}, [book], view)["object_list"][
        0
    ]
    cell_map = {cell["name"]: cell for cell in row["cells"]}

    assert (
        cell_map["a_really_long_property_header_for_title"]["link"]["url"]
        == reverse("sample:author-detail", kwargs={"pk": author.pk})
    ), "BookCRUDView should keep a real sample list-cell link on its non-inline title-like property column, now targeting the related author detail."
    assert (
        cell_map["a_really_long_property_header_for_title"]["link"]["use_modal"] is True
    ), "BookCRUDView should now demonstrate modal list-cell links on its existing non-inline sample column."


@pytest.mark.django_db
def test_book_sample_inline_row_endpoint_renders_edit_form(monkeypatch):
    """Book sample inline row endpoint should still return editable row markup."""
    author = Author.objects.create(name="Inline Author")
    genre = Genre.objects.create(name="Inline Genre")
    author.genres.add(genre)
    book = Book.objects.create(
        title="Inline Endpoint Book",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9781234500002",
        pages=89,
    )
    book.genres.set([genre])

    monkeypatch.setattr(
        sample_views.BookCRUDView,
        "is_inline_row_locked",
        lambda self, obj: False,
    )
    client = Client()
    response = client.get(
        reverse("sample:bigbook-inline-row", args=[book.pk]),
        HTTP_HX_REQUEST="true",
    )

    assert (
        response.status_code == 200
    ), "The sample inline row endpoint should render successfully for editable rows."
    assert (
        b"data-inline-save" in response.content
    ), "The sample inline row endpoint should include inline save controls."
    assert (
        b'type="hidden" name="description"' in response.content
    ), "The sample inline row endpoint should repost non-rendered full-form fields like description as hidden inputs."


@pytest.mark.django_db
def test_book_sample_list_renders_inline_trigger_targets(monkeypatch):
    """Book sample list rows should render inline trigger buttons with HTMX targets."""
    author = Author.objects.create(name="Inline List Author")
    book = Book.objects.create(
        title="Inline List Book",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9781234500003",
        pages=90,
        description="List page regression",
    )

    monkeypatch.setattr(
        sample_views.BookCRUDView,
        "is_inline_row_locked",
        lambda self, obj: False,
    )
    client = Client()
    response = client.get(
        reverse("sample:bigbook-list"),
    )

    assert (
        response.status_code == 200
    ), "The sample list page should render successfully when inline editing is enabled."
    assert (
        f'id="pc-row-{book.pk}"'.encode() in response.content
    ), "Sample list rows should render stable DOM ids so inline swaps have a valid HTMX target."
    assert (
        reverse("sample:bigbook-inline-row", args=[book.pk]).encode() in response.content
    ), "Sample list rows should render the inline-row endpoint URL into the trigger button markup."
    assert (
        b'hx-target="#pc-row-' in response.content
    ), "Sample inline trigger buttons should target the row DOM id for outerHTML swaps."
    assert (
        re.search(rb"<tr[^>]*data-inline-active=\"true\"", response.content) is None
    ), "The sample list page should not render an already-active inline row on initial load."
