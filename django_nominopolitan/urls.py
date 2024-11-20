from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

from django.contrib import admin
from django.urls import path, include

from . import views
from sample import views as sample_views

urlpatterns = [
    path(
        "favicon.ico", RedirectView.as_view(url=staticfiles_storage.url("favicon.ico"))
    ),
    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
    path("sample/", include("sample.urls", namespace="sample")),
]
