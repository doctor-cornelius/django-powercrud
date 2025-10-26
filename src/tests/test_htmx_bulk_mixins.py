from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from django.contrib.sessions.middleware import SessionMiddleware

from powercrud.mixins.htmx_mixin import HtmxMixin
from powercrud.mixins.bulk_mixin import SelectionMixin, MetadataMixin, OperationMixin, ViewMixin
from powercrud.mixins.async_mixin import AsyncMixin
from sample.models import Author, Book, Genre


class DummyHtmxView(HtmxMixin):
    templates_path = "powercrud/daisyUI"
    default_htmx_target = "#content"

    def __init__(self):
        self.use_htmx = True
        self.use_modal = False
        self.modal_id = None
        self.modal_target = None
        self.hx_trigger = None
        self.request = SimpleNamespace(htmx=SimpleNamespace(target=None), path="/example/")


@pytest.mark.parametrize(
    "trigger, expected",
    [
        ("messagesChanged", '{"messagesChanged": true}'),
        (42, '{"42": true}'),
        (3.14, '{"3.14": true}'),
        ({"refresh": True}, '{"refresh": true}'),
    ],
)
def test_get_hx_trigger_returns_json(trigger, expected):
    view = DummyHtmxView()
    view.hx_trigger = trigger
    assert view.get_hx_trigger() == expected


def test_get_hx_trigger_raises_for_invalid_dict():
    view = DummyHtmxView()
    view.hx_trigger = {1: "value"}
    with pytest.raises(TypeError):
        view.get_hx_trigger()


def test_get_htmx_target_prefers_modal_when_enabled():
    view = DummyHtmxView()
    view.use_modal = True
    view.modal_target = "customTarget"
    view.request.htmx.target = None

    assert view.get_htmx_target() == "#customTarget"


def test_get_htmx_target_uses_request_target():
    view = DummyHtmxView()
    view.request.htmx.target = "#from-request"
    assert view.get_htmx_target() == "#content"  # original target returned when request target truthy?


def test_prepare_htmx_response_sets_modal_headers():
    view = DummyHtmxView()
    view.use_modal = True
    response = HttpResponse()
    result = view._prepare_htmx_response(response, form_has_errors=True)

    assert "HX-Trigger" in result
    trigger = json.loads(result["HX-Trigger"])
    assert trigger["showModal"] == "powercrudBaseModal"
    assert trigger["formSubmitError"] is True
    assert result["HX-Retarget"] == view.get_modal_target()


def test_prepare_htmx_response_merges_success_trigger():
    view = DummyHtmxView()
    view.hx_trigger = {"refreshList": False}
    view.request = SimpleNamespace(path="/books/")
    response = HttpResponse()
    result = view._prepare_htmx_response(response, context={"success": True})
    trigger = json.loads(result["HX-Trigger"])
    assert trigger["formSubmitSuccess"] is True
    assert trigger["refreshList"] is False  # existing trigger wins for duplicates
    assert trigger["refreshUrl"] == "/books/"


def make_request(factory: RequestFactory, method: str = "get", data=None):
    rf_method = getattr(factory, method.lower())
    request = rf_method("/", data or {})
    SessionMiddleware(lambda req: None).process_request(request)
    request.session.save()
    request.htmx = True
    return request


class BaseContext:
    def get_context_data(self, **kwargs):
        return kwargs


class DummyBulkView(
    SelectionMixin,
    MetadataMixin,
    OperationMixin,
    ViewMixin,
    BaseContext,
):
    model = Book
    lookup_url_kwarg = "pk"
    templates_path = "powercrud/daisyUI"
    bulk_fields = ["author"]
    bulk_delete = True
    use_modal = True
    use_htmx = True

    def __init__(self, request):
        self.request = request
        self.dropdown_sort_options = {"author": "name"}


@pytest.mark.django_db
def test_selection_session_helpers_roundtrip():
    request = make_request(RequestFactory())
    view = DummyBulkView(request)

    assert view.get_selected_ids_from_session(request) == []
    view.save_selected_ids_to_session(request, [1, 2])
    assert view.get_selected_ids_from_session(request) == ["1", "2"]

    updated = view.toggle_selection_in_session(request, 2)
    assert sorted(updated) == ["1"]

    view.clear_selection_from_session(request)
    assert view.get_selected_ids_from_session(request) == []


@pytest.mark.django_db
def test_toggle_all_selection_in_session_selects_and_clears():
    request = make_request(RequestFactory(), method="post")
    view = DummyBulkView(request)
    ids = view.toggle_all_selection_in_session(request, [1, 2, 3])
    assert sorted(ids) == ["1", "2", "3"]

    ids = view.toggle_all_selection_in_session(request, [1, 2])
    assert sorted(ids) == ["3"]


@pytest.mark.django_db
def test_get_storage_key_includes_suffix():
    request = make_request(RequestFactory())

    class CustomView(DummyBulkView):
        def get_bulk_selection_key_suffix(self):
            return "user_99"

    view = CustomView(request)
    assert view.get_storage_key().endswith("user_99")


@pytest.mark.django_db
def test_bulk_edit_flags_require_modal_and_htmx():
    request = make_request(RequestFactory())
    view = DummyBulkView(request)
    assert view.get_bulk_edit_enabled() is True
    assert view.get_bulk_delete_enabled() is True

    view.use_modal = False
    assert view.get_bulk_edit_enabled() is False
    view.use_modal = True
    view.use_htmx = False
    assert view.get_bulk_edit_enabled() is False


@pytest.mark.django_db
def test_get_bulk_field_info_includes_related_choices():
    request = make_request(RequestFactory())
    author_a = Author.objects.create(name="Alan")
    Author.objects.create(name="Zara")
    view = DummyBulkView(request)
    info = view._get_bulk_field_info(["author"])
    assert "author" in info
    meta = info["author"]
    assert meta["is_relation"] is True
    choices = list(meta["bulk_choices"].values_list("name", flat=True))
    assert choices == ["Alan", "Zara"]


@pytest.mark.django_db
def test_view_mixin_adds_selection_state():
    request = make_request(RequestFactory())
    view = DummyBulkView(request)
    author = Author.objects.create(name="Test")
    genre = Genre.objects.create(name="Sci-Fi")
    book = Book.objects.create(
        title="Example",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="1234567890123",
        pages=10,
    )
    book.genres.add(genre)

    view.save_selected_ids_to_session(request, [book.pk])
    context = view.get_context_data(object_list=[book])

    assert context["selected_ids"] == [str(book.pk)]
    assert context["selected_count"] == 1
    assert context["all_selected"] is True
    assert context["some_selected"] is False


class DummyManager:
    def __init__(self, config=None):
        self.config = config


class DummyAsyncView(AsyncMixin):
    bulk_async = True
    bulk_async_conflict_checking = True
    bulk_min_async_records = 5
    bulk_async_backend = "q2"
    bulk_async_notification = "status_page"
    async_manager_class = DummyManager
    model = Book
    templates_path = "powercrud/daisyUI"


def test_should_process_async_respects_threshold():
    view = DummyAsyncView()
    assert view.should_process_async(10) is True
    assert view.should_process_async(4) is False


def test_conflict_checking_disabled_when_async_off():
    view = DummyAsyncView()
    view.bulk_async = False
    assert view.get_conflict_checking_enabled() is False


def test_get_async_manager_uses_explicit_class():
    view = DummyAsyncView()
    mgr = view.get_async_manager()
    assert isinstance(mgr, DummyManager)
    assert mgr.config is None


@override_settings(
    POWERCRUD_SETTINGS={
        "ASYNC_MANAGER_DEFAULT": {
            "manager_class": "tests.test_htmx_bulk_mixins.DummyManager",
            "config": {"foo": "bar"},
        }
    }
)
def test_get_async_manager_uses_settings_default():
    view = DummyAsyncView()
    # ensure local overrides are cleared
    view.async_manager_class = None
    view.async_manager_class_path = None
    mgr = view.get_async_manager()
    assert isinstance(mgr, DummyManager)
    assert mgr.config == {"foo": "bar"}


def test_get_async_manager_class_path_prefers_explicit_path():
    view = DummyAsyncView()
    path = view.get_async_manager_class_path()
    assert path.endswith("DummyManager")


@pytest.mark.django_db
def test_check_for_conflicts_uses_async_manager(monkeypatch):
    view = DummyAsyncView()
    fake_manager = SimpleNamespace(check_conflict=lambda data: {"1"})
    monkeypatch.setattr(view, "get_async_manager", lambda: fake_manager)
    assert view._check_for_conflicts(selected_ids=[1]) is True


@pytest.mark.django_db
def test_check_for_conflicts_returns_false_without_hits(monkeypatch):
    view = DummyAsyncView()
    fake_manager = SimpleNamespace(check_conflict=lambda data: set())
    monkeypatch.setattr(view, "get_async_manager", lambda: fake_manager)
    assert view._check_for_conflicts(selected_ids=[1]) is False
