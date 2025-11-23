from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError
from typing import List, Tuple
from django.conf import settings
from django.shortcuts import render
from django.urls import reverse

from ..async_manager import AsyncManager
from powercrud.logging import get_logger
from .config_mixin import resolve_config

import json
log = get_logger(__name__)


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
       
        cfg = resolve_config(self)
        return bool(cfg.bulk_async and self.is_async_backend_available())

    def get_bulk_min_async_records(self) -> int:
        """
        Get the minimum number of records required to trigger async processing.
        
        Returns:
            int: Minimum record count for async processing
        """
        return resolve_config(self).bulk_min_async_records

    def get_bulk_async_backend(self) -> str:
        """
        Get the configured async backend.
        
        Returns:
            str: Backend name ('q2', 'celery', 'asgi')
        """
        return resolve_config(self).bulk_async_backend

    def get_bulk_async_notification(self) -> str:
        """
        Get the configured notification method for async operations.
        
        Returns:
            str: Notification method ('status_page', 'messages', 'email', 'callback', 'none')
        """
        return resolve_config(self).bulk_async_notification

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
        """Check if conflict checking is enabled using new AsyncManager system."""
           
        cfg = resolve_config(self)
        return bool(cfg.bulk_async_conflict_checking and self.get_bulk_async_enabled())

    def get_async_manager_class(self):
        """Return the AsyncManager class to use for this view.

        Resolution order:
        1. Explicit `async_manager_class` attribute (class/callable)
        2. Import path via `async_manager_class_path`
        3. Global `POWERCRUD_SETTINGS["ASYNC_MANAGER_DEFAULT"]["manager_class"]`
        4. Base `AsyncManager`
        """
        cfg = resolve_config(self)
        manager_cls = getattr(self, "async_manager_class", None) or getattr(cfg, "async_manager_class", None)
        if manager_cls:
            return manager_cls

        path = getattr(self, "async_manager_class_path", None) or getattr(cfg, "async_manager_class_path", None)
        if path:
            return self._import_manager(path)

        from powercrud.conf import get_powercrud_setting

        default_cfg = get_powercrud_setting("ASYNC_MANAGER_DEFAULT", {}) or {}
        default_path = default_cfg.get("manager_class")
        if default_path:
            return self._import_manager(default_path)

        return AsyncManager

    def _import_manager(self, dotted_path: str):
        from importlib import import_module

        module_path, class_name = dotted_path.rsplit(".", 1)
        module = import_module(module_path)
        return getattr(module, class_name)

    def get_async_manager_class_path(self) -> str:
        cfg = resolve_config(self)
        path = getattr(self, "async_manager_class_path", None) or getattr(cfg, "async_manager_class_path", None)
        if path:
            return path

        manager_class = getattr(self, "async_manager_class", None) or getattr(cfg, "async_manager_class", None)
        if manager_class:
            return f"{manager_class.__module__}.{manager_class.__name__}"

        from powercrud.conf import get_powercrud_setting

        default_cfg = get_powercrud_setting("ASYNC_MANAGER_DEFAULT", {}) or {}
        default_path = default_cfg.get("manager_class")
        if default_path:
            return default_path

        manager_class = self.get_async_manager_class()
        return f"{manager_class.__module__}.{manager_class.__name__}"

    def get_async_manager_config(self):
        cfg = resolve_config(self)
        if cfg.async_manager_config is not None:
            return cfg.async_manager_config
        from powercrud.conf import get_powercrud_setting

        default_cfg = get_powercrud_setting("ASYNC_MANAGER_DEFAULT", {}) or {}
        return default_cfg.get("config")

    def get_async_manager(self):
        manager_class = self.get_async_manager_class()
        config = self.get_async_manager_config()

        if config is None:
            return manager_class()

        try:
            coerced_config = self._coerce_manager_config(manager_class, config)
            if coerced_config is None:
                return manager_class()
            return manager_class(config=coerced_config)
        except TypeError:
            # Some manager classes may not accept config kwarg
            return manager_class()

    def _coerce_manager_config(self, manager_class, config):
        if config is None:
            return None

        if isinstance(config, dict):
            try:
                from powercrud.async_dashboard import (
                    AsyncDashboardConfig,
                    ModelTrackingAsyncManager,
                )

                if issubclass(manager_class, ModelTrackingAsyncManager):
                    return AsyncDashboardConfig(**config)
            except Exception:
                return config

        return config

    def _check_for_conflicts(self, selected_ids=None):
        """Check for conflicts using new AsyncManager conflict detection system."""
        if not self.get_bulk_async_enabled():
            return False
            
        try:
            async_manager = self.get_async_manager()
            if not selected_ids:
                return False

            model_name = f"{self.model._meta.app_label}.{self.model._meta.model_name}"
            normalized_ids = [str(pk) for pk in selected_ids]
            conflict_data = {model_name: normalized_ids}
            conflicts = async_manager.check_conflict(conflict_data)
            return len(conflicts) > 0
                
        except Exception as e:
            log.error(f"Error checking conflicts: {e}")
            return False

    def _check_single_record_conflict(self, pk):
        """Check if a single record is involved in any bulk operation"""
        if pk is None:
            return False
        return self._check_for_conflicts(selected_ids=[pk])

    def _render_conflict_response(self, request, pk, operation):
        """Render conflict response for single operations"""
        conflict_message = (
            f"Cannot {operation} - bulk operation in progress on "
            f"{self.model._meta.verbose_name_plural}. Please try again later."
        )
        context = {
            'conflict_detected': True,
            'conflict_message': conflict_message,
            'object': getattr(self, 'object', None),
        }

        if hasattr(request, 'htmx') and request.htmx:
            if operation == "delete":
                template = f"{self.templates_path}/object_confirm_delete.html#conflict_detected"
            else:
                template = f"{self.templates_path}/object_form.html#conflict_detected"
            return render(request, template, context)

        # Fallback: simple HTTP response
        return HttpResponse(conflict_message, status=409)

    def _render_bulk_conflict_response(self, request, selected_ids, delete_selected):
        """Render conflict response for bulk operations"""
        operation = "delete" if delete_selected else "update"
        context = {
            'conflict_detected': True,
            'conflict_message': f"Another bulk operation is already running on {self.model._meta.verbose_name_plural}. Please try again later.",
            'selected_count': len(selected_ids),
            'model_name_plural': self.model._meta.verbose_name_plural,
        }
        return render(
            request,
            f"{self.templates_path}/partial/bulk_edit_errors.html#bulk_edit_conflict",
            context
        )

    def _generate_task_key(self, user, selected_ids, operation):
        """Generate task key for duplicate prevention"""
        # Use the storage key + operation as base
        storage_key = self.get_storage_key()  # e.g., "powercrud_bulk_book_"
        operation_type = "delete" if str(operation).lower() == "delete" else "update"
        
        # Add timestamp to make it unique per attempt
        import time
        timestamp = int(time.time())
        
        return f"{storage_key}_{operation_type}_{timestamp}"

    def confirm_delete(self, request, *args, **kwargs):
        """Override to check for conflicts before showing delete confirmation"""
        pk = kwargs.get(getattr(self, "pk_url_kwarg", "pk")) or kwargs.get('id')
        if pk is None:
            obj = self.get_object()
            self.object = obj
            pk = obj.pk
        if self.get_conflict_checking_enabled() and self._check_for_conflicts(selected_ids=[pk]):
            self.object = getattr(self, "object", None) or self.get_object()
            context = self.get_context_data(
                conflict_detected=True,
                conflict_message=(
                    f"Cannot delete - bulk operation in progress on "
                    f"{self.model._meta.verbose_name_plural}. Please try again later."
                )
            )
            return self.render_to_response(context)
        
        # No conflict, proceed normally
        return super().confirm_delete(request, *args, **kwargs)
    
    def process_deletion(self, request, *args, **kwargs):
        """Override to check for conflicts before actual deletion"""
        pk = kwargs.get(getattr(self, "pk_url_kwarg", "pk")) or kwargs.get('id')
        if self.get_conflict_checking_enabled() and pk and self._check_for_conflicts(selected_ids=[pk]):
            # For HTMX, return conflict response
            if hasattr(request, 'htmx') and request.htmx:
                return self._render_conflict_response(request, pk, "delete")
            else:
                # Redirect back to confirm_delete with conflict
                return self.confirm_delete(request, *args, **kwargs)
        
        # No conflict, proceed with deletion
        return super().process_deletion(request, *args, **kwargs)

    def _handle_async_bulk_operation(self, request, selected_ids, delete_selected, bulk_fields, fields_to_update, field_data):
        """Handle async bulk operations using new AsyncManager system"""
        log.debug("running _handle_async_bulk_operation with new AsyncManager")

        # ✅ Check authentication if required
        cfg = resolve_config(self)
        user = getattr(request, 'user', None)
        if not user or user.is_anonymous:
            if not cfg.bulk_async_allow_anonymous:
                return HttpResponseForbidden("Authentication required for bulk operations")
            user = None  # Handle anonymous user

        # ✅ Check for conflicts using new system
        if self.get_conflict_checking_enabled() and self._check_for_conflicts(selected_ids):
            return self._render_bulk_conflict_response(request, selected_ids, delete_selected)

        # Initialize AsyncManager
        try:
            async_manager = self.get_async_manager()
        except Exception as e:
            log.error(f"Failed to initialize AsyncManager: {e}")
            return HttpResponseServerError("Async system unavailable")

        # Prepare conflict_ids for new system
        model_name = f"{self.model._meta.app_label}.{self.model._meta.model_name}"
        conflict_ids = {model_name: set(map(int, selected_ids))}
        
        # Prepare task arguments
        model_path = f"{self.model._meta.app_label}.{self.model.__name__}"
        user_id = user.id if user else None

        # Generate task_name BEFORE calling launch_async_task
        task_name = async_manager.generate_task_name()
        
        try:
            if delete_selected:
                log.debug(f"Launching async bulk delete task for {len(selected_ids)} records")
                # Launch delete task using new AsyncManager
                async_manager.launch_async_task(
                    'powercrud.tasks.bulk_delete_task',   # positional arg 1
                    model_path,                          # positional arg 2
                    selected_ids,                        # positional arg 3
                    user_id,                             # positional arg 4
                    task_name,                           # positional arg 5 - THIS IS THE KEY!
                    # django-q2 specific params as kwargs
                    conflict_ids=conflict_ids,
                    user=user,
                    affected_objects=f"{len(selected_ids)} {self.model._meta.verbose_name_plural}",
                    manager_class=self.get_async_manager_class_path(),
                    manager_config=self.get_async_manager_config(),
                )
            else:
                log.debug(f"Launching async bulk update task for {len(selected_ids)} records")
                # Launch update task using new AsyncManager
                async_manager.launch_async_task(
                    'powercrud.tasks.bulk_update_task',  # positional arg 1
                    model_path,                          # positional arg 2
                    selected_ids,                        # positional arg 3
                    user_id,                             # positional arg 4
                    bulk_fields,                         # positional arg 5
                    fields_to_update,                    # positional arg 6
                    field_data,                          # positional arg 7
                    task_name,                           # positional arg 8 - THIS IS THE KEY!
                    # django-q2 specific params as kwargs
                    conflict_ids=conflict_ids,
                    user=user,
                    affected_objects=f"{len(selected_ids)} {self.model._meta.verbose_name_plural}",
                    manager_class=self.get_async_manager_class_path(),
                    manager_config=self.get_async_manager_config(),
                )            
            # Success - return response with task_key for progress polling
            return self.async_queue_success(request, task_name, selected_ids)

        except Exception as e:
            log.error(f"Failed to launch async task: {e}")
            return self.async_queue_failure(request, error=e, selected_ids=selected_ids)
        
    def async_queue_success(self, request, task_name: str, selected_ids: List[int]):  # pragma: no cover
        """
        Processes successful async task queueing using new AsyncManager system.
        Clears selection and returns success response with task_name for progress polling.
  
        Can be overridden to customize or extend success handling.
        """
        self.clear_selection_from_session(request)
  
        # Return async success response with task_name for progress polling
        template = f"{self.templates_path}/bulk_edit_form.html#async_queue_success"
        progress_url = reverse("powercrud:async_progress")
        response = render(request, template, context={
            'task_name': task_name,
            'selected_count': len(selected_ids),
            'model_name_plural': self.model._meta.verbose_name_plural,
            'progress_url': progress_url,
        })
        response["HX-ReTarget"] = self.get_modal_target()
        response["HX-Trigger"] = json.dumps({
            "bulkEditQueued": True,
            "taskName": task_name,
            "message": f"Processing {len(selected_ids)} records in background."
        })
        return response

   
    def async_queue_failure(self, request, error: Exception, selected_ids: List[int]):  # pragma: no cover
        """
        Handles failure during async task queueing using new AsyncManager system.
        
        Can be overridden to customize or extend failure handling.
        """
        # ✅ Log the error
        log.error(f"Async task queueing failed: {str(error)}", exc_info=True)

        # Return error response
        template_errors = f"{self.templates_path}/partial/bulk_edit_errors.html"

        response = render(
            request, f"{template_errors}#bulk_edit_error", context={
                'error': f"Failed to queue background task for {len(selected_ids)} {self.model._meta.verbose_name_plural}:\n\n{str(error)}",
            }
        )
        response['HX-ReTarget'] = self.get_modal_target()
        return response
