from datetime import date

import pytest
from django import forms
from django.test import RequestFactory

from powercrud.mixins.form_mixin import FormMixin
from powercrud.mixins.filtering_mixin import (
    FilteringMixin,
    AllValuesModelMultipleChoiceFilter,
)
from powercrud.mixins.htmx_mixin import HtmxMixin
from powercrud.templatetags import powercrud as powercrud_tags

from sample.models import Author, Book, Genre


@pytest.mark.django_db
def test_form_mixin_generates_modelform_with_sorted_dropdown():
    Author.objects.create(name="Alan")
    Author.objects.create(name="Zara")

    class BookFormView(FormMixin):
        model = Book
        form_fields = ["title", "author", "published_date"]
        dropdown_sort_options = {"author": "name"}
        use_crispy = False
        form_class = None

    view = BookFormView()
    form_class = view.get_form_class()

    assert set(form_class.base_fields.keys()) == {"title", "author", "published_date"}

    author_field = form_class.base_fields["author"]
    ordered_authors = list(author_field.queryset.values_list("name", flat=True))
    assert ordered_authors == ["Alan", "Zara"]

    date_widget = form_class.base_fields["published_date"].widget
    assert isinstance(date_widget, forms.DateInput)
    assert date_widget.input_type == "date"


@pytest.mark.django_db
def test_form_mixin_respects_use_crispy_setting(settings):
    settings.INSTALLED_APPS = [
        app for app in settings.INSTALLED_APPS if app != "crispy_forms"
    ]

    class BookFormView(FormMixin):
        model = Book
        form_fields = ["title"]
        use_crispy = True
        form_class = None

    view = BookFormView()
    form_class = view.get_form_class()

    # Crispy helper should not be attached if crispy_forms not installed
    form_instance = form_class()
    assert not hasattr(form_instance, "helper")


@pytest.mark.django_db
def test_filtering_mixin_builds_dynamic_filterset(rf: RequestFactory):
    author_a = Author.objects.create(name="Alan")
    Author.objects.create(name="Zara")
    genre1 = Genre.objects.create(name="Sci-Fi")
    genre2 = Genre.objects.create(name="Fantasy")

    book = Book.objects.create(
        title="Sample",
        author=author_a,
        published_date=date(2024, 1, 1),
        bestseller=True,
        isbn="1234567890123",
        pages=100,
    )
    book.genres.set([genre1, genre2])

    class FilterView(HtmxMixin, FormMixin, FilteringMixin):
        model = Book
        filterset_fields = ["author", "genres", "bestseller"]
        dropdown_sort_options = {"author": "name"}
        use_htmx = True
        use_modal = False
        use_crispy = False
        modal_id = None
        modal_target = None
        form_class = None

        def get_use_crispy(self):
            return False

    view = FilterView()
    view.m2m_filter_and_logic = True
    view.request = rf.get(
        "/",
        {"author": author_a.pk},
        HTTP_X_FILTER_SETTING_REQUEST="true",
    )

    filterset = view.get_filterset(Book.objects.all())
    assert filterset is not None
    assert filterset.form.fields["author"].queryset.first().name == "Alan"

    # Dropdown sorting applied (Alan before Zara)
    author_names = list(
        filterset.form.fields["author"].queryset.values_list("name", flat=True)
    )
    assert author_names == ["Alan", "Zara"]

    genres_filter = filterset.filters["genres"]
    assert isinstance(genres_filter, AllValuesModelMultipleChoiceFilter)
    assert "hx-trigger" in filterset.form.fields["author"].widget.attrs


class StubView:
    model = Author
    fields = ["name", "birth_date"]
    properties = ["has_bio"]
    detail_fields = ["name", "birth_date"]
    detail_properties = ["has_bio"]
    namespace = "sample"
    url_base = "author"

    def __init__(self, request):
        self.request = request

    # Methods consumed by action_links/object_list
    def get_framework_styles(self):
        return {
            "daisyUI": {
                "base": "btn",
                "actions": {
                    "View": "btn-info",
                    "Edit": "btn-primary",
                    "Delete": "btn-error",
                },
                "extra_default": "btn-secondary",
                "modal_attrs": "",
            }
        }

    def get_action_button_classes(self):
        return "btn-xs"

    def get_prefix(self):
        return f"{self.namespace}:{self.url_base}"

    def get_use_htmx(self):
        return False

    def get_use_modal(self):
        return False

    def get_htmx_target(self):
        return "#content"

    def get_original_target(self):
        return "#content"

    def safe_reverse(self, *args, **kwargs):
        return "/dummy"

    def get_bulk_edit_enabled(self):
        return False

    def get_selected_ids_from_session(self, request):
        return []

    def get_bulk_selection_key_suffix(self):
        return ""

    def get_table_pixel_height_other_page_elements(self):
        return "0px"

    def get_table_max_height(self):
        return 70

    def get_table_classes(self):
        return "table"


@pytest.mark.django_db
def test_object_detail_renders_fields_and_properties():
    author = Author.objects.create(
        name="Test Author",
        bio="Biography",
        birth_date=date(2024, 1, 1),
    )
    request = RequestFactory().get("/")
    view = StubView(request)

    detail_context = powercrud_tags.object_detail(author, view)
    rendered = list(detail_context["object"])

    field_names = [name for name, _ in rendered]
    assert "name" in field_names
    assert "birth date" in field_names
    assert "Has Bio" in field_names


@pytest.mark.django_db
def test_object_list_formats_rows_and_headers():
    author = Author.objects.create(
        name="Test Author",
        bio="Biography",
        birth_date=date(2024, 1, 1),
    )
    request = RequestFactory().get("/")
    view = StubView(request)

    context = {"request": request}
    result = powercrud_tags.object_list(context, [author], view)

    assert result["headers"][0] == ("Name", "name", True)
    assert result["headers"][1][1] == "birth_date"

    row = result["object_list"][0]["fields"]
    assert "Test Author" in row
    # birth_date formatted dd/mm/YYYY
    assert "01/01/2024" in row

    # property renders truthy icon (contains svg markup)
    property_output = row[-1]
    assert "<svg" in property_output


def test_get_proper_elided_page_range():
    from django.core.paginator import Paginator

    paginator = Paginator(range(50), 1)
    page_range = powercrud_tags.get_proper_elided_page_range(paginator, 10)
    assert "…" in page_range
