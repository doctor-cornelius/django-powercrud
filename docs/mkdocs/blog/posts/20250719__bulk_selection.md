---
date: 2025-07-19
categories:
  - django
  - bulk
  - edit
---
# Plan for Background Processing for Long-Running Tasks

The current bulk edit functionality is synchronous and can take 30+ seconds for large datasets, creating poor UX with browser timeouts and user confusion. We need to implement asynchronous processing with progress tracking and user notifications.
<!-- more -->

## Strategy: Configurable with Graceful Degradation

The implementation will support multiple async backends while maintaining backward compatibility:

1. **Default**: Include `django-q2` as a standard dependency for database-based task queuing
2. **Fallback**: Graceful degradation to synchronous processing if async is disabled or unavailable
3. **Extensible**: Architecture supports future backends (Celery, ASGI) without breaking changes
4. **Smart Thresholds**: Small operations remain synchronous for better UX

## Configuration Options

```python
class NominopolitanMixin:
   bulk_async = True  # Default enabled since django-q2 included
   bulk_min_async_records = 20  # Sync for operations below this threshold
   bulk_async_backend = 'q2'  # 'q2', 'celery', 'asgi' (future)
   bulk_async_notification = 'status_page'  # 'status_page', 'messages', 'email', 'callback', 'none'
```

## Backend Implementation Plan

**Phase 1: Database Backend (django-q2)**
- Include `django-q2` as standard dependency
- No additional infrastructure required for downstream users
- Uses existing database for task storage and processing
- Suitable for most use cases up to medium scale

**Future Phases:**
- **Celery Backend**: For high-volume production environments
- **ASGI Backend**: For Django 4.1+ async views (single-server deployments)

## User Experience Flow

1. **Small Operations** (< `bulk_min_async_records`):
  - Process synchronously as current behavior
  - Immediate feedback and completion

2. **Large Operations** (≥ `bulk_min_async_records`):
  - Queue task in background
  - Show immediate confirmation: "Processing X records in background. [View Status]"
  - User can continue working or monitor progress
  - Completion notification via configured method

## Status Tracking System

**BulkTask Model:**
```python
class BulkTask(models.Model):
   user = ForeignKey(AUTH_USER_MODEL)
   model_name = CharField(max_length=100)
   operation = CharField(max_length=20)  # 'update', 'delete'
   total_records = IntegerField()
   processed_records = IntegerField(default=0)
   status = CharField(choices=['PENDING', 'STARTED', 'SUCCESS', 'FAILURE'])
   created_at = DateTimeField(auto_now_add=True)
   completed_at = DateTimeField(null=True, blank=True)
   error_message = TextField(blank=True)
   task_key = CharField(max_length=255, db_index=True)  # Prevent duplicates
```

**Status Page Features:**
- List of user's bulk operations with progress
- Real-time status updates (pending, in progress, completed, failed)
    - use `htmx` for this (haha if htmx enabled) with potential to use [celery-progress](https://www.saaspegasus.com/guides/django-celery-progress-bars/)
- Detailed error reporting for failed operations
- Operation history and audit trail
- Links back to relevant model list views
- consider whether to persist an estimated progress_percent field in the BulkTask model to avoid recalculating in templates or clients.
- consider optionally (or as standard) allowing: task cancel, retry operations

## Duplicate Request Handling

**Problem**: Impatient users might trigger the same bulk operation multiple times.

**Solution**: 
- Generate unique `task_key` based on user, selected IDs, and operation data. Consider providing hook for downstream user to modify and further specialise key to ensure uniqueness.
- Check for existing pending/running tasks before creating new ones
- Return status of existing task instead of creating duplicates
- Provide clear feedback: "This bulk operation is already in progress"
- **OR** consider option to cancel / rollback existing task and start a new one (consider class param for this or provide hooks for downstream user to modify)

## Notification Options

1. **Status Page** (Recommended Default):
  - Dedicated page showing all user's bulk operations
  - Persistent across sessions
  - Detailed progress and error information
  - Best UX for power users
  - Consider whether to go direct to this page when calling task ends, or not, or provide alert or django message, etc. Consider parameterising this or providing a hook. Discuss when we get to the relevant task.

2. **Django Messages**:
  - Good for small operations
  - May be missed if user navigates away
  - Simple to implement

3. **Email Notifications**:
  - Good for very long operations
  - Works when user is offline
  - Requires email configuration

4. **Custom Callback**:
  - For advanced integrations
  - Allows custom notification logic

## Error Handling and Atomicity

**Current Behavior**: Bulk operations are atomic - either all records succeed or none are modified.

**Async Behavior**: 
- Maintain atomicity within reasonable batch sizes
- For very large operations, consider chunked processing with partial success reporting
- Detailed error reporting showing which records failed and why
- Option to retry failed records

## Technical Implementation Details

**Task Queue Integration:**
```python
def bulk_edit_process_post(self, request, queryset, bulk_fields):
   selected_count = len(selected_ids)
    
   if self.should_process_async(selected_count):
       # Create task record
       task = BulkTask.objects.create(
           user=request.user,
           model_name=self.model.__name__,
           operation='update',
           total_records=selected_count,
           task_key=self._generate_task_key(request.user, selected_ids, field_data)
       )
        
       # Queue async task
       async_task('nominopolitan.tasks.bulk_edit_task', 
                 task.id, selected_ids, field_data)
        
       return JsonResponse({
           'status': 'queued',
           'task_id': task.id,
           'message': f'Processing {selected_count} records in background.'
       })
   else:
       # Process synchronously (current behavior)
       return self._bulk_edit_sync(request, queryset, bulk_fields)
```

**Progress Updates:**
- Update `BulkTask.processed_records` periodically during processing
- Use database transactions appropriately to ensure consistency
- Provide percentage completion for UI progress bars

## Dependencies and Setup

**For Package Maintainers:**
- Add `django-q2>=1.4.0` to package dependencies
- Include migration for `BulkTask` model
- Add default templates for status page

**For Downstream Users:**
- **Zero additional setup** required for basic async functionality
- Optional: Configure `Q_CLUSTER` settings in Django settings for advanced tuning
- Optional: Set up email backend for email notifications

## Planned Implementation Tasks

1. **Add django-q2 dependency**

  - Update `pyproject.toml` or `setup.py`
  - Add to package requirements

2. **Create BulkTask model**

  - Define model with all required fields
  - Create and test migrations
  - Add model admin interface for debugging

3. **Implement async detection logic**

  - `should_process_async()` method
  - `get_bulk_async_enabled()` method
  - Backend availability checking

4. **Create async task functions**

  - `bulk_edit_task()` function for django-q2
  - `bulk_delete_task()` function for django-q2
  - Progress tracking and error handling
  - Task completion and status updates

5. **Modify bulk_edit_process_post method**

  - Add async/sync routing logic
  - Task creation and queuing
  - Duplicate request detection
  - Response handling for async operations

6. **Create BulkTask status views**

  - List view for user's bulk operations
  - Detail view for individual task status
  - HTMX integration for real-time updates
  - URL patterns and navigation

7. **Create status page templates**

  - List template with progress indicators
  - Detail template with error reporting
  - HTMX partials for live updates
  - Integration with existing modal system

8. **Update bulk edit form responses**

  - Handle async responses in JavaScript
  - Show "processing in background" messages
  - Provide links to status page
  - Update modal behavior for async operations

9.  **Add notification system**

  - Django messages integration
  - Status page notifications
  - Framework for future email/callback notifications

10. **Testing and documentation**

   - Unit tests for async functionality
   - Integration tests with django-q2
   - Update README with async configuration options
   - Add example configurations for different use cases

11. **Error handling and edge cases**

   - Handle django-q2 unavailability gracefully
   - Test with various record counts and thresholds
   - Validate duplicate request prevention
   - Test progress tracking accuracy

12. **UI/UX improvements**

   - Progress bars or indicators
   - Better feedback for queued operations
   - Status page styling and usability
   - Mobile-responsive design for status pages
