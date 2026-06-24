from typing import Any, Callable, Dict, List, Optional

from django.db import models, transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from powercrud.logging import get_logger
from powercrud.bulk_persistence import (
    BulkUpdateExecutionContext,
    resolve_bulk_update_persistence_backend,
)
from ..config_mixin import resolve_config

log = get_logger(__name__)


class OperationMixin:
    """Mixin for core bulk operations including delete, update, and permission checks."""

    def _get_bulk_update_selected_ids(self, queryset: models.QuerySet) -> tuple[Any, ...]:
        """Extract selected primary keys from a queryset-like object.

        Args:
            queryset: QuerySet or iterable of model instances.

        Returns:
            Tuple of selected primary key values, omitting missing ``pk``
            attributes.
        """
        values_list = getattr(queryset, "values_list", None)
        if callable(values_list):
            try:
                return tuple(values_list("pk", flat=True))
            except Exception:
                pass

        selected_ids = []
        for obj in queryset:
            if hasattr(obj, "pk"):
                selected_ids.append(getattr(obj, "pk"))
        return tuple(selected_ids)

    def _build_bulk_update_execution_context(
        self,
        *,
        mode: str,
        queryset: models.QuerySet,
        task_name: str | None = None,
        user_id: int | None = None,
        manager_class_path: str | None = None,
    ) -> BulkUpdateExecutionContext:
        """Build plain execution context for bulk update persistence backends.

        Args:
            mode: Execution surface using the backend, currently ``"sync"`` or
                ``"async"``.
            queryset: QuerySet or queryset-like object being updated.
            task_name: Optional async task identifier.
            user_id: Optional initiating user primary key.
            manager_class_path: Optional async manager class path.

        Returns:
            Plain-data execution context suitable for worker-safe backends.
        """
        model = getattr(self, "model", None)
        model_path = None
        if model is not None and hasattr(model, "_meta") and hasattr(model, "__name__"):
            model_path = f"{model._meta.app_label}.{model.__name__}"

        request = getattr(self, "request", None)
        request_user = getattr(request, "user", None)
        if user_id is None and request_user is not None:
            user_id = getattr(request_user, "id", None)

        return BulkUpdateExecutionContext(
            mode=mode,
            model_path=model_path,
            selected_ids=self._get_bulk_update_selected_ids(queryset),
            user_id=user_id,
            task_name=task_name,
            manager_class_path=manager_class_path,
        )

    def persist_bulk_update(
        self,
        *,
        queryset: models.QuerySet,
        fields_to_update: List[str],
        field_data: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Persist a sync bulk update and return the standard result payload.

        Args:
            queryset: QuerySet of objects to update.
            fields_to_update: Field names selected for the current operation.
            field_data: Normalized bulk field payload built from the request.
            progress_callback: Optional progress callback used by sync or async
                callers to report progress during the operation.

        Returns:
            Dict matching PowerCRUD's standard bulk result contract with
            ``success``, ``success_records``, and ``errors`` keys.
        """
        bulk_fields = list(resolve_config(self).bulk_fields or [])
        backend_path_getter = getattr(
            self, "get_bulk_update_persistence_backend_path", None
        )
        backend_config_getter = getattr(
            self, "get_bulk_update_persistence_backend_config", None
        )
        backend_path = (
            backend_path_getter()
            if callable(backend_path_getter)
            else getattr(self, "bulk_update_persistence_backend_path", None)
        )
        backend_config = (
            backend_config_getter()
            if callable(backend_config_getter)
            else getattr(self, "bulk_update_persistence_backend_config", None)
        )
        backend = resolve_bulk_update_persistence_backend(
            backend_path,
            config=backend_config,
        )
        context = self._build_bulk_update_execution_context(
            mode="sync",
            queryset=queryset,
        )
        return backend.persist_bulk_update(
            queryset=queryset,
            bulk_fields=bulk_fields,
            fields_to_update=fields_to_update,
            field_data=field_data,
            context=context,
            progress_callback=progress_callback,
        )

    def _validate_bulk_update_fields(
        self, *, bulk_fields: List[str], fields_to_update: List[str]
    ) -> None:
        """
        Ensure the requested bulk-update fields are configured for this view.

        Args:
            bulk_fields: Field names configured as bulk-editable.
            fields_to_update: Field names submitted for the current operation.

        Raises:
            ValidationError: If any submitted field is outside ``bulk_fields``.
        """
        allowed_fields = set(bulk_fields)
        invalid_fields = [
            field for field in fields_to_update if field not in allowed_fields
        ]
        if invalid_fields:
            invalid_field_list = ", ".join(invalid_fields)
            raise ValidationError(
                f"Bulk edit request contained invalid fields: {invalid_field_list}."
            )

    def get_bulk_edit_enabled(self) -> bool:
        """
        Determine if the bulk action modal should be available.

        Returns:
            bool: True if bulk update or bulk delete is configured and permitted.
        """
        return bool(self.get_bulk_update_enabled() or self.get_bulk_delete_enabled())

    def get_bulk_update_configured(self) -> bool:
        """
        Return whether bulk update is configured before runtime permissions.
        """
        cfg = resolve_config(self)
        return bool((cfg.bulk_fields or []) and cfg.use_modal_enabled)

    def get_bulk_delete_configured(self) -> bool:
        """
        Return whether bulk delete is configured before runtime permissions.
        """
        cfg = resolve_config(self)
        return bool(cfg.bulk_delete and cfg.use_modal_enabled)

    def _get_bulk_permission_request(self):
        """
        Return the request used for runtime bulk permission hooks, when available.
        """
        return getattr(self, "request", None)

    def get_bulk_update_permission_allowed(self) -> bool:
        """
        Return whether runtime permission allows bulk update.
        """
        request = self._get_bulk_permission_request()
        if request is None:
            return True
        permission_checker = getattr(self, "has_power_bulk_update_permission", None)
        if permission_checker is None:
            return True
        return bool(permission_checker(request))

    def get_bulk_delete_permission_allowed(self) -> bool:
        """
        Return whether runtime permission allows bulk delete.
        """
        request = self._get_bulk_permission_request()
        if request is None:
            return True
        permission_checker = getattr(self, "has_power_bulk_delete_permission", None)
        if permission_checker is None:
            return True
        return bool(permission_checker(request))

    def get_bulk_update_enabled(self) -> bool:
        """
        Return whether configured bulk update is visible and callable.
        """
        return bool(
            self.get_bulk_update_configured()
            and self.get_bulk_update_permission_allowed()
        )

    def get_bulk_delete_enabled(self) -> bool:
        """
        Determine if bulk delete is allowed.

        Returns:
            bool: True if bulk_delete is configured and permitted.
        """
        return bool(
            self.get_bulk_delete_configured()
            and self.get_bulk_delete_permission_allowed()
        )

    def _extra_button_permission_allows_selection(self, button: dict) -> bool:
        """
        Return whether a selection-aware extra button should drive selection controls.
        """
        if hasattr(button, "to_dict"):
            button = button.to_dict()
        if not isinstance(button, dict):
            return False

        if not bool(button.get("uses_selection", False)):
            return False

        request = self._get_bulk_permission_request()
        permission = button.get("permission")
        permission_check_name = button.get("permission_check")
        if request is None or (not permission and not permission_check_name):
            return True

        if permission:
            permission_resolver = getattr(self, "has_power_permission", None)
            if permission_resolver is None:
                return False
            return bool(permission_resolver(permission, request, obj=None))

        permission_check = getattr(self, permission_check_name, None)
        if not callable(permission_check):
            return False
        return bool(permission_check(request, None))

    def has_permitted_selection_aware_extra_buttons(self) -> bool:
        """
        Return whether any permitted extra button needs row selection controls.
        """
        extra_buttons = getattr(self, "extra_buttons", []) or []
        if not isinstance(extra_buttons, (list, tuple)):
            return False
        return any(
            self._extra_button_permission_allows_selection(button)
            for button in extra_buttons
        )

    def get_selection_controls_enabled(self) -> bool:
        """
        Determine if row selection controls should render for this list view.

        Bulk edit/delete require selection controls. Selection-aware extra
        buttons may also enable them unless the view opts out.
        """
        cfg = resolve_config(self)
        return bool(
            self.get_bulk_edit_enabled()
            or (
                cfg.use_htmx_enabled
                and not cfg.extra_button_selection_controls_disabled
                and self.has_permitted_selection_aware_extra_buttons()
            )
        )

    def _perform_bulk_delete(
        self,
        queryset: models.QuerySet,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """
        Perform bulk delete with graceful handling of missing records.

        Args:
            queryset: QuerySet of objects to delete.
            progress_callback: Optional callable for progress updates,
                               called as progress_callback(current, total).

        Returns:
            Dict with success status, deleted count, and errors.
        """
        total = queryset.count()
        current = 0
        deleted_count = 0
        errors = []

        try:
            with transaction.atomic():
                for obj in queryset:
                    try:
                        obj.delete()
                        deleted_count += 1
                        current += 1
                        if progress_callback:
                            progress_callback(current, total)
                    except ObjectDoesNotExist:
                        # ✅ Record already deleted by another process - that's fine!
                        # log.debug(f"Record {obj.pk} already deleted")
                        current += 1
                        if progress_callback:
                            progress_callback(current, total)
                        continue
                    except Exception as e:
                        # Real errors
                        log.error(f"Error deleting {obj.pk}: {e}")
                        raise

        except Exception as e:
            log.error(f"Error during bulk delete: {e}")
            errors.append((None, [str(e)]))

        return {
            "success": len(errors) == 0,
            "success_records": deleted_count,
            "errors": errors,
        }

    def _perform_bulk_update(
        self,
        queryset: models.QuerySet,
        bulk_fields: List[str],
        fields_to_update: List[str],
        field_data: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """
        Perform bulk update with progress reporting and atomic transactions.

        Args:
            queryset: QuerySet of objects to update.
            bulk_fields: List of fields allowed for bulk update.
            fields_to_update: List of fields actually being updated.
            field_data: List of dicts containing field data and metadata.
            progress_callback: Optional callable for progress updates.

        Returns:
            Dict with success status, updated count, and errors.
        """
        total = queryset.count()
        current = 0
        errors = []
        updated_count = 0

        try:
            self._validate_bulk_update_fields(
                bulk_fields=bulk_fields,
                fields_to_update=fields_to_update,
            )
        except ValidationError as e:
            return {
                "success": False,
                "success_records": 0,
                "errors": [("general", list(getattr(e, "messages", [str(e)])))],
            }

        # Bulk update - collect all changes first, then apply in transaction
        updates_to_apply = []

        # First pass: collect all changes without saving
        for obj in queryset:
            # log.debug(f"Preparing bulk edit for object {obj.pk}")
            obj_changes = {"object": obj, "changes": {}}

            for field_dict in field_data:
                field = field_dict["field"]
                value = field_dict["value"]
                info = field_dict["info"]
                m2m_action = field_dict.get("m2m_action")
                m2m_values = field_dict.get("m2m_values", [])

                # Process value based on field type
                if info.get("type") == "BooleanField":
                    if value == "true":
                        value = True
                    elif value == "false":
                        value = False
                    elif value in (None, "", "null"):
                        value = None
                elif (
                    value == "null"
                    and info.get("choices")
                    and not info.get("is_relation")
                ):
                    if info.get("null"):
                        value = None
                    elif info.get("blank"):
                        value = ""

                # Store the change to apply later
                obj_changes["changes"][field] = {
                    "value": value,
                    "info": info,
                    "m2m_action": m2m_action,
                    "m2m_values": m2m_values,
                }

            updates_to_apply.append(obj_changes)

        # Second pass: apply all changes in a transaction
        error_occurred = False
        error_message = None

        try:
            with transaction.atomic():
                for update in updates_to_apply:
                    obj = update["object"]
                    changes = update["changes"]

                    # log.debug(f"_perform_bulk_update on {obj}")

                    # Apply all changes to the object
                    for field, change_info in changes.items():
                        info = change_info["info"]
                        value = change_info["value"]

                        if info.get("is_m2m"):
                            # Handle M2M fields
                            m2m_action = change_info.get("m2m_action")
                            m2m_values = change_info.get("m2m_values", [])
                            m2m_manager = getattr(obj, field)

                            if m2m_action == "add":
                                m2m_manager.add(*m2m_values)
                            elif m2m_action == "remove":
                                m2m_manager.remove(*m2m_values)
                            else:  # replace
                                m2m_manager.set(m2m_values)
                        elif info.get("is_relation"):
                            # Handle relation fields
                            if value == "null" or value == "" or value is None:
                                setattr(obj, field, None)
                            else:
                                try:
                                    # Get the related model
                                    related_model = info["field"].related_model

                                    # Fetch the actual instance
                                    instance = related_model.objects.get(pk=int(value))

                                    # Set the field to the instance
                                    setattr(obj, field, instance)
                                except Exception as e:
                                    raise ValidationError(
                                        f"Invalid value for {info['verbose_name']}: {str(e)}"
                                    )
                        else:
                            # Handle regular fields
                            setattr(obj, field, value)

                    # Validate and save the object
                    if getattr(self, "bulk_full_clean", True):
                        # log.debug("running full_clean()")
                        obj.full_clean()  # This will raise ValidationError if validation fails
                    # log.debug("running save()")
                    obj.save()
                    updated_count += 1
                    current += 1
                    if progress_callback:
                        progress_callback(current, total)

        except Exception as e:
            # If any exception occurs, the transaction is rolled back
            error_occurred = True
            error_message = str(e)
            log.error(
                f"Error during bulk update, transaction rolled back: {error_message}"
            )

            # Directly add the error to our list
            if isinstance(e, ValidationError):
                # Handle different ValidationError formats
                if hasattr(e, "message_dict"):
                    # This is a dictionary of field names to error messages
                    for field, messages in e.message_dict.items():
                        errors.append((field, messages))
                elif hasattr(e, "messages"):
                    # This is a list of error messages
                    errors.append(("general", e.messages))
                else:
                    # Fallback
                    errors.append(("general", [str(e)]))
            else:
                # For other exceptions, just add the error message
                errors.append(("general", [str(e)]))

        # Force an error if we caught an exception but didn't add any specific errors
        if error_occurred and not errors:
            errors.append(("general", [error_message or "An unknown error occurred"]))

        if errors:
            return {
                "success": False,
                "success_records": 0,
                "errors": errors,
            }
        else:
            return {
                "success": True,
                "success_records": updated_count,
                "errors": [],
            }
