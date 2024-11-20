from django.contrib import admin
from django.urls import path, include

from . import views
from . import views 

app_name = "sample"

urlpatterns = views.BookCRUDView.get_urls()
urlpatterns += views.AuthorCRUDView.get_urls()
