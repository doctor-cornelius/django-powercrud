from django.db import models
from django.conf import settings
from django.utils import timezone
from django_q.models import Task
import logging
log = logging.getLogger("powercrud")

class BulkTask(models.Model):
    """
    Model to track bulk operations (edit/delete) for progress monitoring and history.
    """
    
    # Status choices
    PENDING = 'PENDING'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (STARTED, 'Started'),
        (SUCCESS, 'Success'),
        (FAILURE, 'Failed'),
    ]
    
    # Operation types
    UPDATE = 'update'
    DELETE = 'delete'
    
    OPERATION_CHOICES = [
        (UPDATE, 'Update'),
        (DELETE, 'Delete'),
    ]
    
    # Core fields
    async_backend = models.CharField(
        max_length=20,
        null=True, blank=True,
        choices=[('q2', 'Django-Q2'), ('celery', 'Celery')],
        help_text="Async backend used for this task"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        null=True, blank=True, # allow Anonymous
        help_text="User who initiated the bulk operation"
    )
    model_name = models.CharField(
        max_length=100,
        help_text="Name of the model being processed"
    )
    operation = models.CharField(
        max_length=20, 
        choices=OPERATION_CHOICES,
        help_text="Type of bulk operation"
    )
    
    # Progress tracking
    total_records = models.IntegerField(
        help_text="Total number of records to process"
    )
    processed_records = models.IntegerField(
        default=0,
        help_text="Number of records processed so far"
    )
    
    # Status and timing
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=PENDING,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(
        blank=True,
        help_text="Error details if the operation failed"
    )
    
    # Duplicate prevention
    task_key = models.CharField(
        max_length=255, 
        db_index=True,
        help_text="Unique key to prevent duplicate operations"
    )

    # Model unique key to test whether operation is unique
    # This derives from bulk_mixin.get_storage_key()
    unique_model_key = models.CharField(max_length=255, db_index=True)  
    
    # Additional metadata
    operation_data = models.JSONField(
        default=dict,
        null=True, blank=True,
        help_text="Serialized data about the operation (fields, values, etc.)"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['task_key']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Bulk Task"
        verbose_name_plural = "Bulk Tasks"
    
    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"{self.get_operation_display()} {self.model_name} - {username} ({self.status})"
    
    @property
    def progress_percentage(self):
        """Calculate completion percentage"""
        if self.total_records == 0:
            return 0
        if self.is_complete:
            return 100
        return min(100, (self.processed_records / self.total_records) * 100)
    
    @property
    def is_complete(self):
        """Check if the task is complete (success or failure)"""
        return self.status in [self.SUCCESS, self.FAILURE]
    
    @property
    def is_running(self):
        """Check if the task is currently running"""
        return self.status == self.STARTED
    
    @property
    def duration(self):
        """Get task duration if completed"""
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return timezone.now() - self.started_at
        return None
    
    @classmethod
    def clear_q2_queue(cls):
        """Clear all django-q2 tasks - useful for debugging"""
        try:
            count = Task.objects.count()
            Task.objects.all().delete()
            log.info(f"Cleared {count} tasks from django-q2 queue")
            return f"Cleared {count} tasks"
        except Exception as e:
            log.error(f"Failed to clear Q2 queue: {e}")
            return f"Error: {e}"

    def mark_started(self):
        """Mark the task as started"""
        self.status = self.STARTED
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self, success=True, error_message=''):
        """Mark the task as completed"""
        self.status = self.SUCCESS if success else self.FAILURE
        self.completed_at = timezone.now()
        if error_message:
            self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message'])
    
    def update_progress(self, processed_count):
        """Update the progress counter"""
        self.processed_records = processed_count
        self.save(update_fields=['processed_records'])

    def delete(self, *args, **kwargs):
        """Override delete to also remove async task if it exists"""
        if self.async_backend == 'q2':
            try:
                # Use BulkTask ID to find and delete Q2 task
                Task.objects.filter(
                    func='powercrud.tasks.bulk_delete_task',
                    args__contains=str(self.id)
                ).delete()
                Task.objects.filter(
                    func='powercrud.tasks.bulk_update_task', 
                    args__contains=str(self.id)
                ).delete()
                log.debug(f"Deleted Q2 tasks for BulkTask {self.id}")
            except Exception as e:
                log.warning(f"Failed to delete Q2 tasks for BulkTask {self.id}: {e}")
        
        super().delete(*args, **kwargs)