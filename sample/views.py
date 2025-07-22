import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from neapolitan.views import CRUDView
from nominopolitan.mixins import NominopolitanMixin

from django import forms
from . import models
from . import forms
from . import filters

class BookCRUDView(NominopolitanMixin, CRUDView):
    model = models.Book
    namespace = "sample"
    base_template_path = "sample/base.html"
    use_htmx = True
    use_modal = True
    # use_crispy = False

    # standard neapolitan setting; this demonstrates how to override the default url_base (ie model name)
    # useful if you want multiple CRUDViews for the same model
    url_base = "bigbook" 
    paginate_by = 5

    # use_crispy = False

    # fields = ["author","title","published_date",]
    fields =  "__all__"
    exclude = ['description']
    properties = '__all__'
    detail_fields = '__all__'
    detail_properties = '__all__'

    bulk_fields = [
        'title',
        'published_date',
        'bestseller',
        'pages',
        'author',
        'genres',
    ]
    bulk_delete = True
    bulk_async = True
    bulk_min_async_records = 2

    # form_fields = ['title', 'author', 'bestseller', 'genres', 'published_date', 'isbn',]
    form_class = forms.BookForm

    # filterset_class = filters.BookFilterSet
    filterset_fields = ['author', 'title', 'published_date','isbn', 'isbn_empty','pages', 'description', 'genres']
    # Define how filter dropdown options should be sorted
    dropdown_sort_options = {
        "author": "name",  # Sort authors by name field in all dropdowns
        "unknown_model": 'zebra_face',
    }
    m2m_filter_and_logic = False  # Use AND logic for M2M filters

    # filter_queryset_options = {
    #     'author': {
    #         # 'name': 'Nancy Wilson',
    #         # 'name__in': ['Nancy Wilson', 'Thomas Adams', ],
    #         'name__icontains': 'Nancy',
    #     },
    # }

    table_pixel_height_other_page_elements = 100
    table_max_height = 80
    table_header_min_wrap_width = '15' # characters
    table_max_col_width = '25' # characters

    table_classes = 'table-zebra table-sm'
    # action_button_classes = 'btn-sm min-h-0 h-6 leading-6'
    action_button_classes = 'btn-xs'
    extra_button_classes = 'btn-sm'

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
            "extra_class_attrs": "",
            "extra_attrs": 'hx-push-url="false" hx-replace-url="false"',
        },
        {
            "url_name": "home",
            "text": "Home in Modal!",
            "button_class": "btn-warning",
            "htmx_target": "content",
            "display_modal": True, # NB if True then htmx_target is ignored
            "extra_class_attrs": "bg-warning",
        },
    ]

    extra_actions = [
        {
            "url_name": "sample:book-update-view",  # namespace:url_pattern
            "text": "Normal Edit", # bypasses nominopolitan & uses regular view
            "needs_pk": True,  # if the URL needs the object's primary key
            "button_class": "btn-info",
            "htmx_target": "content",
            "display_modal": False,
        },
    ]


    # def get_bulk_choices_for_field(self, field_name, field):
    #     """Example of how to override to further restrict foreign key choices for 
    #         dropdown in bulk edit form.
    #     """
    #     if field_name == 'author' and hasattr(field, "related_model") and field.related_model is not None:
    #         return field.related_model.objects.filter(
    #             id=19
    #         )
    #     return super().get_bulk_choices_for_field(field_name, field)


class GenreCRUDView(NominopolitanMixin, CRUDView):
    model = models.Genre
    namespace = "sample"
    base_template_path = "sample/base.html"
    use_htmx = True
    use_modal = True

    table_classes = 'table-zebra table-sm'
    action_button_classes = 'btn-xs'
    extra_button_classes = 'btn-sm'

    fields = ['name', 'numeric_string']


class ProfileCRUDView(NominopolitanMixin, CRUDView):
    model = models.Profile
    namespace = "sample"
    base_template_path = "sample/base.html"
    use_htmx = True
    use_modal = True

    table_classes = "table-zebra table-sm"
    action_button_classes = "btn-xs"
    extra_button_classes = "btn-sm"

    fields = "__all__"
    properties = "__all__"


    # Add the OneToOneField to bulk_fields to test it
    bulk_fields = [
        "author", # OneToOneField
        "nickname",
        "favorite_genre",
    ]


class AuthorCRUDView(NominopolitanMixin, CRUDView):
    model = models.Author
    namespace = "sample"
    base_template_path = "sample/base.html"
    use_htmx = True
    use_modal = True

    table_classes = 'table-zebra table-sm'
    action_button_classes = 'btn-xs'
    extra_button_classes = 'btn-sm'

    paginate_by = 15

    # fields = ["name","bio","birth_date",]
    fields = "__all__"
    # exclude = ['bio',]
    properties = '__all__'
    # properties_exclude = ['has_bio',]
    detail_fields = '__fields__'
    detail_properties = '__properties__'

    # filterset_class = filters.AuthorFilterSet
    filterset_fields = ['name', 'birth_date', 'bio']

    # form_class = forms.AuthorForm

    table_header_min_wrap_width = '15' # characters
    table_max_col_width = '25' # characters

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
