from django.shortcuts import render

from neapolitan.views import CRUDView
from nominopolitan.mixins import NominopolitanMixin

from django import forms
from . import models
from . import forms

class BookCRUDView(NominopolitanMixin, CRUDView):
    model = models.Book
    # fields = ["title","author","published_date",]
    fields =  "all"
    properties = 'all'
    # detail_fields = "all"

    namespace = "sample"
    base_template_path = "django_nominopolitan/base.html"
    form_class = forms.BookForm
    use_htmx = True


class AuthorCRUDView(NominopolitanMixin, CRUDView):
    model = models.Author
    # fields = ["name","bio","birth_date",]
    fields = "all"
    form_class = forms.AuthorForm
    namespace = "sample"
    use_htmx = True
    use_modal = True
    base_template_path = "django_nominopolitan/base.html"
    extra_actions = [
        {
            "url_name": "home",  # namespace:url_pattern
            "text": "Home",
            "needs_pk": False,  # if the URL needs the object's primary key
            "button_class": "is-primary",
            "htmx_target": "content",
        },
        {
            "url_name": "sample:author-detail",
            "text": "View Again",
            "needs_pk": True,  # if the URL doesn't need the object's primary key
        },
    ]
