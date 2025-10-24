from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional

from django.db import models

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from .async_manager import AsyncManager
from powercrud.logging import get_logger

log = get_logger(__name__)


FieldFormatter = Callable[[Any], Any]


@dataclass(frozen=True)
class AsyncDashboardConfig:
    """Configuration payload for ModelTrackingAsyncManager."""

    record_model_path: str
    field_map: Mapping[str, str] = field(default_factory=dict)
    create_defaults: Mapping[str, Any] = field(default_factory=dict)
    format_user: Optional[FieldFormatter] = None
    format_affected: Optional[FieldFormatter] = None
    format_payload: Optional[FieldFormatter] = None

    def resolve_field(self, logical_name: str, default: Optional[str]) -> Optional[str]:
        """Return configured field name or provided default."""
        if logical_name in self.field_map:
            return self.field_map[logical_name]
        return default


class ModelTrackingAsyncManager(AsyncManager):
    """Concrete AsyncManager that persists lifecycle events to a configured model.

    Downstream projects can supply a config at construction time or override
    the class attributes `record_model_path`, `field_map`, or formatter
    helpers. Only the `task_name` field is required on the target model;
    all other fields are optional and will be skipped if not mapped.
    """

    record_model_path: Optional[str] = None
    field_map: Mapping[str, str] = {}
    create_defaults: Mapping[str, Any] = {}

    def __init__(self, config: Optional[AsyncDashboardConfig] = None):
        super().__init__()
        self._config = config or AsyncDashboardConfig(
            record_model_path=self.get_record_model_path(),
            field_map=self.field_map,
            create_defaults=self.create_defaults,
        )
        self._record_model = self._resolve_model(self._config.record_model_path)

    # --------------------------------------------------------------------- #
    # Configuration helpers
    # --------------------------------------------------------------------- #
    def get_record_model_path(self) -> str:
        if not self.record_model_path:
            raise ImproperlyConfigured(
                "ModelTrackingAsyncManager requires 'record_model_path' to be set "
                "or provided via AsyncDashboardConfig."
            )
        return self.record_model_path

    @staticmethod
    def _resolve_model(model_path: str):
        try:
            return apps.get_model(model_path)
        except Exception as exc:  # pragma: no cover - guard clause
            raise ImproperlyConfigured(
                f"Async dashboard model '{model_path}' could not be resolved"
            ) from exc

    def _field(self, logical_name: str, default: Optional[str]) -> Optional[str]:
        return self._config.resolve_field(logical_name, default)

    # --------------------------------------------------------------------- #
    # Formatting hooks
    # --------------------------------------------------------------------- #
    def format_user(self, user: Any) -> Any:
        if self._config.format_user:
            return self._config.format_user(user)
        if not user:
            return ""
        if hasattr(user, "get_username"):
            return user.get_username()
        if hasattr(user, "username"):
            return str(user.username)
        return str(user)

    def format_affected(self, affected_objects: Any) -> Any:
        formatter = self._config.format_affected
        if formatter:
            return formatter(affected_objects)
        if not affected_objects:
            return ""
        if isinstance(affected_objects, (list, tuple, set)):
            return ", ".join(str(obj) for obj in affected_objects)
        return str(affected_objects)

    def format_payload(self, payload: Any) -> Any:
        formatter = self._config.format_payload
        if formatter:
            return formatter(payload)
        if payload is None:
            return None
        try:
            return json.loads(json.dumps(payload, default=str))
        except TypeError:
            return str(payload)

    def _prepare_field_value(self, field_name: str, value: Any) -> Any:
        if value is None:
            return None

        try:
            field = self._record_model._meta.get_field(field_name)
        except Exception:
            return value

        if isinstance(field, models.JSONField):
            return value

        if isinstance(field, (models.TextField, models.CharField)):
            if isinstance(value, str):
                return value
            try:
                return json.dumps(value, default=str)
            except TypeError:
                return str(value)

        return value

    # --------------------------------------------------------------------- #
    # Core lifecycle implementation
    # --------------------------------------------------------------------- #
    def _get_or_create_record(self, task_name: str, defaults: Mapping[str, Any]):
        task_field = self._field("task_name", "task_name")
        if not task_field:
            raise ImproperlyConfigured(
                "ModelTrackingAsyncManager requires a 'task_name' field mapping."
            )
        lookup = {task_field: task_name}
        combined_defaults: MutableMapping[str, Any] = {}
        combined_defaults.update(self._config.create_defaults)
        combined_defaults.update(defaults)
        return self._record_model.objects.get_or_create(
            defaults=combined_defaults,
            **lookup,
        )

    def _maybe_set(self, record, field_name: Optional[str], value: Any, updated_fields: set[str]):
        if field_name and value is not None:
            prepared = self._prepare_field_value(field_name, value)
            setattr(record, field_name, prepared)
            updated_fields.add(field_name)

    def async_task_lifecycle(self, event: str, task_name: str, **kwargs):
        status_field = self._field("status", "status")
        message_field = self._field("message", "message")
        progress_field = self._field("progress", "progress_payload")
        user_field = self._field("user", "user_label")
        affected_field = self._field("affected", "affected_objects")
        kwargs_field = self._field("kwargs", "task_kwargs")
        args_field = self._field("args", "task_args")
        result_field = self._field("result", "result_payload")
        cleaned_field = self._field("cleaned", "cleaned_up")
        completed_at_field = self._field("completed_at", "completed_at")
        failed_at_field = self._field("failed_at", "failed_at")

        incoming_status = kwargs.get("status")
        message = kwargs.get("message")
        timestamp = kwargs.get("timestamp")

        defaults: Dict[str, Any] = {}
        if status_field and incoming_status is not None:
            defaults[status_field] = self._prepare_field_value(status_field, incoming_status)
        if message_field and message:
            defaults[message_field] = self._prepare_field_value(message_field, message)
        if user_field:
            user_val = kwargs.get("user")
            if user_val is not None:
                defaults[user_field] = self._prepare_field_value(user_field, self.format_user(user_val))
        if affected_field:
            affected_val = kwargs.get("affected_objects")
            if affected_val is not None:
                defaults[affected_field] = self._prepare_field_value(affected_field, self.format_affected(affected_val))
        if kwargs_field:
            kw_payload = kwargs.get("task_kwargs")
            if kw_payload is not None:
                defaults[kwargs_field] = self._prepare_field_value(kwargs_field, self.format_payload(kw_payload))
        if args_field:
            args_payload = kwargs.get("task_args")
            if args_payload is not None:
                defaults[args_field] = self._prepare_field_value(args_field, self.format_payload(args_payload))

        record, created = self._get_or_create_record(task_name, defaults)

        updated_fields: set[str] = set()

        if not created:
            if status_field and incoming_status is not None:
                self._maybe_set(record, status_field, incoming_status, updated_fields)
            if message_field and message and event != "progress":
                self._maybe_set(record, message_field, message, updated_fields)

        if event == "create":
            # ensure create preserves user + affected when record exists
            if user_field:
                self._maybe_set(
                    record,
                    user_field,
                    self.format_user(kwargs.get("user")),
                    updated_fields,
                )
            if affected_field:
                self._maybe_set(
                    record,
                    affected_field,
                    self.format_affected(kwargs.get("affected_objects")),
                    updated_fields,
                )
            if kwargs_field:
                self._maybe_set(
                    record,
                    kwargs_field,
                    self.format_payload(kwargs.get("task_kwargs")),
                    updated_fields,
                )
            if args_field:
                self._maybe_set(
                    record,
                    args_field,
                    self.format_payload(kwargs.get("task_args")),
                    updated_fields,
                )

        elif event == "progress":
            if status_field:
                setattr(record, status_field, self.STATUSES.IN_PROGRESS)
                updated_fields.add(status_field)
            progress_payload = kwargs.get("progress_payload") or message
            if progress_field and progress_payload is not None:
                setattr(record, progress_field, progress_payload)
                updated_fields.add(progress_field)

        elif event == "complete":
            if status_field:
                setattr(record, status_field, self.STATUSES.SUCCESS)
                updated_fields.add(status_field)
            if result_field:
                self._maybe_set(
                    record,
                    result_field,
                    self.format_payload(kwargs.get("result")),
                    updated_fields,
                )
            if completed_at_field and timestamp:
                self._maybe_set(record, completed_at_field, timestamp, updated_fields)

        elif event == "fail":
            if status_field:
                setattr(record, status_field, self.STATUSES.FAILED)
                updated_fields.add(status_field)
            if result_field:
                self._maybe_set(
                    record,
                    result_field,
                    self.format_payload(kwargs.get("result")),
                    updated_fields,
                )
            if failed_at_field and timestamp:
                self._maybe_set(record, failed_at_field, timestamp, updated_fields)

        elif event == "cleanup":
            if cleaned_field:
                self._maybe_set(record, cleaned_field, True, updated_fields)

        if updated_fields:
            record.save(update_fields=sorted(updated_fields))
        elif created:
            # Newly created records with no extra updates still need persistence.
            record.save()
