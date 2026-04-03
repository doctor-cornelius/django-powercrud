"""Tutorial-oriented sample backends for persistence hook documentation.

These helpers demonstrate the async-safe bulk update backend contract using
the sample book domain. They exist to support the advanced docs tutorials.
"""

from __future__ import annotations

from typing import Any, Callable

from django.db.models import QuerySet

from powercrud.bulk_persistence import (
    BulkUpdateExecutionContext,
    BulkUpdatePersistenceBackend,
)

from .services import BookBulkUpdateService


class BookBulkUpdateBackend(BulkUpdatePersistenceBackend):
    """Worker-safe sample backend used by the advanced persistence tutorials."""

    def persist_bulk_update(
        self,
        *,
        queryset: QuerySet,
        bulk_fields: list[str],
        fields_to_update: list[str],
        field_data: list[dict[str, Any]],
        context: BulkUpdateExecutionContext,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Delegate bulk update persistence to the sample bulk service.

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
        return BookBulkUpdateService().apply(
            queryset=queryset,
            bulk_fields=bulk_fields,
            fields_to_update=fields_to_update,
            field_data=field_data,
            context=context,
            progress_callback=progress_callback,
        )
