"""Manager classes available to coordinator reconstruction tests."""

from powercrud.async_manager import AsyncManager


class CoordinatorAsyncManager(AsyncManager):
    """Importable manager stand-in for generic completion-hook tests."""

    pass
