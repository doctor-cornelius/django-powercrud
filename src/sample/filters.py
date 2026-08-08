from django import forms
from crispy_forms.helper import FormHelper
from django_filters import CharFilter, DateFilter, DateTimeFilter, FilterSet

from powercrud.mixins import HTMXFilterSetMixin

from .models import AsyncTaskRecord, Author, Book


class AsyncTaskRecordFilterSet(HTMXFilterSetMixin, FilterSet):
    """Filter async task records by an inclusive completion range."""

    completed_from = DateTimeFilter(
        field_name="completed_at",
        lookup_expr="gte",
        label="Completed from",
        widget=forms.DateTimeInput(attrs={"step": "60"}),
    )
    completed_to = DateTimeFilter(
        field_name="completed_at",
        lookup_expr="lte",
        label="Completed to",
        widget=forms.DateTimeInput(attrs={"step": "60"}),
    )

    class Meta:
        """Expose useful task metadata without exact timestamp filters."""

        model = AsyncTaskRecord
        fields = [
            "task_name",
            "user_label",
            "status",
            "cleaned_up",
            "completed_from",
            "completed_to",
        ]


class AuthorFilterSet(HTMXFilterSetMixin, FilterSet):
    """Filterset class used for the Author model.
    It uses the powercrud.HTMXFilterSetMixin to add HTMX attributes
    to the form fields.
    """

    name = CharFilter(lookup_expr="icontains")
    birth_date = DateFilter(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = Author
        fields = ["name", "birth_date", "genres"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # setup htmx attributes by using helper class from Nominoopolitan
        self.setup_htmx_attrs()


class BookFilterSet(HTMXFilterSetMixin, FilterSet):
    title = CharFilter(lookup_expr="icontains")
    published_date = DateFilter(
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        )
    )

    class Meta:
        model = Book
        fields = [
            "author",
            "title",
            "published_date",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        HTMX_ATTRS = {
            "hx-get": "",
            # 'hx-target': '#content',
            "hx-include": "[name]",  # This will include all named form fields
        }

        FIELD_TRIGGERS = {
            forms.DateInput: "change",
            forms.TextInput: "keyup changed delay:300ms",
            "default": "change",
        }

        def _update_field_attrs(self, field, trigger):
            attrs = {**HTMX_ATTRS, "hx-trigger": trigger}
            field.widget.attrs.update(attrs)

        for field in self.form.fields.values():
            widget_class = type(field.widget)
            trigger = FIELD_TRIGGERS.get(widget_class, FIELD_TRIGGERS["default"])
            _update_field_attrs(self, field, trigger)

        # Set up crispy form helper after field modifications
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.wrapper_class = "col-auto"
        self.helper.template = "powercrud/daisyUI/layout/inline_field.html"
