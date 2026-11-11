from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional

from django.db import models
from django.db import transaction

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from .manager import AsyncManager

import logging

log = logging.getLogger(__name__)


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


class ModelTrackingMixin:
    """Persist coordinator lifecycle events to an application-selected model.

    Downstream projects can supply a config at construction time or override
    the class attributes `record_model_path`, `field_map`, or formatter
    helpers. Only the `task_name` field is required on the target model;
    all other fields are optional and will be skipped if not mapped.
    """

    record_model_path: Optional[str] = None
    field_map: Mapping[str, str] = {}
    create_defaults: Mapping[str, Any] = {}

    def __init__(self, config: Optional[AsyncDashboardConfig] = None, *, coordination_config=None, executor=None):
        """Initialize tracking and continue the manager constructor chain once."""
        super().__init__(coordination_config=coordination_config, executor=executor)
        self._factory_manager_config = config
        self._config = config or AsyncDashboardConfig(
            record_model_path=self.get_record_model_path(),
            field_map=self.field_map,
            create_defaults=self.create_defaults,
        )
        self._record_model = self._resolve_model(self._config.record_model_path)

    @classmethod
    def prepare_manager_config(cls, config):
        """Convert legacy mapping configuration for tracking managers."""
        if isinstance(config, dict):
            return AsyncDashboardConfig(**config)
        return config

    def export_manager_config(self):
        """Export the effective tracking configuration."""
        return self._config

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

    def _maybe_set(
        self, record, field_name: Optional[str], value: Any, updated_fields: set[str]
    ):
        if field_name and value is not None:
            prepared = self._prepare_field_value(field_name, value)
            setattr(record, field_name, prepared)
            updated_fields.add(field_name)

    def async_task_lifecycle(self, event: str, task_name: str, **kwargs):
        """Persist lifecycle data without allowing stale events to undo outcomes."""
        try:
            observation = self.get_task_observation(task_name, cache_only=True)
        except Exception:
            observation = {"terminal": False}
        if observation.get("terminal"):
            kwargs = dict(kwargs)
            kwargs.update(
                status=observation["status"],
                result=observation["details"],
                timestamp=observation["finished_at"],
                canonical_terminal=True,
            )
            if event in {"create", "progress"}:
                event = "terminal_repair"

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

        task_name_field = self._field("task_name", "task_name")
        if not task_name_field:
            raise ImproperlyConfigured("ModelTrackingAsyncManager requires a task_name field mapping.")
        using = self._record_model.objects.db
        lookup = {task_name_field: task_name}
        defaults = dict(self._config.create_defaults)
        if status_field and incoming_status is not None:
            defaults[status_field] = self._prepare_field_value(status_field, incoming_status)

        metadata = {}
        if message_field and message and event != "progress":
            metadata[message_field] = self._prepare_field_value(message_field, message)
        if user_field and "user" in kwargs and (kwargs.get("user") is not None or event == "create"):
            metadata[user_field] = self._prepare_field_value(user_field, self.format_user(kwargs.get("user")))
        if affected_field and kwargs.get("affected_objects") is not None:
            metadata[affected_field] = self._prepare_field_value(affected_field, self.format_affected(kwargs["affected_objects"]))
        if kwargs_field and kwargs.get("task_kwargs") is not None:
            metadata[kwargs_field] = self._prepare_field_value(kwargs_field, self.format_payload(kwargs["task_kwargs"]))
        if args_field and kwargs.get("task_args") is not None:
            metadata[args_field] = self._prepare_field_value(args_field, self.format_payload(kwargs["task_args"]))
        defaults.update(metadata)

        with transaction.atomic(using=using):
            self._record_model.objects.using(using).get_or_create(defaults=defaults, **lookup)
            record = self._record_model.objects.using(using).select_for_update().get(**lookup)
            current_status = getattr(record, status_field, None) if status_field else None
            terminal = current_status in {self.STATUSES.SUCCESS, self.STATUSES.FAILED}
            updates = dict(metadata)

            if event == "progress":
                progress_payload = kwargs.get("progress_payload") or message
                if progress_field and progress_payload is not None:
                    updates[progress_field] = self._prepare_field_value(progress_field, progress_payload)
                next_status = self.STATUSES.IN_PROGRESS
            elif event == "create":
                next_status = incoming_status
            elif event in {"complete", "fail"}:
                next_status = incoming_status or (self.STATUSES.SUCCESS if event == "complete" else self.STATUSES.FAILED)
                if next_status not in {self.STATUSES.SUCCESS, self.STATUSES.FAILED}:
                    next_status = self.STATUSES.UNKNOWN
                if result_field and kwargs.get("result") is not None:
                    updates[result_field] = self._prepare_field_value(result_field, self.format_payload(kwargs.get("result")))
                terminal_time_field = completed_at_field if next_status == self.STATUSES.SUCCESS else failed_at_field
                if terminal_time_field and timestamp:
                    updates[terminal_time_field] = timestamp
            elif event == "cleanup" and kwargs.get("canonical_terminal"):
                next_status = incoming_status
                if result_field and kwargs.get("result") is not None:
                    updates[result_field] = self._prepare_field_value(result_field, self.format_payload(kwargs.get("result")))
                terminal_time_field = completed_at_field if next_status == self.STATUSES.SUCCESS else failed_at_field
                if terminal_time_field and timestamp:
                    updates[terminal_time_field] = timestamp
            elif event == "terminal_repair":
                next_status = incoming_status
                if result_field and kwargs.get("result") is not None:
                    updates[result_field] = self._prepare_field_value(result_field, self.format_payload(kwargs.get("result")))
                terminal_time_field = completed_at_field if next_status == self.STATUSES.SUCCESS else failed_at_field
                if terminal_time_field and timestamp:
                    updates[terminal_time_field] = timestamp
            else:
                next_status = incoming_status

            if status_field and next_status is not None:
                updates[status_field] = self._prepare_field_value(status_field, next_status)
            if event == "cleanup" and cleaned_field:
                updates[cleaned_field] = True

            queryset = self._record_model.objects.using(using).filter(pk=record.pk)
            if status_field and event != "cleanup":
                queryset = queryset.exclude(**{f"{status_field}__in": [self.STATUSES.SUCCESS, self.STATUSES.FAILED]})
            if terminal and event not in {"cleanup"}:
                # Existing terminal rows accept harmless metadata only.
                updates = {key: value for key, value in metadata.items() if key not in {status_field, result_field, completed_at_field, failed_at_field}}
            elif terminal and event == "cleanup":
                updates.pop(status_field, None)
                if incoming_status != current_status:
                    updates.pop(result_field, None)
                    updates.pop(completed_at_field, None)
                    updates.pop(failed_at_field, None)
            if updates:
                queryset.update(**updates)


class ModelTrackingAsyncManager(ModelTrackingMixin, AsyncManager):
    """Internal coordinator manager with optional ORM lifecycle tracking."""

    pass
