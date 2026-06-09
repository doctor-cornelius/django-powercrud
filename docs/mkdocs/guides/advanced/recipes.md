# PowerCRUD Recipes

These recipes show how Base Configuration API options compose through class attributes, hooks, lists, and dictionaries.

Start with [PowerCRUD Concepts](../concepts.md) if you want the mental model behind Surface, Field intent, Action, Presentation, Selection, Bulk operation, and Async operation.

For repeated field and action declarations, see [Structured API Recipes](../structured_api/recipes.md).

## Read-Only Review Surface

Use this when a team needs a searchable or filterable review screen, but should not edit records from the list.

Concepts involved:

1. Surface
2. Field intent
3. Presentation
4. Compatibility and defaults

```python
from neapolitan.views import CRUDView
from powercrud.mixins import PowerCRUDMixin


class AuditEventCRUDView(PowerCRUDMixin, CRUDView):
    model = AuditEvent
    base_template_path = "core/base.html"

    view_title = "Audit Events"
    fields = [
        "id",
        "source",
        "event_type",
        "actor",
        "created_at",
        "severity",
    ]
    detail_fields = "__all__"

    filterset_fields = ["source", "event_type", "actor", "severity", "created_at"]
    default_filterset_fields = ["source", "event_type", "severity"]

    form_fields = ["pages"]
    inline_edit_fields = ["pages"]
    bulk_fields = []
    bulk_delete = False
```

Notes:

1. `fields` controls the list columns.
2. `filterset_fields` controls filtering, independently of list visibility.
3. Explicit empty lists make the no-edit intent clear.

## Filtered Operational List

Use this when a list is an active working queue and users need focused default filters without losing access to the wider filter set.

Concepts involved:

1. Surface
2. Field intent
3. Styling

```python
class ProjectQueueCRUDView(PowerCRUDMixin, CRUDView):
    model = Project
    base_template_path = "core/base.html"

    view_title = "Project Queue"
    view_instructions = "Review open projects and update ownership or status."
    fields = ["name", "owner", "status", "due_date", "priority"]
    properties = ["is_overdue"]

    filterset_fields = [
        "owner",
        "status",
        "due_date",
        "priority",
        "customer",
    ]
    default_filterset_fields = ["owner", "status", "priority"]
    column_help_text = {
        "is_overdue": "Calculated from due date and current status.",
    }
    show_record_count = True
    paginate_by = 25
```

Notes:

1. `default_filterset_fields` keeps the first screen compact.
2. Users can still add optional filters from the configured filter allow-list.
3. `properties` are display fields, not editable model fields.

## Annotated Operational Columns

Use this when an operational value is computed by the queryset and should appear in the list order as a sortable/filterable column.

For the queryset declaration details behind this pattern, see [Queryset Annotation Fields](queryset_annotation_fields.md).

Concepts involved:

1. Surface
2. Field intent
3. Filtering

```python
from django.db.models import BooleanField, Case, Value, When


class BookQueueCRUDView(PowerCRUDMixin, CRUDView):
    model = Book
    base_template_path = "core/base.html"

    def get_queryset(self):
        """Expose the public annotation name used by PowerCRUD config."""
        return super().get_queryset().annotate(
            long_book=Case(
                When(pages__gte=400, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    fields = ["title", "author", "pages", "long_book", "published_date"]
    filterset_fields = ["author", "long_book", "pages"]
    default_filterset_fields = ["author", "long_book"]
    column_help_text = {
        "long_book": "Queryset annotation: true when pages is at least 400.",
    }

    form_fields = []
    inline_edit_fields = []
    bulk_fields = []
```

Notes:

1. The name in `fields` and `filterset_fields` must match the public `annotate(...)` keyword.
2. Use `output_field` so PowerCRUD can infer the generated filter type.
3. Annotation fields are read-only; keep them out of form, inline-edit, and bulk-edit config. Editable model fields such as `pages` can still be inline-editable on the same view.
4. Use `properties` instead when the value is Python-only display output and does not need queryset-backed filtering or list ordering.

## Inline Editable Lookup Table

Use this for small reference tables where users should make quick row edits without opening a full form.

Concepts involved:

1. Field intent
2. Action
3. Presentation
4. Styling

```python
class StatusCRUDView(PowerCRUDMixin, CRUDView):
    model = Status
    base_template_path = "core/base.html"

    fields = ["name", "object_type", "sort_order", "is_active"]
    detail_fields = "__all__"
    form_fields = ["name", "object_type", "sort_order", "is_active"]
    inline_edit_fields = ["name", "sort_order", "is_active"]

    use_htmx = True
    use_modal = True
    inline_edit_always_visible = True
    inline_edit_highlight_accent = "#14b8a6"
```

Notes:

1. `inline_edit_fields` is an editability setting.
2. Inline editable fields must be real editable model fields.
3. Keep `form_fields` broad enough that inline saves can preserve required form state.

## Row Action With Disabled Reason

Use this when a row-level operation is available only for some records and users need to know why it is unavailable.

Concepts involved:

1. Action
2. Presentation
3. Field intent

```python
class InvoiceCRUDView(PowerCRUDMixin, CRUDView):
    model = Invoice
    base_template_path = "core/base.html"

    fields = ["number", "customer", "status", "total", "due_date"]
    extra_actions_mode = "dropdown"
    extra_actions = [
        {
            "url_name": "billing:invoice-send-reminder",
            "text": "Send Reminder",
            "button_class": "btn-accent",
            "display_modal": True,
            "needs_pk": True,
            "disabled_state": "get_send_reminder_disabled_state",
        },
    ]

    def get_send_reminder_disabled_state(self, obj, request) -> str | None:
        """Return the tooltip reason when reminder sending is disabled."""
        if obj.status != "overdue":
            return "Reminders can only be sent for overdue invoices."
        return None
```

Notes:

1. Keep the business rule in server-side hooks.
2. `display_modal` controls presentation, not whether the operation is allowed.
3. Use `extra_actions_mode = "dropdown"` when row actions would crowd the table.

## Selection-Aware Header Action

Use this when an operation works on the current selected row set.

Concepts involved:

1. Selection
2. Action
3. Presentation

```python
class CaseCRUDView(PowerCRUDMixin, CRUDView):
    model = Case
    base_template_path = "core/base.html"

    fields = ["id", "title", "status", "assigned_to", "priority"]
    bulk_delete = True
    show_bulk_selection_meta = True
    extra_buttons = [
        {
            "url_name": "cases:bulk-assign",
            "text": "Assign Selection",
            "button_class": "btn-primary",
            "display_modal": True,
            "uses_selection": True,
            "selection_min_count": 1,
            "selection_min_behavior": "disable",
            "selection_min_reason": "Select at least one case first.",
        },
    ]
```

Notes:

1. `uses_selection` means the endpoint operates on the persisted PowerCRUD selection.
2. `selection_min_behavior = "disable"` keeps the button visible but unavailable until enough rows are selected.
3. A selection-aware `extra_buttons` entry can render selector controls without enabling built-in bulk edit/delete.
4. Set `extra_button_selection_controls_disabled = True` if the button uses selected rows, but this list should not show checkboxes just because of that button.
5. This is mainly useful when the selected rows come from somewhere else, or when the page has its own custom way to choose rows. Bulk edit and bulk delete still show checkboxes because they need them.
6. The endpoint should still validate the selection server-side.

## Bulk Edit With Service-Backed Persistence

Use this when PowerCRUD should render the bulk edit UI, but application services own write logic.

Concepts involved:

1. Bulk operation
2. Action
3. Field intent
4. Compatibility and defaults

```python
class TicketCRUDView(PowerCRUDMixin, CRUDView):
    model = Ticket
    base_template_path = "core/base.html"

    fields = ["title", "status", "owner", "priority", "updated_at"]
    form_fields = ["title", "status", "owner", "priority", "description"]
    bulk_fields = ["status", "owner", "priority"]
    bulk_delete = True

    def persist_bulk_update(
        self,
        *,
        queryset,
        fields_to_update,
        field_data,
        progress_callback=None,
        **kwargs,
    ):
        """Persist bulk ticket edits through the application service layer."""
        return TicketUpdateService().persist_bulk_update(
            queryset=queryset,
            fields_to_update=fields_to_update,
            field_data=field_data,
            progress_callback=progress_callback,
            default_persist=lambda **persist_kwargs: super(
                TicketCRUDView,
                self,
            ).persist_bulk_update(**persist_kwargs),
        )
```

Notes:

1. `bulk_fields` controls which model fields appear in the bulk edit form.
2. The service can enforce workflow locks, audit rules, notifications, or domain validation.
3. Passing a `default_persist` fallback lets the service delegate ordinary cases back to PowerCRUD.

## Linked Cell Drill-In

Use this when a visible list cell should navigate to related detail without turning the whole row into a link.

Concepts involved:

1. Field intent
2. Presentation
3. Surface

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = Book
    base_template_path = "core/base.html"

    fields = ["title", "author", "published_date", "isbn"]
    list_cell_link_default_open_in = "modal"
    link_fields = {
        "author": {
            "view_name": "library:author-detail",
            "pk_attr": "author_id",
            "open_in": "modal",
            "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-4xl flex-col",
        },
    }
```

Notes:

1. `link_fields` applies only to rendered list fields or properties.
2. Inline-editable cells are not linked; inline editing wins.
3. Use `get_list_cell_link(...)` when link metadata needs row-specific logic.

## What To Do Next

Use these recipes as starting points, then consult:

1. [Setup & Core CRUD basics](../setup_core_crud.md) for the full first-view walkthrough.
2. [Configuration Options](../../reference/config_options.md) for accepted values and defaults.
3. [Hooks](../../reference/hooks.md) for method signatures and return contracts.
4. [Structured API Recipes](../structured_api/recipes.md) when repeated field or action declarations would be clearer as `PowerField`, `PowerAction`, or `PowerButton`.
