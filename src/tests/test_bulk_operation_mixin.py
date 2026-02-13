from __future__ import annotations

import contextlib
from types import SimpleNamespace

import pytest
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from powercrud.mixins.bulk_mixin.operation_mixin import OperationMixin
from sample.models import Author, Book, Genre


class OperationHarness(OperationMixin):
    """Lightweight concrete class so we can exercise OperationMixin directly."""

    bulk_delete = True
    use_modal = True
    use_htmx = True


class DummyQueryset(list):
    def count(self):
        return len(self)


@pytest.fixture
def noop_atomic(monkeypatch):
    def fake_atomic(*args, **kwargs):
        return contextlib.nullcontext()

    monkeypatch.setattr(
        "powercrud.mixins.bulk_mixin.operation_mixin.transaction.atomic",
        fake_atomic,
    )


def test_perform_bulk_delete_handles_missing_records(noop_atomic):
    deleted = []

    def delete_ok():
        deleted.append("ok")

    def delete_missing():
        raise ObjectDoesNotExist("already gone")

    queryset = DummyQueryset(
        [
            SimpleNamespace(pk=1, delete=delete_ok),
            SimpleNamespace(pk=2, delete=delete_missing),
        ]
    )

    mixin = OperationHarness()
    progress = []
    result = mixin._perform_bulk_delete(
        queryset,
        progress_callback=lambda current, total: progress.append((current, total)),
    )

    assert result["success"] is True
    assert result["success_records"] == 1
    assert result["errors"] == []
    # both objects should have triggered the progress callback
    assert progress == [(1, 2), (2, 2)]
    assert deleted == ["ok"]


def test_perform_bulk_delete_collects_errors(noop_atomic):
    def delete_boom():
        raise RuntimeError("explode")

    queryset = DummyQueryset([SimpleNamespace(pk=99, delete=delete_boom)])

    mixin = OperationHarness()
    result = mixin._perform_bulk_delete(queryset)

    assert result["success"] is False
    assert result["success_records"] == 0
    assert result["errors"][0][1][0].startswith("explode")


@pytest.mark.django_db
def test_perform_bulk_update_mutates_boolean_fk_and_m2m(noop_atomic):

    author_a = Author.objects.create(name="Alpha")
    author_b = Author.objects.create(name="Beta")
    genre_one = Genre.objects.create(name="Sci-Fi")
    genre_two = Genre.objects.create(name="Fantasy")
    book = Book.objects.create(
        title="Example",
        author=author_a,
        bestseller=False,
        published_date="2024-01-01",
        isbn="1111111111111",
        pages=10,
    )
    book.genres.set([genre_one])

    class BulkUpdateHarness(OperationHarness):
        bulk_fields = ["bestseller", "author", "genres"]

        def __init__(self):
            # attribute used when coercing dropdown sorting in metadata mixin
            self.dropdown_sort_options = {"author": "name"}

    harness = BulkUpdateHarness()

    queryset = Book.objects.filter(pk=book.pk)

    field_data = [
        {
            "field": "bestseller",
            "value": "true",
            "info": {
                "type": "BooleanField",
                "is_relation": False,
                "is_m2m": False,
                "field": Book._meta.get_field("bestseller"),
            },
        },
        {
            "field": "author",
            "value": str(author_b.pk),
            "info": {
                "type": "ForeignKey",
                "is_relation": True,
                "is_m2m": False,
                "field": Book._meta.get_field("author"),
                "verbose_name": "author",
            },
        },
        {
            "field": "genres",
            "value": None,
            "info": {
                "type": "ManyToManyField",
                "is_relation": True,
                "is_m2m": True,
                "field": Book._meta.get_field("genres"),
            },
            "m2m_action": "set",
            "m2m_values": [genre_one.pk, genre_two.pk],
        },
    ]

    progress: list[tuple[int, int]] = []
    result = harness._perform_bulk_update(
        queryset,
        bulk_fields=["bestseller", "author", "genres"],
        fields_to_update=["bestseller", "author", "genres"],
        field_data=field_data,
        progress_callback=lambda current, total: progress.append((current, total)),
    )

    book.refresh_from_db()

    assert result["success"] is True
    assert result["success_records"] == 1
    assert progress == [(1, 1)]
    assert book.bestseller is True
    assert book.author == author_b
    assert list(book.genres.order_by("name").values_list("name", flat=True)) == [
        "Fantasy",
        "Sci-Fi",
    ]


@pytest.mark.django_db
def test_perform_bulk_update_returns_validation_errors(monkeypatch, noop_atomic):

    author = Author.objects.create(name="Alpha")
    book = Book.objects.create(
        title="Broken",
        author=author,
        bestseller=False,
        published_date="2024-01-01",
        isbn="2222222222222",
        pages=5,
    )

    queryset = Book.objects.filter(pk=book.pk)

    field_data = [
        {
            "field": "title",
            "value": "Updated",
            "info": {
                "type": "CharField",
                "is_relation": False,
                "is_m2m": False,
                "field": Book._meta.get_field("title"),
                "verbose_name": "title",
            },
        }
    ]

    def failing_full_clean(self):
        raise ValidationError({"title": ["invalid state"]})

    monkeypatch.setattr(Book, "full_clean", failing_full_clean, raising=False)

    harness = OperationHarness()
    errors = harness._perform_bulk_update(
        queryset,
        bulk_fields=["title"],
        fields_to_update=["title"],
        field_data=field_data,
    )

    assert errors["success"] is False
    assert errors["success_records"] == 0
    assert errors["errors"] == [("title", ["invalid state"])]
