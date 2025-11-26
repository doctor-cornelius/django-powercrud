from .async_mixin import AsyncMixin
from . import PowerCRUDMixin


class PowerCRUDAsyncMixin(AsyncMixin, PowerCRUDMixin):
    """
    Convenience composite mixin that layers async bulk support on top of the
    standard PowerCRUDMixin. Downstream views that require async behaviour
    should inherit from this (or include AsyncMixin explicitly) and ensure
    django-q2 / Q_CLUSTER are configured.
    """
    pass


__all__ = ["PowerCRUDAsyncMixin"]

