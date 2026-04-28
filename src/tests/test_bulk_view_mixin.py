from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import RequestFactory

from powercrud.mixins.async_mixin import AsyncMixin
from powercrud.mixins.bulk_mixin.metadata_mixin import MetadataMixin
from powercrud.mixins.bulk_mixin.operation_mixin import OperationMixin
from powercrud.mixins.bulk_mixin.selection_mixin import SelectionMixin
from powercrud.mixins.bulk_mixin.view_mixin import ViewMixin
from powercrud.mixins.htmx_mixin import HtmxMixin
from sample.models import Author, Book


class DummyResponse(HttpResponse):
    def __init__(self, template_name, context):
        super().__init__(content=b"")
        self.template_name = template_name
        self.context_data = context


def make_htmx_request(rf: RequestFactory, method: str = "get", data=None):
    handler = getattr(rf, method.lower())
    request = handler("/", data or {})
    SessionMiddleware(lambda req: None).process_request(request)
    request.session.save()
    if method.lower() == "post":
        request._dont_enforce_csrf_checks = True
    request.htmx = SimpleNamespace(target=None)
    return request


class HarnessView(
    HtmxMixin,
    AsyncMixin,
    SelectionMixin,
    MetadataMixin,
    OperationMixin,
    ViewMixin,
):
    model = Book
    lookup_url_kwarg = "pk"
    templates_path = "powercrud/daisyUI"
    bulk_fields = ["author"]
    bulk_delete = True
    use_modal = True
    use_htmx = True
    modal_id = "bulkModal"
    modal_target = "bulkContent"
    default_htmx_target = "#content"
    dropdown_sort_options = {"author": "name"}
    bulk_async = False
    bulk_async_conflict_checking = False

    def __init__(self, request):
        self.request = request


class StaticBulkHarnessView(HarnessView):
    field_queryset_dependencies = {
        "author": {
            "static_filters": {"name__startswith": "A"},
            "order_by": "name",
        }
    }


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def fake_render(monkeypatch):
    def _render(request, template_name, context):
        return DummyResponse(template_name, context)

    monkeypatch.setattr(
        "powercrud.mixins.bulk_mixin.view_mixin.render",
        _render,
    )


def test_bulk_edit_requires_htmx(rf):
    request = rf.get("/")
    request.session = {}
    view = HarnessView(request)

    response = view.bulk_edit(request)
    assert response.status_code == 400


@pytest.mark.django_db
def test_bulk_edit_returns_error_without_ids(rf, fake_render):
    request = make_htmx_request(rf)
    view = HarnessView(request)

    response = view.bulk_edit(request)

    assert response.template_name.endswith("#bulk_edit_error")
    assert response.context_data["error"] == "No items selected for bulk edit."


@pytest.mark.django_db
def test_bulk_edit_detects_conflicts(rf, fake_render):
    author = Author.objects.create(name="Alpha")
    book = Book.objects.create(
        title="Example",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="3333333333333",
        pages=9,
    )

    request = make_htmx_request(rf, data={"selected_ids[]": [book.pk]})
    view = HarnessView(request)
    view.get_conflict_checking_enabled = lambda: True
    view._check_for_conflicts = lambda ids: True

    response = view.bulk_edit(request)

    assert response.template_name.endswith("#bulk_edit_conflict")
    assert response.context_data["conflict_detected"] is True
    assert response.context_data["selected_count"] == 1


@pytest.mark.django_db
def test_bulk_edit_handles_missing_bulk_fields(rf, fake_render):
    author = Author.objects.create(name="Alpha")
    book = Book.objects.create(
        title="Example",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="4444444444444",
        pages=12,
    )

    request = make_htmx_request(rf, data={"selected_ids[]": [book.pk]})
    view = HarnessView(request)
    view.bulk_fields = []
    view.bulk_delete = False

    response = view.bulk_edit(request)
    assert response.context_data["error"] == "No fields configured for bulk editing."


@pytest.mark.django_db
def test_bulk_edit_rejects_submitted_fields_outside_configured_bulk_fields(
    rf, fake_render, monkeypatch
):
    author = Author.objects.create(name="Alpha")
    book = Book.objects.create(
        title="Example",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="4545454545454",
        pages=12,
    )

    request = make_htmx_request(
        rf,
        method="post",
        data={
            "bulk_submit": "1",
            "selected_ids[]": [book.pk],
            "fields_to_update": ["author", "title"],
            "author": str(author.pk),
            "title": "Tampered",
        },
    )
    view = HarnessView(request)
    called = {"update": False}

    def fail_if_called(*args, **kwargs):
        called["update"] = True
        raise AssertionError(
            "_perform_bulk_update should not run when submitted bulk fields are invalid."
        )

    monkeypatch.setattr(view, "_perform_bulk_update", fail_if_called)

    response = view.bulk_edit(request)

    assert response.template_name.endswith("#bulk_edit_error")
    assert (
        response.context_data["error"]
        == "Bulk edit request contained invalid fields: title."
    ), "Bulk edit should reject tampered fields_to_update values before processing the update."
    assert (
        called["update"] is False
    ), "Bulk edit should refuse invalid submitted fields before reaching the update helper."


@pytest.mark.django_db
def test_bulk_edit_rejects_invalid_fields_before_async_queueing(
    rf, fake_render, monkeypatch
):
    author = Author.objects.create(name="Async Author")
    book = Book.objects.create(
        title="Async Example",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="5656565656565",
        pages=15,
    )

    request = make_htmx_request(
        rf,
        method="post",
        data={
            "bulk_submit": "1",
            "selected_ids[]": [book.pk],
            "fields_to_update": ["title"],
            "title": "Tampered Async",
        },
    )
    view = HarnessView(request)
    called = {"queued": False}

    monkeypatch.setattr(view, "should_process_async", lambda count: True)

    def fail_if_called(*args, **kwargs):
        called["queued"] = True
        raise AssertionError(
            "_handle_async_bulk_operation should not run when submitted bulk fields are invalid."
        )

    monkeypatch.setattr(view, "_handle_async_bulk_operation", fail_if_called)

    response = view.bulk_edit(request)

    assert response.template_name.endswith("#bulk_edit_error")
    assert (
        response.context_data["error"]
        == "Bulk edit request contained invalid fields: title."
    ), "Bulk edit should reject invalid submitted fields before deciding whether to queue async work."
    assert (
        called["queued"] is False
    ), "Bulk edit should not queue async work for tampered submitted fields."


@pytest.mark.django_db
def test_bulk_edit_process_post_delete_success(rf):
    author = Author.objects.create(name="Alpha")
    book = Book.objects.create(
        title="DeleteMe",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="5555555555555",
        pages=20,
    )

    request = make_htmx_request(
        rf,
        method="post",
        data={
            "bulk_submit": "1",
            "delete_selected": "1",
            "selected_ids[]": [book.pk],
        },
    )
    view = HarnessView(request)
    view._perform_bulk_delete = lambda queryset: {
        "success": True,
        "success_records": queryset.count(),
        "errors": [],
    }

    response = view.bulk_edit(request)
    assert isinstance(response, HttpResponse)
    assert json.loads(response["HX-Trigger"]) == {
        "bulkEditSuccess": True,
        "refreshTable": True,
    }


@pytest.mark.django_db
def test_bulk_edit_process_post_async(rf, monkeypatch):
    author = Author.objects.create(name="Ada")
    book = Book.objects.create(
        title="Async",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="7777777777777",
        pages=20,
    )

    request = make_htmx_request(
        rf,
        method="post",
        data={
            "bulk_submit": "1",
            "selected_ids[]": [book.pk],
            "fields_to_update": ["author"],
            "author": str(author.pk),
        },
    )
    view = HarnessView(request)

    monkeypatch.setattr(view, "should_process_async", lambda count: True)
    called = {"invoked": False}

    def fake_handle(*args, **kwargs):
        called["invoked"] = True
        return "async"

    monkeypatch.setattr(view, "_handle_async_bulk_operation", fake_handle)

    response = view.bulk_edit(request)
    assert called["invoked"] is True
    assert response == "async"


@pytest.mark.django_db
def test_bulk_edit_process_post_update_error(rf, fake_render):
    author = Author.objects.create(name="Alpha")
    book = Book.objects.create(
        title="Needs Update",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="6666666666666",
        pages=22,
    )

    request = make_htmx_request(
        rf,
        method="post",
        data={
            "bulk_submit": "1",
            "selected_ids[]": [book.pk],
            "fields_to_update": ["author"],
            "author": str(author.pk),
        },
    )
    view = HarnessView(request)
    view.persist_bulk_update = lambda **kwargs: {
        "success": False,
        "errors": [("author", ["bad value"])],
        "success_records": 0,
    }

    response = view.bulk_edit(request)

    assert response.template_name.endswith("bulk_edit_form.html")
    trigger = json.loads(response["HX-Trigger"])
    assert trigger["formError"] is True
    assert response["HX-Retarget"] == view.get_modal_target()


@pytest.mark.django_db
def test_bulk_edit_process_post_uses_persist_bulk_update_hook(rf):
    author = Author.objects.create(name="Hook Author")
    book = Book.objects.create(
        title="Needs Hook",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="6868686868686",
        pages=22,
    )

    request = make_htmx_request(
        rf,
        method="post",
        data={
            "bulk_submit": "1",
            "selected_ids[]": [book.pk],
            "fields_to_update": ["author"],
            "author": str(author.pk),
        },
    )
    view = HarnessView(request)
    captured = {}

    def fake_persist_bulk_update(*, queryset, fields_to_update, field_data, progress_callback=None):
        captured["queryset_ids"] = [obj.pk for obj in queryset]
        captured["fields_to_update"] = fields_to_update
        captured["field_data"] = field_data
        captured["progress_callback"] = progress_callback
        return {"success": True, "success_records": len(captured["queryset_ids"]), "errors": []}

    view.persist_bulk_update = fake_persist_bulk_update

    response = view.bulk_edit(request)

    assert captured["queryset_ids"] == [book.pk], (
        "Sync bulk update should pass the selected queryset through persist_bulk_update."
    )
    assert captured["fields_to_update"] == ["author"], (
        "Sync bulk update should pass the normalized fields_to_update list through persist_bulk_update."
    )
    assert captured["field_data"][0]["field"] == "author", (
        "Sync bulk update should pass the normalized field_data payload through persist_bulk_update."
    )
    assert json.loads(response["HX-Trigger"]) == {
        "bulkEditSuccess": True,
        "refreshTable": True,
    }, (
        "Sync bulk update responses should preserve the existing success trigger after routing through persist_bulk_update."
    )


@pytest.mark.django_db
def test_bulk_field_info_flags_searchable_select_only_for_eligible_fields(rf):
    """Flag only select-like bulk fields for searchable select enhancement."""
    request = make_htmx_request(rf)
    view = HarnessView(request)
    field_info = view._get_bulk_field_info(["author", "bestseller"])

    assert (
        field_info["author"]["searchable_select"] is True
    ), "ForeignKey bulk fields should opt into searchable-select enhancement."
    assert (
        field_info["bestseller"]["searchable_select"] is False
    ), "Boolean bulk fields should remain native selects and not use searchable-select enhancement."


def test_bulk_edit_template_renders_nullable_charfield_choices_without_leaked_tags(rf):
    """Render nullable choice fields as one select without leaking template source."""
    request = rf.get("/bulk-edit/")
    rendered = render_to_string(
        "powercrud/daisyUI/bulk_edit_form.html#full_form",
        {
            "request": request,
            "selected_count": 2,
            "selected_ids": ["1", "2"],
            "bulk_fields": ["uptick_target_pattern"],
            "enable_bulk_delete": False,
            "model_name_plural": "ddm cases",
            "field_info": {
                "uptick_target_pattern": {
                    "type": "CharField",
                    "is_relation": False,
                    "is_m2m": False,
                    "verbose_name": "Uptick Target Pattern",
                    "null": True,
                    "blank": True,
                    "choices": [
                        ("task_and_remarks", "Task & Remarks"),
                        ("remarks_only", "Remarks only"),
                    ],
                    "searchable_select": False,
                }
            },
            "modal_target": "powercrudModalContent",
        },
        request=request,
    )

    assert "{% elif info.type ==" not in rendered, (
        "Bulk edit template tags should be parsed, not emitted into the modal."
    )
    assert 'name="uptick_target_pattern"' in rendered, (
        "Nullable CharField choices should render a select control for the bulk field."
    )
    assert '<option value="null">-- None --</option>' in rendered, (
        "Nullable choice fields should offer an explicit null option."
    )
    assert '<option value="task_and_remarks">Task &amp; Remarks</option>' in rendered, (
        "Bulk edit choice selects should include the model field choices."
    )
    assert 'type="number" name="uptick_target_pattern"' not in rendered, (
        "Choice fields should not fall through into the numeric field branch."
    )


@pytest.mark.django_db
def test_bulk_choices_apply_static_field_queryset_filters(rf):
    request = make_htmx_request(rf)
    view = StaticBulkHarnessView(request)
    author_alpha = Author.objects.create(name="Alpha")
    author_beta = Author.objects.create(name="Beta")
    field = Book._meta.get_field("author")

    qs = view.get_bulk_choices_for_field("author", field)
    author_names = list(qs.values_list("name", flat=True))

    assert author_names == [
        "Alpha"
    ], "Bulk relation choices should apply static field queryset filters from field_queryset_dependencies."
    assert (
        author_beta.name not in author_names
    ), "Bulk relation choices should exclude rows that fail the declared static field queryset filters."


@pytest.mark.django_db
def test_bulk_choices_use_dependency_ordering_when_present(rf):
    request = make_htmx_request(rf)
    view = StaticBulkHarnessView(request)
    Author.objects.create(name="Aardvark")
    Author.objects.create(name="Alpha")
    field = Book._meta.get_field("author")

    qs = view.get_bulk_choices_for_field("author", field)
    author_names = list(qs.values_list("name", flat=True))

    assert author_names == [
        "Aardvark",
        "Alpha",
    ], "Bulk declarative field queryset ordering should be applied after static filtering."


@pytest.mark.django_db
def test_bulk_choices_override_can_bypass_static_field_queryset_filters(rf):
    class OverrideBulkHarnessView(StaticBulkHarnessView):
        def get_bulk_choices_for_field(self, field_name, field):
            return field.related_model.objects.order_by("name")

    request = make_htmx_request(rf)
    view = OverrideBulkHarnessView(request)
    Author.objects.create(name="Alpha")
    Author.objects.create(name="Beta")
    field = Book._meta.get_field("author")

    qs = view.get_bulk_choices_for_field("author", field)
    author_names = list(qs.values_list("name", flat=True))

    assert author_names == [
        "Alpha",
        "Beta",
    ], "Overridden get_bulk_choices_for_field should retain full control over bulk relation choices instead of reapplying declarative static filters."
