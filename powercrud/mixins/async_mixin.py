from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError
from typing import List, Tuple
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import render


from django_q.tasks import async_task

from ..models import BulkTask

import json
import logging
log = logging.getLogger("powercrud")


class AsyncMixin:
    """
    Provides asynchronous bulk processing capabilities.
    """
    # bulk async methods
    def get_bulk_async_enabled(self) -> bool:
        """
        Determine if async bulk processing should be enabled.
        
        Returns:
            bool: True if async processing is enabled and backend is available
        """
        return self.bulk_async and self.is_async_backend_available()

    def get_bulk_min_async_records(self) -> int:
        """
        Get the minimum number of records required to trigger async processing.
        
        Returns:
            int: Minimum record count for async processing
        """
        return self.bulk_min_async_records

    def get_bulk_async_backend(self) -> str:
        """
        Get the configured async backend.
        
        Returns:
            str: Backend name ('database', 'celery', 'asgi')
        """
        return self.bulk_async_backend

    def get_bulk_async_notification(self) -> str:
        """
        Get the configured notification method for async operations.
        
        Returns:
            str: Notification method ('status_page', 'messages', 'email', 'callback', 'none')
        """
        return self.bulk_async_notification

    def should_process_async(self, record_count: int) -> bool:
        """
        Determine if a bulk operation should be processed asynchronously.
        
        Args:
            record_count: Number of records to be processed
            
        Returns:
            bool: True if operation should be async, False for sync processing
        """
        log.debug("running should_process_async")
        if not self.get_bulk_async_enabled():
            log.debug("async not enabled")
            return False
        result = record_count >= self.get_bulk_min_async_records()
        log.debug(f"should_process_async: {result} for {record_count} records")
        return result
   
    def is_async_backend_available(self) -> bool:
        """
        Check if the configured async backend is available and properly configured.
        
        Returns:
            bool: True if backend is available, False otherwise
        """
        backend = self.get_bulk_async_backend()
        
        if backend == 'q2':
            try:
                import django_q
                
                # Check if django_q is in INSTALLED_APPS
                if 'django_q' not in settings.INSTALLED_APPS:
                    return False
                    
                # Basic check - more comprehensive validation can be added later
                return True
                
            except ImportError:
                return False
        
        # Future backends (celery, etc.) would be checked here
        return False

    def validate_async_configuration(self) -> Tuple[bool, List[str]]:
        """
        Placeholder for validating async config.
        """

        return (False, [])

    def get_conflict_checking_enabled(self):
        return (
            self.bulk_async_conflict_checking 
            and self.get_bulk_async_enabled()
        )

 
    def _check_for_conflicts(self):
        """Get all active bulk tasks for this model & suffix combo"""
        unique_model_key = self.get_storage_key()
        
        return BulkTask.objects.filter(
            unique_model_key=unique_model_key,
            # Could add suffix logic here if get_storage_key() includes it
            status__in=[BulkTask.PENDING, BulkTask.STARTED]
        ).exists()

    def _check_single_record_conflict(self, pk):
        """Check if a single record is involved in any bulk operation"""
        # For now, just check model+suffix level
        return self._check_for_conflicts()

    def _render_conflict_response(self, request, pk, operation):
        """Render conflict response for single operations"""
        if hasattr(request, 'htmx') and request.htmx:
            # HTMX response
            response = HttpResponse("")
            response["HX-Trigger"] = json.dumps({
                "operationBlocked": True,
                "message": f"Cannot {operation} - bulk operation in progress on {self.model._meta.verbose_name_plural}. Please try again later."
            })
            return response
        else:
            # Regular HTTP response - redirect with message?
            # Or render an error page
            pass

    def _render_bulk_conflict_response(self, request, selected_ids, delete_selected):
        """Render conflict response for bulk operations"""
        operation = "delete" if delete_selected else "update"
        response = HttpResponse("")
        response["HX-Trigger"] = json.dumps({
            "bulkConflict": True,
            "message": f"Another bulk operation is already running on {self.model._meta.verbose_name_plural}. Please try again later."
        })
        return response

    def _generate_task_key(self, user, selected_ids, operation):
        """Generate task key for duplicate prevention"""
        # Use the storage key + operation as base
        storage_key = self.get_storage_key()  # e.g., "powercrud_bulk_book_"
        operation_type = "delete" if operation == BulkTask.DELETE else "update"
        
        # Add timestamp to make it unique per attempt
        import time
        timestamp = int(time.time())
        
        return f"{storage_key}_{operation_type}_{timestamp}"

    def confirm_delete(self, request, *args, **kwargs):
        """Override to check for conflicts before showing delete confirmation"""
        if self.get_conflict_checking_enabled() and self._check_for_conflicts():
            pk = kwargs.get('pk') or kwargs.get('id') 
            if self._check_for_conflicts():  # Model+suffix level for now
                # Add conflict flag to context
                self.object = self.get_object()
                context = self.get_context_data(
                    conflict_detected=True,
                    conflict_message=f"Cannot delete - bulk operation in progress on {self.model._meta.verbose_name_plural}. Please try again later."
                )
                return self.render_to_response(context)
        
        # No conflict, proceed normally
        return super().confirm_delete(request, *args, **kwargs)
    
    def process_deletion(self, request, *args, **kwargs):
        """Override to check for conflicts before actual deletion"""
        if self.get_conflict_checking_enabled() and self._check_for_conflicts():
            # For HTMX, return conflict response
            if hasattr(request, 'htmx') and request.htmx:
                response = HttpResponse("")
                response["HX-Trigger"] = json.dumps({
                    "operationBlocked": True,
                    "message": f"Cannot delete - bulk operation in progress."
                })
                return response
            else:
                # Redirect back to confirm_delete with conflict
                return self.confirm_delete(request, *args, **kwargs)
        
        # No conflict, proceed with deletion
        return super().process_deletion(request, *args, **kwargs)

    def _handle_async_bulk_operation(self, request, selected_ids, delete_selected, bulk_fields, fields_to_update, field_data):
        """Handle async bulk operations - create task and queue it"""
        log.debug("running _handle_async_bulk_operation")

        # ✅ Check authentication if required
        user = getattr(request, 'user', None)
        if not user or user.is_anonymous:
            if not self.bulk_async_allow_anonymous:
                return HttpResponseForbidden("Authentication required for bulk operations")
            user = None  # Handle anonymous user

        # ✅ Check for conflicts first
        if self.get_conflict_checking_enabled() and self._check_for_conflicts():
            return self._render_bulk_conflict_response(request, selected_ids, delete_selected)

        # Determine operation type
        operation = BulkTask.DELETE if delete_selected else BulkTask.UPDATE
        
        # Create task record
        task = BulkTask.objects.create(
            async_backend=self.get_bulk_async_backend(),
            user=user,
            model_name=f"{self.model._meta.app_label}.{self.model.__name__}",
            operation=BulkTask.DELETE if delete_selected else BulkTask.UPDATE,
            total_records=len(selected_ids),
            unique_model_key=self.get_storage_key(),
            task_key=self._generate_task_key(request.user, selected_ids, operation)
        )
        model_path = f"{self.model._meta.app_label}.{self.model.__name__}"
        
        try:
            if delete_selected:
                log.debug(f"Queueing async bulk delete task for {len(selected_ids)} records")
                # Queue delete task
                async_task('powercrud.tasks.bulk_delete_task', 
                        task.id, model_path, selected_ids, request.user.id)
                return self.async_queue_success(request, task, selected_ids)
            else:
                # Queue update task
                async_task('powercrud.tasks.bulk_update_task',
                        task.id, model_path, selected_ids, request.user.id,
                        bulk_fields, fields_to_update, field_data)
            
                # Successful queue handling
                return self.async_queue_success(request, task, selected_ids)

        except Exception as e:
            return self.async_queue_failure(request, task=task, error=e, selected_ids=selected_ids)
        
    def async_queue_success(self, request, task: BulkTask, selected_ids: List[int]):
        """
        Processes successful async task queueing. Clears selection and returns success response.

        Can be overridden to customize or extend success handling.
        """

        self.clear_selection_from_session(request)

        # Return async success response
        template = "powercrud/daisyUI/bulk_edit_form.html#async_queue_success"
        response = render(request, template, context={})
        response["HX-ReTarget"] = self.get_modal_target()
        response["HX-Trigger"] = json.dumps({
            "bulkEditQueued": True, 
            "taskId": task.id,
            "message": f"Processing {len(selected_ids)} records in background."
        })
        return response
    
    def async_queue_failure(self, request, task: BulkTask, error: str, selected_ids: List[int]):
        """
        Handles failure during async task queueing. Logs error and returns error response.
        Note there is no BulkTask instance since the task failed to be queued.

        Can be overridden to customize or extend failure handling.
        """
        # ✅ Log the error and fail hard
        log.error(f"Async task queueing failed for task {task.id}: {str(error)}", exc_info=True)
        
        # Mark task as failed
        task.mark_completed(success=False, error_message=f"Failed to queue task: {str(error)}")

        # Return error response
        template_errors = f"{self.templates_path}/partial/bulk_edit_errors.html"

        response = render(
            request, f"{template_errors}#bulk_edit_error", context={
                'error': f"Failed to queue background tasks for {len(selected_ids)} {self.model._meta.verbose_name_plural}:\n\n{str(error)}",
                'task_id': task.id,
                'task': task
            }
        )
        response['HX-ReTarget'] = self.get_modal_target()
        return response
