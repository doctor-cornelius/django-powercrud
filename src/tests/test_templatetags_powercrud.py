from __future__ import annotations

from datetime import date

import pytest
from django.test import RequestFactory

from powercrud.templatetags import powercrud
from sample.models import Author, Book, Genre


class DummySession(dict):
    modified = False


def apply_session(request):
    request.session = DummySession()
    return request


class TemplateViewStub:
    model = Book
    fields = ["title", "bestseller", "published_date", "author", "genres"]
    properties = ["isbn_empty"]
    namespace = "sample"
    url_base = "book"
    dropdown_sort_options = {"author": "name"}

    def __init__(self, request, *, use_htmx=True, use_modal=True):
        self.request = request
        self.use_htmx = use_htmx
        self.use_modal = use_modal
        self.extra_actions = [
            {
                "url_name": "sample:book-detail",
                "text": "Preview",
                "button_class": "btn-secondary",
                "display_modal": True,
            },
            {
                "url_name": "sample:book-list",
                "text": "Refresh",
                "htmx_target": "list",
                "hx_post": False,
                "needs_pk": False,
            },
        ]
        self.extra_buttons = [
            {
                "url_name": "sample:book-list",
                "text": "Reload",
                "display_modal": False,
                "htmx_target": "filters",
            },
            {
                "url_name": "sample:book-create",
                "text": "New",
                "display_modal": True,
            },
        ]

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
                "modal_attrs": 'onclick="modal.showModal()"',
            }
        }

    def get_action_button_classes(self):
        return "btn-xs"

    def get_extra_button_classes(self):
        return "btn-sm"

    def get_prefix(self):
        return f"{self.namespace}:{self.url_base}"

    def get_use_htmx(self):
        return self.use_htmx

    def get_use_modal(self):
        return self.use_modal

    def get_htmx_target(self):
        return "#content"

    def get_modal_target(self):
        return "#modal"

    def safe_reverse(self, url_name, kwargs=None):
        if url_name.endswith("missing"):
            return None
        if kwargs:
            return f"/{url_name}/{kwargs['pk']}"
        return f"/{url_name}"

    def get_use_crispy(self):
        return False

    def get_original_target(self):
        return "#content"

    def get_bulk_edit_enabled(self):
        return True

    def get_bulk_delete_enabled(self):
        return True

    def get_storage_key(self):
        return "bulk-key"

    def get_table_pixel_height_other_page_elements(self):
        return "0px"

    def get_table_max_height(self):
        return 70

    def get_table_max_col_width(self):
        return "20ch"

    def get_table_header_min_wrap_width(self):
        return "12ch"

    def get_table_classes(self):
        return "table-zebra"

    def get_selected_ids_from_session(self, request):
        return request.session.get("selected", [])

    def get_bulk_selection_key_suffix(self):
        return "user"

    def get_model_session_key(self):
        return "sample.book"


@pytest.mark.django_db
def test_action_links_include_extra_actions():
    author = Author.objects.create(name="Ada")
    book = Book.objects.create(
        title="Example",
        author=author,
        published_date=date(2024, 1, 1),
        bestseller=True,
        isbn="9876543210987",
        pages=123,
    )
    request = apply_session(RequestFactory().get("/?page=1"))
    view = TemplateViewStub(request)

    html = powercrud.action_links(view, book)
    assert "Preview" in html
    assert "hx-get" in html
    assert "btn-info" in html
    # Modal actions should include query string parameters from the request
    assert "?page=1" in html


@pytest.mark.django_db
def test_object_list_renders_booleans_dates_and_selection():
    author = Author.objects.create(name="Grace")
    genre = Genre.objects.create(name="Sci-Fi")
    book = Book.objects.create(
        title="Neon Tensors",
        author=author,
        published_date=date(2023, 5, 1),
        bestseller=False,
        isbn="1234567890000",
        pages=15,
    )
    book.genres.add(genre)
    request = apply_session(RequestFactory().get("/?sort=title&filter=1"))
    request.session["selected"] = ["1"]
    view = TemplateViewStub(request)

    context = {
        "request": request,
        "use_htmx": True,
        "original_target": "#content",
        "htmx_target": "#content",
    }
    result = powercrud.object_list(context, [book], view)

    assert result["headers"][0][0] == "Title"
    row = result["object_list"][0]
    assert row["id"] == str(book.pk)
    assert any("<svg" in fragment for fragment in row["fields"])
    # m2m field rendered as string
    assert genre.name in row["fields"][4]
    assert result["selected_ids"] == ["1"]
    assert result["selected_count"] == 1
    assert result["filter_params"] == "filter=1"


@pytest.mark.django_db
def test_action_links_disable_when_locked():
    author = Author.objects.create(name="Linnea")
    book = Book.objects.create(
        title="Locked",
        author=author,
        published_date=date(2024, 6, 1),
        bestseller=True,
        isbn="9876543210111",
        pages=42,
    )
    book._blocked_reason = "locked"
    book._blocked_label = "Row locked"

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.extra_actions[0]["lock_sensitive"] = True

    html = powercrud.action_links(view, book)

    assert html.count("btn-disabled opacity-50 pointer-events-none") >= 3
    assert "data-tippy-content='Row locked'" in html
    assert "Preview" in html  # sanity check extra action rendered


@pytest.mark.django_db
def test_object_list_sets_alignment_metadata():
    author = Author.objects.create(name="Ada")
    genre = Genre.objects.create(name="Speculative")
    book = Book.objects.create(
        title="Alignment Matters",
        author=author,
        published_date=date(2024, 3, 15),
        bestseller=False,
        isbn="9876543210222",
        pages=999,
    )
    book.genres.add(genre)

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.fields = ["title", "pages", "bestseller"]

    context = {
        "request": request,
        "use_htmx": True,
        "original_target": "#content",
        "htmx_target": "#content",
    }
    result = powercrud.object_list(context, [book], view)
    row = result["object_list"][0]
    cell_map = {cell["name"]: cell for cell in row["cells"]}

    assert cell_map["title"]["align"] == "left"
    assert cell_map["pages"]["align"] == "center"
    assert cell_map["bestseller"]["align"] == "center"


@pytest.mark.django_db
def test_object_list_marks_locked_rows_with_metadata():
    author = Author.objects.create(name="Jules")
    book = Book.objects.create(
        title="Locked Payload",
        author=author,
        published_date=date(2024, 7, 4),
        bestseller=True,
        isbn="9876543210333",
        pages=77,
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.extra_actions[0]["lock_sensitive"] = True
    view.is_inline_row_locked = lambda obj: True
    view.get_inline_lock_details = lambda obj: {
        "label": "Locked by QA",
        "task": "task-007",
    }

    inline_config = {
        "enabled": True,
        "fields": ["title"],
        "dependencies": {},
        "row_endpoint_name": "sample:book-inline-row",
    }
    context = {
        "request": request,
        "use_htmx": True,
        "original_target": "#content",
        "htmx_target": "#content",
        "inline_edit": inline_config,
    }

    row = powercrud.object_list(context, [book], view)["object_list"][0]

    assert row["inline_blocked_reason"] == "locked"
    assert row["inline_blocked_meta"]["label"] == "Locked by QA"
    assert "btn-disabled" in row["actions"]


def test_extra_buttons_handles_modal_and_htmx():
    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    html = powercrud.extra_buttons(view)
    assert "Reload" in html
    assert 'hx-target="#filters"' in html
    assert 'onclick="modal.showModal()"' in html


def test_get_powercrud_session_data_returns_value():
    request = apply_session(RequestFactory().get("/"))
    request.session["powercrud"] = {"sample.book": {"original_template": "custom.html"}}
    view = TemplateViewStub(request)
    context = {"request": request, "view": view}

    value = powercrud.get_powercrud_session_data(context, "original_template")
    assert value == "custom.html"
