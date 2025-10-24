"""
Async task functions for django-q2 (and future backends like Celery)
"""
from django.apps import apps

from powercrud.logging import get_logger

from .mixins.bulk_mixin import BulkMixin
from .async_manager import AsyncManager

log = get_logger(__name__)

def bulk_delete_task(
        model_path, selected_ids,
        user_id,
        **kwargs
        ):
    """
    Async bulk delete worker (django-q2 compatible).

    - No dependency on BulkTask ORM.
    - Reports progress via AsyncManager using task_key injected by AsyncManager.
    - Uses BulkMixin business logic for deletion.
    """
    manager_class_path = kwargs.pop('manager_class', None)
    manager_config = kwargs.pop('manager_config', None)
    # Retrieve task identifier injected by AsyncManager
    task_name = kwargs.pop('task_key', None) or kwargs.get('task_name')

    # DEBUG: Show what we actually received
    log.debug(f"[WORKER] bulk_delete_task STARTED")
    log.debug(f"[WORKER] extracted task_name={task_name}")
    log.debug(f"[WORKER] model_path={model_path}")
    log.debug(f"[WORKER] selected_ids={selected_ids}")
    log.debug(f"[WORKER] kwargs keys={list(kwargs.keys())}")

    try:
        manager = AsyncManager.resolve_manager(manager_class_path, config=manager_config)
        if task_name:
            manager.update_progress(task_name, "starting delete")

        model_class = apps.get_model(model_path)
        queryset = model_class.objects.filter(pk__in=selected_ids)

        # Use the shared business logic with progress callback
        mixin = BulkMixin()
        def progress_cb(current, total):
            if task_name:
                manager.update_progress(task_name, f"deleting: {current}/{total}")
        result = mixin._perform_bulk_delete(queryset, progress_callback=progress_cb)

        success = bool(result.get('success'))
        processed = int(result.get('success_records', 0))

        if task_name:
            if success:
                manager.update_progress(task_name, f"completed delete: {processed} processed")
            else:
                manager.update_progress(task_name, f"failed delete: {result.get('errors')}")

        return success

    except Exception as e:
        log.error(f"Bulk delete task failed: {e}", exc_info=True)
        try:
            if task_name:
                manager.update_progress(task_name, f"failed delete: {e}")
        except Exception:
            pass
        return False

def bulk_update_task(
        model_path, selected_ids, user_id,
        bulk_fields, fields_to_update, field_data,
        **kwargs
        ):
    """
    Async bulk update worker (django-q2 compatible).

    - No dependency on BulkTask ORM.
    - Reports progress via AsyncManager using task_key injected by AsyncManager.
    - Uses BulkMixin business logic for updates.
    """
    manager_class_path = kwargs.pop('manager_class', None)
    manager_config = kwargs.pop('manager_config', None)
    # Retrieve task identifier injected by AsyncManager
    task_name = kwargs.pop('task_key', None) or kwargs.get('task_name')

    # DEBUG: Show what we actually received
    log.debug(f"[WORKER] bulk_update_task STARTED")
    log.debug(f"[WORKER] extracted task_name={task_name}")
    log.debug(f"[WORKER] model_path={model_path}")
    log.debug(f"[WORKER] selected_ids={selected_ids}")
    log.debug(f"[WORKER] kwargs keys={list(kwargs.keys())}")

    try:
        manager = AsyncManager.resolve_manager(manager_class_path, config=manager_config)
        if task_name:
            manager.update_progress(task_name, "starting update")

        model_class = apps.get_model(model_path)
        queryset = model_class.objects.filter(pk__in=selected_ids)

        # Use the shared business logic with progress callback
        mixin = BulkMixin()
        def progress_cb(current, total):
            if task_name:
                manager.update_progress(task_name, f"updating: {current}/{total}")
        result = mixin._perform_bulk_update(queryset, bulk_fields, fields_to_update, field_data, progress_callback=progress_cb)

        success = bool(result.get('success'))
        processed = int(result.get('success_records', 0))

        if task_name:
            if success:
                manager.update_progress(task_name, f"completed update: {processed} processed")
            else:
                manager.update_progress(task_name, f"failed update: {result.get('errors')}")

        return success
             
    except Exception as e:
        log.error(f"Bulk update task failed: {e}", exc_info=True)
        try:
            if task_name:
                manager.update_progress(task_name, f"failed update: {e}")
        except Exception:
            pass
        return False


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
