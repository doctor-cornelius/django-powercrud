from django.contrib import admin
from django.urls import path, include

from . import views
from sample import views as sample_views

urlpatterns = [
    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
    path("sample/", include("sample.urls", namespace="sample")),
]
