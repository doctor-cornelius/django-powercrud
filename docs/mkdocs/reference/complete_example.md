# Complete Example

This page shows a deliberately feature-rich `PowerCRUDMixin` view so you can see current configuration syntax in one place. It is not intended as a recommended starting point; most projects should begin much smaller and add options only when needed.

```python
from neapolitan.views import CRUDView

from powercrud.mixins import PowerCRUDMixin
from . import models
from .forms import ProjectForm


class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # ------------------------------------------------------------------
    # Core model / URLs
    # ------------------------------------------------------------------
    model = models.Project
    namespace = "projects"
    url_base = "active-project"

    # ------------------------------------------------------------------
    # Templates / base rendering
    # ------------------------------------------------------------------
    base_template_path = "core/base.html"
    templates_path = "projects/powercrud"
    view_title = "Active Client Projects"  # visible list heading only
    view_instructions = "Use the list below to review and update active projects."
    column_help_text = {
        "owner": "Business owner responsible for the project.",
        "display_status": "Calculated status shown for quick triage.",
    }
    column_alignments = {
        "status": "center",
    }
    list_cell_tooltip_fields = ["owner", "is_overdue"]
    link_fields = {
        "owner": "crm:owner-detail",
        "reference_code": {
            "view_name": "projects:project-detail",
            "use_modal": True,
        },
    }

    # ------------------------------------------------------------------
    # HTMX / modal behaviour
    # ------------------------------------------------------------------
    use_htmx = True
    use_modal = True
    default_htmx_target = "#content"
    modal_id = "projectModal"
    modal_target = "projectModalContent"
    modal_box_classes = "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-4xl flex-col"
    bulk_modal_box_classes = "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-6xl flex-col"
    hx_trigger = {
        "projectsChanged": True,
        "refreshSidebar": True,
    }

    # ------------------------------------------------------------------
    # List, detail, and form scopes
    # ------------------------------------------------------------------
    fields = "__all__"
    exclude = ["internal_notes"]
    properties = ["is_overdue", "display_status"]
    properties_exclude = ["display_status"]

    detail_fields = "__fields__"
    detail_exclude = ["internal_notes"]
    detail_properties = "__properties__"
    detail_properties_exclude = []

    form_class = ProjectForm
    form_display_fields = ["reference_code", "created_by"]
    form_disabled_fields = ["status"]

    # ------------------------------------------------------------------
    # Filtering / dropdown behaviour
    # ------------------------------------------------------------------
    filterset_fields = ["owner", "project_manager", "status", "due_date", "tags"]
    default_filterset_fields = ["owner", "status"]
    filter_favourites_enabled = True
    filter_null_fields_exclude = ["due_date"]
    dropdown_sort_options = {
        "owner": "name",
        "project_manager": "name",
        "status": "label",
    }
    m2m_filter_and_logic = True
    searchable_selects = True
    # Auto-generated text filters use icontains; switch to filterset_class
    # if you need per-field lookup expressions such as iexact or startswith.

    field_queryset_dependencies = {
        "tags": {
            "depends_on": ["owner"],
            "filter_by": {"owners": "owner"},
            "order_by": "name",
            "empty_behavior": "none",
        },
        "project_manager": {
            "static_filters": {"is_active": True},
            "order_by": "name",
        }
    }

    # ------------------------------------------------------------------
    # Inline editing
    # ------------------------------------------------------------------
    inline_edit_fields = ["status", "project_manager", "due_date"]
    inline_edit_always_visible = True
    inline_edit_highlight_accent = "#14b8a6"
    inline_edit_requires_perm = "projects.change_project"
    inline_preserve_required_fields = True

    # ------------------------------------------------------------------
    # Bulk editing
    # ------------------------------------------------------------------
    bulk_fields = ["status", "project_manager", "tags"]
    bulk_delete = True
    bulk_full_clean = True

    # ------------------------------------------------------------------
    # Pagination / metadata
    # ------------------------------------------------------------------
    paginate_by = 25
    show_record_count = True
    show_bulk_selection_meta = True

    # ------------------------------------------------------------------
    # Table styling
    # ------------------------------------------------------------------
    table_pixel_height_other_page_elements = 96
    table_max_height = 75
    table_max_col_width = 30
    table_header_min_wrap_width = 18
    table_classes = "table-sm"
    action_button_classes = "btn-sm"
    extra_button_classes = "btn-sm"
    extra_actions_mode = "dropdown"
    extra_actions_dropdown_open_upward_bottom_rows = 3

    # ------------------------------------------------------------------
    # Extra buttons / row actions
    # ------------------------------------------------------------------
    extra_buttons = [
        {
            "url_name": "projects:dashboard",
            "text": "Dashboard",
            "button_class": "btn-info",
            "needs_pk": False,
            "display_modal": False,
            "htmx_target": "content",
        },
        {
            "url_name": "projects:project-report",
            "text": "Summary Report",
            "button_class": "btn-accent",
            "needs_pk": False,
            "display_modal": True,
            "uses_selection": True,
            "selection_min_count": 1,
            "selection_min_behavior": "disable",
            "selection_min_reason": "Select at least one project first.",
            "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-5xl flex-col",
        },
    ]

    extra_actions = [
        {
            "url_name": "projects:project-archive",
            "text": "Archive",
            "needs_pk": True,
            "hx_post": True,
            "button_class": "btn-warning",
            "display_modal": False,
            "htmx_target": "content",
        },
        {
            "url_name": "projects:project-history",
            "text": "History",
            "needs_pk": True,
            "button_class": "btn-secondary",
            "display_modal": True,
            "disabled_if": "is_history_action_disabled",
            "disabled_reason": "get_history_action_disabled_reason",
            "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-5xl flex-col",
        },
    ]

    def is_history_action_disabled(self, obj, request):
        return obj.archived_at is None

    def get_history_action_disabled_reason(self, obj, request):
        if obj.archived_at is None:
            return "History is only available for archived projects."
        return None

    def get_list_cell_tooltip(self, obj, field_name, *, is_property, request=None):
        if field_name == "owner":
            return f"{obj.owner.email} - {obj.owner.team.name}"
        if field_name == "is_overdue":
            return "Past due and needs follow-up" if obj.is_overdue else "On schedule"
        return None

    def get_list_cell_link(self, obj, field_name, value, *, is_property, request=None):
        if field_name == "display_status" and obj.status_report_url:
            return {
                "url": obj.status_report_url,
                "title": "Open external status report",
                "target": "_blank",
                "rel": "noopener noreferrer",
            }
        if field_name == "owner_card":
            return {
                "url": self.safe_reverse("crm:owner-detail", kwargs={"pk": obj.owner_id}),
                "use_modal": True,
            }
        return None
```

## Notes

- `base_template_path` is required. PowerCRUD does not ship a bundled site shell.
- `show_record_count` and `show_bulk_selection_meta` are separate toggles. You can show record counts without bulk-selection prompts, or vice versa.
- `view_title` overrides only the visible list heading. It does not change create-button text, empty-state copy, or the model’s own verbose names.
- `view_instructions` adds plain-text helper copy directly below the visible list heading. The content is escaped and does not accept HTML.
- `column_help_text` adds optional plain-text tooltips to specific header labels. The help trigger is a separate info icon, so sortable headers keep sorting behavior.
- `column_alignments` lets you override list body-cell alignment for specific rendered fields or properties without changing the default heuristic for the rest of the table.
- `list_cell_tooltip_fields` opts selected rendered columns into semantic list-cell tooltips. The shared `get_list_cell_tooltip(...)` hook is only called for configured names that are actually visible in the current list, and returned plain text may include newline characters when the semantic cell tooltip should render on multiple lines.
- `link_fields` is intentionally narrow. Use it for the boring common case of “this visible column should reverse to a named detail page”. Use the dict form when you want the same link to open in PowerCRUD’s normal modal flow via `use_modal=True`.
- `get_list_cell_link(...)` is the escape hatch for conditional or richer link behavior. Returning `None` falls back to `link_fields`; returning `False` suppresses declarative linking for that cell. Hook metadata can also set `use_modal=True`.
- Semantic list-cell tooltips take precedence over the fallback overflow tooltip for the same cell. Unconfigured cells keep the existing overflow behavior.
- Tooltip appearance is styled through CSS variables such as `--pc-tooltip-bg` and `--pc-tooltip-fg`, not Python view parameters. PowerCRUD defaults those to neutral daisyUI tokens, and you can override them in your app CSS when you want project-level theming.
- Inline-editable cells are never linked, so if a field appears in both `inline_edit_fields` and `link_fields`, PowerCRUD logs a warning and silently keeps inline editing authoritative.
- `form_class` is the source of truth for editable inputs in this example. Because a custom form class is configured, the example intentionally does not also set `form_fields`.
- `form_display_fields` renders model fields in a separate read-only `Context` block above update forms. This is useful for `editable=False` fields or other contextual data the user should see while editing.
- `form_disabled_fields` keeps real update-form inputs visible but disabled. PowerCRUD uses Django field disabling rather than widget-only attrs, so posted tampering is ignored and the saved instance value is preserved.
- A good use case for `view_title` is when the page heading needs UX-friendly wording such as `My List of Books` or `Active Client Projects`, while the underlying model metadata should stay reusable elsewhere.
- `extra_actions_mode = "dropdown"` is optional. When omitted, `extra_actions` keep the legacy visible-button behavior. Dropdown mode keeps `View/Edit/Delete` visible and moves only the extra row actions into the `More` menu.
- `extra_actions_dropdown_open_upward_bottom_rows = 3` makes the `More` menu open upward for the last three rendered rows on the current page. Set it to `0` if you want every dropdown to keep opening downward.
- `uses_selection = True` turns a header button into a selection-aware action that reads the persisted PowerCRUD selection at the endpoint.
- `selection_min_behavior = "disable"` lets the frontend grey out a selection-aware header button until enough rows are selected, but the endpoint should still validate the selection server-side.
- `modal_box_classes` on a modal `extra_buttons` item replaces the view-level modal box classes only while that button's modal is open. Keep `flex max-h-[calc(100dvh-2rem)] flex-col` in the string if you want the supplied viewport-bounded behavior plus a custom width.
- `disabled_if` / `disabled_reason` let row `extra_actions` disable themselves per object using named view methods.
- `modal_box_classes` works the same way on modal `extra_actions`, including actions rendered inside the dropdown `More` menu.
- `inline_edit_fields` is the current inline-editing configuration. Older `inline_edit_enabled` usage is legacy and should not be used in new code.
- `inline_edit_always_visible = True` is the current default, so editable cells keep a subtle resting hint unless you disable it.
- `inline_edit_highlight_accent = "#14b8a6"` is the current default accent. PowerCRUD derives the lighter resting tint and stronger hover/focus tint from that single hex value.
- `field_queryset_dependencies` is the current declarative way to scope child select querysets in regular forms and inline editing, and to apply static queryset restrictions reused by bulk edit dropdowns.
- `static_filters` is the static-rule companion to the dynamic `depends_on` / `filter_by` shape. In the example above, `project_manager` is always limited to active rows, while `tags` still depend on the selected `owner`.
- `bulk_fields` and `bulk_delete` enable the synchronous bulk-edit UI. The queryset-wide bulk-selection metadata action also depends on the global `POWERCRUD_SETTINGS["BULK_MAX_SELECTED_RECORDS"]` cap.
- `searchable_selects = True` enables Tom Select enhancement for eligible select widgets in forms, inline editing, bulk edit forms, and filter forms.
- `default_filterset_fields = ["owner", "status"]` keeps the rest of the allowed filters available but hidden behind the built-in `Add filter` control on first render.
- `filter_favourites_enabled = True` turns on the optional saved filter favourites toolbar when the `powercrud.contrib.favourites` app is installed and the shared `powercrud` URLs are mounted. Otherwise, PowerCRUD silently leaves the favourites UI disabled.
- Saved filter favourites are optional. They require adding `powercrud.contrib.favourites` to `INSTALLED_APPS`, running its migrations, mounting `include("powercrud.urls", namespace="powercrud")`, and following the setup described in the advanced guide.

For focused explanations of individual options, use the dedicated guides and the main [Configuration Options](config_options.md) reference:

- [Filtering](../guides/filtering.md)
- [Saved Filter Favourites](../guides/advanced/filter_favourites.md)
