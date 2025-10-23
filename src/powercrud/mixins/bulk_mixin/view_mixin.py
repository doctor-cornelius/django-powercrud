import logging
import json
from typing import Any, Dict, List, Optional

from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import render
from django.core.exceptions import SuspiciousOperation
from django.db import models

log = logging.getLogger("powercrud")


class ViewMixin:
    """
    Provides view handling functionality for bulk operations.
    Handles context preparation, bulk edit form display, and form processing.
    """

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Add bulk selection context to the template rendering data.
        
        IMPORTANT: This method participates in Django's Method Resolution Order (MRO) chain.
        It calls super().get_context_data(**kwargs) to receive context from earlier mixins
        (like UrlMixin which provides URLs, HTMX settings, etc.), then adds bulk-specific
        context for selection state and page-level selection tracking.
        
        MRO Context Flow: UrlMixin (URLs/settings) → Other mixins → ViewMixin (bulk selection)
        The final context contains both URL-related data AND bulk selection state, allowing
        templates to render both navigation links and selection checkboxes/counts properly.
        
        This method was extracted from the original monolithic BulkMixin during refactoring
        and works in conjunction with SelectionMixin (handles session storage) and other
        bulk mixins via the composite BulkMixin pattern.

        Args:
            **kwargs: Additional keyword arguments passed through the MRO chain.

        Returns:
            dict: Extended context with bulk selection data added to parent context.
        """
        context = super().get_context_data(**kwargs)
        selected_ids = self.get_selected_ids_from_session(self.request)
        context['selected_ids'] = selected_ids
        context['selected_count'] = len(selected_ids)
        # Determine if all items on the current page are selected
        # This requires object_list to be available in context
        if 'object_list' in context:
            current_page_ids = set(str(obj.pk) for obj in context['object_list'])
            all_selected_on_page = current_page_ids.issubset(set(selected_ids))
            some_selected_on_page = bool(current_page_ids.intersection(set(selected_ids)))
            context['all_selected'] = all_selected_on_page and len(current_page_ids) > 0
            context['some_selected'] = some_selected_on_page and not all_selected_on_page
        else:
            context['all_selected'] = False
            context['some_selected'] = False
        return context

    def bulk_edit(self, request, *args, **kwargs) -> HttpResponse:
        """
        Handle GET and POST requests for bulk editing.

        GET: Return a form for bulk editing selected objects.
        POST: Process the form and update selected objects.

        Args:
            request: The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            HttpResponse: The response containing the form or processing result.
        """
        template_name = f"{self.templates_path}/bulk_edit_form.html#full_form"
        template_errors = f"{self.templates_path}/partial/bulk_edit_errors.html"
        # Ensure HTMX is being used for both GET and POST
        if not hasattr(request, 'htmx'):
            return HttpResponseBadRequest("Bulk edit only supported via HTMX requests.")

        # Get selected IDs from the request
        selected_ids = []
        try:
            selected_ids = request.POST.getlist('selected_ids[]') or request.GET.getlist('selected_ids[]')

            if not selected_ids:
                # If no IDs provided via POST/GET, try to get from session first
                selected_ids = self.get_selected_ids_from_session(request)

                if not selected_ids:
                    # If still no IDs, try to get from JSON body
                    try:
                        if request.body and request.content_type == 'application/json':
                            data = json.loads(request.body)
                            selected_ids = data.get('selected_ids', [])
                    except:
                        pass
                    # If still no IDs, check for individual selected_ids parameters (without [])
                    if not selected_ids:
                        selected_ids = request.POST.getlist('selected_ids') or request.GET.getlist('selected_ids')
        except SuspiciousOperation as e:
            log.error(f"SuspiciousOperation during bulk edit parameter retrieval: {e}")
            return render(
                request,
                f"{template_errors}#bulk_edit_error",
                {"error": "Too many items selected for bulk edit. Please select fewer items or contact your administrator to increase DATA_UPLOAD_MAX_NUMBER_FIELDS."}
            )
        except Exception as e:
            log.error(f"Unexpected error during bulk edit parameter retrieval: {e}")
            return render(
                request,
                f"{template_errors}#bulk_edit_error",
                {"error": f"An unexpected error occurred: {e}"}
            )

        # If still no IDs, return an error
        if not selected_ids:
            return render(
                request,
                f"{template_errors}#bulk_edit_error",
                {"error": "No items selected for bulk edit."}
            )
        # Get the queryset of selected objects
        queryset = self.model.objects.filter(pk__in=selected_ids)

        # Check for conflicts before showing the form
        if (self.get_conflict_checking_enabled() and 
            self._check_for_conflicts(selected_ids)):
            # Show conflict message instead of form
            context = {
                'conflict_detected': True,
                'conflict_message': f"Another bulk operation is already running on {self.model._meta.verbose_name_plural}. Please try again later.",
                'selected_count': len(selected_ids),
                'model_name_plural': self.model._meta.verbose_name_plural,
            }
            return render(
                request,
                f"{template_errors}#bulk_edit_conflict",
                context
            )

        # Get bulk fields (fields that can be bulk edited)
        bulk_fields = getattr(self, 'bulk_fields', [])
        if not bulk_fields and not getattr(self, "bulk_delete", False):
            return render(
                request,
                f"{template_errors}#bulk_edit_error",
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
            'selected_ids': [str(pk) for pk in queryset.values_list('pk', flat=True)], # Ensure selected_ids in context reflect the actual queryset
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
        log.debug(f"bulk_edit: template_name = {template_name}")
        response = render(request, template_name, context)
        return response

    def bulk_edit_process_post(
            self,
            request,
            queryset: models.QuerySet,
            bulk_fields: List[str],
            selected_ids: Optional[List[str]] = None,
            ) -> HttpResponse:
        """
        Process the POST logic for bulk editing. Handles deletion and updates with atomicity.

        On success: returns an empty response and sets HX-Trigger for the main page to refresh the list.
        On error: re-renders the form with errors.

        Args:
            request: The HTTP request object.
            queryset: QuerySet of objects to process.
            bulk_fields: List of fields available for bulk editing.
            selected_ids: List of selected IDs (optional, defaults to None).

        Returns:
            HttpResponse: Success response or error form rendering.
        """
        field_info = self._get_bulk_field_info(bulk_fields)        
        # extract necessary data from the request
        delete_selected = request.POST.get('delete_selected')
        fields_to_update = request.POST.getlist('fields_to_update')
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

        log.debug(f"Processing bulk edit for {len(selected_ids)} selected records")
        if delete_selected:
            if not self.get_bulk_delete_enabled():
                return HttpResponseForbidden("Bulk delete is not allowed.")

            # check if should process asynchronously
            if self.should_process_async(len(selected_ids)):
                log.debug(f"Processing bulk delete asynchronously for {len(selected_ids)} records.")
                return self._handle_async_bulk_operation(
                    request, selected_ids, 
                    delete_selected, 
                    bulk_fields, fields_to_update, field_data = []
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
                    "selected_ids": [str(pk) for pk in queryset.values_list('pk', flat=True)], # Ensure selected_ids in context reflect the actual queryset
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
                    f"{self.templates_path}/bulk_edit_form.html",
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
                log.debug(f"BulkMixin: bulk_edit_process_post (DELETE ERROR) - Returning response of type {type(response)}")
                log.debug(f"BulkMixin: bulk_edit_process_post (DELETE ERROR) - Response content (first 500 chars): {response.content.decode('utf-8')[:500]}")
                log.debug(f"BulkMixin: bulk_edit_process_post (DELETE ERROR) - Response headers: {response.headers}")
                return response

            else: # no errors
                self.clear_selection_from_session(request)
                response = HttpResponse("")
                response["HX-Trigger"] = json.dumps({
                    "bulkEditSuccess": True, "refreshTable": True
                    })
                log.debug(f"Bulk edit: Deleted {deleted_count} objects successfully.")
                log.debug(f"BulkMixin: bulk_edit_process_post (DELETE SUCCESS) - Returning response of type {type(response)}")
                log.debug(f"BulkMixin: bulk_edit_process_post (DELETE SUCCESS) - Response content: {response.content.decode('utf-8')}")
                log.debug(f"BulkMixin: bulk_edit_process_post (DELETE SUCCESS) - Response headers: {response.headers}")
                return response

        # Bulk Update Logic
        # Check whether async processing required
        if self.should_process_async(len(selected_ids)):
            log.debug(f"Processing bulk update asynchronously for {len(selected_ids)} records.")
            return self._handle_async_bulk_operation(
                request, selected_ids, 
                delete_selected,  # This will be None/False
                bulk_fields, fields_to_update, field_data
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
                "selected_ids": [str(pk) for pk in queryset.values_list('pk', flat=True)], # Ensure selected_ids in context reflect the actual queryset
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
                f"{self.templates_path}/bulk_edit_form.html",
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
            log.debug(f"BulkMixin: bulk_edit_process_post (UPDATE ERROR) - Returning response of type {type(response)}")
            log.debug(f"BulkMixin: bulk_edit_process_post (UPDATE ERROR) - Response content (first 500 chars): {response.content.decode('utf-8')[:500]}")
            log.debug(f"BulkMixin: bulk_edit_process_post (UPDATE ERROR) - Response headers: {response.headers}")
            return response
        
        else: # Success case (no errors)
            self.clear_selection_from_session(request)
            response = HttpResponse("")
            response["HX-Trigger"] = json.dumps({
                "bulkEditSuccess": True, "refreshTable": True
                })
            log.debug(f"Bulk edit: Updated {updated_count} objects successfully.")
            return response
