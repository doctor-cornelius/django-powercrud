from django.db import models
from django.utils import timezone


class Book(models.Model):
    """Minimal model for task-context model resolution tests."""

    title = models.CharField(max_length=255, blank=True)


class AsyncTaskRecord(models.Model):
    """Small stand-in for the sample dashboard tracking model."""

    class STATUS(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In progress"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        UNKNOWN = "unknown", "Unknown"

    task_name = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=32, choices=STATUS.choices, default=STATUS.PENDING)
    message = models.TextField(blank=True)
    progress_payload = models.TextField(blank=True)
    user_label = models.CharField(max_length=255, blank=True)
    affected_objects = models.TextField(blank=True)
    task_kwargs = models.JSONField(blank=True, null=True)
    task_args = models.JSONField(blank=True, null=True)
    result_payload = models.TextField(blank=True)
    cleaned_up = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    failed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["-created_at"])]

    def mark_completed(self, timestamp=None):
        """Set success status and completion time as the sample model does."""
        self.status = self.STATUS.SUCCESS
        self.completed_at = timestamp or timezone.now()

    def mark_failed(self, message, timestamp=None):
        """Set failure status, message, and failure time as the sample model does."""
        self.status = self.STATUS.FAILED
        self.message = message
        self.failed_at = timestamp or timezone.now()
