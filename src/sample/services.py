"""Tutorial-oriented sample services for persistence hook documentation.

These helpers are intentionally small and explicit. They exist so the advanced
tutorials can point at real, importable example code without changing the
default sample app behavior.
"""

from __future__ import annotations

from typing import Any, Callable

from django.db.models import QuerySet

from powercrud.bulk_persistence import (
    BulkUpdateExecutionContext,
    DefaultBulkUpdatePersistenceBackend,
)
from sample.models import Book


class BookWriteService:
    """Small write service used by the persistence hook tutorials.

    The service keeps the example focused on the boundary between validated
    forms and app-owned write orchestration. It deliberately does not try to
    model a complex domain service.
    """

    def save_book(self, *, form, mode: str):
        """Save a validated book form and handle many-to-many persistence.

        Args:
            form: Validated ``BookForm`` instance.
            mode: Surface that triggered the save, such as ``"form"`` or
                ``"inline"``.

        Returns:
            The saved ``Book`` instance.
        """
        del mode
        book = form.save(commit=False)
        book.save()
        form.save_m2m()
        return book


class BookBulkUpdateService:
    """Small bulk-update service used by the advanced persistence tutorials.

    This service deliberately delegates to PowerCRUD's built-in bulk update
    backend so the tutorials can focus on wiring and extension seams rather
    than reimplementing the default update algorithm. It also includes one
    narrow sample validation rule so the docs can point at a real handled
    bulk-error path.
    """

    def _validate_demo_bulk_update(
        self,
        *,
        queryset: QuerySet,
        fields_to_update: list[str],
        field_data: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Return a handled bulk error payload for the tutorial demo rule.

        The sample app uses a deliberately small rule: if a selected book is
        named ``Bulk Validation Sample Book`` and the current bulk operation
        tries to set ``bestseller`` to ``true``, the service returns the normal
        PowerCRUD bulk error payload instead of delegating the write.
        """
        if "bestseller" not in fields_to_update:
            return None

        submitted_bestseller = None
        for item in field_data:
            if item.get("field") == "bestseller":
                submitted_bestseller = item.get("value")
                break

        if submitted_bestseller != "true":
            return None

        guarded_titles = list(
            queryset.filter(title=Book.BULK_VALIDATION_SAMPLE_TITLE).values_list(
                "title",
                flat=True,
            )
        )
        if not guarded_titles:
            return None

        return {
            "success": False,
            "success_records": 0,
            "errors": [
                (
                    "bestseller",
                    [
                        (
                            "Bulk Validation Sample Book refuses bulk bestseller "
                            "promotion to demonstrate handled validation errors."
                        )
                    ],
                )
            ],
        }

    def apply(
        self,
        *,
        queryset: QuerySet,
        bulk_fields: list[str],
        fields_to_update: list[str],
        field_data: list[dict[str, Any]],
        context: BulkUpdateExecutionContext,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Apply a bulk update using PowerCRUD's default update behavior.

        Args:
            queryset: Objects selected for update.
            bulk_fields: Configured allow-list of bulk-editable fields.
            fields_to_update: Requested fields for the current operation.
            field_data: Normalized bulk payload built from the request.
            context: Execution metadata describing sync or async mode.
            progress_callback: Optional progress callback.

        Returns:
            Standard PowerCRUD bulk result payload.
        """
        demo_error = self._validate_demo_bulk_update(
            queryset=queryset,
            fields_to_update=fields_to_update,
            field_data=field_data,
        )
        if demo_error is not None:
            return demo_error

        backend = DefaultBulkUpdatePersistenceBackend()
        return backend.persist_bulk_update(
            queryset=queryset,
            bulk_fields=bulk_fields,
            fields_to_update=fields_to_update,
            field_data=field_data,
            context=context,
            progress_callback=progress_callback,
        )
