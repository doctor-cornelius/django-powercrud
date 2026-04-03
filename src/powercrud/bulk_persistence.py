"""Worker-safe bulk update persistence backends.

This module provides a small public contract for routing bulk update writes
through an importable backend class instead of a request-scoped view instance.
The contract is intentionally focused on update persistence only; delete
operations remain separate follow-up work.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from django.db import models

from powercrud.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True)
class BulkUpdateExecutionContext:
    """Plain-data context passed to bulk update persistence backends.

    Attributes:
        mode: Execution surface using the backend, currently ``"sync"`` or
            ``"async"``.
        model_path: Optional ``app_label.ModelName`` string for the model being
            updated.
        selected_ids: Selected object primary keys for the operation.
        user_id: Optional initiating user primary key.
        task_name: Optional async task identifier.
        manager_class_path: Optional async manager class path for async workers.
    """

    mode: str
    model_path: str | None = None
    selected_ids: tuple[Any, ...] = ()
    user_id: int | None = None
    task_name: str | None = None
    manager_class_path: str | None = None


class BulkUpdatePersistenceBackend:
    """Base class for worker-safe bulk update persistence backends."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Store optional backend configuration.

        Args:
            config: Optional backend-specific configuration payload.
        """
        self.config = config or {}

    def persist_bulk_update(
        self,
        *,
        queryset: models.QuerySet,
        bulk_fields: List[str],
        fields_to_update: List[str],
        field_data: List[Dict[str, Any]],
        context: BulkUpdateExecutionContext,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Persist a bulk update operation.

        Subclasses must implement this method and return the standard PowerCRUD
        bulk result contract.
        """
        raise NotImplementedError(
            "BulkUpdatePersistenceBackend.persist_bulk_update() must be implemented."
        )


class DefaultBulkUpdatePersistenceBackend(BulkUpdatePersistenceBackend):
    """Default backend that preserves PowerCRUD's existing bulk update behavior."""

    def persist_bulk_update(
        self,
        *,
        queryset: models.QuerySet,
        bulk_fields: List[str],
        fields_to_update: List[str],
        field_data: List[Dict[str, Any]],
        context: BulkUpdateExecutionContext,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Run the built-in bulk update implementation unchanged.

        Args:
            queryset: Objects selected for the update.
            bulk_fields: Configured allowed bulk-edit field names.
            fields_to_update: Field names requested for this operation.
            field_data: Normalized bulk field payload.
            context: Plain execution context for this operation.
            progress_callback: Optional progress callback.

        Returns:
            Dict matching PowerCRUD's standard bulk result contract.
        """
        del context
        from powercrud.mixins.bulk_mixin import BulkMixin

        mixin = BulkMixin()
        return mixin._perform_bulk_update(
            queryset,
            bulk_fields=bulk_fields,
            fields_to_update=fields_to_update,
            field_data=field_data,
            progress_callback=progress_callback,
        )


def resolve_bulk_update_persistence_backend(
    backend_path: str | None,
    *,
    config: dict[str, Any] | None = None,
) -> BulkUpdatePersistenceBackend:
    """Resolve a configured bulk update persistence backend.

    Args:
        backend_path: Import path for a backend class. When unset, the default
            PowerCRUD backend is returned.
        config: Optional backend-specific configuration payload.

    Returns:
        Resolved backend instance.

    Raises:
        ImportError: If the module or attribute cannot be imported.
        TypeError: If the resolved object is not a backend subclass.
    """
    if not backend_path:
        return DefaultBulkUpdatePersistenceBackend(config=config)

    module_path, class_name = backend_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    backend_cls = getattr(module, class_name)
    if not isinstance(backend_cls, type) or not issubclass(
        backend_cls, BulkUpdatePersistenceBackend
    ):
        raise TypeError(
            f"Bulk update persistence backend '{backend_path}' must subclass "
            "BulkUpdatePersistenceBackend."
        )

    log.debug("Resolving bulk update persistence backend '%s'", backend_path)
    return backend_cls(config=config)
