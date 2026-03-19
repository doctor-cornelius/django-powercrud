from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from django import forms
from django.http import HttpResponse
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

from neapolitan.views import Role

from powercrud.mixins.core_mixin import CoreMixin
from powercrud.mixins.form_mixin import FormMixin
from powercrud.mixins.bulk_mixin.view_mixin import ViewMixin
from powercrud.mixins.htmx_mixin import HtmxMixin
from sample.models import Author, Book, Genre


class BaseContext:
    def get_context_data(self, **kwargs):
        kwargs.setdefault("request", self.request)
        return kwargs


class DummyFormView(HtmxMixin, ViewMixin, FormMixin, BaseContext):
    model = Book
    form_fields = ["title", "author", "published_date"]
    dropdown_sort_options = {"author": "name"}
    use_crispy = None
    use_htmx = True
    bulk_fields = ["author"]
    bulk_delete = True
    role = Role.UPDATE
    templates_path = "powercrud/daisyUI"
    form_class = None
    base_template_path = "powercrud/base.html"
    namespace = "sample"
    url_base = "book"
    template_name_suffix = "_form"
    modal_id = None
    modal_target = None

    def __init__(self, request):
        self.request = request
        self._object = None
        self.kwargs = {}

    def get_object(self):
        return self._object

    def get_conflict_checking_enabled(self):
        return True

    def _check_for_conflicts(self, selected_ids):
        return True

    def list(self, request, *args, **kwargs):
        return HttpResponse("list")

    def get_original_target(self):
        return "#content"

    def get_modal_target(self):
        return "#modal"

    def get_selected_ids_from_session(self, request):
        return request.session.get("selected", [])

    def save_selected_ids_to_session(self, request, ids):
        request.session["selected"] = list(ids)

    def clear_selection_from_session(self, request):
        request.session["selected"] = []

    def get_bulk_selection_key_suffix(self):
        return "test"


class MinimalBookForm(forms.ModelForm):
    """Minimal custom form used to prove form_class precedence over form_fields."""

    class Meta:
        model = Book
        fields = ["title", "isbn"]


class CustomFormPriorityView(FormMixin, CoreMixin):
    """Configured view that intentionally conflicts form_class and form_fields."""

    model = Book
    fields = "__all__"
    use_crispy = False
    form_class = MinimalBookForm
    form_fields = ["author", "published_date"]
    form_fields_exclude = ["published_date"]


def attach_session(request):
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.mark.django_db
def test_get_form_class_uses_crispy(settings):
    if "crispy_forms" not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS = tuple(settings.INSTALLED_APPS) + ("crispy_forms",)

    author = Author.objects.create(name="Ada")
    request = attach_session(RequestFactory().get("/"))
    view = DummyFormView(request)
    view.use_crispy = True
    view._object = Book.objects.create(
        title="Book",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="1234567890123",
        pages=10,
    )

    form_class = view.get_form_class()
    form = form_class()
    assert hasattr(form, "helper")
    assert form.helper.form_tag is False
    assert form.base_fields["published_date"].widget.input_type == "date"


@pytest.mark.django_db
def test_get_form_class_without_crispy(settings):
    settings.INSTALLED_APPS = tuple(
        app for app in settings.INSTALLED_APPS if app != "crispy_forms"
    )
    request = attach_session(RequestFactory().get("/"))
    view = DummyFormView(request)
    view.use_crispy = True
    form_class = view.get_form_class()
    form = form_class()
    assert not hasattr(form, "helper")


@pytest.mark.django_db
def test_form_class_clears_resolved_form_fields_when_present():
    """Resolved form_fields should be ignored when a custom form_class is configured."""
    view = CustomFormPriorityView()

    assert view.form_fields == [], (
        "Config resolution should clear form_fields when form_class is configured so custom forms remain the sole source of editable fields."
    )


@pytest.mark.django_db
def test_get_form_class_prefers_custom_form_over_form_fields():
    """A configured form_class should define the actual editable form surface."""
    view = CustomFormPriorityView()

    form_class = view.get_form_class()

    assert list(form_class.base_fields.keys()) == ["title", "isbn"], (
        "get_form_class should use the explicit custom form fields instead of any configured form_fields when form_class is present."
    )


@pytest.mark.django_db
def test_finalize_form_disables_configured_fields():
    """Configured form_disabled_fields should disable the built form fields."""
    request = attach_session(RequestFactory().get("/"))
    view = DummyFormView(request)
    view.form_disabled_fields = ["published_date"]

    form = view._finalize_form(view.get_form_class()())

    assert form.fields["published_date"].disabled is True, (
        "Configured form_disabled_fields should set Django field.disabled=True on matching form fields."
    )


@pytest.mark.django_db
def test_disabled_form_field_preserves_instance_value_on_submit():
    """Disabled form fields should ignore submitted tampering and keep instance values."""
    author = Author.objects.create(name="Ada")
    book = Book.objects.create(
        title="Original Title",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="1234500000001",
        pages=10,
    )
    request = attach_session(RequestFactory().post("/"))
    view = DummyFormView(request)
    view.form_disabled_fields = ["title"]

    form = view._finalize_form(
        view.get_form_class()(
            instance=book,
            data={
                "title": "Tampered Title",
                "author": author.pk,
                "published_date": "2024-02-02",
            },
        )
    )

    assert form.is_valid(), (
        "A form with disabled fields should still validate when the remaining required fields are supplied."
    )

    saved_book = form.save()

    assert saved_book.title == "Original Title", (
        "Disabled form fields should preserve the persisted instance value instead of accepting submitted tampering."
    )
    assert str(saved_book.published_date) == "2024-02-02", (
        "Non-disabled form fields should continue to save updated values normally alongside disabled fields."
    )


@pytest.mark.django_db
def test_get_form_display_items_formats_configured_model_fields():
    """Display-only form context should format configured model fields for update forms."""
    author = Author.objects.create(name="Display Author")
    book = Book.objects.create(
        title="Display Book",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="1234500000002",
        pages=10,
    )
    request = attach_session(RequestFactory().get("/"))
    view = DummyFormView(request)
    view.form_display_fields = [
        "uneditable_field",
        "author",
        "published_date",
        "bestseller",
    ]

    items = view.get_form_display_items(instance=book)

    assert items == [
        {
            "name": "uneditable_field",
            "label": "Uneditable Field",
            "value": "This field is uneditable",
        },
        {
            "name": "author",
            "label": "Author",
            "value": "Display Author",
        },
        {
            "name": "published_date",
            "label": "Published Date",
            "value": "01/01/2024",
        },
        {
            "name": "bestseller",
            "label": "Bestseller",
            "value": "No",
        },
    ], (
        "Configured form_display_fields should resolve to plain label/value metadata with sensible formatting for update forms."
    )


@pytest.mark.django_db
def test_get_form_display_items_returns_empty_for_create_forms():
    """Display-only form context should stay empty until there is a persisted object."""
    request = attach_session(RequestFactory().get("/"))
    view = DummyFormView(request)
    view.form_display_fields = ["uneditable_field"]

    assert view.get_form_display_items() == [], (
        "Create forms should not render display-only context because there is no persisted object yet."
    )


@pytest.mark.django_db
def test_show_form_conflict_returns_render(monkeypatch):
    author = Author.objects.create(name="Ada")
    book = Book.objects.create(
        title="Conflict",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="3213213210000",
        pages=5,
    )
    request = attach_session(RequestFactory().get("/"))
    request.htmx = SimpleNamespace()
    view = DummyFormView(request)
    view._object = book
    view.object = book

    captured = {}

    def fake_render(request, template_name, context):
        captured["template"] = template_name
        captured["context"] = context
        return HttpResponse("conflict")

    monkeypatch.setattr("powercrud.mixins.form_mixin.render", fake_render)

    def fake_render_response(self, context):
        return fake_render(self.request, "template", context)

    monkeypatch.setattr(DummyFormView, "render_to_response", fake_render_response)
    response = view.show_form(request)
    assert response.content == b"conflict"
    assert captured["context"]["conflict_detected"] is True


@pytest.mark.django_db
def test_form_valid_htmx_returns_list(monkeypatch):
    author = Author.objects.create(name="Ada")
    book = Book.objects.create(
        title="Async",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="5555555550000",
        pages=50,
    )
    request = attach_session(RequestFactory().post("/"))
    request.htmx = SimpleNamespace()
    view = DummyFormView(request)
    view._object = book
    view.object = book
    view.role = Role.UPDATE

    monkeypatch.setattr(
        "powercrud.mixins.form_mixin.reverse", lambda name, kwargs=None: f"/{name}"
    )

    form = view.get_form_class()(
        instance=book,
        data={"title": "Async", "author": author.pk, "published_date": "2024-01-01"},
    )
    assert form.is_valid()

    monkeypatch.setattr(view, "_check_for_conflicts", lambda selected_ids: False)
    response = view.form_valid(form)
    assert isinstance(response, HttpResponse)
    assert json.loads(response["HX-Trigger"]) == {"formSuccess": True}
    assert response["HX-Retarget"] == view.get_original_target()


@pytest.mark.django_db
def test_form_invalid_htmx_keeps_modal(monkeypatch):
    author = Author.objects.create(name="Ada")
    book = Book.objects.create(
        title="Invalid",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="4545454545000",
        pages=12,
    )
    request = attach_session(RequestFactory().post("/"))
    request.htmx = True
    view = DummyFormView(request)
    view._object = book
    view.object = book
    view.role = Role.UPDATE
    view.use_modal = True

    monkeypatch.setattr(
        "powercrud.mixins.form_mixin.render",
        lambda request, template_name, context: HttpResponse("invalid", headers={}),
    )
    monkeypatch.setattr(
        "powercrud.mixins.form_mixin.reverse", lambda name, kwargs=None: f"/{name}"
    )

    form = view.get_form_class()(instance=book, data={})
    assert not form.is_valid()

    response = view.form_invalid(form)
    assert "formError" in json.loads(response["HX-Trigger"])
    assert response["HX-Retarget"] == view.get_modal_target()


@pytest.mark.django_db
def test_searchable_select_marker_added_to_foreign_key_field():
    request = attach_session(RequestFactory().get("/"))
    view = DummyFormView(request)
    form = view.get_form_class()()
    view._apply_searchable_select_attrs(form)

    assert (
        form.fields["author"].widget.attrs.get("data-powercrud-searchable-select")
        == "true"
    ), "Author select should be marked for searchable-select enhancement by default."
    assert (
        "data-powercrud-searchable-select"
        not in form.fields["title"].widget.attrs
    ), "Non-select text fields should never be marked for searchable-select enhancement."


@pytest.mark.django_db
def test_searchable_select_marker_respects_global_toggle():
    request = attach_session(RequestFactory().get("/"))
    view = DummyFormView(request)
    view.searchable_selects = False
    form = view.get_form_class()()
    view._apply_searchable_select_attrs(form)

    assert (
        "data-powercrud-searchable-select"
        not in form.fields["author"].widget.attrs
    ), "Global searchable_selects=False should suppress select enhancement markers."


@pytest.mark.django_db
def test_searchable_select_marker_respects_field_hook():
    class OptOutDummyView(DummyFormView):
        def get_searchable_select_enabled_for_field(
            self, field_name: str, bound_field=None
        ) -> bool:
            return field_name != "author"

    request = attach_session(RequestFactory().get("/"))
    view = OptOutDummyView(request)
    form = view.get_form_class()()
    view._apply_searchable_select_attrs(form)

    assert (
        "data-powercrud-searchable-select"
        not in form.fields["author"].widget.attrs
    ), "Per-field searchable-select hook should be able to opt out individual fields."


class DependencyFormView(DummyFormView):
    form_fields = [
        "title",
        "author",
        "genres",
        "published_date",
        "isbn",
        "pages",
        "bestseller",
    ]
    field_queryset_dependencies = {
        "genres": {
            "depends_on": ["author"],
            "filter_by": {"authors": "author"},
            "order_by": "name",
            "empty_behavior": "none",
        }
    }


class StaticFilterFormView(DummyFormView):
    form_fields = ["title", "author", "published_date"]
    field_queryset_dependencies = {
        "author": {
            "static_filters": {"name__startswith": "A"},
            "order_by": "name",
        }
    }


class StaticAndDynamicDependencyFormView(DummyFormView):
    form_fields = [
        "title",
        "author",
        "genres",
        "published_date",
        "isbn",
        "pages",
        "bestseller",
    ]
    field_queryset_dependencies = {
        "genres": {
            "static_filters": {"name__startswith": "A"},
            "depends_on": ["author"],
            "filter_by": {"authors": "author"},
            "order_by": "name",
            "empty_behavior": "all",
        }
    }


class CustomDependencyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["genres"].required = False

    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "genres",
            "published_date",
            "isbn",
            "pages",
            "bestseller",
        ]


class CustomDependencyFormView(DependencyFormView):
    form_class = CustomDependencyForm


@pytest.mark.django_db
def test_field_queryset_dependencies_scope_form_from_bound_parent_value():
    author_a = Author.objects.create(name="Author A")
    author_b = Author.objects.create(name="Author B")
    genre_z = Genre.objects.create(name="Zebra Genre")
    genre_a = Genre.objects.create(name="Alpha Genre")
    author_a.genres.add(genre_z)
    author_b.genres.add(genre_a)
    book = Book.objects.create(
        title="Scoped Book",
        author=author_a,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9780000001234",
        pages=25,
    )

    request = attach_session(RequestFactory().post("/"))
    view = DependencyFormView(request)
    view._object = book
    form = view._finalize_form(
        view.get_form_class()(
            instance=book,
            data={
                "title": "Scoped Book",
                "author": str(author_b.pk),
                "published_date": "2024-01-01",
                "isbn": "9780000001234",
                "pages": "25",
                "bestseller": "",
            },
        )
    )

    genre_names = list(form.fields["genres"].queryset.values_list("name", flat=True))
    assert genre_names == [
        "Alpha Genre"
    ], "Bound parent values should scope dependent child querysets to the selected parent and apply ordering."


@pytest.mark.django_db
def test_field_queryset_dependencies_scope_form_from_instance_when_unbound():
    author_a = Author.objects.create(name="Author A")
    author_b = Author.objects.create(name="Author B")
    genre_a = Genre.objects.create(name="Genre A")
    genre_b = Genre.objects.create(name="Genre B")
    author_a.genres.add(genre_a)
    author_b.genres.add(genre_b)
    book = Book.objects.create(
        title="Instance Scoped Book",
        author=author_a,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9780000001235",
        pages=26,
    )

    request = attach_session(RequestFactory().get("/"))
    view = DependencyFormView(request)
    view._object = book
    form = view._finalize_form(view.get_form_class()(instance=book))

    genre_ids = list(form.fields["genres"].queryset.values_list("id", flat=True))
    assert genre_ids == [
        genre_a.pk
    ], "Unbound forms should fall back to the instance parent value when scoping dependent querysets."


@pytest.mark.django_db
def test_field_queryset_dependencies_empty_behavior_none_returns_no_choices_without_parent():
    genre = Genre.objects.create(name="Unscoped Genre")
    request = attach_session(RequestFactory().get("/"))
    view = DependencyFormView(request)
    form = view._finalize_form(view.get_form_class()())

    genre_ids = list(form.fields["genres"].queryset.values_list("id", flat=True))
    assert genre_ids == [], "empty_behavior='none' should hide dependent choices until a parent value is available."
    assert genre.pk not in genre_ids, "Dependent querysets should not leak unrelated choices when no parent value is present."


@pytest.mark.django_db
def test_field_queryset_dependencies_apply_after_custom_form_class_init():
    author_a = Author.objects.create(name="Author A")
    author_b = Author.objects.create(name="Author B")
    genre_a = Genre.objects.create(name="Genre A")
    genre_b = Genre.objects.create(name="Genre B")
    author_a.genres.add(genre_a)
    author_b.genres.add(genre_b)
    book = Book.objects.create(
        title="Custom Form Book",
        author=author_a,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9780000001236",
        pages=27,
    )

    request = attach_session(RequestFactory().post("/"))
    view = CustomDependencyFormView(request)
    view._object = book
    form = view._finalize_form(
        view.get_form_class()(
            instance=book,
            data={
                "title": "Custom Form Book",
                "author": str(author_b.pk),
                "published_date": "2024-01-01",
                "isbn": "9780000001236",
                "pages": "27",
                "bestseller": "",
            },
        )
    )

    genre_ids = list(form.fields["genres"].queryset.values_list("id", flat=True))
    assert genre_ids == [
        genre_b.pk
    ], "Custom form classes should still receive PowerCRUD dependency scoping after form construction."
    assert (
        form.fields["genres"].required is False
    ), "Custom form initialization should still be able to tweak dependent fields before PowerCRUD applies queryset scoping."


@pytest.mark.django_db
def test_field_queryset_dependencies_apply_static_filters_to_regular_forms():
    author_alpha = Author.objects.create(name="Alpha")
    author_beta = Author.objects.create(name="Beta")
    request = attach_session(RequestFactory().get("/"))
    view = StaticFilterFormView(request)

    form = view._finalize_form(view.get_form_class()())
    author_names = list(form.fields["author"].queryset.values_list("name", flat=True))

    assert author_names == [
        "Alpha"
    ], "Static field queryset filters should restrict regular form dropdown choices without requiring dynamic parent fields."
    assert (
        author_beta.name not in author_names
    ), "Static field queryset filters should exclude unrelated dropdown choices from regular forms."


@pytest.mark.django_db
def test_field_queryset_dependencies_apply_static_filters_to_inline_forms():
    author_alpha = Author.objects.create(name="Alpha")
    Author.objects.create(name="Beta")
    book = Book.objects.create(
        title="Inline Static Book",
        author=author_alpha,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9780000002236",
        pages=18,
    )

    request = attach_session(RequestFactory().get("/"))
    view = StaticFilterFormView(request)
    form = view.build_inline_form(instance=book)

    author_names = list(form.fields["author"].queryset.values_list("name", flat=True))
    assert author_names == [
        "Alpha"
    ], "Inline form construction should reuse static field queryset filters from the shared form pipeline."


@pytest.mark.django_db
def test_field_queryset_dependencies_combine_static_and_dynamic_filters():
    author_a = Author.objects.create(name="Author A")
    author_b = Author.objects.create(name="Author B")
    genre_alpha = Genre.objects.create(name="Alpha Genre")
    genre_beta = Genre.objects.create(name="Beta Genre")
    author_a.genres.add(genre_alpha, genre_beta)
    author_b.genres.add(genre_alpha)
    book = Book.objects.create(
        title="Combined Rules Book",
        author=author_a,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9780000003236",
        pages=28,
    )

    request = attach_session(RequestFactory().post("/"))
    view = StaticAndDynamicDependencyFormView(request)
    view._object = book
    form = view._finalize_form(
        view.get_form_class()(
            instance=book,
            data={
                "title": "Combined Rules Book",
                "author": str(author_a.pk),
                "published_date": "2024-01-01",
                "isbn": "9780000003236",
                "pages": "28",
                "bestseller": "",
            },
        )
    )

    genre_names = list(form.fields["genres"].queryset.values_list("name", flat=True))
    assert genre_names == [
        "Alpha Genre"
    ], "Static and dynamic field queryset rules should compose so only records matching both restrictions remain available."
