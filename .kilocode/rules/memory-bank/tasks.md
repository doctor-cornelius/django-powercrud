# Async Processing Tasks

## Overview

Django Nominopolitan implements async processing for bulk operations to handle large datasets efficiently. The system supports multiple async backends and provides a unified interface for task management.

## Task Implementation

### Core Task Functions (`nominopolitan/tasks.py`)

The async processing is implemented through backend-agnostic task functions that can work with both django-q2 and Celery:

#### Bulk Delete Task
```python
def bulk_delete_task(task_id, model_path, selected_ids, user_id):
    """Core backend-agnostic bulk delete task"""
    - Retrieves BulkTask instance by ID
    - Marks task as started
    - Uses BulkMixin._perform_bulk_delete() for business logic
    - Updates task status and processed record count
    - Handles exceptions and error logging
```

#### Bulk Update Task
```python
def bulk_update_task(task_id, model_path, selected_ids, user_id, bulk_fields, fields_to_update, field_data):
    """Core backend-agnostic bulk update task"""
    - Retrieves BulkTask instance by ID
    - Marks task as started
    - Uses BulkMixin._perform_bulk_update() for business logic
    - Updates task status and processed record count
    - Handles exceptions and error logging
```

### Backend Support

#### Django-Q2 (Primary)
- **Configuration**: Uses database ORM for task storage
- **Workers**: Single worker configuration for development
- **Integration**: Direct function calls through django-q2's async_task()

#### Celery (Future Support)
- **Decorators**: @shared_task wrappers for Celery integration
- **Fallback**: Graceful handling when Celery is not available
- **Functions**: 
  - `bulk_celery_delete_task()`
  - `bulk_celery_update_task()`

## Task Lifecycle

### 1. Task Creation
- BulkTask model instance created with initial status
- Task parameters stored (model_path, selected_ids, operation type)
- User association for permission tracking

### 2. Task Execution
- Task marked as 'started' when picked up by worker
- Business logic executed through mixin methods
- Progress tracking through processed_records field
- Atomic operations ensure data consistency

### 3. Task Completion
- Success: Task marked as 'completed' with success=True
- Failure: Task marked as 'completed' with success=False and error message
- Results available for UI feedback

## Task Model (`nominopolitan/models.py`)

### BulkTask Fields
```python
class BulkTask(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    model_name = models.CharField(max_length=100)
    operation = models.CharField(choices=OPERATION_CHOICES)
    total_records = models.IntegerField()
    processed_records = models.IntegerField(default=0)
    status = models.CharField(choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    success = models.BooleanField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    async_backend = models.CharField(max_length=50, default='django-q2')
    operation_data = models.JSONField(default=dict, blank=True)
```

### Status Tracking
- **PENDING**: Task created but not yet started
- **STARTED**: Task picked up by worker and in progress
- **COMPLETED**: Task finished (check success field for outcome)
- **FAILED**: Task failed with error (deprecated in favor of completed + success=False)

## Integration with Bulk Operations

### Async Trigger Conditions
- Large dataset operations (configurable threshold)
- User preference for async processing
- System load considerations

### Synchronous Fallback
- Small datasets processed synchronously
- Immediate feedback for quick operations
- Error handling maintains consistency

### Progress Monitoring
- Real-time progress updates through BulkTask model
- UI polling for task status updates
- Completion notifications via HTMX triggers

## Configuration

### Django-Q2 Setup
```python
# settings.py
Q_CLUSTER = {
    'name': 'nominopolitan',
    'workers': 1,
    'recycle': 500,
    'timeout': 250,
    'retry': 300,
    'orm': 'default',
    'save_limit': 250,
    'queue_limit': 500,
}
```

### Task Parameters
- **Timeout**: 250 seconds for bulk operations
- **Retry**: 300 seconds retry interval
- **Workers**: Configurable based on system resources
- **Queue Limit**: 500 tasks maximum in queue

## Error Handling

### Exception Management
- All exceptions caught and logged
- Task status updated with error details
- User-friendly error messages provided
- System stability maintained

### Logging
- Comprehensive logging through nominopolitan logger
- Task lifecycle events tracked
- Error details preserved for debugging
- Performance metrics available

## Future Enhancements

### Planned Features
1. **Progress Callbacks**: Real-time progress updates during execution
2. **Task Cancellation**: Ability to cancel running tasks
3. **Batch Processing**: Chunked processing for very large datasets
4. **Result Caching**: Cache results for repeated operations
5. **Task Scheduling**: Scheduled bulk operations
6. **Multi-Backend**: Dynamic backend selection based on load

### Performance Optimizations
1. **Queryset Optimization**: Efficient database queries for bulk operations
2. **Memory Management**: Chunked processing to manage memory usage
3. **Connection Pooling**: Database connection optimization
4. **Parallel Processing**: Multi-worker support for large operations

## Usage Examples

### Triggering Async Bulk Delete
```python
# In BulkMixin
if should_use_async(selected_ids):
    task = BulkTask.objects.create(
        user=request.user,
        model_name=f"{model._meta.app_label}.{model._meta.model_name}",
        operation='delete',
        total_records=len(selected_ids)
    )
    async_task('nominopolitan.tasks.bulk_delete_task', 
               task.id, model_path, selected_ids, request.user.id)
```

### Monitoring Task Progress
```python
# Check task status
task = BulkTask.objects.get(id=task_id)
progress = {
    'status': task.status,
    'progress': task.processed_records / task.total_records * 100,
    'success': task.success,
    'error': task.error_message
}