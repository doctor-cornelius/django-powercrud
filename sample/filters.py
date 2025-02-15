from django import forms
from django_filters import FilterSet
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Row, Column

from crispy_forms.bootstrap import Div
from crispy_forms import bootstrap, layout

from .models import Book

class BookFilterSet(FilterSet):
    class Meta:
        model = Book
        fields = ['author', 'title']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("DEBUG: Fields after super:", hasattr(self, 'fields'))
        
        # Now we can access self.fields
        # for field in self.fields.values():
        #     if isinstance(field.widget, forms.TextInput):
        #         field.widget.attrs.update({
        #             'hx-get': '',
        #             'hx-trigger': 'keyup changed delay:300ms',
        #             'hx-target': '#filter-results'
        #         })
        #     else:
        #         field.widget.attrs.update({
        #             'hx-get': '',
        #             'hx-trigger': 'change',
        #             'hx-target': '#filter-results'
        #         })

        # Set up crispy form helper after field modifications
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.wrapper_class = 'col-auto'
        self.helper.template = 'bootstrap5/layout/inline_field.html'