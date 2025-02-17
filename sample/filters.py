from django import forms
from django_filters import FilterSet, CharFilter, DateFilter
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Row, Column

from crispy_forms.bootstrap import Div
from crispy_forms import bootstrap, layout

from .models import Book, Author
from nominopolitan.mixins import HTMXFilterSetMixin

class AuthorFilterSet(HTMXFilterSetMixin, FilterSet):
    """Filterset class used for the Author model.
        It uses the Nominopolitan.HTMXFilterSetMixin to add HTMX attributes
        to the form fields.
    """
    name = CharFilter(lookup_expr='icontains')
    birth_date = DateFilter(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    class Meta:
        model = Author
        fields = ['name', 'birth_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # setup htmx attributes by using helper class from Nominoopolitan
        self.setup_htmx_attrs()

class BookFilterSet(FilterSet):
    title = CharFilter(lookup_expr='icontains')
    published_date = DateFilter(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    class Meta:
        model = Book
        fields = ['author', 'title', 'published_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        hx_get = ''
        hx_target = '#content'

        HTMX_ATTRS = {
            'hx-get': '',
            'hx-target': '#content',
            'hx-include': '[name]',  # This will include all named form fields
        }

        FIELD_TRIGGERS = {
            forms.DateInput: 'change',
            forms.TextInput: 'keyup changed delay:300ms',
            'default': 'change'
        }

        def _update_field_attrs(self, field, trigger):
            attrs = {**HTMX_ATTRS, 'hx-trigger': trigger}
            field.widget.attrs.update(attrs)

        for field in self.form.fields.values():
            widget_class = type(field.widget)
            trigger = FIELD_TRIGGERS.get(widget_class, FIELD_TRIGGERS['default'])
            _update_field_attrs(self, field, trigger)


        # Set up crispy form helper after field modifications
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.wrapper_class = 'col-auto'
        self.helper.template = 'bootstrap5/layout/inline_field.html'