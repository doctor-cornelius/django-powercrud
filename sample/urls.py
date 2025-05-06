from django.contrib import admin
from django.urls import path, include

from . import views

app_name = "sample"

urlpatterns = []

urlpatterns = views.BookCRUDView.get_urls()
urlpatterns += views.AuthorCRUDView.get_urls()
urlpatterns += views.GenreCRUDView.get_urls()

# Add the regular book update view URL
urlpatterns += [
    path('book/<int:pk>/update/', views.book_update_view, name='book-update-view'),
]
