from __future__ import annotations

from typing import Any
import json

from django.utils import timezone

from powercrud.async_manager import AsyncManager

from .models import AsyncTaskRecord

import logging
log = logging.getLogger("powercrud")

class SampleAsyncManager(AsyncManager):
    """Async manager that persists lifecycle events to AsyncTaskRecord."""

    def _user_label(self, user: Any) -> str:
        if not user:
            return ""
        if hasattr(user, "get_username"):
            return user.get_username()
        if hasattr(user, "username"):
            return str(user.username)
        return str(user)

    def _serialise_objects(self, objects: Any) -> str:
        if not objects:
            return ""
        if isinstance(objects, (list, tuple, set)):
            return ", ".join(str(obj) for obj in objects)
        return str(objects)

    def _serialise_json(self, value: Any) -> Any:
        try:
            json.dumps(value)
            return value
        except Exception:
            if isinstance(value, dict):
                return {str(k): self._serialise_json(v) for k, v in value.items()}
            if isinstance(value, (list, tuple, set)):
                return [self._serialise_json(v) for v in value]
            return str(value)

    def async_task_lifecycle(self, event, task_name, **kwargs):  # noqa: D401
        incoming_status = kwargs.get("status")
        message = kwargs.get("message") or ""
        timestamp = kwargs.get("timestamp") or timezone.now()
        log.debug(
            f"[SampleAsyncManager] lifecycle event={event} task={task_name} status={incoming_status}"
        )

        record, created = AsyncTaskRecord.objects.get_or_create(
            task_name=task_name,
            defaults={
                "status": incoming_status
                    if incoming_status is not None
                    else AsyncTaskRecord.STATUS.UNKNOWN,
                "message": message,
                "user_label": self._user_label(kwargs.get("user")),
                "affected_objects": self._serialise_objects(
                    kwargs.get("affected_objects")
                ),
                "task_kwargs": self._serialise_json(kwargs.get("task_kwargs")),
                "task_args": self._serialise_json(kwargs.get("task_args")),
            },
        )

        if not created:
            if incoming_status is not None:
                record.status = incoming_status
            if message:
                record.message = message

        if event == "create":
            record.user_label = self._user_label(kwargs.get("user"))
            record.affected_objects = self._serialise_objects(kwargs.get("affected_objects"))
            record.task_kwargs = self._serialise_json(kwargs.get("task_kwargs"))
            record.task_args = self._serialise_json(kwargs.get("task_args"))
            record.cleaned_up = False
        elif event == "progress":
            record.status = AsyncTaskRecord.STATUS.IN_PROGRESS
            record.progress_payload = kwargs.get("progress_payload") or message
        elif event == "complete":
            record.status = AsyncTaskRecord.STATUS.SUCCESS
            record.result_payload = kwargs.get("result")
            record.completed_at = timestamp
        elif event == "fail":
            record.status = AsyncTaskRecord.STATUS.FAILED
            record.result_payload = kwargs.get("result")
            record.failed_at = timestamp
        elif event == "cleanup":
            record.cleaned_up = True

        record.save(update_fields=[
            "status",
            "message",
            "progress_payload",
            "user_label",
            "affected_objects",
            "task_kwargs",
            "result_payload",
            "cleaned_up",
            "updated_at",
            "completed_at",
            "failed_at",
        ])
