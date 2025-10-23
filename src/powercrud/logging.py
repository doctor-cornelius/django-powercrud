import logging

BASE_LOGGER_NAME = "powercrud"


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a namespaced logger for PowerCRUD.

    Args:
        name: Optional dotted path suffix (typically __name__).
    """
    if not name:
        return logging.getLogger(BASE_LOGGER_NAME)
    # Ensure child loggers share the base namespace for easy configuration
    return logging.getLogger(f"{BASE_LOGGER_NAME}.{name}")
