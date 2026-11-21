"""Typed configuration failures raised by explicit coordinator operations."""

from django.core.exceptions import ImproperlyConfigured


class AsyncConfigurationError(ImproperlyConfigured):
    """An explicit async operation cannot run with the current configuration."""


class AsyncDisabledError(AsyncConfigurationError):
    """A new async launch was requested while launches are disabled."""


class DescendantConflictError(Exception):
    """A descendant could not join its parent's protected work set."""


class SubmissionError(Exception):
    """A launch could not confirm submission of the specified logical task."""

    def __init__(self, task_key: str, message: str):
        """Keep the task key available to callers that can display progress."""
        super().__init__(message)
        self.task_key = task_key


class SubmissionRejected(SubmissionError):
    """Preparation failed before either broker delivery or inline execution."""


class SubmissionUncertain(SubmissionError):
    """The submission boundary could not establish whether work was delivered."""
