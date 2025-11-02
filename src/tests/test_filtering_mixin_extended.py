from __future__ import annotations

from datetime import date

import pytest
from django.test import RequestFactory

from powercrud.mixins.filtering_mixin import FilteringMixin
from powercrud.mixins.form_mixin import FormMixin
from powercrud.mixins.htmx_mixin import HtmxMixin
from sample.models import Author, Book, Genre


class FilterHarness(HtmxMixin, FormMixin, FilteringMixin):
    model = Book
    filterset_fields = ["author", "genres", "bestseller"]
    dropdown_sort_options = {"author": "name"}
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
        self.m2m_filter_and_logic = True


@pytest.mark.django_db
def test_filterset_builds_choices():
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
    assert filterset is not None
    assert list(filterset.form.fields["author"].queryset.values_list("name", flat=True)) == ["Alan"]
    assert "genres" in filterset.filters
    assert filterset.filters["genres"].extra["queryset"].count() == 1
