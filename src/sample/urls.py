from django.contrib import admin
from django.urls import path, include

from neapolitan.views import Role
from powercrud.async_manager import AsyncManager
from . import views

app_name = "sample"

urlpatterns = []

urlpatterns += [AsyncManager.get_url()]
urlpatterns += views.BookCRUDView.get_urls()
urlpatterns += views.AuthorCRUDView.get_urls()
urlpatterns += views.GenreCRUDView.get_urls()
urlpatterns += views.ProfileCRUDView.get_urls()
urlpatterns += views.AsyncTaskRecordCRUDView.get_urls(roles={Role.LIST})
urlpatterns += [
    path("async-dashboard/<str:pk>/", views.async_task_detail, name="async-dashboard-detail"),
]
