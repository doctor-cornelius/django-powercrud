from django.urls import path

from powercrud._coordinator.manager import AsyncManager
from coordinator_tests.managers import coordinator_manager_factory


urlpatterns = [
    path(
        "async/progress/",
        AsyncManager.as_view(manager_factory=coordinator_manager_factory),
        name="async_progress",
    )
]
