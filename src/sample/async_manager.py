from __future__ import annotations

from typing import Any

from powercrud.async_dashboard import ModelTrackingAsyncManager
class SampleAsyncManager(ModelTrackingAsyncManager):
    """Sample app manager that reuses the base dashboard implementation."""

    record_model_path = "sample.AsyncTaskRecord"

    def format_user(self, user: Any) -> str:
        if not user:
            return "Anonymous"

        try:
            if hasattr(user, "is_anonymous") and user.is_anonymous:
                return "Anonymous"

            if hasattr(user, "get_username"):
                label = user.get_username()
                if label:
                    return label

            if hasattr(user, "username"):
                label = str(user.username)
                if label:
                    return label
        except Exception:
            pass

        return str(user) or "Anonymous"

    def format_affected(self, affected_objects: Any) -> str:
        if not affected_objects:
            return ""
        if isinstance(affected_objects, (list, tuple, set)):
            return ", ".join(str(obj) for obj in affected_objects)
        return str(affected_objects)
