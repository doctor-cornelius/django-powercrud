"""
Async task functions for django-q2 (and future backends like Celery)
"""
import logging
from django.apps import apps
from .models import BulkTask
from .mixins.bulk_mixin import BulkMixin

log = logging.getLogger("powercrud")

def bulk_delete_task(
        task_id, model_path, selected_ids, 
        user_id
        ):
    """Core backend-agnostic bulk delete task"""
    task = BulkTask.objects.get(id=task_id)
    task.mark_started()
    
    try:
        model_class = apps.get_model(model_path)
        queryset = model_class.objects.filter(pk__in=selected_ids)
        
        # Use the shared business logic
        mixin = BulkMixin()
        result = mixin._perform_bulk_delete(queryset)
        
        if result['success']:
            task.processed_records = result['success_records']
            task.mark_completed(success=True)
        else:
            task.mark_completed(success=False, error_message=str(result['errors']))
            
    except Exception as e:
        log.error(f"Bulk delete task {task_id} failed: {e}")
        task.mark_completed(success=False, error_message=str(e))


def bulk_update_task(
        task_id, model_path, selected_ids, 
        user_id, 
        bulk_fields, fields_to_update, field_data
        ):
    """Core backend-agnostic bulk update task"""
    task = BulkTask.objects.get(id=task_id)
    task.mark_started()
    
    try:
        model_class = apps.get_model(model_path)
        queryset = model_class.objects.filter(pk__in=selected_ids)
        
        # Use the shared business logic  
        mixin = BulkMixin()
        result = mixin._perform_bulk_update(queryset, bulk_fields, fields_to_update, field_data)
        
        if result['success']:
            task.processed_records = result['success_records']
            task.mark_completed(success=True)
        else:
            task.mark_completed(success=False, error_message=str(result['errors']))
            
    except Exception as e:
        log.error(f"Bulk update task {task_id} failed: {e}")
        task.mark_completed(success=False, error_message=str(e))


# # Future: Celery wrappers
# try:
#     from celery import shared_task
    
#     @shared_task
#     def bulk_celery_delete_task(task_id, model_path, selected_ids, user_id):
#         return bulk_delete_task(task_id, model_path, selected_ids, user_id)
    
#     @shared_task  
#     def bulk_celery_update_task(task_id, model_path, selected_ids, user_id, bulk_fields, fields_to_update, field_data):
#         return bulk_update_task(task_id, model_path, selected_ids, user_id, bulk_fields, fields_to_update, field_data)
        
# except ImportError:
#     # Celery not available
#     pass
