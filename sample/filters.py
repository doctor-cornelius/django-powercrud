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
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.wrapper_class = 'col-auto mb-0'  # Override the margin-bottom
        self.helper.template = 'bootstrap5/layout/inline_field.html'
