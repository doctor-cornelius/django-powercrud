from __future__ import annotations

import copy
import json
from typing import Any, Optional, Sequence

from django.http import Http404, HttpResponse, HttpResponseBadRequest, QueryDict
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.formats import date_format
from django.forms.forms import NON_FIELD_ERRORS

from powercrud.templatetags import powercrud as powercrud_tags
from powercrud.logging import get_logger
from .config_mixin import resolve_config

log = get_logger(__name__)


class InlineEditingMixin:
    """Handle HTMX endpoints for inline row editing."""

    inline_action: str | None = None

    def dispatch(self, request, *args, **kwargs):  # pragma: no cover - thin wrapper
        inline_action = getattr(self, "inline_action", None)
        if inline_action == "inline_row":
            return self._dispatch_inline_row(request, *args, **kwargs)
        if inline_action == "inline_dependency":
            return self._dispatch_inline_dependency(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    # ------------------------------------------------------------------
    # Inline row handling
    # ------------------------------------------------------------------
    def _dispatch_inline_row(self, request, *args, **kwargs):
        if not self.get_inline_editing():
            raise Http404("Inline editing disabled")

        self.kwargs = kwargs
        self.request = request
        obj = self.get_object()

        should_render_display = request.GET.get("inline_display") or request.POST.get(
            "inline_display"
        )

        auth_state = self._evaluate_inline_state(obj, request)
        if auth_state["status"] != "ok":
            return self._build_inline_guard_response(obj, auth_state)

        if should_render_display:
            html = self._render_inline_row_display(obj)
            return HttpResponse(html)

        if request.method == "POST":
            lock_state = self._evaluate_inline_state(obj, request)
            if lock_state["status"] != "ok":
                return self._build_inline_guard_response(obj, lock_state)

            form = self.build_inline_form(
                instance=obj, data=request.POST, files=request.FILES
            )
            self._prepare_inline_number_widgets(form)
            self._prepare_inline_preservation(form, request.POST)
            self._preserve_inline_raw_data(form, request.POST)
            self._restore_inline_preserved_dataset(form)
            if form.is_valid():
                post_save_state = self._evaluate_inline_state(obj, request)
                if post_save_state["status"] != "ok":
                    return self._build_inline_guard_response(obj, post_save_state)

                self.object = form.save()
                row_html = self._render_inline_row_display(self.object)
                response = HttpResponse(row_html)
                response["HX-Trigger"] = json.dumps(
                    {"inline-row-saved": {"pk": self.object.pk}}
                )
                return response

            # Log validation context to help downstream debugging.
            posted_fields = [
                key for key in request.POST.keys() if key != "csrfmiddlewaretoken"
            ]
            try:
                error_details = form.errors.get_json_data()
            except Exception:
                error_details = form.errors
            log.error(
                "Inline save failed for pk %s (row id %s). Errors=%s | posted_fields=%s | inline_edit_fields=%s",
                getattr(obj, "pk", None),
                getattr(self, "get_inline_row_id", lambda _: None)(obj)
                if callable(getattr(self, "get_inline_row_id", None))
                else None,
                error_details,
                posted_fields,
                resolve_config(self).inline_edit_fields,
            )

            error_summary = self._get_inline_form_error_summary(form)
            html = self._render_inline_row_form(
                obj, form=form, error_summary=error_summary
            )
            response = HttpResponse(html)
            row_id = None
            row_id_getter = getattr(self, "get_inline_row_id", None)
            if callable(row_id_getter):
                try:
                    row_id = row_id_getter(obj)
                except Exception:
                    row_id = None
            response["HX-Trigger"] = json.dumps(
                {
                    "inline-row-error": {
                        "pk": obj.pk,
                        "row_id": row_id,
                        "message": error_summary
                        or str(_("Inline save failed. Fix the errors and try again.")),
                    }
                }
            )
            return response

        html = self._render_inline_row_form(obj, form=None)
        return HttpResponse(html)

    # ------------------------------------------------------------------
    # Dependency handling
    # ------------------------------------------------------------------
    def _dispatch_inline_dependency(self, request, *args, **kwargs):
        if not self.get_inline_editing():
            raise Http404("Inline editing disabled")
        cfg = resolve_config(self)

        field = request.POST.get("field")
        if not field:
            return HttpResponseBadRequest("Missing field parameter")

        pk = request.POST.get("pk")
        self.kwargs = kwargs
        self.request = request

        obj = None
        if pk:
            self.kwargs[getattr(self, "pk_url_kwarg", "pk")] = pk
            try:
                obj = self.get_object()
            except Http404:
                obj = None

        form = self.build_inline_form(
            instance=obj, data=request.POST, files=request.FILES
        )
        if field not in form.fields:
            return HttpResponseBadRequest("Invalid field")

        widget_html = render_to_string(
            f"{cfg.templates_path}/partial/inline_field.html",
            {
                "field": form[field],
                "field_name": field,
            },
            request=request,
        )
        return HttpResponse(widget_html)

    # ------------------------------------------------------------------
    # Required-field preservation
    # ------------------------------------------------------------------
    def build_inline_form(self, *, instance, data=None, files=None):
        """Construct the inline form and prime preservation metadata.

        Args:
            instance: Model instance being edited inline.
            data: POST payload when handling a save.
            files: Uploaded files (unused for inline rows today).

        Returns:
            forms.ModelForm: Inline form wired with any required-field preservation
            metadata so subsequent POSTs can be rehydrated.
        """
        form = super().build_inline_form(instance=instance, data=data, files=files)
        self._prepare_inline_preservation(form, data)
        return form

    def get_inline_preserve_required_fields(self) -> bool:
        """Flag controlling whether PowerCRUD auto-preserves missing required inputs."""
        return bool(resolve_config(self).inline_preserve_required_fields)

    def _prepare_inline_preservation(self, form, data=None):
        """Record which fields need preservation and hydrate initial POST clones.

        Args:
            form: Inline ModelForm instance.
            data: POST data to seed the preserved QueryDict (may be None on GET).
        """
        if not self.get_inline_preserve_required_fields() or not form:
            return

        ready = getattr(form, "_inline_preservation_ready", False)
        preserved = getattr(form, "_inline_preserved_fields", None)
        if not ready or preserved is None:
            preserved = self._configure_inline_preserved_fields(form)
            form._inline_preservation_ready = True

        if (
            preserved
            and data is not None
            and not getattr(form, "_inline_preserved_data", None)
        ):
            dataset = self._build_inline_preserved_dataset(form, data)
            if dataset is not None:
                form._inline_preserved_data = dataset

    def _configure_inline_preserved_fields(self, form) -> list[str]:
        """Determine which required fields must be silently re-posted.

        Args:
            form: Inline ModelForm instance.

        Returns:
            list[str]: Field names that will be cloned into hidden inputs.
        """
        if not form:
            return []

        inline_fields = set(self.get_inline_edit_fields())
        if not inline_fields:
            form._inline_preserved_fields = []
            return []
        preserved: list[str] = []
        fields = getattr(form, "fields", {})
        for name, field in fields.items():
            if not getattr(field, "required", False):
                continue
            if inline_fields and name in inline_fields:
                continue
            widget = getattr(field, "widget", None)
            if widget and getattr(widget, "is_hidden", False):
                continue
            preserved.append(name)

        form._inline_preserved_fields = preserved
        return preserved

    def _build_inline_preserved_dataset(self, form, data):
        """Create a mutable QueryDict containing preserved field values.

        Args:
            form: Inline ModelForm instance.
            data: Original POST payload.

        Returns:
            QueryDict | None: Cloned data including preserved required fields, or
            None if cloning failed.
        """
        preserved = getattr(form, "_inline_preserved_fields", None)
        if not preserved or not data:
            return None

        mutable = self._clone_inline_post_data(data)
        if mutable is None:
            return None

        for name in preserved:
            field = form.fields.get(name)
            if not field:
                continue
            values = self._format_inline_preserved_values(form, field, name)
            key = form.add_prefix(name) if hasattr(form, "add_prefix") else name
            mutable.setlist(key, values)

        return mutable

    def _restore_inline_preserved_dataset(self, form):
        """Swap the inline form's data with the preserved QueryDict, if any."""
        if not self.get_inline_preserve_required_fields():
            return
        dataset = getattr(form, "_inline_preserved_data", None)
        if dataset is not None:
            form.data = dataset

    def _format_inline_preserved_values(self, form, field, name) -> list[str]:
        """Serialize initial field values into POST-friendly strings."""
        try:
            raw_value = form.initial_for_field(field, name)
        except Exception:
            instance = getattr(form, "instance", None)
            raw_value = getattr(instance, name, None) if instance is not None else None

        try:
            prepared = field.prepare_value(raw_value)
        except Exception:
            prepared = raw_value

        if prepared is None:
            return []
        if isinstance(prepared, (list, tuple, set)):
            return ["" if value is None else str(value) for value in prepared]
        if isinstance(prepared, QueryDict):
            combined: list[str] = []
            for key in prepared.keys():
                combined.extend(prepared.getlist(key))
            return combined
        return ["" if prepared is None else str(prepared)]

    def _clone_inline_post_data(self, data):
        """Return a mutable copy of the current POST data (if QueryDict)."""
        if isinstance(data, QueryDict):
            clone = data.copy()
            clone._mutable = True
            return clone
        return None

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _render_inline_row_form(
        self, obj, form=None, error_summary: str | None = None
    ) -> str:
        cfg = resolve_config(self)
        row_payload = self._build_inline_row_payload(obj)
        inline_form = form or self.build_inline_form(instance=obj)
        self._prepare_inline_number_widgets(inline_form)
        summary = error_summary
        if summary is None:
            summary = self._get_inline_form_error_summary(inline_form)
        context = {
            "row": row_payload,
            "form": inline_form,
            "inline_config": self.get_inline_context(),
            "inline_save_url": self._get_inline_row_url(obj),
            "inline_cancel_url": self._get_inline_row_url(obj),
            "enable_bulk_edit": self.get_bulk_edit_enabled(),
            "selected_ids": self._get_selected_ids(),
            "list_view_url": self._get_list_url(),
            "action_button_classes": self.get_action_button_classes(),
        }
        return render_to_string(
            f"{cfg.templates_path}/partial/list.html#inline_row_form",
            context,
            request=self.request,
        )

    def _render_inline_row_display(self, obj) -> str:
        cfg = resolve_config(self)
        row_payload = self._build_inline_row_payload(obj)
        context = {
            "row": row_payload,
            "inline_config": self.get_inline_context(),
            "enable_bulk_edit": self.get_bulk_edit_enabled(),
            "selected_ids": self._get_selected_ids(),
            "list_view_url": self._get_list_url(),
        }
        return render_to_string(
            f"{cfg.templates_path}/partial/list.html#inline_row_display",
            context,
            request=self.request,
        )

    def _resolve_inline_field_list(self, source: Sequence[str] | None) -> list[str]:
        if not source:
            return []
        all_editable = set(self._get_all_editable_fields())
        return [field for field in source if field in all_editable]

    def _get_inline_form_field_names(self) -> list[str]:
        """
        Return the set of field names exposed by the view's form.
        """
        try:
            form_class = self.get_form_class()
        except Exception:
            return []

        base_fields = getattr(form_class, "base_fields", None)
        if base_fields:
            return list(base_fields.keys())

        try:
            form = form_class()
        except Exception:
            return []
        fields = getattr(form, "fields", None)
        if fields:
            return list(fields.keys())
        return []

    def _filter_inline_fields_by_form(self, fields: list[str]) -> list[str]:
        if not fields:
            return []
        form_field_names = set(self._get_inline_form_field_names())
        if not form_field_names:
            return fields

        filtered = [field for field in fields if field in form_field_names]
        missing = sorted(set(fields) - set(filtered))
        if missing:
            log.warning(
                f"Inline edit fields {missing} ignored because they are not present on the form_class for {self.__class__.__name__}"
            )
        return filtered

    def get_inline_edit_fields(self) -> list[str]:
        """
        Return the list of fields that should be editable inline.
        Falls back to the form_fields list so inline and modal forms stay aligned.
        """
        if not self.get_inline_editing():
            return []

        cfg = resolve_config(self)
        config = cfg.inline_edit_fields
        if not config:
            return self._filter_inline_fields_by_form(
                self._resolve_inline_field_list(cfg.form_fields)
            )

        if config == "__all__":
            return self._filter_inline_fields_by_form(self._get_all_editable_fields())

        if config == "__fields__":
            return self._filter_inline_fields_by_form(
                self._resolve_inline_field_list(cfg.fields)
            )

        return self._filter_inline_fields_by_form(
            self._resolve_inline_field_list(config)
        )

    def _resolve_inline_endpoint(self, endpoint_name: str | None) -> str | None:
        """
        Convert a named endpoint into a URL if possible.
        """
        if not endpoint_name:
            return None
        resolver = getattr(self, "safe_reverse", None)
        if not callable(resolver):
            return None
        try:
            return resolver(endpoint_name)
        except Exception:
            return None

    def get_inline_field_dependencies(self) -> dict[str, dict[str, Any]]:
        """
        Return dependency metadata for inline fields, including resolved endpoints.
        """
        cfg = resolve_config(self)
        dependencies = cfg.inline_field_dependencies or {}
        inline_fields = set(self.get_inline_edit_fields())
        endpoint_getter = getattr(self, "get_inline_dependency_endpoint_name", None)
        default_endpoint_name = endpoint_getter() if callable(endpoint_getter) else None
        default_endpoint_url = self._resolve_inline_endpoint(default_endpoint_name)

        resolved: dict[str, dict[str, Any]] = {}
        for field, meta in dependencies.items():
            if not isinstance(meta, dict):
                continue
            if inline_fields and field not in inline_fields:
                log.warning(
                    "Inline dependency for '%s' ignored because the field is not inline-editable on %s",
                    field,
                    self.__class__.__name__,
                )
                continue
            entry = dict(meta)
            endpoint_name = entry.get("endpoint_name") or default_endpoint_name
            entry["endpoint_name"] = endpoint_name
            entry["endpoint_url"] = (
                self._resolve_inline_endpoint(endpoint_name) or default_endpoint_url
            )

            depends_on = entry.get("depends_on") or []
            valid_parents = [
                parent
                for parent in depends_on
                if not inline_fields or parent in inline_fields
            ]
            missing_parents = sorted(set(depends_on) - set(valid_parents))
            if missing_parents:
                log.warning(
                    "Inline dependency for '%s' references non-inline parent fields %s on %s",
                    field,
                    missing_parents,
                    self.__class__.__name__,
                )
            entry["depends_on"] = valid_parents
            if not valid_parents:
                log.warning(
                    "Inline dependency for '%s' ignored because it has no valid parent fields on %s",
                    field,
                    self.__class__.__name__,
                )
                continue
            resolved[field] = entry
        return resolved

    def can_inline_edit(self, obj, request) -> bool:
        """
        Determine whether the provided object can be edited inline for this request.
        """
        if not self.get_inline_editing():
            return False

        if obj is None:
            return False

        if self.is_inline_row_locked(obj):
            return False

        cfg = resolve_config(self)
        perm = cfg.inline_edit_requires_perm
        user = getattr(request, "user", None)

        if perm:
            if not user or not user.has_perm(perm):
                return False

        allowed_callable = cfg.inline_edit_allowed
        if callable(allowed_callable):
            return bool(allowed_callable(obj, request))

        return True

    def is_inline_row_locked(self, obj) -> bool:
        """
        Check whether the provided object is currently locked by an async conflict.
        """
        if obj is None:
            return False

        pk = getattr(obj, "pk", None)
        if pk in (None, ""):
            return False

        conflict_enabled = getattr(self, "get_conflict_checking_enabled", None)
        if not callable(conflict_enabled) or not conflict_enabled():
            return False

        checker = getattr(self, "_check_single_record_conflict", None)
        if not callable(checker):
            return False

        try:
            return bool(checker(pk))
        except Exception:
            return False

    def _build_inline_row_payload(self, obj) -> dict[str, Any]:
        object_list_context = powercrud_tags.object_list(
            {
                "request": self.request,
                "inline_edit": self.get_inline_context(),
                "use_htmx": self.get_use_htmx(),
                "original_target": self.get_original_target(),
                "htmx_target": self.get_htmx_target(),
                "selected_ids": self._get_selected_ids(),
            },
            [obj],
            self,
        )
        return object_list_context["object_list"][0]

    def _get_inline_row_url(self, obj) -> str:
        endpoint = self.get_inline_row_endpoint_name()
        return self.safe_reverse(endpoint, kwargs={"pk": obj.pk})

    def _get_selected_ids(self):
        if hasattr(self, "get_selected_ids_from_session") and self.request:
            ids = self.get_selected_ids_from_session(self.request)
            return [str(pk) for pk in ids]
        return []

    def _get_list_url(self) -> str:
        if self.namespace:
            list_url_name = f"{self.namespace}:{self.url_base}-list"
        else:
            list_url_name = f"{self.url_base}-list"
        return self.safe_reverse(list_url_name) or ""

    # ------------------------------------------------------------------
    # Inline guard helpers
    # ------------------------------------------------------------------
    def _evaluate_inline_state(self, obj, request) -> dict[str, Any]:
        """
        Return a dict describing whether inline editing is allowed.
        """
        if obj is None:
            return {
                "status": "forbidden",
                "message": _("Inline editing unavailable for this row."),
            }

        locker = getattr(self, "is_inline_row_locked", None)
        if callable(locker) and locker(obj):
            return {
                "status": "locked",
                "message": _("Inline editing blocked – record is locked."),
                "lock": self._get_inline_lock_metadata(obj),
            }

        checker = getattr(self, "can_inline_edit", None)
        if callable(checker) and not checker(obj, request):
            return {
                "status": "forbidden",
                "message": _("Inline editing not permitted for this row."),
            }

        return {"status": "ok"}

    def _build_inline_guard_response(self, obj, state: dict[str, Any]) -> HttpResponse:
        """
        Construct an HTMX-friendly response when inline editing is blocked.
        """
        message = state.get("message") or _("Inline editing unavailable.")
        trigger = {
            "locked": "inline-row-locked",
            "forbidden": "inline-row-forbidden",
        }.get(state.get("status"), "inline-row-error")

        payload = {
            "pk": getattr(obj, "pk", None),
            "message": message,
            "refresh": self._get_inline_refresh_payload(obj),
        }
        if state.get("lock"):
            payload["lock"] = state["lock"]

        # Render display row so the UI falls back to read-only state
        html = self._render_inline_row_display(obj)
        status_code = 423 if state.get("status") == "locked" else 403
        response = HttpResponse(html, status=status_code)
        response["HX-Trigger"] = json.dumps({trigger: payload})
        return response

    def get_inline_lock_details(self, obj) -> dict[str, Any]:
        """
        Public helper so templates can retrieve lock metadata for a row.
        """
        return self._get_inline_lock_metadata(obj)

    def _get_inline_lock_metadata(self, obj) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if not obj or not getattr(self, "model", None):
            return metadata

        get_manager = getattr(self, "get_async_manager", None)
        if not callable(get_manager):
            return metadata

        try:
            manager = get_manager()
        except Exception:
            return metadata

        cache = getattr(manager, "cache", None)
        prefix = getattr(manager, "conflict_model_prefix", None)
        if not cache or not prefix:
            return metadata

        model_label = f"{self.model._meta.app_label}.{self.model._meta.model_name}"
        lock_key = f"{prefix}{model_label}:{obj.pk}"
        task_name = cache.get(lock_key)
        if not task_name:
            return metadata

        metadata["task"] = str(task_name)
        metadata["lock_key"] = lock_key

        record = self._lookup_async_record(manager, task_name)
        if record is not None:
            metadata["user"] = self._extract_record_field(
                manager, record, "user", "user_label"
            )
            metadata["status"] = getattr(record, "status", None)
            metadata["message"] = getattr(record, "message", None)
            created_iso, created_display = self._serialize_datetime(
                getattr(record, "created_at", None)
            )
            updated_iso, updated_display = self._serialize_datetime(
                getattr(record, "updated_at", None)
            )
            metadata["created_at"] = created_iso
            metadata["created_at_display"] = created_display
            metadata["updated_at"] = updated_iso
            metadata["updated_at_display"] = updated_display

        metadata["label"] = self._format_lock_label(metadata)
        return metadata

    def _lookup_async_record(self, manager, task_name: str) -> Optional[Any]:
        record_model = getattr(manager, "_record_model", None)
        field_getter = getattr(manager, "_field", None)
        if not record_model or not callable(field_getter):
            return None

        task_field = field_getter("task_name", "task_name")
        if not task_field:
            return None

        try:
            return record_model.objects.filter(**{task_field: task_name}).first()
        except Exception:
            return None

    def _extract_record_field(self, manager, record, logical_name: str, default: str):
        field_getter = getattr(manager, "_field", None)
        field_name = (
            field_getter(logical_name, default) if callable(field_getter) else default
        )
        if not field_name:
            return None
        return getattr(record, field_name, None)

    def _serialize_datetime(self, value):
        if not value:
            return (None, None)
        try:
            aware = timezone.localtime(value) if timezone.is_aware(value) else value
        except Exception:
            aware = value
        try:
            display = date_format(aware, "DATETIME_FORMAT")
        except Exception:
            display = str(aware)
        try:
            iso_value = aware.isoformat()
        except Exception:
            iso_value = str(aware)
        return (iso_value, display)

    def _format_lock_label(self, metadata: dict[str, Any]) -> str:
        user = metadata.get("user")
        timestamp = metadata.get("created_at_display") or metadata.get(
            "updated_at_display"
        )
        if user and timestamp:
            return _("Locked by %(user)s at %(timestamp)s") % {
                "user": user,
                "timestamp": timestamp,
            }
        if user:
            return _("Locked by %(user)s") % {"user": user}
        if timestamp:
            return _("Lock acquired at %(timestamp)s") % {"timestamp": timestamp}
        return _("Inline editing blocked – record is locked.")

    def _get_inline_refresh_payload(self, obj) -> dict[str, Any]:
        if not obj:
            return {}
        row_id = None
        row_id_getter = getattr(self, "get_inline_row_id", None)
        if callable(row_id_getter):
            try:
                row_id = row_id_getter(obj)
            except Exception:
                row_id = None
        return {
            "pk": getattr(obj, "pk", None),
            "row_id": row_id,
            "url": self._get_inline_row_url(obj) if getattr(obj, "pk", None) else None,
        }

    def _preserve_inline_raw_data(self, form, data):
        if not form or not data:
            return
        try:
            form.data = data
        except Exception:
            pass

    def _prepare_inline_number_widgets(self, form):
        if not form:
            return
        for field in form.fields.values():
            widget = getattr(field, "widget", None)
            if not widget:
                continue
            if getattr(widget, "input_type", None) != "number":
                continue
            try:
                cloned = copy.deepcopy(widget)
            except Exception:
                cloned = widget
            cloned.input_type = "text"
            attrs = dict(getattr(cloned, "attrs", {}))
            attrs.setdefault("inputmode", "numeric")
            attrs.setdefault("data-inline-number", "true")
            cloned.attrs = attrs
            field.widget = cloned

    def _get_inline_form_error_summary(self, form) -> str:
        if not form or not getattr(form, "errors", None):
            return ""
        try:
            non_field = form.non_field_errors()
        except Exception:
            non_field = []
        if non_field:
            return str(non_field[0])
        errors = getattr(form, "errors", {})
        for field, messages in errors.items():
            if field == NON_FIELD_ERRORS:
                continue
            if messages:
                return str(messages[0])
        return ""
