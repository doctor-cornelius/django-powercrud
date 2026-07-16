from copy import deepcopy
from datetime import date
import re

import pytest
from crispy_forms.helper import FormHelper
from django import forms
from django.conf import settings
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.test import RequestFactory, override_settings
from django.utils.formats import date_format
from django.utils.safestring import mark_safe

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
    assert (
        filterset.form.fields["author"].widget.attrs.get(
            "data-powercrud-searchable-select"
        )
        == "true"
    ), "Author filter should be marked for single-select Tom Select enhancement."
    assert (
        filterset.form.fields["genres"].widget.attrs.get(
            "data-powercrud-searchable-multiselect"
        )
        == "true"
    ), "Genres filter should be marked for multi-select Tom Select enhancement."


@pytest.mark.django_db
def test_filtering_mixin_respects_searchable_select_field_hook(rf: RequestFactory):
    author = Author.objects.create(name="Alan")
    genre = Genre.objects.create(name="Sci-Fi")
    book = Book.objects.create(
        title="Sample",
        author=author,
        published_date=date(2024, 1, 1),
        bestseller=True,
        isbn="1234567890123",
        pages=100,
    )
    book.genres.set([genre])

    class FilterView(HtmxMixin, FormMixin, FilteringMixin):
        model = Book
        filterset_fields = ["author", "genres"]
        use_htmx = True
        use_modal = False
        use_crispy = False
        modal_id = None
        modal_target = None
        form_class = None

        def get_use_crispy(self):
            return False

        def get_searchable_select_enabled_for_field(
            self, field_name: str, bound_field=None
        ) -> bool:
            return field_name != "author"

    view = FilterView()
    view.request = rf.get("/")
    filterset = view.get_filterset(Book.objects.all())

    assert filterset is not None, "Expected a filterset for configured filterset_fields."
    assert (
        "data-powercrud-searchable-select"
        not in filterset.form.fields["author"].widget.attrs
    ), "Per-field searchable-select hook should disable author filter enhancement."
    assert (
        filterset.form.fields["genres"].widget.attrs.get(
            "data-powercrud-searchable-multiselect"
        )
        == "true"
    ), "Per-field searchable-select hook should still allow genres multi-select enhancement."


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

    def get_link_fields(self):
        return {}

    def get_list_cell_link(self, obj, field_name, value, *, is_property, request=None):
        return None


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
    values = dict(rendered)
    assert values["name"] == "Test Author" and values["birth date"] == "2024-01-01", (
        "Ordinary detail fields should retain model field string conversion."
    )
    assert values["Has Bio"] == "True", (
        "Detail properties should retain string conversion and title-cased labels."
    )


@pytest.mark.django_db
def test_detail_shell_content_and_legacy_fragment_render():
    """The legacy detail fragment should compose the built-in shell and content."""
    author = Author.objects.create(
        name="Detail Author",
        bio="Biography",
        birth_date=date(2024, 2, 3),
    )
    view = StubView(RequestFactory().get("/authors/1/"))
    rendered = render_to_string(
        "powercrud/daisyUI/object_detail.html#pcrud_content",
        {
            "object": author,
            "view": view,
            "detail_shell_template_paths": [
                "powercrud/daisyUI/partial/detail_shell.html"
            ],
        },
    )

    assert "card-title" in rendered and "Detail Author" in rendered, (
        "The focused shell should retain the object heading."
    )
    assert '<table class="table w-full border border-base-300">' in rendered, (
        "The inclusion-tag façade should retain the focused detail table."
    )
    assert "birth date" in rendered and "2024-02-03" in rendered and "Has Bio" in rendered, (
        "The composed detail should retain configured fields and properties."
    )
    assert "<script" not in rendered, (
        "Focused detail rendering should not need copied PowerCRUD JavaScript."
    )


@pytest.mark.django_db
def test_detail_shell_and_content_prefer_independent_model_overrides(tmp_path):
    """Detail shell and content candidates should remain independently composable."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_detail_shell.html").write_text(
        '<section data-custom-detail-shell>{{ object }}</section>'
    )
    (override_path / "author_detail_content.html").write_text(
        '<dl data-custom-detail-content>{% for label, value in object %}<dt>{{ label }}</dt><dd>{{ value }}</dd>{% endfor %}</dl>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]
    author = Author.objects.create(
        name="Override Author",
        bio="Biography",
        birth_date=date(2024, 4, 5),
    )
    view = StubView(RequestFactory().get("/authors/1/"))
    view.get_focused_component_template_paths = lambda component: [
        f"sample/author_{component}.html",
        f"powercrud/daisyUI/partial/{component}.html",
    ]

    with override_settings(TEMPLATES=template_settings):
        custom_shell = render_to_string(
            "powercrud/daisyUI/object_detail.html#pcrud_content",
            {
                "object": author,
                "view": view,
                "detail_shell_template_paths": [
                    "sample/author_detail_shell.html",
                    "powercrud/daisyUI/partial/detail_shell.html",
                ],
            },
        )
        custom_content = render_to_string(
            "powercrud/daisyUI/partial/detail_shell.html",
            {"object": author, "view": view},
        )

    assert "data-custom-detail-shell" in custom_shell and "Override Author" in custom_shell, (
        "The model detail shell should win at the legacy root fragment."
    )
    assert "data-custom-detail-content" in custom_content and "2024-04-05" in custom_content, (
        "The built-in shell should retain independently resolved model detail content."
    )
    assert "<script" not in custom_shell + custom_content, (
        "Neither focused detail override should require copied PowerCRUD JavaScript."
    )


def test_delete_legacy_fragments_preserve_transport_errors_and_state():
    """Delete façades should retain confirmation transport and repeated query state."""
    request = RequestFactory().get(
        "/authors/7/delete/?status=open&status=review&page=3&csrfmiddlewaretoken=leaked"
    )
    context = {
        "request": request,
        "object_verbose_name": "author",
        "object": "Ada",
        "delete_errors": ["Protected relationship"],
        "delete_view_url": "/authors/7/delete/",
        "use_htmx": True,
        "original_target": "#author-list",
        "csrf_token": "delete-token",
        "delete_shell_template_paths": [
            "powercrud/daisyUI/partial/delete_shell.html"
        ],
        "delete_content_template_paths": [
            "powercrud/daisyUI/partial/delete_content.html"
        ],
    }
    routed = render_to_string(
        "powercrud/daisyUI/object_confirm_delete.html#pcrud_content",
        context,
        request=request,
    )
    direct = render_to_string(
        "powercrud/daisyUI/object_confirm_delete.html#normal_content",
        context,
        request=request,
    )
    normal = render_to_string(
        "powercrud/daisyUI/object_confirm_delete.html#normal_content",
        {**context, "use_htmx": False},
        request=request,
    )

    assert 'class="card bg-base-100 shadow-xl"' in routed and "Are you sure" in routed, (
        "The routed normal surface should retain one outer delete card."
    )
    assert 'class="card-body"' in direct and 'class="card bg-base-100 shadow-xl"' not in direct, (
        "The direct normal fragment should remain body-only."
    )
    assert "Protected relationship" in direct and "Ada" in direct, (
        "Delete errors and the target object should remain visible."
    )
    assert 'method="POST"' in direct and 'action="/authors/7/delete/"' in direct, (
        "Delete content should retain its POST form action."
    )
    assert 'name="csrfmiddlewaretoken"' in direct, (
        "Delete content should retain CSRF rendering."
    )
    assert direct.count('name="_powercrud_filter_status"') == 2, (
        "Repeated retained list values should remain repeated hidden inputs."
    )
    assert "_powercrud_filter_page" not in direct and "_powercrud_filter_csrfmiddlewaretoken" not in direct, (
        "Page and CSRF query values should remain excluded from retained state."
    )
    assert 'hx-post="/authors/7/delete/"' in direct and 'hx-target="#author-list"' in direct, (
        "HTMX delete confirmation should retain its post URL and list target."
    )
    assert 'hx-push-url="false"' in direct and "X-Redisplay-Object-List" in direct, (
        "HTMX delete confirmation should retain history and list-redisplay semantics."
    )
    assert "hx-post" not in normal and "<script" not in routed + direct + normal, (
        "Normal rendering should omit HTMX transport and focused copies should remain script-free."
    )


def test_delete_shell_and_content_prefer_independent_model_overrides(tmp_path):
    """Delete shell and content candidates should remain independently composable."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_delete_shell.html").write_text(
        '<section data-custom-delete-shell>{{ object }}</section>'
    )
    (override_path / "author_delete_content.html").write_text(
        '<div data-custom-delete-content>{{ object }}{% include "powercrud/daisyUI/partial/_delete_actions.html" %}</div>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]
    context = {
        "request": RequestFactory().get("/authors/7/delete/"),
        "object": "Ada",
        "object_verbose_name": "author",
        "delete_view_url": "/authors/7/delete/",
    }

    with override_settings(TEMPLATES=template_settings):
        custom_shell = render_to_string(
            "powercrud/daisyUI/object_confirm_delete.html#pcrud_content",
            {
                **context,
                "delete_shell_template_paths": [
                    "sample/author_delete_shell.html",
                    "powercrud/daisyUI/partial/delete_shell.html",
                ],
            },
        )
        custom_content = render_to_string(
            "powercrud/daisyUI/partial/delete_shell.html",
            {
                **context,
                "delete_content_template_paths": [
                    "sample/author_delete_content.html",
                    "powercrud/daisyUI/partial/delete_content.html",
                ],
            },
        )

    assert "data-custom-delete-shell" in custom_shell and "Ada" in custom_shell, (
        "The model delete shell should win at the legacy content router."
    )
    assert "data-custom-delete-content" in custom_content and "Delete" in custom_content, (
        "The built-in shell should retain independently resolved model delete content."
    )
    assert "<script" not in custom_shell + custom_content, (
        "Neither focused delete override should require copied PowerCRUD JavaScript."
    )


def test_delete_actions_preserve_submit_semantics_and_model_override(tmp_path):
    """The actions leaf should remain a destructive submit control and compose by model."""
    built_in = render_to_string("powercrud/daisyUI/partial/delete_actions.html")
    assert 'type="submit"' in built_in and "btn-error" in built_in, (
        "The built-in delete action should retain submit and destructive presentation semantics."
    )
    assert ">Delete</button>" in built_in and "<script" not in built_in, (
        "The built-in delete action should retain its label without copied JavaScript."
    )

    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_delete_actions.html").write_text(
        '<button type="submit" data-custom-delete-action>Delete author</button>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]
    request = RequestFactory().get("/authors/7/delete/")

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/partial/delete_content.html",
            {
                "request": request,
                "object": "Ada",
                "object_verbose_name": "author",
                "delete_view_url": "/authors/7/delete/",
                "delete_actions_template_paths": [
                    "sample/author_delete_actions.html",
                    "powercrud/daisyUI/partial/delete_actions.html",
                ],
            },
            request=request,
        )

    assert "data-custom-delete-action" in rendered and "Delete author" in rendered, (
        "The model delete action should win before the built-in submit control."
    )
    assert 'method="POST"' in rendered and 'action="/authors/7/delete/"' in rendered, (
        "The package delete content should continue owning the surrounding form."
    )
    assert "<script" not in rendered, (
        "A focused delete action should not need copied PowerCRUD JavaScript."
    )


def test_delete_conflict_preserves_normal_htmx_and_modal_returns():
    """The delete conflict leaf should retain each existing return mode."""
    request = RequestFactory().get("/authors/7/delete/?page_size=25")
    base_context = {
        "request": request,
        "conflict_message": "A bulk delete is running",
        "object": "Ada",
        "list_view_url": "/authors/",
        "default_page_size": 10,
        "original_target": "#author-list",
    }
    normal = render_to_string(
        "powercrud/daisyUI/partial/delete_conflict.html",
        {**base_context, "use_htmx": False, "use_modal": False},
        request=request,
    )
    htmx = render_to_string(
        "powercrud/daisyUI/partial/delete_conflict.html",
        {**base_context, "use_htmx": True, "use_modal": False},
        request=request,
    )
    modal = render_to_string(
        "powercrud/daisyUI/partial/delete_conflict.html",
        {**base_context, "use_htmx": True, "use_modal": True},
        request=request,
    )

    for rendered in (normal, htmx, modal):
        assert "Edit Conflict" in rendered and "A bulk delete is running" in rendered and "Ada" in rendered, (
            "Every delete conflict mode should retain its heading, message, and object."
        )
        assert "<script" not in rendered, (
            "The focused delete conflict should not copy PowerCRUD JavaScript."
        )
    assert 'href="/authors/"' in normal, (
        "Normal delete conflict rendering should retain its list link."
    )
    assert 'hx-get="/authors/"' in htmx and '"page_size": "25"' in htmx, (
        "HTMX delete conflict rendering should retain its list URL and page-size value."
    )
    assert 'hx-target="#author-list"' in htmx and 'hx-push-url="true"' in htmx, (
        "HTMX delete conflict rendering should retain its target and history behavior."
    )
    assert "Return to List" not in modal, (
        "Modal delete conflict rendering should continue suppressing the return control."
    )


def test_delete_conflict_legacy_fragments_prefer_model_override(tmp_path):
    """Both legacy delete-conflict addresses should select a model component."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_delete_conflict.html").write_text(
        '<div data-custom-delete-conflict>{{ conflict_message }}</div>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]
    context = {
        "conflict_detected": True,
        "conflict_message": "Custom delete conflict",
        "delete_conflict_template_paths": [
            "sample/author_delete_conflict.html",
            "powercrud/daisyUI/partial/delete_conflict.html",
        ],
    }

    with override_settings(TEMPLATES=template_settings):
        direct = render_to_string(
            "powercrud/daisyUI/object_confirm_delete.html#conflict_detected",
            context,
        )
        routed = render_to_string(
            "powercrud/daisyUI/object_confirm_delete.html#pcrud_content",
            context,
        )

    assert "data-custom-delete-conflict" in direct and "Custom delete conflict" in direct, (
        "The direct legacy conflict fragment should select the model override."
    )
    assert "data-custom-delete-conflict" in routed and 'class="card bg-base-100 shadow-xl"' in routed, (
        "The legacy router should retain its outer card around model conflict content."
    )
    assert "<script" not in direct + routed, (
        "A focused delete conflict override should not need copied PowerCRUD JavaScript."
    )


def test_inline_field_component_preserves_value_and_dependency_contract():
    """The direct inline-field path should retain widget and dependency hooks."""

    class DependentChoiceForm(forms.Form):
        """Minimal bound searchable field used for direct component rendering."""

        genre = forms.ChoiceField(
            choices=[("alpha", "Genre Alpha"), ("beta", "Genre Beta")],
            widget=forms.Select(
                attrs={"data-powercrud-searchable-select": "true"}
            ),
        )

    form = DependentChoiceForm(data={"genre": "beta"})
    assert form.is_valid(), "The inline-field fixture should contain a valid bound value."
    rendered = render_to_string(
        "powercrud/daisyUI/partial/inline_field.html",
        {
            "field": form["genre"],
            "field_name": "genre",
            "field_dependency": {
                "depends_on": ["author", "category"],
                "endpoint_url": "/books/7/dependency/",
            },
            "dependency_endpoint_url": "/books/dependency/",
        },
    )

    assert 'class="inline-field-widget w-full"' in rendered and 'data-inline-field="genre"' in rendered, (
        "The direct component should retain its stable replacement root and field marker."
    )
    assert 'data-inline-dependent="true"' in rendered and 'data-inline-depends-on="author,category"' in rendered, (
        "The direct component should retain ordered dependency parent metadata."
    )
    assert 'data-inline-endpoint="/books/7/dependency/"' in rendered, (
        "Field-specific dependency endpoints should retain precedence over the fallback."
    )
    assert 'value="beta" selected' in rendered and 'data-powercrud-searchable-select="true"' in rendered, (
        "The bound value and widget-supplied searchable hook should survive rendering."
    )
    assert "<script" not in rendered, (
        "The focused inline field should not copy PowerCRUD JavaScript."
    )


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

    assert result["headers"][0]["label"] == "Name", (
        "Object-list headers should expose the resolved display label in the header metadata mapping."
    )
    assert result["headers"][0]["field_name"] == "name", (
        "Object-list headers should expose the original field name in the header metadata mapping."
    )
    assert result["headers"][0]["is_sortable"] is True, (
        "Regular field headers should remain sortable in the header metadata mapping."
    )
    assert result["headers"][1]["field_name"] == "birth_date", (
        "Subsequent header entries should expose the expected field name in the metadata mapping."
    )

    row = result["object_list"][0]["fields"]
    assert "Test Author" in row
    assert date_format(author.birth_date, "DATE_FORMAT", use_l10n=False) in row, (
        "DateField list values should use the project's configured DATE_FORMAT."
    )

    # property renders truthy icon (contains svg markup)
    property_output = row[-1]
    assert "<svg" in property_output


@pytest.mark.django_db
def test_list_partial_renders_anchor_for_linked_non_inline_cell():
    author = Author.objects.create(
        name="Link Render Author",
        bio="Biography",
        birth_date=date(2024, 1, 1),
    )
    request = RequestFactory().get("/")

    class LinkedStubView(StubView):
        def get_link_fields(self):
            return {"name": "sample:author-detail"}

        def safe_reverse(self, url_name, kwargs=None):
            if kwargs:
                return f"/resolved/{url_name}/{kwargs['pk']}"
            return f"/resolved/{url_name}"

    view = LinkedStubView(request)
    context = {"request": request}
    result = powercrud_tags.object_list(context, [author], view)

    rendered = render_to_string(
        "powercrud/daisyUI/partial/list.html",
        {
            **result,
            "request": request,
            "view": view,
            "list_view_url": "/sample/author/",
            "inline_edit": {},
        },
        request=request,
    )

    assert (
        'href="/resolved/sample:author-detail/%s"' % author.pk in rendered
    ), "Rendered list rows should output a real anchor for linked non-inline cells."
    assert "link link-info" in rendered, (
        "Rendered linked list cells should use the default list-link styling when no hook classes override it."
    )


@pytest.mark.django_db
def test_list_partial_renders_modal_attrs_for_linked_modal_cell():
    author = Author.objects.create(
        name="Modal Link Render Author",
        bio="Biography",
        birth_date=date(2024, 1, 1),
    )
    request = RequestFactory().get("/")

    class ModalLinkedStubView(StubView):
        def get_use_htmx(self):
            return True

        def get_use_modal(self):
            return True

        def get_modal_target(self):
            return "#sample-modal"

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
                    "modal_attrs": 'onclick="sampleModal.showModal()"',
                }
            }

        def get_link_fields(self):
            return {"name": {"view_name": "sample:author-detail", "open_in": "modal"}}

        def safe_reverse(self, url_name, kwargs=None):
            if kwargs:
                return f"/resolved/{url_name}/{kwargs['pk']}"
            return f"/resolved/{url_name}"

    view = ModalLinkedStubView(request)
    context = {"request": request}
    result = powercrud_tags.object_list(context, [author], view)

    rendered = render_to_string(
        "powercrud/daisyUI/partial/list.html",
        {
            **result,
            "request": request,
            "view": view,
            "list_view_url": "/sample/author/",
            "inline_edit": {},
        },
        request=request,
    )

    assert 'hx-get="/resolved/sample:author-detail/%s"' % author.pk in rendered, (
        "Modal list-cell links should add hx-get for the resolved cell URL."
    )
    assert 'hx-target="#sample-modal"' in rendered, (
        "Modal list-cell links should target the resolved modal content container."
    )
    assert 'onclick="sampleModal.showModal()"' in rendered, (
        "Modal list-cell links should reuse the framework modal open attrs already used by actions and extra buttons."
    )
    assert "&quot;sampleModal.showModal()&quot;" not in rendered, (
        "Modal list-cell links should render modal_attrs as a real HTML attribute, not an escaped string literal."
    )


def test_get_proper_elided_page_range():
    paginator = Paginator(range(50), 1)
    page_range = powercrud_tags.get_proper_elided_page_range(paginator, 10)
    assert "…" in page_range


def test_legacy_pagination_fragment_renders_focused_component():
    """The legacy named fragment should delegate to the focused pagination component."""
    request = RequestFactory().get("/?page_size=10")
    paginator = Paginator(range(30), 10)
    page_obj = paginator.page(2)

    rendered = render_to_string(
        "powercrud/daisyUI/object_list.html#pagination",
        {
            "request": request,
            "is_paginated": True,
            "paginator": paginator,
            "page_obj": page_obj,
            "use_htmx": True,
            "original_target": "#content",
            "pagination_template_paths": [
                "powercrud/daisyUI/partial/pagination.html"
            ],
        },
        request=request,
    )

    assert 'data-powercrud-pagination="true"' in rendered, (
        "The legacy pagination fragment should retain the pagination runtime hook."
    )
    assert 'href="?page=1&page_size=10"' in rendered, (
        "Previous-page links should retain the selected page size."
    )
    assert 'href="?page=3&page_size=10"' in rendered, (
        "Next-page links should retain the selected page size."
    )
    assert 'hx-get="?page=1"' in rendered, (
        "HTMX pagination should retain the previous-page request URL."
    )
    assert 'hx-vals="js:{...getCurrentFilters()}"' in rendered, (
        "HTMX pagination should retain current filter collection."
    )


def test_pagination_component_prefers_downstream_model_override(tmp_path):
    """A model-scoped pagination template should replace markup without JavaScript."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_pagination.html").write_text(
        '<nav data-powercrud-pagination="true">Custom pagination</nav>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]
    request = RequestFactory().get("/?page_size=10")
    paginator = Paginator(range(30), 10)

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/object_list.html#pagination",
            {
                "request": request,
                "is_paginated": True,
                "paginator": paginator,
                "page_obj": paginator.page(2),
                "use_htmx": False,
                "original_target": None,
                "pagination_template_paths": [
                    "sample/author_pagination.html",
                    "powercrud/daisyUI/partial/pagination.html",
                ],
            },
            request=request,
        )

    assert "Custom pagination" in rendered, (
        "A downstream model override should be selected before the built-in pagination component."
    )
    assert "<script" not in rendered, (
        "A focused pagination override should not need copied PowerCRUD JavaScript."
    )


def test_page_size_selector_fragment_renders_focused_component():
    """The page-size wrapper should retain the selector runtime contract."""
    request = RequestFactory().get("/?page_size=10")

    rendered = render_to_string(
        "powercrud/daisyUI/object_list.html#page_size_selector",
        {
            "request": request,
            "page_size_options": ["5", "10", "25"],
            "default_page_size": "25",
            "page_size_all_enabled": False,
            "page_size_selector_template_paths": [
                "powercrud/daisyUI/partial/page_size_selector.html"
            ],
        },
        request=request,
    )

    assert 'id="page-size-form"' in rendered and 'id="page-size-select"' in rendered, (
        "The focused page-size component should retain the form and select IDs used by runtime state."
    )
    assert 'name="page_size"' in rendered and 'data-powercrud-page-size-select="true"' in rendered, (
        "The focused page-size component should retain the page-size form and selector hooks."
    )
    assert 'data-tippy-content="Rows per page"' in rendered, (
        "The focused page-size component should retain its tooltip metadata."
    )
    assert re.search(r'<option value="10"\s+selected\s*>\s*10\s*</option>', rendered), (
        "The request-selected page size should remain selected after component extraction."
    )


@pytest.mark.parametrize(
    ("selected_count", "expected_state"),
    [(0, "hidden"), (2, "visible")],
)
def test_bulk_selection_status_fragment_renders_focused_component(
    selected_count, expected_state
):
    """The legacy status fragment should delegate without losing runtime hooks."""

    class BulkStatusView:
        """Provide the toolbar class contract consumed by the component."""

        def get_extra_button_classes(self):
            """Return the configured compact toolbar classes."""
            return "btn-sm custom-action"

    rendered = render_to_string(
        "powercrud/daisyUI/object_list.html#bulk_selection_status",
        {
            "selected_count": selected_count,
            "enable_bulk_edit": True,
            "list_view_url": "/books/",
            "view": BulkStatusView(),
            "modal_target": "customModalContent",
            "modal_id": "customModal",
            "bulk_modal_box_classes": "modal-box max-w-5xl",
            "bulk_selection_status_template_paths": [
                "powercrud/daisyUI/partial/bulk_selection_status.html"
            ],
        },
    )

    assert 'id="bulk-actions-container"' in rendered and 'data-powercrud-bulk-actions="true"' in rendered, (
        "The focused status component should retain its outer-swap identity and runtime hook."
    )
    assert f'id="selected-items-counter">{selected_count}</span>' in rendered, (
        "The focused status component should retain the selected-count runtime source."
    )
    assert 'href="/books/bulk-edit/"' in rendered and 'hx-target="#customModalContent"' in rendered, (
        "The built-in bulk action should retain normal and HTMX modal navigation."
    )
    assert 'data-powercrud-modal-box-classes="modal-box max-w-5xl"' in rendered and "customModal" in rendered, (
        "The built-in bulk action should retain modal sizing and opening metadata."
    )
    assert 'data-powercrud-clear-selection' in rendered and 'hx-post="/books/clear-selection/"' in rendered, (
        "The focused status component should retain the clear-selection action."
    )
    if expected_state == "hidden":
        assert 'class="join hidden"' in rendered, (
            "A zero-count status container should remain in the DOM but hidden."
        )
    else:
        assert 'class="join hidden"' not in rendered, (
            "A non-zero status container should remain visible."
        )


def test_bulk_selection_status_component_prefers_downstream_model_override(tmp_path):
    """A model-scoped status template should replace markup without copied JavaScript."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_bulk_selection_status.html").write_text(
        '<div id="bulk-actions-container" data-powercrud-bulk-actions="true">'
        '<span id="selected-items-counter">3</span>'
        '<button data-powercrud-clear-selection>Clear custom selection</button></div>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/object_list.html#bulk_selection_status",
            {
                "selected_count": 3,
                "bulk_selection_status_template_paths": [
                    "sample/author_bulk_selection_status.html",
                    "powercrud/daisyUI/partial/bulk_selection_status.html",
                ],
            },
        )

    assert "Clear custom selection" in rendered, (
        "A downstream model override should be selected before the built-in status component."
    )
    assert "<script" not in rendered, (
        "A focused status override should not need copied PowerCRUD JavaScript."
    )


def test_bulk_selection_controls_render_all_three_modes():
    """The focused controls component should preserve matching, header, and row hooks."""
    request = RequestFactory().get("/books/?title=Power")
    template = "powercrud/daisyUI/partial/bulk_selection_controls.html"

    matching = render_to_string(
        template,
        {
            "selection_control": "matching",
            "show_select_all_matching": True,
            "select_all_matching_label": "Select all 12 matching records",
            "list_view_url": "/books/",
            "request": request,
        },
        request=request,
    ).replace("&amp;", "&")
    select_all = render_to_string(
        template,
        {
            "selection_control": "select_all",
            "all_selected": False,
            "some_selected": True,
        },
    )
    row = render_to_string(
        template,
        {
            "selection_control": "row",
            "row": {"id": "7"},
            "selected_ids": ["7"],
            "list_view_url": "/books/",
        },
    )

    assert 'hx-post="/books/select-all-matching/?title=Power"' in matching and 'hx-target="#bulk-actions-container"' in matching, (
        "Matching mode should retain the filtered queryset action and status target."
    )
    assert 'data-powercrud-select-all="true"' in select_all and 'data-powercrud-initial-indeterminate="true"' in select_all, (
        "Select-all mode should retain truthful initial header state."
    )
    assert 'data-powercrud-row-select="true"' in row and 'data-powercrud-initial-checked="true"' in row, (
        "Row mode should retain selected-row hydration metadata."
    )
    assert 'hx-post="/books/toggle-selection/7/"' in row and 'hx-swap="outerHTML"' in row, (
        "Row mode should retain its selection endpoint and outer swap."
    )


def test_legacy_modal_template_delegates_to_focused_shell():
    """The direct modal template should retain its complete dialog contract."""
    rendered = render_to_string(
        "powercrud/daisyUI/partial/modal.html",
        {
            "modal_id": "customModal",
            "modal_target": "customModalContent",
            "modal_classes": "modal custom-modal",
            "modal_box_classes": "modal-box max-w-4xl",
            "modal_body_classes": "overflow-y-auto py-4",
            "modal_shell_template_paths": [
                "powercrud/daisyUI/partial/modal_shell.html"
            ],
        },
    )

    assert '<dialog id="customModal" class="modal custom-modal" data-powercrud-modal>' in rendered, (
        "The legacy façade should retain configured dialog identity and hooks."
    )
    assert 'data-powercrud-modal-box' in rendered and 'data-powercrud-default-modal-box-classes="modal-box max-w-4xl"' in rendered, (
        "The focused shell should retain modal-box sizing restoration metadata."
    )
    assert 'id="customModalContent" class="overflow-y-auto py-4"' in rendered, (
        "The focused shell should retain the configured content target."
    )
    assert 'aria-label="Close modal"' in rendered and 'class="modal-backdrop"' in rendered, (
        "The focused shell should retain explicit close and backdrop controls."
    )


def test_modal_shell_prefers_downstream_model_override(tmp_path):
    """The legacy modal façade should select a script-free model override."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_modal_shell.html").write_text(
        '<dialog id="custom" data-powercrud-modal><div data-powercrud-modal-box>'
        '<div id="target">Custom modal shell</div></div></dialog>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/partial/modal.html",
            {
                "modal_shell_template_paths": [
                    "sample/author_modal_shell.html",
                    "powercrud/daisyUI/partial/modal_shell.html",
                ]
            },
        )

    assert "Custom modal shell" in rendered, (
        "A downstream model modal shell should be selected before the built-in dialog."
    )
    assert "<script" not in rendered, (
        "A focused modal shell override should not need copied PowerCRUD JavaScript."
    )


def test_modal_content_component_preserves_empty_target_contract():
    """The content component should remain an empty configured HTMX host."""
    rendered = render_to_string(
        "powercrud/daisyUI/partial/modal_content.html",
        {
            "modal_target": "customModalContent",
            "modal_body_classes": "min-h-0 overflow-y-auto",
        },
    )

    assert rendered.strip() == '<div id="customModalContent" class="min-h-0 overflow-y-auto"></div>', (
        "The focused modal content should contain only the configured empty target."
    )


def test_modal_content_prefers_downstream_model_override_through_shell(tmp_path):
    """A content-only override should not take ownership of modal chrome."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_modal_content.html").write_text(
        '<div id="customModalContent" class="custom-body"></div>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/partial/modal.html",
            {
                "modal_id": "customModal",
                "modal_classes": "modal",
                "modal_box_classes": "modal-box",
                "modal_shell_template_paths": [
                    "powercrud/daisyUI/partial/modal_shell.html"
                ],
                "modal_content_template_paths": [
                    "sample/author_modal_content.html",
                    "powercrud/daisyUI/partial/modal_content.html",
                ],
            },
        )

    assert 'id="customModalContent" class="custom-body"' in rendered, (
        "The built-in shell should select the downstream content host."
    )
    assert 'data-powercrud-modal' in rendered and 'class="modal-backdrop"' in rendered, (
        "A content override should leave dialog and backdrop ownership with the shell."
    )
    assert "<script" not in rendered, (
        "A focused modal content override should not need copied PowerCRUD JavaScript."
    )


def test_form_shell_preserves_create_update_transport_and_state():
    """The legacy normal fragment should delegate complete form transport semantics."""

    class UploadForm(forms.Form):
        """Minimal multipart form for the focused shell contract."""

        attachment = forms.FileField(required=False)

    request = RequestFactory().get(
        "/books/new/?status=open&status=review&page=3&csrfmiddlewaretoken=leaked"
    )
    context = {
        "request": request,
        "form": UploadForm(),
        "object": None,
        "object_verbose_name": "book",
        "form_display_items": [],
        "create_view_url": "/books/new/",
        "use_htmx": True,
        "use_modal": True,
        "original_target": "#powercrudModalContent",
        "use_crispy": False,
        "csrf_token": "focused-token",
        "form_shell_template_paths": [
            "powercrud/daisyUI/partial/form_shell.html"
        ],
    }

    create_rendered = render_to_string(
        "powercrud/daisyUI/object_form.html#normal_content",
        context,
        request=request,
    )
    update_rendered = render_to_string(
        "powercrud/daisyUI/object_form.html#normal_content",
        {
            **context,
            "object": object(),
            "form_display_items": [{"label": "Project", "value": "Apollo"}],
            "update_view_url": "/books/7/edit/",
            "use_modal": False,
        },
        request=request,
    )

    assert "Create book" in create_rendered and 'action="/books/new/"' in create_rendered, (
        "Create rendering should retain its heading and action URL."
    )
    assert 'enctype="multipart/form-data"' in create_rendered and 'data-powercrud-form="object"' in create_rendered, (
        "The focused shell should retain multipart and form runtime hooks."
    )
    assert 'hx-post="/books/new/"' in create_rendered and 'hx-target="#powercrudModalContent"' in create_rendered, (
        "Modal create rendering should retain its HTMX post and target."
    )
    assert 'hx-push-url="false"' in create_rendered and "X-Redisplay-Object-List" in create_rendered, (
        "Modal create rendering should retain history and list-redisplay semantics."
    )
    assert create_rendered.count('name="_powercrud_filter_status"') == 2, (
        "Repeated retained query values should remain repeated hidden inputs."
    )
    assert "_powercrud_filter_page" not in create_rendered and "_powercrud_filter_csrfmiddlewaretoken" not in create_rendered, (
        "Page and CSRF query parameters should remain excluded from retained state."
    )
    assert "Edit book" in update_rendered and 'action="/books/7/edit/"' in update_rendered, (
        "Update rendering should retain its heading and action URL."
    )
    assert "Project" in update_rendered and "Apollo" in update_rendered, (
        "Update rendering should retain display-only context items."
    )
    assert 'hx-push-url="true"' in update_rendered, (
        "A non-modal HTMX form should continue to push browser history."
    )


def test_form_shell_prefers_downstream_model_override(tmp_path):
    """The legacy normal fragment should select a script-free model shell."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_form_shell.html").write_text(
        '<form data-powercrud-form="object">Custom form shell</form>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/object_form.html#normal_content",
            {
                "form_shell_template_paths": [
                    "sample/author_form_shell.html",
                    "powercrud/daisyUI/partial/form_shell.html",
                ]
            },
        )

    assert "Custom form shell" in rendered, (
        "A downstream model form shell should be selected before the built-in structure."
    )
    assert "<script" not in rendered, (
        "A focused form shell override should not need copied PowerCRUD JavaScript."
    )


def test_form_fields_render_native_and_crispy_validation():
    """The focused fields leaf should preserve both declared rendering paths."""

    class RequiredNameForm(forms.Form):
        """Minimal bound form used to expose a validation message."""

        name = forms.CharField(label="Display name")

    form = RequiredNameForm(data={"name": ""})
    form.helper = FormHelper()
    form.helper.form_tag = False
    form.helper.disable_csrf = True
    assert not form.is_valid(), "The focused fields fixture should contain a required-field error."

    native = render_to_string(
        "powercrud/daisyUI/partial/form_fields.html",
        {"form": form, "use_crispy": False},
    )
    crispy = render_to_string(
        "powercrud/daisyUI/partial/form_fields.html",
        {
            "form": form,
            "use_crispy": True,
            "framework_template_path": "powercrud/daisyUI",
        },
    )

    for rendered in (native, crispy):
        assert 'name="name"' in rendered and "Display name" in rendered, (
            "Both field renderers should preserve the bound input and label."
        )
        assert "This field is required" in rendered, (
            "Both field renderers should preserve validation feedback."
        )
    assert "<form" not in crispy, (
        "The crispy fragment should not introduce a form inside the focused shell."
    )


def test_form_shell_prefers_downstream_fields_override(tmp_path):
    """The built-in shell should compose a script-free model fields override."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_form_fields.html").write_text(
        '<div data-custom-form-fields>{{ form.name }}</div>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/partial/form_shell.html",
            {
                "request": RequestFactory().get("/authors/new/"),
                "form": forms.Form(),
                "object_verbose_name": "author",
                "create_view_url": "/authors/new/",
                "use_htmx": False,
                "form_fields_template_paths": [
                    "sample/author_form_fields.html",
                    "powercrud/daisyUI/partial/form_fields.html",
                ],
            },
        )

    assert "data-custom-form-fields" in rendered, (
        "The model fields override should win before the built-in renderer."
    )
    assert 'data-powercrud-form="object"' in rendered and "data-form-save" in rendered, (
        "The package shell and actions should continue surrounding custom fields."
    )
    assert "<script" not in rendered, (
        "A focused fields override should not need copied PowerCRUD JavaScript."
    )


def test_form_actions_preserve_save_hook_and_model_override(tmp_path):
    """The actions leaf should retain submission semantics and compose by model."""
    built_in = render_to_string("powercrud/daisyUI/partial/form_actions.html")
    assert 'type="submit"' in built_in and "data-form-save" in built_in, (
        "The built-in action should remain a submit control and runtime spinner target."
    )
    assert ">Save</button>" in built_in and "<script" not in built_in, (
        "The built-in action should keep its accessible label without copied JavaScript."
    )

    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_form_actions.html").write_text(
        '<button type="submit" data-form-save data-custom-form-action>Save author</button>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/partial/form_shell.html",
            {
                "request": RequestFactory().get("/authors/new/"),
                "form": forms.Form(),
                "object_verbose_name": "author",
                "create_view_url": "/authors/new/",
                "use_htmx": False,
                "use_crispy": False,
                "form_actions_template_paths": [
                    "sample/author_form_actions.html",
                    "powercrud/daisyUI/partial/form_actions.html",
                ],
            },
        )

    assert "data-custom-form-action" in rendered and "Save author" in rendered, (
        "The model actions override should win before the built-in save control."
    )
    assert 'data-powercrud-form="object"' in rendered and 'action="/authors/new/"' in rendered, (
        "The package form shell should continue owning the surrounding transport."
    )
    assert "<script" not in rendered, (
        "A focused actions override should not need copied PowerCRUD JavaScript."
    )


def test_form_conflict_preserves_normal_htmx_and_modal_returns():
    """The conflict leaf should retain each existing return-to-list mode."""
    request = RequestFactory().get("/authors/7/edit/?page_size=25")
    base_context = {
        "request": request,
        "conflict_message": "An update is running",
        "object": "Ada",
        "list_view_url": "/authors/",
        "filter_params": "status=open",
        "original_target": "#author-list",
    }
    normal = render_to_string(
        "powercrud/daisyUI/partial/form_conflict.html",
        {**base_context, "use_htmx": False, "use_modal": False},
        request=request,
    )
    htmx = render_to_string(
        "powercrud/daisyUI/partial/form_conflict.html",
        {**base_context, "use_htmx": True, "use_modal": False},
        request=request,
    )
    modal = render_to_string(
        "powercrud/daisyUI/partial/form_conflict.html",
        {**base_context, "use_htmx": True, "use_modal": True},
        request=request,
    )

    for rendered in (normal, htmx, modal):
        assert "Edit Conflict" in rendered and "An update is running" in rendered and "Ada" in rendered, (
            "Every conflict mode should retain its heading, message, and object."
        )
        assert "<script" not in rendered, (
            "The focused conflict presentation should not copy PowerCRUD JavaScript."
        )
    assert 'href="/authors/"' in normal, (
        "Normal conflict rendering should retain its list link."
    )
    assert 'hx-get="/authors/?page_size=25&status=open"' in htmx, (
        "HTMX conflict rendering should retain its current query construction."
    )
    assert 'hx-target="#author-list"' in htmx and 'hx-push-url="true"' in htmx, (
        "HTMX conflict rendering should retain its list target and history behavior."
    )
    assert "Return to List" not in modal, (
        "Modal conflict rendering should continue suppressing the return control."
    )


def test_form_conflict_legacy_fragments_prefer_model_override(tmp_path):
    """Both legacy conflict addresses should select a model-first component."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_form_conflict.html").write_text(
        '<div data-custom-form-conflict>{{ conflict_message }}</div>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]
    context = {
        "conflict_detected": True,
        "conflict_message": "Custom conflict",
        "form_conflict_template_paths": [
            "sample/author_form_conflict.html",
            "powercrud/daisyUI/partial/form_conflict.html",
        ],
    }

    with override_settings(TEMPLATES=template_settings):
        direct = render_to_string(
            "powercrud/daisyUI/object_form.html#conflict_detected", context
        )
        routed = render_to_string(
            "powercrud/daisyUI/object_form.html#pcrud_content", context
        )

    assert "data-custom-form-conflict" in direct and "Custom conflict" in direct, (
        "The direct legacy conflict fragment should select the model override."
    )
    assert "data-custom-form-conflict" in routed and "Custom conflict" in routed, (
        "The legacy content router should retain conflict selection and delegation."
    )
    assert "<script" not in direct + routed, (
        "A focused conflict override should not need copied PowerCRUD JavaScript."
    )


def test_bulk_selection_controls_component_prefers_downstream_model_override(tmp_path):
    """One model override should receive every documented selection-control mode."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_bulk_selection_controls.html").write_text(
        "Custom selection mode={{ selection_control }}"
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]
    candidates = [
        "sample/author_bulk_selection_controls.html",
        "powercrud/daisyUI/partial/bulk_selection_controls.html",
    ]

    with override_settings(TEMPLATES=template_settings):
        header = render_to_string(
            "powercrud/daisyUI/partial/table_header.html",
            {
                "headers": [],
                "enable_selection_controls": True,
                "bulk_selection_controls_template_paths": candidates,
            },
        )
        row = render_to_string(
            "powercrud/daisyUI/partial/table_row.html",
            {
                "row": {"id": "7", "cells": []},
                "inline_edit": {"enabled": False},
                "enable_selection_controls": True,
                "bulk_selection_controls_template_paths": candidates,
            },
        )

    assert "Custom selection mode=select_all" in header, (
        "The table header should select the downstream three-mode component."
    )
    assert "Custom selection mode=row" in row, (
        "The table row should select the same downstream three-mode component."
    )
    assert "<script" not in header + row, (
        "A focused selection-controls override should not need copied PowerCRUD JavaScript."
    )


def test_page_size_selector_prefers_downstream_model_override(tmp_path):
    """A model-scoped page-size template should replace markup without JavaScript."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_page_size_selector.html").write_text(
        '<form id="page-size-form"><select id="page-size-select" '
        'data-powercrud-page-size-select="true"></select>Custom page size</form>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]
    request = RequestFactory().get("/")

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/object_list.html#page_size_selector",
            {
                "request": request,
                "page_size_options": ["10"],
                "default_page_size": "10",
                "page_size_all_enabled": False,
                "page_size_selector_template_paths": [
                    "sample/author_page_size_selector.html",
                    "powercrud/daisyUI/partial/page_size_selector.html",
                ],
            },
            request=request,
        )

    assert "Custom page size" in rendered, (
        "A downstream page-size override should be selected before the built-in component."
    )
    assert "<script" not in rendered, (
        "A focused page-size override should not need copied PowerCRUD JavaScript."
    )


def test_list_actions_fragment_renders_focused_component():
    """The focused list-actions fragment should retain create and extra-action behaviour."""

    class ListActionsView:
        """Minimal list-view contract used by the extra-buttons template tag."""

        extra_buttons = [
            {
                "url_name": "sample:author-list",
                "text": "Review authors",
                "display_modal": False,
                "needs_pk": False,
            }
        ]

        def get_extra_button_classes(self):
            """Return the default compact toolbar button classes."""
            return "btn-sm"

        def get_framework_styles(self):
            """Provide the DaisyUI styles used by the extra-buttons tag."""
            return {
                "daisyUI": {
                    "base": "btn",
                    "extra_default": "btn-secondary",
                    "modal_attrs": 'onclick="modal.showModal()"',
                }
            }

        def get_use_htmx(self):
            """Enable HTMX to exercise the preserved action contract."""
            return True

        def get_use_modal(self):
            """Enable modal support for the extra-buttons contract."""
            return True

        def get_extra_buttons_mode(self):
            """Keep the configured action in its normal inline mode."""
            return "buttons"

        def safe_reverse(self, viewname, kwargs=None):
            """Return a stable URL for the configured extra action."""
            return "/authors/review/"

    request = RequestFactory().get("/")
    rendered = render_to_string(
        "powercrud/daisyUI/object_list.html#list_actions",
        {
            "request": request,
            "create_view_url": "/authors/create/",
            "use_htmx": True,
            "htmx_target": "#powercrudModalContent",
            "modal_id": "powercrudBaseModal",
            "object_verbose_name": "author",
            "view": ListActionsView(),
            "list_actions_template_paths": [
                "powercrud/daisyUI/partial/list_actions.html"
            ],
        },
        request=request,
    )

    assert 'href="/authors/create/"' in rendered and "Create author" in rendered, (
        "The focused component should retain the Create link and its label."
    )
    assert 'hx-get="/authors/create/"' in rendered and 'hx-target="#powercrudModalContent"' in rendered, (
        "The focused component should retain HTMX modal targeting for Create."
    )
    assert 'data-powercrud-modal-trigger="true"' in rendered and "powercrudBaseModal" in rendered, (
        "The focused component should retain the Create modal trigger and opener."
    )
    assert "Review authors" in rendered and 'href="/authors/review/"' in rendered, (
        "The focused component should retain PowerCRUD-rendered extra actions."
    )


def test_list_actions_component_prefers_downstream_model_override(tmp_path):
    """A model-scoped list-actions template should replace markup without JavaScript."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_list_actions.html").write_text("Custom list actions")
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]
    request = RequestFactory().get("/")

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/object_list.html#list_actions",
            {
                "request": request,
                "list_actions_template_paths": [
                    "sample/author_list_actions.html",
                    "powercrud/daisyUI/partial/list_actions.html",
                ],
            },
            request=request,
        )

    assert "Custom list actions" in rendered, (
        "A downstream list-actions override should be selected before the built-in component."
    )
    assert "<script" not in rendered, (
        "A focused list-actions override should not need copied PowerCRUD JavaScript."
    )


def test_filter_trigger_fragment_renders_focused_component():
    """The focused filter trigger should retain its runtime and accessibility hooks."""

    class FilterTriggerView:
        """Minimal view contract used by the focused filter trigger."""

        def get_extra_button_classes(self):
            """Return compact toolbar classes for the trigger button."""
            return "btn-sm"

    rendered = render_to_string(
        "powercrud/daisyUI/object_list.html#filter_trigger",
        {
            "view": FilterTriggerView(),
            "filter_trigger_template_paths": [
                "powercrud/daisyUI/partial/filter_trigger.html"
            ],
        },
    )

    assert 'id="filterToggleBtn"' in rendered and 'aria-controls="filterCollapse"' in rendered, (
        "The focused trigger should retain its stable button and filter-panel IDs."
    )
    assert 'data-powercrud-filter-toggle' in rendered and 'data-tippy-content="Show filters"' in rendered, (
        "The focused trigger should retain its runtime and tooltip hooks."
    )
    assert 'data-powercrud-filter-toggle-icon-outline="true"' in rendered and 'data-powercrud-filter-toggle-icon-filled="true"' in rendered, (
        "The focused trigger should retain both icons used for active-filter state."
    )


def test_filter_trigger_component_prefers_downstream_model_override(tmp_path):
    """A model-scoped filter trigger should replace markup without JavaScript."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_filter_trigger.html").write_text(
        "Custom filter trigger"
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/object_list.html#filter_trigger",
            {
                "filter_trigger_template_paths": [
                    "sample/author_filter_trigger.html",
                    "powercrud/daisyUI/partial/filter_trigger.html",
                ],
            },
        )

    assert "Custom filter trigger" in rendered, (
        "A downstream filter-trigger override should be selected before the built-in component."
    )
    assert "<script" not in rendered, (
        "A focused filter-trigger override should not need copied PowerCRUD JavaScript."
    )


def test_filter_panel_actions_fragment_renders_focused_component():
    """Focused filter-panel actions should retain their add, submit, and reset contract."""

    class FilterPanelActionsView:
        """Minimal view contract used by focused filter-panel actions."""

        def get_extra_button_classes(self):
            """Return compact toolbar classes for filter actions."""
            return "btn-sm"

    rendered = render_to_string(
        "powercrud/daisyUI/object_list.html#filter_panel_actions",
        {
            "addable_filter_choices": [
                {"name": "isbn", "label": "Isbn"},
            ],
            "use_htmx": False,
            "view": FilterPanelActionsView(),
            "original_target": "#content",
            "filter_panel_actions_template_paths": [
                "powercrud/daisyUI/partial/filter_panel_actions.html"
            ],
        },
    )

    assert 'data-powercrud-add-filter-container' in rendered and 'data-powercrud-add-filter-select' in rendered, (
        "The focused component should retain the add-filter container and selector hooks."
    )
    assert '<option value="isbn">Isbn</option>' in rendered, (
        "The focused component should retain the available optional-filter choices."
    )
    assert 'type="submit"' in rendered and 'form="filter-form"' in rendered, (
        "The non-HTMX Filter action should retain its external filter-form target."
    )
    assert 'data-powercrud-filter-reset' in rendered and 'hx-target="#content"' in rendered, (
        "The focused component should retain the progressive reset and HTMX target hooks."
    )


def test_filter_panel_actions_component_prefers_downstream_model_override(tmp_path):
    """A model-scoped filter-panel action template should replace markup without JavaScript."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_filter_panel_actions.html").write_text(
        "Custom filter panel actions"
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/object_list.html#filter_panel_actions",
            {
                "filter_panel_actions_template_paths": [
                    "sample/author_filter_panel_actions.html",
                    "powercrud/daisyUI/partial/filter_panel_actions.html",
                ],
            },
        )

    assert "Custom filter panel actions" in rendered, (
        "A downstream filter-panel action override should be selected before the built-in component."
    )
    assert "<script" not in rendered, (
        "A focused filter-panel action override should not need copied PowerCRUD JavaScript."
    )


def test_filter_form_fragment_renders_focused_component():
    """The focused filter form should retain fields, visibility state, and HTMX wiring."""
    filter_form = forms.Form(
        data={"title": "PowerCRUD", "isbn": "978", "visible_filters": "isbn"}
    )
    filter_form.fields["title"] = forms.CharField(label="Title", required=False)
    filter_form.fields["isbn"] = forms.CharField(label="Isbn", required=False)
    filter_form.is_valid()
    request = RequestFactory().get("/books/")

    rendered = render_to_string(
        "powercrud/daisyUI/object_list.html#filter_form",
        {
            "request": request,
            "visible_filter_fields": [filter_form["title"], filter_form["isbn"]],
            "persisted_optional_filter_names": ["isbn"],
            "visible_filter_param_name": "visible_filters",
            "filter_form_template_paths": [
                "powercrud/daisyUI/partial/filter_form.html"
            ],
        },
        request=request,
    )

    assert 'id="filter-form"' in rendered and 'action="/books/"' in rendered, (
        "The focused component should retain the stable form ID and current-path action."
    )
    assert 'hx-target="#filtered_results"' in rendered and 'hx-push-url="true"' in rendered and 'hx-replace-url="true"' in rendered, (
        "The focused component should retain HTMX result targeting and history behavior."
    )
    assert "X-Filter-Sort-Request" in rendered and "X-Filter-Setting-Request" in rendered, (
        "The focused component should retain both HTMX filter request headers."
    )
    assert 'value="PowerCRUD"' in rendered and 'name="visible_filters" value="isbn"' in rendered, (
        "The focused component should retain bound filter values and persisted optional-filter state."
    )
    assert 'data-powercrud-remove-filter="isbn"' in rendered and 'aria-label="Remove Isbn filter"' in rendered, (
        "The focused component should retain optional-filter removal controls."
    )


def test_filter_form_component_prefers_downstream_model_override(tmp_path):
    """A model-scoped filter form should replace markup without JavaScript."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_filter_form.html").write_text("Custom filter form")
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/object_list.html#filter_form",
            {
                "filter_form_template_paths": [
                    "sample/author_filter_form.html",
                    "powercrud/daisyUI/partial/filter_form.html",
                ],
            },
        )

    assert "Custom filter form" in rendered, (
        "A downstream filter-form override should be selected before the built-in component."
    )
    assert "<script" not in rendered, (
        "A focused filter-form override should not need copied PowerCRUD JavaScript."
    )


def test_list_columns_fragment_renders_focused_component():
    """The focused list-column chooser should retain its form and runtime contract."""

    class ListColumnsView:
        """Provide the button-class contract needed by the chooser component."""

        def get_extra_button_classes(self):
            """Return a recognizable class for the rendered chooser trigger."""
            return "btn-sm"

    request = RequestFactory().get(
        "/books/?author=1&author=2&page=3&csrfmiddlewaretoken=query-token"
    )
    list_column_state = {
        "active_columns": ["title"],
        "allowed_columns": ["title", "author"],
        "choices": [
            {
                "name": "title",
                "label": "Title",
                "is_active": True,
                "is_default": True,
            },
            {
                "name": "author",
                "label": "Author",
                "is_active": False,
                "is_default": False,
            },
        ],
    }

    rendered = render_to_string(
        "powercrud/daisyUI/object_list.html#list_columns",
        {
            "request": request,
            "view": ListColumnsView(),
            "list_column_state": list_column_state,
            "list_options_url": "/books/list-options/",
            "list_view_url": "/books/",
            "use_htmx": True,
            "original_target": "#content",
            "list_columns_template_paths": [
                "powercrud/daisyUI/partial/list_columns.html"
            ],
        },
        request=request,
    )

    assert 'data-powercrud-list-columns="true"' in rendered and 'data-powercrud-list-columns-trigger="true"' in rendered, (
        "The focused component should retain its chooser and trigger hooks."
    )
    assert 'data-powercrud-list-columns-template="true"' in rendered and 'data-powercrud-list-columns-panel="true"' in rendered, (
        "The focused component should retain the detachable template and panel hooks."
    )
    assert 'action="/books/list-options/"' in rendered and 'hx-post="/books/list-options/"' in rendered, (
        "The chooser should retain normal and HTMX form destinations."
    )
    assert 'hx-target="#content"' in rendered and 'hx-swap="innerHTML"' in rendered, (
        "The chooser should retain its HTMX list replacement contract."
    )
    assert 'name="csrfmiddlewaretoken"' in rendered and 'name="list_view_url" value="/books/"' in rendered, (
        "The chooser should retain CSRF protection and its list-view return URL."
    )
    assert rendered.count('name="author"') == 2 and 'value="1"' in rendered and 'value="2"' in rendered, (
        "The chooser should preserve repeated non-pagination query values."
    )
    assert 'name="page"' not in rendered and "query-token" not in rendered, (
        "The chooser should omit page and query-string CSRF state from hidden inputs."
    )
    assert re.search(r'name="visible_columns"\s+value="title"', rendered) and 'data-powercrud-initial-checked="true"' in rendered, (
        "The chooser should retain its checkbox name and initial-state hook."
    )
    assert 'name="list_columns_action"' in rendered and 'value="reset"' in rendered and 'value="apply"' in rendered, (
        "The chooser should retain its Reset and Save submission contract."
    )


def test_list_columns_component_prefers_downstream_model_override(tmp_path):
    """A model-scoped list-column chooser should replace markup without JavaScript."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_list_columns.html").write_text(
        '<details data-powercrud-list-columns="true">Custom columns</details>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/object_list.html#list_columns",
            {
                "list_columns_template_paths": [
                    "sample/author_list_columns.html",
                    "powercrud/daisyUI/partial/list_columns.html",
                ],
            },
        )

    assert "Custom columns" in rendered, (
        "A downstream list-column override should be selected before the built-in component."
    )
    assert "<script" not in rendered, (
        "A focused list-column override should not need copied PowerCRUD JavaScript."
    )


def test_row_actions_component_renders_resolved_presentation_metadata():
    """The focused row-actions template should emit resolved runtime metadata only."""
    base_action = {
        "href": "/books/1/edit/",
        "text": "Edit",
        "class_name": "btn btn-primary",
        "label_html": "<svg aria-hidden='true'></svg><span>Edit</span>",
        "style": "min-width: 2.5rem;",
        "use_htmx": True,
        "hx_post": False,
        "target": "#content",
        "use_history": False,
        "modal_attrs": 'onclick="modal.showModal()"',
        "modal_box_classes": "modal-box max-w-3xl",
        "refresh_list_on_modal_close": True,
        "disable": False,
        "tooltip_text": "Edit",
        "inline_action": "edit",
    }
    dropdown_action = {
        "href": "/books/1/archive/",
        "text": "Archive",
        "class_name": "justify-start whitespace-nowrap btn-disabled opacity-50",
        "label_html": None,
        "style": "pointer-events: auto !important; cursor: not-allowed;",
        "use_htmx": True,
        "hx_post": True,
        "target": "#content",
        "use_history": True,
        "modal_attrs": "",
        "modal_box_classes": "",
        "refresh_list_on_modal_close": False,
        "disable": True,
        "tooltip_text": "Archive is locked.",
        "inline_action": "archive",
        "lazy_row_action_state": True,
        "action_index": 4,
        "lazy_hidden_if": True,
    }

    rendered = render_to_string(
        "powercrud/daisyUI/partial/row_actions.html",
        {
            "row_actions": {
                "standard_actions": [base_action],
                "extra_actions": [dropdown_action],
                "show_extra_dropdown": True,
                "row_action_states_url": "/books/1/action-states/",
                "dropdown_trigger_class": "btn btn-secondary",
            }
        },
    )

    assert "<svg aria-hidden='true'></svg>" in rendered and "data-inline-action='edit'" in rendered, (
        "The component should render trusted standard-action presentation and its stable action hook."
    )
    assert "hx-get='/books/1/edit/'" in rendered and "data-powercrud-modal-box-classes='modal-box max-w-3xl'" in rendered, (
        "The component should retain resolved HTMX and modal presentation metadata."
    )
    assert "data-powercrud-refresh-list-on-modal-close='true'" in rendered, (
        "The component should retain resolved modal-close refresh behavior."
    )
    assert "data-powercrud-row-actions-trigger='true'" in rendered and "data-powercrud-row-actions-template='true'" in rendered and "data-powercrud-row-actions-panel='true'" in rendered, (
        "The component should retain the floating dropdown runtime hooks."
    )
    assert "hx-post='/books/1/archive/'" in rendered and "hx-push-url='true'" in rendered, (
        "The component should render resolved non-modal HTMX POST and history metadata."
    )
    assert "aria-disabled='true'" in rendered and "data-tippy-content='Archive is locked.'" in rendered, (
        "The component should retain resolved disabled and tooltip presentation."
    )
    assert "data-powercrud-row-action-state-mode='lazy'" in rendered and "data-powercrud-row-action-index='4'" in rendered and "data-powercrud-row-action-hidden-mode='lazy'" in rendered, (
        "The component should retain resolved lazy-state metadata and original action index."
    )


def test_row_actions_component_prefers_downstream_model_override(tmp_path):
    """A model-scoped row-actions template should replace markup without JavaScript."""

    class RowActionsView:
        """Provide model-specific row-action candidates to the renderer."""

        request = RequestFactory().get("/authors/")

        def get_focused_component_template_paths(self, component_name):
            """Return the model override before the built-in focused component."""
            assert component_name == "row_actions", (
                "The row-action renderer should request only its focused component."
            )
            return [
                "sample/author_row_actions.html",
                "powercrud/daisyUI/partial/row_actions.html",
            ]

    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_row_actions.html").write_text(
        "<div data-inline-action='custom'>Custom row actions</div>"
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = powercrud_tags._render_row_actions(
            RowActionsView(),
            {"object": None, "row_actions": {}},
        )

    assert "Custom row actions" in rendered, (
        "A downstream row-actions override should be selected before the built-in component."
    )
    assert "<script" not in rendered, (
        "A focused row-actions override should not need copied PowerCRUD JavaScript."
    )


def test_table_header_component_preserves_sort_help_selection_and_actions_contract():
    """The focused table header should retain navigation and system columns."""
    request = RequestFactory().get("/books/?page_size=5")
    context = {
        "request": request,
        "headers": [
            {
                "label": "Title",
                "field_name": "title",
                "is_sortable": True,
                "help_text": "Primary title",
            },
            {
                "label": "Computed",
                "field_name": "computed",
                "is_sortable": False,
                "help_text": "",
            },
        ],
        "current_sort": "title",
        "filter_params": "title=Existing&visible_filters=title&page_size=5",
        "use_htmx": True,
        "enable_selection_controls": True,
        "all_selected": False,
        "some_selected": True,
        "has_row_actions": True,
    }

    rendered = render_to_string(
        "powercrud/daisyUI/partial/table_header.html",
        context,
        request=request,
    )
    normalized = rendered.replace("&amp;", "&")

    assert "<thead>" in rendered and 'data-powercrud-select-all="true"' in rendered, (
        "The component should retain the table header and select-all bridge."
    )
    assert 'data-powercrud-initial-indeterminate="true"' in rendered and "indeterminate" in rendered, (
        "The select-all bridge should retain its initial indeterminate state contract."
    )
    assert 'hx-get="?sort=-title&page_size=5&title=Existing&visible_filters=title&page_size=5"' in normalized, (
        "Ascending state should toggle to descending while preserving existing list state exactly."
    )
    assert "X-Filter-Sort-Request" in rendered and 'hx-target="#filtered_results"' in rendered and 'hx-push-url="true"' in rendered, (
        "The component should retain the HTMX sort request, target, and history contract."
    )
    assert 'aria-label="Help for Title"' in rendered and 'data-tippy-content="Primary title"' in rendered and 'onclick="event.stopPropagation();"' in rendered, (
        "Header help should remain accessible and should not trigger sorting."
    )
    computed_header = rendered.split("Computed", maxsplit=1)[0].rsplit("<th", maxsplit=1)[-1]
    assert "hx-get" not in computed_header and "onclick=" not in computed_header, (
        "Non-sortable headers should not gain navigation behavior."
    )
    assert '<span class="text-center block w-full h-full">Actions</span>' in rendered, (
        "The component should retain the conditional row-actions heading."
    )

    normal_rendered = render_to_string(
        "powercrud/daisyUI/partial/table_header.html",
        {**context, "use_htmx": False},
        request=request,
    ).replace("&amp;", "&")
    assert "window.location.href='?sort=-title&page_size=5&title=Existing&visible_filters=title&page_size=5'" in normal_rendered, (
        "Non-HTMX sorting should retain equivalent normal navigation."
    )
    assert "X-Filter-Sort-Request" not in normal_rendered and "hx-get=" not in normal_rendered, (
        "Non-HTMX headers should not emit HTMX navigation attributes."
    )


def test_table_header_component_prefers_downstream_model_override(tmp_path):
    """The legacy list partial should select a model-scoped table header without JavaScript."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_table_header.html").write_text(
        "<thead><tr><th>Custom table header</th></tr></thead>"
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/partial/list.html",
            {
                "inline_edit": {"enabled": False},
                "object_list": [],
                "table_header_template_paths": [
                    "sample/author_table_header.html",
                    "powercrud/daisyUI/partial/table_header.html",
                ],
            },
        )

    assert "Custom table header" in rendered, (
        "The legacy list façade should select a downstream table-header override first."
    )
    assert "<script" not in rendered, (
        "A focused table-header override should not need copied PowerCRUD JavaScript."
    )


def test_table_row_component_preserves_cells_inline_selection_and_actions_contract():
    """The focused normal row should retain cell and compatibility hooks."""
    row = {
        "row_id": "book-row-7",
        "id": "7",
        "is_selected": True,
        "inline_blocked_reason": "",
        "inline_blocked_label": "",
        "inline_url": "/books/7/inline/",
        "inline_allowed": True,
        "actions": mark_safe("<div data-inline-action='edit'>Edit</div>"),
        "cells": [
            {
                "name": "title",
                "value": "Focused title",
                "align": "left",
                "is_inline_editable": True,
                "dependency": {
                    "depends_on": ["author"],
                    "endpoint_url": "/books/7/dependencies/",
                },
                "tooltip_text": "Full focused title",
                "tooltip_url": None,
                "link": None,
            },
            {
                "name": "author",
                "value": "Ada",
                "align": "center",
                "is_inline_editable": False,
                "dependency": None,
                "tooltip_text": None,
                "tooltip_url": "/books/7/tooltips/author/",
                "link": {
                    "url": "/authors/1/",
                    "classes": "link link-primary",
                    "hx_method": "get",
                    "hx_target": "#powercrudModalContent",
                    "title": "Author detail",
                    "target": "",
                    "rel": "",
                    "modal_attrs": 'onclick="modal.showModal()"',
                    "modal_box_classes": "modal-box max-w-3xl",
                },
            },
            {
                "name": "pages",
                "value": "250",
                "align": "right",
                "is_inline_editable": False,
                "dependency": None,
                "tooltip_text": None,
                "tooltip_url": None,
                "link": None,
            },
        ],
    }
    context = {
        "row": row,
        "inline_edit": {
            "enabled": True,
            "dependency_endpoint_url": "/books/dependencies/",
        },
        "enable_selection_controls": True,
        "selected_ids": ["7"],
        "list_view_url": "/books/",
        "has_row_actions": True,
    }

    rendered = render_to_string(
        "powercrud/daisyUI/partial/table_row.html",
        context,
    )

    assert 'id="book-row-7"' in rendered and "bg-base-200" in rendered and 'data-inline-row-url="/books/7/inline/"' in rendered, (
        "The component should retain row identity, selected state, and inline URL metadata."
    )
    assert 'data-powercrud-row-select="true"' in rendered and 'data-powercrud-initial-checked="true"' in rendered, (
        "The component should retain the selection-cell compatibility hooks."
    )
    assert 'hx-post="/books/toggle-selection/7/"' in rendered and 'hx-target="#bulk-actions-container"' in rendered, (
        "The selection bridge should retain its HTMX update endpoint and target."
    )
    assert 'data-field-name="title"' in rendered and 'data-inline-dependent-field="title"' in rendered and 'data-inline-depends-on="author"' in rendered, (
        "The component should retain field and inline dependency metadata."
    )
    assert 'data-inline-field="title"' in rendered and 'hx-target="#book-row-7"' in rendered, (
        "Editable display cells should retain their inline trigger and row-swap target."
    )
    assert 'data-tippy-content="Full focused title"' in rendered and 'data-powercrud-tooltip="semantic-cell"' in rendered, (
        "Eager semantic cell tooltip metadata should remain intact."
    )
    assert 'href="/authors/1/"' in rendered and 'hx-get="/authors/1/"' in rendered and 'onclick="modal.showModal()"' in rendered, (
        "Resolved normal and modal link attributes should remain intact."
    )
    assert 'data-powercrud-tooltip-mode="lazy"' in rendered and 'data-powercrud-tooltip-url="/books/7/tooltips/author/"' in rendered, (
        "Lazy semantic cell tooltip metadata should remain intact."
    )
    assert 'style="text-align:right;"' in rendered and 'data-tippy-content="250" data-powercrud-tooltip="overflow"' in rendered, (
        "Right alignment and plain-value overflow tooltip metadata should remain intact."
    )
    assert 'data-inline-actions="true"' in rendered and "data-inline-action='edit'" in rendered, (
        "The globally aligned row-action cell should retain resolved safe action markup."
    )

    blocked_rendered = render_to_string(
        "powercrud/daisyUI/partial/table_row.html",
        {
            **context,
            "enable_selection_controls": False,
            "has_row_actions": False,
            "row": {
                **row,
                "is_selected": False,
                "inline_allowed": False,
                "inline_blocked_reason": "locked",
                "inline_blocked_label": "Editing locked by policy.",
            },
        },
    )
    assert 'data-inline-status="locked"' in blocked_rendered and 'aria-disabled="true"' in blocked_rendered, (
        "Blocked inline rows should retain status and disabled affordances."
    )
    assert 'data-tippy-content="Editing locked by policy."' in blocked_rendered, (
        "Blocked inline cells should retain their semantic reason tooltip."
    )


def test_table_row_component_prefers_downstream_model_override(tmp_path):
    """The legacy list partial should select model-scoped rows without JavaScript."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_table_row.html").write_text(
        '<tr data-inline-row="true"><td>Custom table row</td></tr>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/partial/list.html",
            {
                "inline_edit": {"enabled": False},
                "object_list": [{"id": "1"}],
                "table_row_template_paths": [
                    "sample/author_table_row.html",
                    "powercrud/daisyUI/partial/table_row.html",
                ],
            },
        )

    assert "Custom table row" in rendered, (
        "The legacy list façade should select a downstream table-row override first."
    )
    assert "<script" not in rendered, (
        "A focused table-row override should not need copied PowerCRUD JavaScript."
    )


def test_inline_row_display_legacy_fragment_prefers_model_override(tmp_path):
    """The direct legacy display fragment should select the focused row component."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_inline_row_display.html").write_text(
        '<tr data-inline-row="true" data-custom-inline-display><td>{{ row.id }}</td></tr>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        direct = render_to_string(
            "powercrud/daisyUI/partial/list.html#inline_row_display",
            {
                "row": {"id": "7"},
                "inline_row_display_template_paths": [
                    "sample/author_inline_row_display.html",
                    "powercrud/daisyUI/partial/inline_row_display.html",
                ],
            },
        )
        normal_table_row = render_to_string(
            "powercrud/daisyUI/partial/table_row.html",
            {
                "row": {"id": "8"},
                "inline_row_display_template_paths": [
                    "sample/author_inline_row_display.html",
                    "powercrud/daisyUI/partial/inline_row_display.html",
                ],
            },
        )

    assert "data-custom-inline-display" in direct and ">7</td>" in direct, (
        "The direct legacy fragment should select the model display row."
    )
    assert "data-custom-inline-display" in normal_table_row and ">8</td>" in normal_table_row, (
        "The built-in table-row façade should share the canonical model display row."
    )
    assert "<script" not in direct + normal_table_row, (
        "A focused inline display row should not need copied PowerCRUD JavaScript."
    )


def test_table_shell_component_preserves_geometry_state_and_delegation(tmp_path):
    """The focused table shell should retain geometry and nested components."""
    component_path = tmp_path / "components"
    component_path.mkdir()
    (component_path / "test_header.html").write_text(
        "<thead><tr><th>Delegated header</th></tr></thead>"
    )
    (component_path / "test_row.html").write_text(
        '<tr data-inline-row="true"><td>Delegated row {{ row.id }}</td></tr>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/partial/table_shell.html",
            {
                "inline_edit": {"enabled": True},
                "table_classes": "table-sm custom-table",
                "enable_selection_controls": True,
                "keyBase": "sample_book",
                "selection_key_suffix": "staff",
                "table_header_template_paths": ["components/test_header.html"],
                "table_row_template_paths": ["components/test_row.html"],
                "object_list": [{"id": "1"}, {"id": "2"}],
            },
        )

    assert 'class="box-border w-full max-w-full overflow-x-auto table-max-height"' in rendered, (
        "The shell should retain its responsive overflow and height classes."
    )
    assert 'style="overflow-y: auto; padding-right: 20px;"' in rendered, (
        "The shell should retain its vertical scrolling and padding geometry."
    )
    assert 'data-selection-key="sample_book_staff_selected"' in rendered, (
        "The shell should retain its selection-key metadata expression."
    )
    assert 'class="table table-sm custom-table w-auto min-w-max"' in rendered and 'data-inline-enabled="true"' in rendered, (
        "The shell should retain configured table classes and inline-enabled metadata."
    )
    assert rendered.count("Delegated header") == 1, (
        "The shell should delegate to the resolved table-header component once."
    )
    assert rendered.count("Delegated row") == 2 and "Delegated row 1" in rendered and "Delegated row 2" in rendered, (
        "The shell should delegate every object to the resolved table-row component."
    )
    assert "No selection restore JS here; handled globally in object_list.html" in rendered, (
        "The shell should retain the explicit global selection-runtime boundary."
    )


def test_table_shell_component_prefers_downstream_model_override(tmp_path):
    """The legacy list partial should select a model-scoped shell without JavaScript."""
    override_path = tmp_path / "sample"
    override_path.mkdir()
    (override_path / "author_table_shell.html").write_text(
        '<div class="table-max-height">Custom table shell</div>'
    )
    template_settings = deepcopy(settings.TEMPLATES)
    template_settings[0]["DIRS"] = [str(tmp_path), *template_settings[0]["DIRS"]]

    with override_settings(TEMPLATES=template_settings):
        rendered = render_to_string(
            "powercrud/daisyUI/partial/list.html",
            {
                "table_shell_template_paths": [
                    "sample/author_table_shell.html",
                    "powercrud/daisyUI/partial/table_shell.html",
                ],
            },
        )

    assert "Custom table shell" in rendered, (
        "The legacy list façade should select a downstream table-shell override first."
    )
    assert "<script" not in rendered, (
        "A focused table-shell override should not need copied PowerCRUD JavaScript."
    )


def test_filtered_results_empty_state_omits_create_prompt_without_create_url():
    """Empty-state copy should stay neutral when create is unavailable."""
    request = RequestFactory().get("/")

    rendered = render_to_string(
        "powercrud/daisyUI/object_list.html#filtered_results",
        {
            "request": request,
            "object_list": [],
            "object_verbose_name_plural": "blocking issues",
            "show_record_count": False,
            "show_bulk_selection_meta": False,
            "create_view_url": None,
        },
        request=request,
    )

    assert (
        "There are no blocking issues." in rendered
    ), "Empty-state copy should still explain that no records are available."
    assert (
        "Create one now?" not in rendered
    ), "Empty-state copy should not suggest creating a record when no create URL exists."


def test_filtered_results_empty_state_keeps_create_prompt_with_create_url():
    """Empty-state copy should preserve the create prompt when create is available."""
    request = RequestFactory().get("/")

    rendered = render_to_string(
        "powercrud/daisyUI/object_list.html#filtered_results",
        {
            "request": request,
            "object_list": [],
            "object_verbose_name_plural": "blocking issues",
            "show_record_count": False,
            "show_bulk_selection_meta": False,
            "create_view_url": "/issues/create/",
        },
        request=request,
    )

    assert (
        "There are no blocking issues. Create one now?" in rendered
    ), "Empty-state copy should keep the create prompt when a create URL is available."
