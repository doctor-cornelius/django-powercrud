import logging
import json

from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.urls import path


log = logging.getLogger("nominopolitan")


# Create a standalone BulkEditRole class
class BulkEditRole:
    """A role for bulk editing that mimics the interface of Role"""
    
    def handlers(self):
        return {"get": "bulk_edit", "post": "bulk_edit"}
    
    def extra_initkwargs(self):
        return {"template_name_suffix": "_bulk_edit"}
    
    @property
    def url_name_component(self):
        return "bulk-edit"
    
    def url_pattern(self, view_cls):
        return f"{view_cls.url_base}/bulk-edit/"
    
    def get_url(self, view_cls):
        return path(
            self.url_pattern(view_cls),
            view_cls.as_view(role=self),
            name=f"{view_cls.url_base}-{self.url_name_component}",
        )


class BulkMixin:
    """
    Provides all bulk editing functionality for Nominopolitan views.
    """
    def get_bulk_edit_enabled(self):
        """
        Determine if bulk edit functionality should be enabled.
        
        Returns:
            bool: True if bulk edit is enabled (bulk_fields is not empty)
        """

        allowed = bool(
            (self.bulk_fields or self.bulk_delete)
            and (self.use_modal and self.use_htmx)
            )
        return allowed

    def get_bulk_delete_enabled(self):
        """
        Determine if bulk delete is allowed.

        Returns:
            bool: True if both get_bulk_edit_enabled and self.bulk_delete are True
        """
        return self.bulk_delete and self.get_bulk_edit_enabled()

    def get_bulk_fields_metadata(self):
        """
        Get metadata for bulk editable fields.
        
        Returns:
            list: List of dictionaries with field metadata
        """
        result = []

        for field_name in self.bulk_fields:
            try:
                model_field = self.model._meta.get_field(field_name)
                field_type = model_field.get_internal_type()
                verbose_name = model_field.verbose_name.title() if hasattr(model_field, 'verbose_name') else field_name.replace('_', ' ').title()

                result.append({
                    'name': field_name,
                    'verbose_name': verbose_name,
                    'type': field_type,
                    'is_relation': model_field.is_relation,
                    'null': model_field.null if hasattr(model_field, 'null') else False,
                    'config': config
                })
            except Exception as e:
                log.warning(f"Error processing bulk field {field_name}: {str(e)}")

        return result

    def get_storage_key(self):
        """
        Return the storage key for the bulk selection.
        """
        return f"nominopolitan_bulk_{self.model.__name__.lower()}_{self.get_bulk_selection_key_suffix()}"

    def get_bulk_selection_key_suffix(self):
        """
        Return a suffix to be appended to the bulk selection storage key.
        Override this method to add custom constraints to selection persistence.
        
        Returns:
            str: A string to append to the selection storage key
        """
        return ""

    def bulk_edit(self, request, *args, **kwargs):
        """
        Handle GET and POST requests for bulk editing.
        GET: Return a form for bulk editing selected objects
        POST: Process the form and update selected objects
        """
        # Ensure HTMX is being used for both GET and POST
        if not (hasattr(request, 'htmx') and request.htmx):
            from django.http import HttpResponseBadRequest
            return HttpResponseBadRequest("Bulk edit only supported via HTMX requests.")

        # Get selected IDs from the request
        selected_ids = request.POST.getlist('selected_ids[]') or request.GET.getlist('selected_ids[]')
        if not selected_ids:
            # If no IDs provided, try to get from JSON body
            try:
                if request.body and request.content_type == 'application/json':
                    data = json.loads(request.body)
                    selected_ids = data.get('selected_ids', [])
            except:
                pass
            # If still no IDs, check for individual selected_ids parameters
            if not selected_ids:
                selected_ids = request.POST.getlist('selected_ids') or request.GET.getlist('selected_ids')
        # If still no IDs, return an error
        if not selected_ids:
            return render(
                request,
                f"{self.templates_path}/partial/bulk_edit_error.html",
                {"error": "No items selected for bulk edit."}
            )
        # Get the queryset of selected objects
        queryset = self.model.objects.filter(pk__in=selected_ids)
        # Get bulk fields (fields that can be bulk edited)
        bulk_fields = getattr(self, 'bulk_fields', [])
        if not bulk_fields and not getattr(self, "bulk_delete", False):
            return render(
                request,
                f"{self.templates_path}/partial/bulk_edit_error.html",
                {"error": "No fields configured for bulk editing."}
            )
        # Handle form submission
        if request.method == 'POST' and 'bulk_submit' in request.POST:
            # If logic gets too large, move to a helper method
            return self.bulk_edit_process_post(
                request, queryset, bulk_fields, selected_ids
            )
        # Prepare context for the form
        context = {
            'selected_ids': selected_ids,
            'selected_count': len(selected_ids),
            'bulk_fields': bulk_fields,
            'enable_bulk_delete': self.get_bulk_delete_enabled(),
            'enable_bulk_edit': self.get_bulk_edit_enabled(),
            'model': self.model,
            'model_name': self.model.__name__.lower() if hasattr(self.model, '__name__') else '',
            'model_name_plural': self.model._meta.verbose_name_plural,
            'queryset': queryset,
            'field_info': self._get_bulk_field_info(bulk_fields),
            'storage_key': self.get_storage_key(),
            'original_target': self.get_original_target(),
        }
        # Render the bulk edit form
        return render(
            request,
            f"{self.templates_path}/partial/bulk_edit_form.html",
            context
        )

    def _perform_bulk_delete(self, queryset):
        deleted_count = 0
        errors = []
        # Call delete() on each object individually for model-specific logic
        try:
            with transaction.atomic():
            # Make bulk delete atomic
                for obj in queryset:
                    obj.delete()
                    deleted_count += 1
        except Exception as e:
            log.debug(f"Error during bulk delete, transaction rolled back: {e}")
            errors.append((None, [str(e)]))
        
        if errors:
            return {
                'success': False,
                'success_records': 0,
                'errors': errors,
            }
        else:
            return{
                'success': True,
                'success_records': deleted_count,
                'errors': [],
            }

    def _perform_bulk_update(
            self, queryset, 
            bulk_fields, fields_to_update, field_data,
            ):
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
                        obj.full_clean()  # This will raise ValidationError if validation fails
                    obj.save()
                    updated_count += 1

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

    def bulk_edit_process_post(
            self, request, queryset, bulk_fields,
            selected_ids=None,
            ):
        """
        Process the POST logic for bulk editing. Handles deletion and updates with atomicity.
        On success: returns an empty response and sets HX-Trigger for the main page to refresh the list.
        On error: re-renders the form with errors.
        """
        from .async_mixin import AsyncMixin

        delete_selected = request.POST.get('delete_selected')
        log.debug(f"Processing bulk edit for {len(selected_ids)} selected records")

        if delete_selected:
            if not self.get_bulk_delete_enabled():
                return HttpResponseForbidden("Bulk delete is not allowed.")

            # check if should process asynchronously
            if self.should_process_async(len(selected_ids)):
                log.debug(f"Processing bulk delete asynchronously for {len(selected_ids)} records.")
                return self._handle_async_bulk_operation(
                    request, selected_ids, delete_selected, bulk_fields, fields_to_update
                )

            # Synchronous processing
            result = self._perform_bulk_delete(queryset)
            success = result.get('success', False)
            errors = result.get('errors', [])
            deleted_count = result.get('success_records', 0)

            # Handle response based on errors
            if errors:
                context = {
                    "errors": errors,
                    "selected_ids": [obj.pk for obj in queryset],
                    "selected_count": queryset.count(),
                    "bulk_fields": bulk_fields,
                    "model": self.model,
                    "model_name": self.model.__name__.lower() if hasattr(self.model, '__name__') else '',
                    "model_name_plural": self.model._meta.verbose_name_plural,
                    "queryset": queryset,
                    "field_info": field_info,
                    "storage_key": self.get_storage_key(),
                    "original_target": self.get_original_target(),
                }
                response = render(
                    request,
                    f"{self.templates_path}/partial/bulk_edit_form.html",
                    context
                )

                # Use formError trigger and include showModal to ensure the modal stays open
                modal_id = self.get_modal_id()[1:]  # Remove the # prefix
                response["HX-Trigger"] = json.dumps({
                    "formError": True,
                    "showModal": modal_id,
                })

                # Make sure the response targets the modal content
                response["HX-Retarget"] = self.get_modal_target()
                log.debug(f"bulk delete errors: {errors}")
                return response

            else: # no errors
                response = HttpResponse("")
                response["HX-Trigger"] = json.dumps({"bulkEditSuccess": True, "refreshTable": True})
                log.debug(f"Bulk edit: Deleted {deleted_count} objects successfully.")
                return response

        # Bulk Update Logic

        fields_to_update = request.POST.getlist('fields_to_update')
        field_info = self._get_bulk_field_info(bulk_fields)
        
        # extract necessary data from the request
        field_data = []
        for field in fields_to_update:
                info = field_info.get(field, {})
                value = request.POST.get(field)

                # Extract M2M-specific data if this is an M2M field
                m2m_action = None
                m2m_values = []
                if info.get('is_m2m'):
                    m2m_action = request.POST.get(f"{field}_action", "replace")
                    m2m_values = request.POST.getlist(field)

                field_data.append({
                    'field': field, 
                    'value': value, 
                    'info': info,
                    'm2m_action': m2m_action,
                    'm2m_values': m2m_values,
                    }
                )

        result = self._perform_bulk_update(
            queryset, bulk_fields, fields_to_update, field_data
            )
        success = result.get('success', False)
        errors = result.get('errors', [])
        updated_count = result.get('success_records', 0)

        # Check if there were any errors during the update process
        log.debug(f"Bulk edit update errors: {errors}")
        if errors:
            context = {
                "errors": errors,
                "selected_ids": [obj.pk for obj in queryset],
                "selected_count": queryset.count(),
                "bulk_fields": bulk_fields,
                "model": self.model,
                "model_name": self.model.__name__.lower() if hasattr(self.model, '__name__') else '',
                "model_name_plural": self.model._meta.verbose_name_plural,
                "queryset": queryset,
                "field_info": field_info,
                "storage_key": self.get_storage_key(),
                "original_target": self.get_original_target(),
            }
            response = render(
                request,
                f"{self.templates_path}/partial/bulk_edit_form.html",
                context
            )

            # Use the same error handling as for delete errors
            modal_id = self.get_modal_id()[1:]  # Remove the # prefix
            response["HX-Trigger"] = json.dumps({
                "formError": True,
                "showModal": modal_id,
            })

            # Make sure the response targets the modal content
            response["HX-Retarget"] = self.get_modal_target()
            log.debug(f"Returning error response with {len(errors)} errors")
            return response
        
        else: # Success case (no errors)
            response = HttpResponse("")
            response["HX-Trigger"] = json.dumps({"bulkEditSuccess": True, "refreshTable": True})
            log.debug(f"Bulk edit: Updated {updated_count} objects successfully.")
            return response

    def _get_bulk_field_info(self, bulk_fields):
        """
        Get information about fields for bulk editing.
        
        Returns:
            dict: A dictionary mapping field names to their metadata
        """
        field_info = {}

        for field_name in bulk_fields:

            try:
                field = self.model._meta.get_field(field_name)

                # Get field type and other metadata
                field_type = field.get_internal_type()
                is_relation = field.is_relation
                is_m2m = field_type == 'ManyToManyField'

                # For related fields, get all possible related objects
                bulk_choices = None
                if is_relation and hasattr(field, 'related_model'):
                    # Use the related model's objects manager directly
                    bulk_choices = self.get_bulk_choices_for_field(field_name=field_name, field=field)

                field_info[field_name] = {
                    'field': field,
                    'type': field_type,
                    'is_relation': is_relation,
                    'is_m2m': is_m2m,  # Add a flag for M2M fields
                    'bulk_choices': bulk_choices,
                    'verbose_name': field.verbose_name,
                    'null': field.null if hasattr(field, 'null') else False,
                    'choices': getattr(field, 'choices', None),  # Add choices for fields with choices
                }
            except Exception as e:
                # Skip invalid fields
                print(f"Error processing field {field_name}: {str(e)}")
                continue

        return field_info

    def get_bulk_choices_for_field(self, field_name, field):
        """
        Hook to get the queryset for bulk_choices for a given field in bulk edit.

        By default, returns all objects for the related model.
        Override this in a subclass to restrict choices as needed.

        Args:
            field_name (str): The name of the field.
            field (models.Field): The Django model field instance.

        Returns:
            QuerySet or None: The queryset of choices, or None if not applicable.
        """
        if hasattr(field, 'related_model') and field.related_model is not None:
            qs = field.related_model.objects.all()
            
            # Apply dropdown sorting if configured
            sort_options = getattr(self, 'dropdown_sort_options', {})
            if field_name in sort_options:
                sort_field = sort_options[field_name]  # Can be "name" or "-name"
                qs = qs.order_by(sort_field)
            
            return qs
        return None