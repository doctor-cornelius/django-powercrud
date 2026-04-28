from __future__ import annotations

import contextlib
from types import SimpleNamespace

import pytest
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from powercrud.bulk_persistence import BulkUpdatePersistenceBackend
from powercrud.mixins.bulk_mixin.operation_mixin import OperationMixin
from sample.models import Author, Book, Genre


class OperationHarness(OperationMixin):
    """Lightweight concrete class so we can exercise OperationMixin directly."""

    bulk_delete = True
    use_modal = True
    use_htmx = True
    bulk_fields = ["title", "author"]


class DummyQueryset(list):
    def count(self):
        return len(self)

    def values_list(self, field_name, flat=False):
        """Return field values to emulate QuerySet.values_list()."""
        return [getattr(obj, field_name) for obj in self]


class RecordingBulkUpdateBackend(BulkUpdatePersistenceBackend):
    """Test backend that records sync bulk update delegation."""

    calls: list[dict] = []

    def persist_bulk_update(
        self,
        *,
        queryset,
        bulk_fields,
        fields_to_update,
        field_data,
        context,
        progress_callback=None,
    ):
        """Record the delegated payload and return a success result."""
        del progress_callback
        self.__class__.calls.append(
            {
                "config": self.config,
                "queryset": queryset,
                "bulk_fields": bulk_fields,
                "fields_to_update": fields_to_update,
                "field_data": field_data,
                "context": context,
            }
        )
        return {
            "success": True,
            "success_records": len(queryset),
            "errors": [],
        }


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


def test_persist_bulk_update_delegates_to_default_operation(monkeypatch):
    mixin = OperationHarness()
    queryset = DummyQueryset([])
    field_data = [{"field": "title", "value": "Updated", "info": {}}]
    captured = {}

    class FakeBackend:
        def persist_bulk_update(
            self,
            *,
            queryset,
            bulk_fields,
            fields_to_update,
            field_data,
            context,
            progress_callback=None,
        ):
            captured["queryset"] = queryset
            captured["bulk_fields"] = bulk_fields
            captured["fields_to_update"] = fields_to_update
            captured["field_data"] = field_data
            captured["progress_callback"] = progress_callback
            captured["context"] = context
            return {"success": True, "success_records": 0, "errors": []}

    monkeypatch.setattr(
        "powercrud.mixins.bulk_mixin.operation_mixin.resolve_bulk_update_persistence_backend",
        lambda backend_path, config=None: FakeBackend(),
    )

    result = mixin.persist_bulk_update(
        queryset=queryset,
        fields_to_update=["title"],
        field_data=field_data,
        progress_callback=None,
    )

    assert result == {"success": True, "success_records": 0, "errors": []}, (
        "persist_bulk_update should return the default bulk operation result payload."
    )
    assert captured["queryset"] is queryset, (
        "persist_bulk_update should forward the queryset unchanged to the default bulk operation."
    )
    assert captured["bulk_fields"] == ["title", "author"], (
        "persist_bulk_update should validate against the configured bulk_fields by default."
    )
    assert captured["fields_to_update"] == ["title"], (
        "persist_bulk_update should forward the selected bulk field names unchanged."
    )
    assert captured["field_data"] == field_data, (
        "persist_bulk_update should forward the normalized field_data payload unchanged."
    )
    assert captured["context"].mode == "sync", (
        "The default bulk persistence backend should receive sync execution context from persist_bulk_update."
    )


def test_persist_bulk_update_uses_configured_backend():
    mixin = OperationHarness()
    mixin.bulk_update_persistence_backend_path = (
        "tests.test_bulk_operation_mixin.RecordingBulkUpdateBackend"
    )
    mixin.bulk_update_persistence_backend_config = {"revalidate": True}
    queryset = DummyQueryset([SimpleNamespace(pk=1)])
    field_data = [{"field": "title", "value": "Updated", "info": {}}]
    RecordingBulkUpdateBackend.calls.clear()

    result = mixin.persist_bulk_update(
        queryset=queryset,
        fields_to_update=["title"],
        field_data=field_data,
        progress_callback=None,
    )

    assert result == {"success": True, "success_records": 1, "errors": []}, (
        "Configured bulk persistence backends should be able to replace the default sync bulk update behavior."
    )
    assert len(RecordingBulkUpdateBackend.calls) == 1, (
        "persist_bulk_update should delegate to the configured bulk persistence backend exactly once."
    )
    call = RecordingBulkUpdateBackend.calls[0]
    assert call["config"] == {"revalidate": True}, (
        "Configured backend instances should receive the declared backend config."
    )
    assert call["bulk_fields"] == ["title", "author"], (
        "Configured bulk persistence backends should still receive the resolved bulk_fields allow-list."
    )
    assert call["fields_to_update"] == ["title"], (
        "Configured bulk persistence backends should receive the selected fields_to_update list unchanged."
    )
    assert call["field_data"] == field_data, (
        "Configured bulk persistence backends should receive the normalized field_data payload unchanged."
    )
    assert call["context"].mode == "sync", (
        "Sync bulk persistence backends should receive execution context marking the operation as sync."
    )
    assert call["context"].selected_ids == (1,), (
        "Sync bulk persistence backends should receive the selected primary keys in the execution context."
    )


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
    """Return structured validation errors from failed bulk updates."""

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


def test_perform_bulk_update_normalizes_nullable_choice_null_sentinel(noop_atomic):
    """Convert nullable choice-field clear sentinels to None before saving."""
    obj = SimpleNamespace(
        pk=1,
        status="legacy",
        full_clean=lambda: None,
        save=lambda: None,
    )
    queryset = DummyQueryset([obj])
    harness = OperationHarness()
    result = harness._perform_bulk_update(
        queryset,
        bulk_fields=["status"],
        fields_to_update=["status"],
        field_data=[
            {
                "field": "status",
                "value": "null",
                "info": {
                    "type": "CharField",
                    "is_relation": False,
                    "is_m2m": False,
                    "field": SimpleNamespace(),
                    "verbose_name": "status",
                    "choices": [("legacy", "Legacy")],
                    "null": True,
                    "blank": True,
                },
            }
        ],
    )

    assert result["success"] is True, (
        "Bulk updates should accept the null sentinel for nullable choice fields."
    )
    assert obj.status is None, (
        "Nullable choice field null sentinels should be persisted as None."
    )


@pytest.mark.django_db
def test_perform_bulk_update_rejects_fields_outside_bulk_fields(noop_atomic):
    author = Author.objects.create(name="Alpha")
    book = Book.objects.create(
        title="Guarded",
        author=author,
        bestseller=False,
        published_date="2024-01-01",
        isbn="2323232323232",
        pages=7,
    )

    queryset = Book.objects.filter(pk=book.pk)
    harness = OperationHarness()
    errors = harness._perform_bulk_update(
        queryset,
        bulk_fields=["author"],
        fields_to_update=["title"],
        field_data=[
            {
                "field": "title",
                "value": "Tampered",
                "info": {
                    "type": "CharField",
                    "is_relation": False,
                    "is_m2m": False,
                    "field": Book._meta.get_field("title"),
                    "verbose_name": "title",
                },
            }
        ],
    )

    assert errors["success"] is False
    assert errors["success_records"] == 0
    assert errors["errors"] == [
        ("general", ["Bulk edit request contained invalid fields: title."])
    ], "The operation layer should reject fields_to_update entries that are outside the configured bulk_fields list."
