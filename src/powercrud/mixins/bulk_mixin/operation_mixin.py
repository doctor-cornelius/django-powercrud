import logging
from typing import Any, Callable, Dict, List, Optional

from django.db import models, transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist

log = logging.getLogger("powercrud")


class OperationMixin:
    """Mixin for core bulk operations including delete, update, and permission checks."""

    def get_bulk_edit_enabled(self) -> bool:
        """
        Determine if bulk edit functionality should be enabled.

        Returns:
            bool: True if bulk_fields are configured and modal/HTMX are enabled.
        """

        allowed = bool(
            (self.bulk_fields or self.bulk_delete)
            and (self.use_modal and self.use_htmx)
            )
        return allowed

    def get_bulk_delete_enabled(self) -> bool:
        """
        Determine if bulk delete is allowed.

        Returns:
            bool: True if bulk_delete is enabled and bulk edit is allowed.
        """
        return self.bulk_delete and self.get_bulk_edit_enabled()

    def _perform_bulk_delete(
        self,
        queryset: models.QuerySet,
        progress_callback: Optional[Callable[[int, int], None]] = None
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
                        log.debug(f"Record {obj.pk} already deleted")
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
            'success': len(errors) == 0,
            'success_records': deleted_count,
            'errors': errors,
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

        # Bulk update - collect all changes first, then apply in transaction
        updates_to_apply = []

        # First pass: collect all changes without saving
        for obj in queryset:
            log.debug(f"Preparing bulk edit for object {obj.pk}")
            obj_changes = {'object': obj, 'changes': {}}

            for field_dict in field_data:
                field = field_dict['field']
                value = field_dict['value']
                info = field_dict['info']
                m2m_action = field_dict.get('m2m_action')
                m2m_values = field_dict.get('m2m_values', [])

                # Process value based on field type
                if info.get('type') == 'BooleanField':
                    if value == "true":
                        value = True
                    elif value == "false":
                        value = False
                    elif value in (None, "", "null"):
                        value = None

                # Store the change to apply later
                obj_changes['changes'][field] = {
                    'value': value,
                    'info': info,
                    'm2m_action': m2m_action,
                    'm2m_values': m2m_values,
                }

            updates_to_apply.append(obj_changes)

        # Second pass: apply all changes in a transaction
        error_occurred = False
        error_message = None

        try:
            with transaction.atomic():
                for update in updates_to_apply:
                    obj = update['object']
                    changes = update['changes']

                    log.debug(f"_perform_bulk_update on {obj}")

                    # Apply all changes to the object
                    for field, change_info in changes.items():
                        info = change_info['info']
                        value = change_info['value']

                        if info.get('is_m2m'):
                            # Handle M2M fields
                            m2m_action = change_info.get('m2m_action')
                            m2m_values = change_info.get('m2m_values', [])
                            m2m_manager = getattr(obj, field)

                            if m2m_action == "add":
                                m2m_manager.add(*m2m_values)
                            elif m2m_action == "remove":
                                m2m_manager.remove(*m2m_values)
                            else:  # replace
                                m2m_manager.set(m2m_values)
                        elif info.get('is_relation'):
                            # Handle relation fields
                            if value == "null" or value == "" or value is None:
                                setattr(obj, field, None)
                            else:
                                try:
                                    # Get the related model
                                    related_model = info['field'].related_model

                                    # Fetch the actual instance
                                    instance = related_model.objects.get(pk=int(value))

                                    # Set the field to the instance
                                    setattr(obj, field, instance)
                                except Exception as e:
                                    raise ValidationError(f"Invalid value for {info['verbose_name']}: {str(e)}")
                        else:
                            # Handle regular fields
                            setattr(obj, field, value)

                    # Validate and save the object
                    if getattr(self, 'bulk_full_clean', True):
                        log.debug("running full_clean()")
                        obj.full_clean()  # This will raise ValidationError if validation fails
                    log.debug("running save()")
                    obj.save()
                    updated_count += 1
                    current += 1
                    if progress_callback:
                        progress_callback(current, total)

        except Exception as e:
            # If any exception occurs, the transaction is rolled back
            error_occurred = True
            error_message = str(e)
            log.error(f"Error during bulk update, transaction rolled back: {error_message}")

            # Directly add the error to our list
            if isinstance(e, ValidationError):
                # Handle different ValidationError formats
                if hasattr(e, 'message_dict'):
                    # This is a dictionary of field names to error messages
                    for field, messages in e.message_dict.items():
                        errors.append((field, messages))
                elif hasattr(e, 'messages'):
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
                'success': False,
                'success_records': 0,
                'errors': errors,
            }
        else:
            return {
                'success': True,
                'success_records': updated_count,
                'errors': [],
            }
