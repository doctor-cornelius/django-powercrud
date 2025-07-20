from typing import List, Tuple
from django.conf import settings
import logging

log = logging.getLogger("nominopolitan")


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

    @classmethod
    def _generate_task_key(self, user, selected_ids, operation):
        """Generate unique task key to prevent duplicates"""
        import hashlib
        data = f"{user.id}:{sorted(selected_ids)}:{operation}:{self.model.__name__}"
        return hashlib.md5(data.encode()).hexdigest()
    
    @classmethod
    def _handle_async_bulk_operation(self, request, selected_ids, delete_selected, bulk_fields, fields_to_update):
        """Handle async bulk operations - create task and queue it"""
        from django_q.tasks import async_task
        from .models import BulkTask
        
        # Determine operation type
        operation = BulkTask.DELETE if delete_selected else BulkTask.UPDATE
        
        # Create task record
        task = BulkTask.objects.create(
            user=request.user,
            model_name=self.model.__name__,
            operation=operation,
            total_records=len(selected_ids),
            task_key=self._generate_task_key(request.user, selected_ids, operation)
        )
        
        model_path = f"{self.model._meta.app_label}.{self.model.__name__}"
        
        try:
            if delete_selected:
                # Queue delete task
                async_task('nominopolitan.tasks.bulk_delete_task', 
                        task.id, model_path, selected_ids, request.user.id)
            else:
                # Extract field data for update task
                field_info = self._get_bulk_field_info(bulk_fields)
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
                    })
                
                # Queue update task
                async_task('nominopolitan.tasks.bulk_update_task',
                        task.id, model_path, selected_ids, request.user.id,
                        bulk_fields, fields_to_update, field_data)
            
            # Return async success response
            response = HttpResponse("")
            response["HX-Trigger"] = json.dumps({
                "bulkEditQueued": True, 
                "taskId": task.id,
                "message": f"Processing {len(selected_ids)} records in background."
            })
            return response
            
        except Exception as e:
            # If queueing fails, fall back to sync processing
            log.warning(f"Async task queueing failed, falling back to sync: {e}")
            task.delete()  # Clean up failed task
            
            # Fall back to synchronous processing
            # You'd call your existing sync logic here
            return self._handle_sync_bulk_operation(request, queryset, bulk_fields, delete_selected, fields_to_update)

