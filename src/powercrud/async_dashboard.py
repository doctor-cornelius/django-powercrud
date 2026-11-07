"""PowerCRUD compatibility exports for optional lifecycle tracking."""

from powercrud.async_manager import AsyncManager
from powercrud._coordinator.tracking import AsyncDashboardConfig, ModelTrackingMixin


class ModelTrackingAsyncManager(ModelTrackingMixin, AsyncManager):
    """Public PowerCRUD manager retaining the established inheritance relation."""

    pass


__all__ = ["AsyncDashboardConfig", "ModelTrackingAsyncManager"]
