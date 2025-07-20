from django.contrib import admin
from .models import BulkTask


@admin.register(BulkTask)
class BulkTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'async_backend', 'user', 'model_name', 'operation', 'status', 
        'progress_display', 'created_at', 'duration_display'
    ]
    list_filter = ['async_backend', 'status', 'operation', 'model_name', 'created_at']
    search_fields = ['user__username', 'model_name', 'task_key']
    readonly_fields = [
        'created_at', 'started_at', 'completed_at', 'task_key', 
        'progress_percentage', 'duration'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('async_backend', 'user', 'model_name', 'operation', 'status')
        }),
        ('Progress', {
            'fields': ('total_records', 'processed_records', 'progress_percentage')
        }),
        ('Timing', {
            'fields': ('created_at', 'started_at', 'completed_at', 'duration')
        }),
        ('Technical Details', {
            'fields': ('task_key', 'operation_data', 'error_message'),
            'classes': ('collapse',)
        }),
    )
    
    def progress_display(self, obj):
        """Display progress as a percentage"""
        return f"{obj.progress_percentage:.1f}% ({obj.processed_records}/{obj.total_records})"
    progress_display.short_description = "Progress"
    
    def duration_display(self, obj):
        """Display task duration"""
        duration = obj.duration
        if duration:
            total_seconds = int(duration.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            return f"{minutes}m {seconds}s"
        return "-"
    duration_display.short_description = "Duration"
    
    def has_add_permission(self, request):
        """Prevent manual creation of bulk tasks"""
        return False
    
    actions = ['clear_q2_queue']
    
    def clear_q2_queue(self, request, queryset):
        """Clear the entire django-q2 task queue"""
        result = BulkTask.clear_q2_queue()
        self.message_user(request, result)
    clear_q2_queue.short_description = "Clear entire Q2 task queue"