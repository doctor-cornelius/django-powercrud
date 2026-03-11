from __future__ import annotations

import pytest
from django.test import Client
from django.test import RequestFactory
from django.urls import reverse

from powercrud.mixins.filtering_mixin import NULL_FILTER_SENTINEL
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
def test_book_sample_inline_row_endpoint_renders_edit_form():
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
