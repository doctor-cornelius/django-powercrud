# src/powercrud/mixins/bulk_mixin/__init__.py
from .roles import BulkEditRole, BulkActions
from .selection_mixin import SelectionMixin
from .metadata_mixin import MetadataMixin
from .operation_mixin import OperationMixin
from .view_mixin import ViewMixin


class BulkMixin(
    SelectionMixin,
    MetadataMixin,
    OperationMixin,
    ViewMixin,
):
    """
    Composite BulkMixin for all bulk editing/deletion functionality.
    Order: Selection first (state), then metadata, operations, and views last (integration).
    """
    pass

__all__ = ["BulkMixin", "BulkEditRole", "BulkActions"]  # Export key symbols