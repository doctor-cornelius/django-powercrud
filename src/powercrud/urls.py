from django.urls import path
from .async_manager import AsyncManager

app_name = 'powercrud'  # Default namespace

urlpatterns = [
    AsyncManager.get_url(name="async_progress"),
]