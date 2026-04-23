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
    column_help_text = {
        "title": "Primary title",
        "isbn_empty": "Whether the ISBN field is blank.",
    }
    column_alignments = {}
    list_cell_tooltip_fields = []
    link_fields = {}
    namespace = "sample"
    url_base = "book"
    dropdown_sort_options = {"author": "name"}
    extra_actions_mode = "buttons"
    extra_actions_dropdown_open_upward_bottom_rows = 3

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
                "disabled_if": "is_preview_disabled",
                "disabled_reason": "get_preview_disabled_reason",
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
            {
                "url_name": "sample:book-list",
                "text": "Selected Summary",
                "display_modal": True,
                "uses_selection": True,
                "selection_min_count": 2,
                "selection_min_behavior": "disable",
                "selection_min_reason": "Select at least two rows first.",
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

    def get_extra_actions_mode(self):
        return self.extra_actions_mode

    def get_extra_actions_dropdown_open_upward_bottom_rows(self):
        return self.extra_actions_dropdown_open_upward_bottom_rows

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

    def get_selected_ids_for_extra_button(self, request, button_spec):
        return self.get_selected_ids_from_session(request)

    def is_preview_disabled(self, obj, request):
        return not bool((obj.description or "").strip())

    def get_preview_disabled_reason(self, obj, request):
        if self.is_preview_disabled(obj, request):
            return "Preview requires a description."
        return None

    def get_bulk_selection_key_suffix(self):
        return "user"

    def get_model_session_key(self):
        return "sample.book"

    def can_delete_object(self, obj, request):
        return True

    def can_update_object(self, obj, request):
        return True

    def get_update_disabled_reason(self, obj, request):
        return None

    def get_delete_disabled_reason(self, obj, request):
        return None

    def get_list_cell_tooltip_fields(self):
        return list(self.list_cell_tooltip_fields)

    def get_column_alignments(self):
        return dict(self.column_alignments)

    def get_link_fields(self):
        return dict(self.link_fields)

    def get_list_cell_tooltip(self, obj, field_name, *, is_property, request=None):
        if field_name == "title":
            return f"Previewing {obj.title}"
        if field_name == "isbn_empty":
            return "ISBN is missing" if obj.isbn_empty else "ISBN is present"
        return None

    def get_list_cell_link(self, obj, field_name, value, *, is_property, request=None):
        return None


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
        description="Preview is available",
    )
    request = apply_session(RequestFactory().get("/?page=1"))
    view = TemplateViewStub(request)

    html = powercrud.action_links(view, book)
    assert "Preview" in html, "Default row action rendering should keep extra actions visible as buttons."
    assert "hx-get" in html, "Default row action rendering should preserve HTMX attributes on action links."
    assert "btn-info" in html, "Standard row actions should keep their framework button classes."
    # Modal actions should include query string parameters from the request
    assert "?page=1" in html, "Modal row actions should preserve the current query string."
    assert "data-powercrud-row-actions-trigger" not in html, (
        "Default row actions mode should not render the overflow More trigger."
    )


@pytest.mark.django_db
def test_action_links_can_render_extra_actions_in_dropdown():
    author = Author.objects.create(name="Dana")
    book = Book.objects.create(
        title="Dropdown",
        author=author,
        published_date=date(2024, 2, 1),
        bestseller=False,
        isbn="9876543210666",
        pages=88,
        description="Dropdown preview",
    )
    request = apply_session(RequestFactory().get("/?page=2"))
    view = TemplateViewStub(request)
    view.extra_actions_mode = "dropdown"

    html = powercrud.action_links(view, book)

    assert "More" in html, "Dropdown row action mode should render a More trigger for extra actions."
    assert (
        "data-powercrud-row-actions-trigger='true'" in html
    ), "Dropdown row action mode should render the row-actions trigger hook for the floating overflow menu."
    assert (
        "data-powercrud-row-actions-template='true'" in html
    ), "Dropdown row action mode should render a hidden template for the floating overflow menu content."
    assert "Preview" in html and "Refresh" in html, (
        "Dropdown row action mode should still include each extra action inside the overflow menu."
    )
    assert (
        html.count("join-item") >= 4
    ), "Dropdown row action mode should keep the visible standard actions in the joined button group."
    assert (
        "?page=2" in html
    ), "Dropdown menu actions should continue to preserve modal query-string context."


@pytest.mark.django_db
def test_action_links_ignore_inline_dropdown_direction_metadata():
    author = Author.objects.create(name="Eve")
    book = Book.objects.create(
        title="Dropdown Up",
        author=author,
        published_date=date(2024, 2, 2),
        bestseller=False,
        isbn="9876543210123",
        pages=99,
        description="Dropdown preview",
    )
    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.extra_actions_mode = "dropdown"
    book._extra_actions_dropdown_open_upward = True

    html = powercrud.action_links(view, book)

    assert "dropdown-top" not in html, (
        "Row action rendering should no longer rely on inline daisy dropdown direction classes once the floating menu is used."
    )
    assert "data-powercrud-row-actions-template='true'" in html, (
        "Row action rendering should continue to emit the floating menu template even when legacy upward-dropdown metadata is present."
    )


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

    assert result["headers"][0]["label"] == "Title", (
        "Object-list header metadata should keep the resolved display label for field columns."
    )
    assert result["headers"][0]["help_text"] == "Primary title", (
        "Object-list header metadata should include configured help text for matching field columns."
    )
    assert result["headers"][-1]["help_text"] == "Whether the ISBN field is blank.", (
        "Object-list header metadata should include configured help text for matching property columns."
    )
    row = result["object_list"][0]
    assert row["id"] == str(book.pk)
    assert any("<svg" in fragment for fragment in row["fields"])
    # m2m field rendered as string
    assert genre.name in row["fields"][4]
    assert result["selected_ids"] == ["1"]
    assert result["selected_count"] == 1
    assert result["filter_params"] == "filter=1"


@pytest.mark.django_db
def test_object_list_renders_row_actions_without_inline_dropdown_direction_classes():
    author = Author.objects.create(name="Bottom Rows")
    books = [
        Book.objects.create(
            title=f"Bottom {index}",
            author=author,
            published_date=date(2024, 3, index),
            bestseller=False,
            isbn=f"9876543210{index:03d}",
            pages=10 + index,
            description="Dropdown preview",
        )
        for index in range(1, 5)
    ]
    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.extra_actions_mode = "dropdown"

    context = {
        "request": request,
        "use_htmx": True,
        "original_target": "#content",
        "htmx_target": "#content",
    }
    result = powercrud.object_list(context, books, view)

    assert all(
        "dropdown-top" not in row["actions"] for row in result["object_list"]
    ), (
        "Object-list row actions should no longer encode inline upward/downward dropdown classes now that viewport-aware floating menus handle placement."
    )
    assert all(
        "data-powercrud-row-actions-template='true'" in row["actions"]
        for row in result["object_list"]
    ), (
        "Each dropdown-mode row should render the floating row-actions menu template."
    )


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
        description="Locked preview",
    )
    book._blocked_reason = "locked"
    book._blocked_label = "Row locked"

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.extra_actions[0]["lock_sensitive"] = True

    html = powercrud.action_links(view, book)

    assert html.count("btn-disabled opacity-50 pointer-events-none") >= 3, (
        "Locked rows should disable each lock-sensitive action, including extra actions rendered as buttons."
    )
    assert "data-tippy-content='Row locked'" in html, (
        "Locked row actions should expose the lock label for semantic tooltips."
    )
    assert "data-powercrud-tooltip='semantic'" in html, (
        "Locked row actions should keep the semantic tooltip marker for the lock explanation."
    )
    assert "Preview" in html, "Locked rows should still render the extra action label in button mode for visibility."


@pytest.mark.django_db
def test_action_links_disable_dropdown_items_when_locked():
    author = Author.objects.create(name="Linnea Dropdown")
    book = Book.objects.create(
        title="Locked Dropdown",
        author=author,
        published_date=date(2024, 6, 1),
        bestseller=True,
        isbn="9876543210777",
        pages=52,
        description="Locked dropdown preview",
    )
    book._blocked_reason = "locked"
    book._blocked_label = "Row locked"

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.extra_actions_mode = "dropdown"
    view.extra_actions[0]["lock_sensitive"] = True

    html = powercrud.action_links(view, book)

    assert "data-powercrud-row-actions-template='true'" in html, (
        "Locked rows should still render floating-menu template markup when dropdown mode is enabled."
    )
    assert "Preview" in html, "Locked dropdown rows should still include the extra action label inside the menu."
    assert "btn-disabled opacity-50 pointer-events-none" in html, (
        "Locked dropdown items should retain the disabled styling classes for consistent affordances."
    )


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
        description="Alignment description",
    )
    book.genres.add(genre)

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.fields = ["title", "pages", "bestseller"]
    view.properties = ["isbn_empty"]

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
    assert cell_map["isbn_empty"]["align"] == "center"


@pytest.mark.django_db
def test_object_list_applies_column_alignment_overrides_for_fields_and_properties():
    author = Author.objects.create(name="Ada")
    book = Book.objects.create(
        title="Override Matters",
        author=author,
        published_date=date(2024, 3, 15),
        bestseller=False,
        isbn="9876543210223",
        pages=999,
        description="Alignment description",
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.fields = ["title", "pages"]
    view.properties = ["isbn_empty"]
    view.column_alignments = {
        "title": "center",
        "pages": "right",
        "isbn_empty": "left",
    }

    context = {
        "request": request,
        "use_htmx": True,
        "original_target": "#content",
        "htmx_target": "#content",
    }
    result = powercrud.object_list(context, [book], view)
    row = result["object_list"][0]
    cell_map = {cell["name"]: cell for cell in row["cells"]}

    assert cell_map["title"]["align"] == "center"
    assert cell_map["pages"]["align"] == "right"
    assert cell_map["isbn_empty"]["align"] == "left"


@pytest.mark.django_db
def test_object_list_only_calls_semantic_tooltip_hook_for_configured_rendered_cells():
    author = Author.objects.create(name="Tooltip Author")
    book = Book.objects.create(
        title="Tooltip Book",
        author=author,
        published_date=date(2024, 3, 16),
        bestseller=False,
        isbn="9876543210999",
        pages=120,
        description="Tooltip coverage",
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.fields = ["title", "author"]
    view.properties = ["isbn_empty"]
    view.list_cell_tooltip_fields = ["title", "isbn_empty", "missing_field", "title"]

    seen_calls = []

    def capture_tooltip(obj, field_name, *, is_property, request=None):
        seen_calls.append((field_name, is_property, request is request_obj))
        if field_name == "title":
            return f"Previewing {obj.title}"
        if field_name == "isbn_empty":
            return "ISBN is present"
        return None

    request_obj = request
    view.get_list_cell_tooltip = capture_tooltip

    context = {
        "request": request,
        "use_htmx": True,
        "original_target": "#content",
        "htmx_target": "#content",
    }
    result = powercrud.object_list(context, [book], view)
    cell_map = {cell["name"]: cell for cell in result["object_list"][0]["cells"]}

    assert seen_calls == [
        ("title", False, True),
        ("isbn_empty", True, True),
    ], (
        "Semantic list cell tooltip hooks should only run for configured fields/properties that are actually rendered in the list."
    )
    assert cell_map["title"]["tooltip_text"] == "Previewing Tooltip Book", (
        "Configured field cells should carry the resolved semantic tooltip text."
    )
    assert cell_map["isbn_empty"]["tooltip_text"] == "ISBN is present", (
        "Configured property cells should carry the resolved semantic tooltip text."
    )
    assert cell_map["author"]["tooltip_text"] is None, (
        "Unconfigured rendered cells should not carry semantic tooltip text."
    )


@pytest.mark.django_db
def test_object_list_trims_blank_semantic_tooltip_results_to_none():
    author = Author.objects.create(name="Blank Tooltip Author")
    book = Book.objects.create(
        title="Blank Tooltip Book",
        author=author,
        published_date=date(2024, 3, 17),
        bestseller=False,
        isbn="9876543210888",
        pages=121,
        description="Blank tooltip coverage",
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.fields = ["title"]
    view.properties = []
    view.list_cell_tooltip_fields = ["title"]
    view.get_list_cell_tooltip = lambda obj, field_name, *, is_property, request=None: "   "

    context = {
        "request": request,
        "use_htmx": True,
        "original_target": "#content",
        "htmx_target": "#content",
    }
    result = powercrud.object_list(context, [book], view)

    assert result["object_list"][0]["cells"][0]["tooltip_text"] is None, (
        "Blank semantic tooltip results should collapse to None so templates can keep existing fallback behavior."
    )


@pytest.mark.django_db
def test_object_list_resolves_relation_link_fields_via_related_id_by_default():
    author = Author.objects.create(name="Linked Author")
    book = Book.objects.create(
        title="Linked Book",
        author=author,
        published_date=date(2024, 4, 1),
        bestseller=False,
        isbn="9876543211111",
        pages=120,
        description="Link coverage",
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.link_fields = {"author": "sample:author-detail"}

    context = {
        "request": request,
        "use_htmx": True,
        "original_target": "#content",
        "htmx_target": "#content",
    }
    row = powercrud.object_list(context, [book], view)["object_list"][0]
    cell_map = {cell["name"]: cell for cell in row["cells"]}

    assert cell_map["author"]["link"] == {
        "url": f"/sample:author-detail/{author.pk}",
        "classes": "link link-primary",
        "use_modal": False,
    }, "Relation list links should default to the related object's <field>_id when pk_attr is omitted."


@pytest.mark.django_db
def test_object_list_resolves_non_relation_link_fields_via_row_pk_by_default():
    author = Author.objects.create(name="Default PK Author")
    book = Book.objects.create(
        title="Linked Title",
        author=author,
        published_date=date(2024, 4, 2),
        bestseller=False,
        isbn="9876543211112",
        pages=121,
        description="Link coverage",
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.link_fields = {"title": "sample:book-detail"}

    context = {
        "request": request,
        "use_htmx": True,
        "original_target": "#content",
        "htmx_target": "#content",
    }
    row = powercrud.object_list(context, [book], view)["object_list"][0]
    cell_map = {cell["name"]: cell for cell in row["cells"]}

    assert cell_map["title"]["link"] == {
        "url": f"/sample:book-detail/{book.pk}",
        "classes": "link link-primary",
        "use_modal": False,
    }, "Non-relation declarative list links should default to the current row's primary key."


@pytest.mark.django_db
def test_object_list_allows_explicit_pk_attr_override_for_list_links():
    author = Author.objects.create(name="Explicit PK Author")
    book = Book.objects.create(
        title="Explicit Link Book",
        author=author,
        published_date=date(2024, 4, 3),
        bestseller=False,
        isbn="9876543211113",
        pages=122,
        description="Link coverage",
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.link_fields = {
        "title": {"view_name": "sample:author-detail", "pk_attr": "author_id"}
    }

    context = {
        "request": request,
        "use_htmx": True,
        "original_target": "#content",
        "htmx_target": "#content",
    }
    row = powercrud.object_list(context, [book], view)["object_list"][0]
    cell_map = {cell["name"]: cell for cell in row["cells"]}

    assert cell_map["title"]["link"]["url"] == f"/sample:author-detail/{author.pk}", (
        "Explicit pk_attr overrides should let declarative list links target a different row-related object."
    )
    assert cell_map["title"]["link"]["use_modal"] is False, (
        "Explicit declarative list links should stay plain-navigation links unless use_modal=True is configured."
    )


@pytest.mark.django_db
def test_object_list_hook_link_overrides_declarative_config():
    author = Author.objects.create(name="Hook Author")
    book = Book.objects.create(
        title="Hook Link Book",
        author=author,
        published_date=date(2024, 4, 4),
        bestseller=False,
        isbn="9876543211114",
        pages=123,
        description="Link coverage",
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.link_fields = {"title": "sample:book-detail"}
    view.get_list_cell_link = lambda obj, field_name, value, *, is_property, request=None: (
        {
            "url": f"/hook/{obj.pk}",
            "title": "Hook wins",
            "classes": "custom-link",
        }
        if field_name == "title"
        else None
    )

    context = {
        "request": request,
        "use_htmx": True,
        "original_target": "#content",
        "htmx_target": "#content",
    }
    row = powercrud.object_list(context, [book], view)["object_list"][0]
    cell_map = {cell["name"]: cell for cell in row["cells"]}

    assert cell_map["title"]["link"] == {
        "url": f"/hook/{book.pk}",
        "title": "Hook wins",
        "classes": "custom-link",
        "use_modal": False,
    }, "Hook-provided list-cell link metadata should override declarative link_fields when both are present."


@pytest.mark.django_db
def test_object_list_hook_can_suppress_declarative_links():
    author = Author.objects.create(name="Suppress Author")
    book = Book.objects.create(
        title="Suppressed Link Book",
        author=author,
        published_date=date(2024, 4, 5),
        bestseller=False,
        isbn="9876543211115",
        pages=124,
        description="Link coverage",
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.link_fields = {"title": "sample:book-detail"}
    view.get_list_cell_link = (
        lambda obj, field_name, value, *, is_property, request=None: False
        if field_name == "title"
        else None
    )

    context = {
        "request": request,
        "use_htmx": True,
        "original_target": "#content",
        "htmx_target": "#content",
    }
    row = powercrud.object_list(context, [book], view)["object_list"][0]
    cell_map = {cell["name"]: cell for cell in row["cells"]}

    assert cell_map["title"]["link"] is None, (
        "Returning False from get_list_cell_link should suppress declarative link_fields for that cell."
    )


@pytest.mark.django_db
def test_object_list_skips_links_for_inline_editable_cells():
    author = Author.objects.create(name="Inline Link Author")
    book = Book.objects.create(
        title="Inline Link Book",
        author=author,
        published_date=date(2024, 4, 6),
        bestseller=False,
        isbn="9876543211116",
        pages=125,
        description="Link coverage",
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.link_fields = {"title": "sample:book-detail"}
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
    cell_map = {cell["name"]: cell for cell in row["cells"]}

    assert cell_map["title"]["is_inline_editable"] is True, (
        "The test fixture should confirm the title cell is inline-editable before asserting link suppression."
    )
    assert cell_map["title"]["link"] is None, (
        "Inline-editable cells should skip declarative list linking so click-to-edit behavior remains authoritative."
    )


@pytest.mark.django_db
def test_object_list_resolves_modal_link_metadata_when_requested():
    author = Author.objects.create(name="Modal Link Author")
    book = Book.objects.create(
        title="Modal Link Book",
        author=author,
        published_date=date(2024, 4, 7),
        bestseller=False,
        isbn="9876543211117",
        pages=126,
        description="Link coverage",
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.link_fields = {
        "title": {"view_name": "sample:book-detail", "use_modal": True}
    }

    context = {
        "request": request,
        "use_htmx": True,
        "original_target": "#content",
        "htmx_target": "#content",
    }
    row = powercrud.object_list(context, [book], view)["object_list"][0]
    cell_map = {cell["name"]: cell for cell in row["cells"]}

    assert cell_map["title"]["link"] == {
        "url": f"/sample:book-detail/{book.pk}",
        "classes": "link link-primary",
        "use_modal": True,
        "hx_method": "get",
        "hx_target": "#modal",
        "modal_attrs": 'onclick="modal.showModal()"',
    }, "Declarative list links should reuse the existing modal target and framework modal attrs when use_modal=True is configured."


@pytest.mark.django_db
def test_object_list_modal_links_degrade_to_plain_links_when_modal_stack_disabled():
    author = Author.objects.create(name="Plain Fallback Author")
    book = Book.objects.create(
        title="Plain Fallback Book",
        author=author,
        published_date=date(2024, 4, 8),
        bestseller=False,
        isbn="9876543211118",
        pages=127,
        description="Link coverage",
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request, use_htmx=False, use_modal=False)
    view.link_fields = {
        "title": {"view_name": "sample:book-detail", "use_modal": True}
    }

    context = {
        "request": request,
        "use_htmx": False,
        "original_target": "#content",
        "htmx_target": "#content",
    }
    row = powercrud.object_list(context, [book], view)["object_list"][0]
    cell_map = {cell["name"]: cell for cell in row["cells"]}

    assert cell_map["title"]["link"] == {
        "url": f"/sample:book-detail/{book.pk}",
        "classes": "link link-primary",
        "use_modal": True,
    }, "use_modal=True should fall back to a normal anchor when the view's HTMX/modal stack is disabled."


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
        description="Locked payload preview",
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


@pytest.mark.django_db
def test_object_list_disables_edit_and_inline_when_update_guard_blocks_row():
    author = Author.objects.create(name="Update Guard")
    book = Book.objects.create(
        title="Guarded Edit",
        author=author,
        published_date=date(2024, 7, 5),
        bestseller=False,
        isbn="9876543210344",
        pages=61,
        description="Guarded edit preview",
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.can_update_object = lambda obj, request: False
    view.get_update_disabled_reason = (
        lambda obj, request: "Editing locked by policy."
    )
    view.can_inline_edit = lambda obj, request: True

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

    assert row["inline_allowed"] is False, (
        "Rows blocked by can_update_object should not expose inline editing even when inline editing is otherwise enabled."
    )
    assert row["inline_blocked_reason"] == "forbidden", (
        "Rows blocked by can_update_object should expose the standard forbidden inline state."
    )
    assert row["inline_blocked_label"] == "Editing locked by policy.", (
        "Rows blocked by can_update_object should reuse the configured update-guard reason for inline affordances."
    )
    assert "Editing locked by policy." in row["actions"], (
        "Rows blocked by can_update_object should disable the built-in Edit action with the configured reason."
    )
    assert ">Delete<" in row["actions"], (
        "Rows blocked by can_update_object should leave the built-in Delete action unaffected."
    )


@pytest.mark.django_db
def test_object_list_keeps_edit_enabled_when_only_inline_policy_blocks_row():
    author = Author.objects.create(name="Inline Only Guard")
    book = Book.objects.create(
        title="Inline Only",
        author=author,
        published_date=date(2024, 7, 6),
        bestseller=False,
        isbn="9876543210355",
        pages=62,
        description="Inline-only restriction",
    )

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.can_inline_edit = lambda obj, request: False

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

    assert row["inline_allowed"] is False, (
        "Rows blocked by inline-only policy should still suppress inline editing."
    )
    assert row["inline_blocked_label"] == "Inline editing not permitted for this row.", (
        "Inline-only row blocks should keep the existing inline-specific reason."
    )
    assert "Editing locked by policy." not in row["actions"], (
        "Inline-only policy blocks should not leak update-guard reasons into standard row actions."
    )
    assert '/sample:book-update/' in row["actions"], (
        "Rows blocked only for inline editing should keep the built-in Edit action enabled."
    )


@pytest.mark.django_db
def test_action_links_disable_custom_extra_action_when_rule_matches():
    author = Author.objects.create(name="No Preview")
    book = Book.objects.create(
        title="No Preview Available",
        author=author,
        published_date=date(2024, 8, 1),
        bestseller=False,
        isbn="9876543210444",
        pages=18,
        description="",
    )
    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)

    html = powercrud.action_links(view, book)

    assert "Preview requires a description." in html, (
        "Custom-disabled extra actions should expose the configured disabled reason tooltip."
    )
    assert "btn-disabled opacity-50 pointer-events-none" in html, (
        "Custom-disabled extra actions should reuse the standard disabled action styling."
    )


@pytest.mark.django_db
def test_action_links_leave_builtin_delete_enabled_by_default():
    author = Author.objects.create(name="Delete Default")
    book = Book.objects.create(
        title="Default Delete",
        author=author,
        published_date=date(2024, 8, 2),
        bestseller=False,
        isbn="9876543210555",
        pages=21,
        description="Delete remains enabled",
    )
    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)

    html = powercrud.action_links(view, book)

    assert "Delete" in html, (
        "Built-in Delete should still render when no delete guard hook blocks the row."
    )
    assert "Delete locked by policy." not in html, (
        "Built-in Delete should not expose any guard reason when the default hook allows the action."
    )


@pytest.mark.django_db
def test_action_links_leave_builtin_edit_enabled_by_default():
    author = Author.objects.create(name="Edit Default")
    book = Book.objects.create(
        title="Default Edit",
        author=author,
        published_date=date(2024, 8, 2),
        bestseller=False,
        isbn="9876543210556",
        pages=22,
        description="Edit remains enabled",
    )
    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)

    html = powercrud.action_links(view, book)

    assert "Edit" in html, (
        "Built-in Edit should still render when no update guard hook blocks the row."
    )
    assert "Editing locked by policy." not in html, (
        "Built-in Edit should not expose any guard reason when the default update hook allows the action."
    )


@pytest.mark.django_db
def test_action_links_disable_builtin_edit_when_update_guard_blocks_row():
    author = Author.objects.create(name="Edit Guard")
    book = Book.objects.create(
        title="Edit Guarded",
        author=author,
        published_date=date(2024, 8, 2),
        bestseller=False,
        isbn="9876543210557",
        pages=23,
        description="Edit should be disabled",
    )
    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.can_update_object = lambda obj, request: False
    view.get_update_disabled_reason = (
        lambda obj, request: "Editing locked by policy."
    )

    html = powercrud.action_links(view, book)

    assert "Editing locked by policy." in html, (
        "Built-in Edit should expose the configured update-guard tooltip reason when the row is blocked."
    )
    assert html.count("btn-disabled opacity-50 pointer-events-none") >= 1, (
        "Built-in Edit should reuse the standard disabled styling when an update guard hook blocks the row."
    )


@pytest.mark.django_db
def test_action_links_disable_builtin_delete_when_delete_guard_blocks_row():
    author = Author.objects.create(name="Delete Guard")
    book = Book.objects.create(
        title="Delete Guarded",
        author=author,
        published_date=date(2024, 8, 3),
        bestseller=False,
        isbn="9876543210667",
        pages=24,
        description="Delete should be disabled",
    )
    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.can_delete_object = lambda obj, request: False
    view.get_delete_disabled_reason = (
        lambda obj, request: "Delete locked by policy."
    )

    html = powercrud.action_links(view, book)

    assert "Delete locked by policy." in html, (
        "Built-in Delete should expose the configured delete-guard tooltip reason when the row is blocked."
    )
    assert html.count("btn-disabled opacity-50 pointer-events-none") >= 1, (
        "Built-in Delete should reuse the standard disabled styling when a delete guard hook blocks the row."
    )


@pytest.mark.django_db
def test_action_links_delete_guard_does_not_disable_builtin_edit():
    author = Author.objects.create(name="Delete Only Guard")
    book = Book.objects.create(
        title="Delete Guard Leaves Edit",
        author=author,
        published_date=date(2024, 8, 3),
        bestseller=False,
        isbn="9876543210668",
        pages=25,
        description="Edit should stay enabled",
    )
    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.can_delete_object = lambda obj, request: False
    view.get_delete_disabled_reason = (
        lambda obj, request: "Delete locked by policy."
    )

    html = powercrud.action_links(view, book)

    assert '/sample:book-update/' in html, (
        "Built-in Edit should still render with its normal update URL when only the delete guard hook blocks the row."
    )
    assert 'title="Delete locked by policy.">Edit<' not in html, (
        "Built-in Edit should not inherit the delete guard tooltip reason."
    )


@pytest.mark.django_db
def test_action_links_update_guard_does_not_disable_builtin_delete():
    author = Author.objects.create(name="Edit Lock")
    book = Book.objects.create(
        title="Edit Lock Leaves Delete",
        author=author,
        published_date=date(2024, 8, 4),
        bestseller=False,
        isbn="9876543210777",
        pages=27,
        description="Delete should stay enabled",
    )
    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.can_update_object = lambda obj, request: False
    view.get_update_disabled_reason = (
        lambda obj, request: "Editing locked by policy."
    )

    html = powercrud.action_links(view, book)

    assert 'title="Editing locked by policy.">Delete<' not in html, (
        "Built-in Delete should not inherit the update guard tooltip reason."
    )
    assert ">Delete<" in html, (
        "Built-in Delete should still render when only the update guard hook blocks the row."
    )


@pytest.mark.django_db
def test_action_links_lock_reason_overrides_update_guard_reason():
    author = Author.objects.create(name="Edit Lock Wins")
    book = Book.objects.create(
        title="Edit Lock Wins",
        author=author,
        published_date=date(2024, 8, 5),
        bestseller=False,
        isbn="9876543210888",
        pages=28,
        description="Lock should win",
    )
    book._blocked_reason = "locked"
    book._blocked_label = "Row locked"

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.can_update_object = lambda obj, request: False
    view.get_update_disabled_reason = (
        lambda obj, request: "Editing locked by policy."
    )

    html = powercrud.action_links(view, book)

    assert "Row locked" in html, (
        "Existing row-lock reasons should remain the primary disabled reason when a row is already blocked."
    )
    assert "Editing locked by policy." not in html, (
        "Update guard hooks should not override the established lock reason when both would disable the built-in Edit action."
    )


@pytest.mark.django_db
def test_action_links_lock_reason_overrides_delete_guard_reason():
    author = Author.objects.create(name="Delete Lock")
    book = Book.objects.create(
        title="Delete Lock Wins",
        author=author,
        published_date=date(2024, 8, 4),
        bestseller=False,
        isbn="9876543210778",
        pages=26,
        description="Lock should win",
    )
    book._blocked_reason = "locked"
    book._blocked_label = "Row locked"

    request = apply_session(RequestFactory().get("/"))
    view = TemplateViewStub(request)
    view.can_delete_object = lambda obj, request: False
    view.get_delete_disabled_reason = (
        lambda obj, request: "Delete locked by policy."
    )

    html = powercrud.action_links(view, book)

    assert "Row locked" in html, (
        "Existing row-lock reasons should remain the primary disabled reason when a row is already blocked."
    )
    assert "Delete locked by policy." not in html, (
        "Delete guard hooks should not override the established lock reason when both would disable the built-in Delete action."
    )


def test_extra_buttons_handles_modal_htmx_and_selection_thresholds():
    request = apply_session(RequestFactory().get("/"))
    request.session["selected"] = ["1"]
    view = TemplateViewStub(request)
    html = powercrud.extra_buttons({"request": request}, view)
    assert "Reload" in html
    assert 'hx-target="#filters"' in html
    assert 'onclick="modal.showModal()"' in html
    assert 'data-powercrud-selection-aware="true"' in html
    assert 'data-powercrud-selection-min-count="2"' in html
    assert "Select at least two rows first." in html
    assert "btn-disabled opacity-50 pointer-events-none" in html, (
        "Selection-aware extra buttons should render disabled styling when the persisted selection is below the minimum."
    )


def test_extra_buttons_enable_selection_aware_button_when_minimum_is_met():
    request = apply_session(RequestFactory().get("/"))
    request.session["selected"] = ["1", "2"]
    view = TemplateViewStub(request)

    html = powercrud.extra_buttons({"request": request}, view)

    assert "Selected Summary" in html
    assert 'data-powercrud-selection-aware="true"' in html
    assert "btn-disabled opacity-50 pointer-events-none" not in html, (
        "Selection-aware extra buttons should stay enabled once the persisted selection meets the configured minimum."
    )


def test_get_powercrud_session_data_returns_value():
    request = apply_session(RequestFactory().get("/"))
    request.session["powercrud"] = {"sample.book": {"original_template": "custom.html"}}
    view = TemplateViewStub(request)
    context = {"request": request, "view": view}

    value = powercrud.get_powercrud_session_data(context, "original_template")
    assert value == "custom.html"
