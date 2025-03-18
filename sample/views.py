from django.shortcuts import render

from neapolitan.views import CRUDView
from nominopolitan.mixins import NominopolitanMixin

from django import forms
from . import models
from . import forms
from . import filters


class BookCRUDView(NominopolitanMixin, CRUDView):
    model = models.Book
    namespace = "sample"
    base_template_path = "django_nominopolitan/base.html"
    use_htmx = True
    use_modal = True
    # use_crispy = False

    # standard neapolitan setting; this demonstrates how to override the default url_base (ie model name)
    # useful if you want multiple CRUDViews for the same model
    url_base = "bigbook" 

    # use_crispy = False

    # fields = ["author","title","published_date",]
    fields =  "__all__"
    exclude = ['pages','description']
    # properties = '__all__'
    detail_fields = '__all__'
    detail_properties = '__all__'

    form_fields = ['title', 'author', 'published_date', 'isbn',]
    create_form_class = forms.BookForm

    filterset_fields = ['author', 'title', 'published_date','isbn', 'isbn_empty','pages', 'description', 'uneditable_field']
    filterset_class = filters.BookFilterSet

    table_pixel_height_other_page_elements = 100
    table_max_height = 80
    table_font_size = '1.05'
    table_max_col_width = '25' # characters
    # paginate_by = 30

    # Example of overrides of get_queryset and get_filter_queryset_for_field
    # def get_queryset(self):
    #     qs = super().get_queryset()
    #     qs = qs.filter(author__id=20)
    #     return qs.select_related('author')

    # def get_filter_queryset_for_field(self, field_name, model_field):
    #     """Override to restrict the available options if the field is author.
    #     """
    #     qs = super().get_filter_queryset_for_field(field_name, model_field)
    #     print(field_name)
    #     if field_name == 'author':
    #         qs = qs.filter(id=20)
    #     return qs

    extra_buttons = [
        {
            "url_name": "home",
            "text": "Home",
            "button_class": "btn-success",
            "htmx_target": "content",
            "needs_pk": False,
            "display_modal": False,
            "extra_class_attrs": "py-10 my-10",
        },
        {
            "url_name": "home",
            "text": "Home in Modal!",
            "button_class": "btn-warning",
            "htmx_target": "nominopolitanModalContent",
            "display_modal": True,
            "extra_class_attrs": "px-10 mx-10",
        },
    ]

class AuthorCRUDView(NominopolitanMixin, CRUDView):
    model = models.Author
    namespace = "sample"
    base_template_path = "django_nominopolitan/base.html"
    use_htmx = True
    use_modal = True

    table_font_size = '0.675'
    table_max_col_width = '20' # characters

    # paginate_by = 40

    # fields = ["name","bio","birth_date",]
    fields = "__all__"
    # exclude = ['bio',]
    properties = '__all__'
    properties_exclude = ['has_bio',]
    detail_fields = '__fields__'
    detail_properties = '__properties__'

    # filterset_class = filters.AuthorFilterSet
    filterset_fields = ['name', 'birth_date', 'bio']

    # form_class = forms.AuthorForm

    extra_actions = [
        {
            "url_name": "home",  # namespace:url_pattern
            "text": "Home",
            "needs_pk": False,  # if the URL needs the object's primary key
            "button_class": "btn-warning",
            "htmx_target": "content",
            "display_modal": False,
        },
        {
            "url_name": "sample:author-detail",
            "text": "View Again",
            "needs_pk": True,  # if the URL doesn't need the object's primary key
        },
    ]

    extra_buttons = [
        {
            "url_name": "home",
            "text": "Home Again",
            "button_class": "btn-success",
            "htmx_target": "content",
            "needs_pk": False,
            "display_modal": False,
        },
    ]

    def get_template_names(self):
        names = super().get_template_names()
        print("DEBUG: Looking for templates:", names)  # Debug print
        return names
