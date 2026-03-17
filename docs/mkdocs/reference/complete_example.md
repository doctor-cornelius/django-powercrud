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

    # ------------------------------------------------------------------
    # HTMX / modal behaviour
    # ------------------------------------------------------------------
    use_htmx = True
    use_modal = True
    default_htmx_target = "#content"
    modal_id = "projectModal"
    modal_target = "projectModalContent"
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
    form_fields = "__fields__"
    form_fields_exclude = ["internal_notes"]

    # ------------------------------------------------------------------
    # Filtering / dropdown behaviour
    # ------------------------------------------------------------------
    filterset_fields = ["owner", "project_manager", "status", "due_date", "tags"]
    filter_null_fields_exclude = ["due_date"]
    dropdown_sort_options = {
        "owner": "name",
        "project_manager": "name",
        "status": "label",
    }
    m2m_filter_and_logic = True
    searchable_selects = True

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
        },
    ]
```

## Notes

- `base_template_path` is required. PowerCRUD does not ship a bundled site shell.
- `show_record_count` and `show_bulk_selection_meta` are separate toggles. You can show record counts without bulk-selection prompts, or vice versa.
- `extra_actions_mode = "dropdown"` is optional. When omitted, `extra_actions` keep the legacy visible-button behavior. Dropdown mode keeps `View/Edit/Delete` visible and moves only the extra row actions into the `More` menu.
- `inline_edit_fields` is the current inline-editing configuration. Older `inline_edit_enabled` usage is legacy and should not be used in new code.
- `field_queryset_dependencies` is the current declarative way to scope child select querysets in regular forms and inline editing, and to apply static queryset restrictions reused by bulk edit dropdowns.
- `static_filters` is the static-rule companion to the dynamic `depends_on` / `filter_by` shape. In the example above, `project_manager` is always limited to active rows, while `tags` still depend on the selected `owner`.
- `bulk_fields` and `bulk_delete` enable the synchronous bulk-edit UI. The queryset-wide bulk-selection metadata action also depends on the global `POWERCRUD_SETTINGS["BULK_MAX_SELECTED_RECORDS"]` cap.
- `searchable_selects = True` enables Tom Select enhancement for eligible select widgets in forms, inline editing, bulk edit forms, and filter forms.

For focused explanations of individual options, use the dedicated guides and the main [Configuration Options](config_options.md) reference.
