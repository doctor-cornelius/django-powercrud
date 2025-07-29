from .htmx_mixin import HtmxMixin
from .async_mixin import AsyncMixin
from .bulk_mixin import BulkEditRole, BulkMixin
from .core_mixin import CoreMixin
from .filtering_mixin import FilteringMixin, AllValuesModelMultipleChoiceFilter, HTMXFilterSetMixin
from .table_mixin import TableMixin
from .form_mixin import FormMixin
from .url_mixin import UrlMixin
from .paginate_mixin import PaginateMixin


class PowerCRUDMixin(
    HtmxMixin, 
    PaginateMixin, 
    FormMixin, 
    TableMixin, 
    AsyncMixin, 
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


__all__ = [
    "PowerCRUDMixin",
    "HTMXFilterSetMixin",
    "BulkEditRole",
]