from django_filters import FilterSet
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field

from crispy_forms.bootstrap import Div
from crispy_forms import bootstrap, layout

from .models import Book

class BookFilterSet(FilterSet):
    class Meta:
        model = Book
        fields = ['author', 'title',]  # Specify your fields here

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap5/layout/inline_field.html'
        self.helper.layout = Layout(
            Field('author', css_class='col-auto'),
            Field('title', css_class='col-auto'),
            # Add more fields as needed
        )