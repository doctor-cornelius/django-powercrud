from django.contrib import admin

from . import models
# Register your models here.


@admin.register(models.Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "birth_date")
    search_fields = ("name",)


@admin.register(models.Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "published_date", "isbn")
    list_filter = ("author", "published_date")
    search_fields = ("title", "isbn")


@admin.register(models.AsyncTaskRecord)
class AsyncTaskRecordAdmin(admin.ModelAdmin):
    list_display = ("task_name", "status", "message", "updated_at")
    list_filter = ("status",)
    search_fields = ("task_name", "message", "user_label")
    readonly_fields = ("created_at", "updated_at", "completed_at", "failed_at")
