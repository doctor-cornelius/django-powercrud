from django.urls import path

from powercrud.async_manager import AsyncManager


urlpatterns = [path("async/progress/", AsyncManager.as_view(), name="async_progress")]
