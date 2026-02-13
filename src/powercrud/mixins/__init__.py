from .htmx_mixin import HtmxMixin
from .bulk_mixin import BulkEditRole, BulkMixin
from .core_mixin import CoreMixin
from .filtering_mixin import (
    FilteringMixin,
    AllValuesModelMultipleChoiceFilter,
    HTMXFilterSetMixin,
)
from .table_mixin import TableMixin
from .form_mixin import FormMixin
from .inline_editing_mixin import InlineEditingMixin
from .url_mixin import UrlMixin
from .paginate_mixin import PaginateMixin


class PowerCRUDMixin(
    HtmxMixin,
    PaginateMixin,
    FormMixin,
    InlineEditingMixin,
    TableMixin,
    BulkMixin,
    FilteringMixin,
    CoreMixin,
    UrlMixin,
):
    """
    The main PowerCRUDMixin, composed of smaller, feature-focused mixins.
    The order of inheritance is important for Method Resolution Order (MRO).
    """

    pass


def __getattr__(name: str):
    """
    Provide lazy access to async-related mixins so importing powercrud.mixins
    does not eagerly load async dependencies. Async classes are only imported
    when explicitly requested.
    """
    if name == "AsyncMixin":
        from .async_mixin import AsyncMixin

        return AsyncMixin
    if name == "PowerCRUDAsyncMixin":
        from .async_crud_mixin import PowerCRUDAsyncMixin

        return PowerCRUDAsyncMixin
    raise AttributeError(f"module 'powercrud.mixins' has no attribute {name!r}")


__all__ = [
    "PowerCRUDMixin",
    "HTMXFilterSetMixin",
    "BulkEditRole",
    "InlineEditingMixin",
    "AsyncMixin",
    "PowerCRUDAsyncMixin",
]
