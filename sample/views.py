from django.shortcuts import render

from neapolitan.views import CRUDView
from nominopolitan.mixins import NominopolitanMixin

from . import models

class BookCRUDView(NominopolitanMixin, CRUDView):
    model = models.Book
    namespace = "sample"
    base_template_path = "django_nominopolitan/base.html"
    fields = [
        "author", "published_date", "isbn", "pages",
    ]
