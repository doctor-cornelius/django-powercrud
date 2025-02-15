from django import forms
from django_filters import FilterSet, CharFilter
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Row, Column

from crispy_forms.bootstrap import Div
from crispy_forms import bootstrap, layout

from .models import Book

class BookFilterSet(FilterSet):
    title = CharFilter(lookup_expr='icontains') 
    class Meta:
        model = Book
        fields = ['author', 'title', 'published_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("DEBUG: Fields after super:", hasattr(self, 'fields'))
        
        # Now we can access self.fields
        for field in self.form.fields.values():
            if isinstance(field.widget, forms.TextInput):
                field.widget.attrs.update({
                    'hx-get': '',
                    'hx-trigger': 'keyup changed delay:300ms',
                    'hx-target': '#content'
                })
            else:
                field.widget.attrs.update({
                    'hx-get': '',
                    'hx-trigger': 'change',
                    'hx-target': '#content'
                })

        # Set up crispy form helper after field modifications
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.wrapper_class = 'col-auto'
        self.helper.template = 'bootstrap5/layout/inline_field.html'