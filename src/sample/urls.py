from django.urls import path

from neapolitan.views import Role
from . import views

app_name = "sample"

urlpatterns = []

urlpatterns += views.BookCRUDView.get_urls()
urlpatterns += views.ManualStaticBookCRUDView.get_urls()
urlpatterns += views.AnnotatedBookCRUDView.get_urls(roles={Role.LIST})
urlpatterns += views.PowerFieldBookCRUDView.get_urls()
urlpatterns += views.AuthorCRUDView.get_urls()
urlpatterns += views.GenreCRUDView.get_urls()
urlpatterns += views.ProfileCRUDView.get_urls(
    roles={Role.LIST, Role.CREATE, Role.UPDATE}
)
urlpatterns += views.AsyncTaskRecordCRUDView.get_urls(roles={Role.LIST})
urlpatterns += [
    path(
        "bigbook/selected-summary/",
        views.book_selected_summary,
        name="bigbook-selected-summary",
    ),
    path(
        "bigbook/<str:pk>/description-preview/",
        views.book_description_preview,
        name="bigbook-description-preview",
    ),
    path(
        "async-dashboard/<str:pk>/",
        views.async_task_detail,
        name="async-dashboard-detail",
    ),
]
