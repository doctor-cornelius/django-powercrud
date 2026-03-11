from __future__ import annotations

import pytest
from django.test import RequestFactory

from powercrud.mixins.filtering_mixin import NULL_FILTER_SENTINEL
from sample import views as sample_views
from sample.models import Author, Genre, Profile


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
