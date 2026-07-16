# Structured API Recipes

These recipes compare the Base Configuration API with the Structured Declaration API for repeated field and action patterns.

Use them when direct class attributes or dictionaries are correct but have started to repeat the same intent across related views.

## Reusable Field Intent

Use this when related CRUD views share most field roles, but one view needs a small local variation.

=== "Base Configuration API"

    ```python
    class ActionCRUDView(PowerCRUDMixin, CRUDView):
        model = Action
        base_template_path = "core/base.html"

        fields = ["status"]
        default_list_fields = ["status"]
        list_cell_tooltip_fields = {"status": "get_status_tooltip"}
        bulk_fields = ["status"]


    class ActionReviewCRUDView(PowerCRUDMixin, CRUDView):
        model = Action
        base_template_path = "core/base.html"

        fields = ["status"]
        default_list_fields = ["status"]
        list_cell_tooltip_fields = {"status": "get_status_tooltip"}
        bulk_fields = []
    ```

=== "Structured Declaration API"

    ```python
    from powercrud.powerfields import PowerField


    ACTION_STATUS = PowerField(
        "status",
        default_list=True,
        tooltip_hook="get_status_tooltip",
        bulk=True,
    )


    class ActionCRUDView(PowerCRUDMixin, CRUDView):
        model = Action
        base_template_path = "core/base.html"

        power_fields = [
            ACTION_STATUS,
        ]


    class ActionReviewCRUDView(PowerCRUDMixin, CRUDView):
        model = Action
        base_template_path = "core/base.html"

        power_fields = [
            ACTION_STATUS.with_options(bulk=False),
        ]
    ```

Use the structured version when the field's roles repeat across views and a local change such as `bulk=False` should be obvious at the declaration site.

## Reusable Row Actions

Use this when row actions share the same modal, disabled-state, or sizing behavior.

=== "Base Configuration API"

    ```python
    extra_actions = [
        {
            "text": "Workflow Action",
            "url_name": "cases:workflow-action",
            "needs_pk": True,
            "display_modal": True,
            "modal_presentation": {"size": "extra_wide"},
            "disabled_state": "get_workflow_action_disabled_state",
        },
        {
            "text": "Timeline",
            "url_name": "cases:timeline",
            "needs_pk": True,
            "display_modal": True,
            "modal_presentation": {"size": "extra_wide"},
        },
    ]
    ```

=== "Structured Declaration API"

    ```python
    from powercrud.actions import PowerAction


    ROW_MODAL = PowerAction(
        text="Workflow Action",
        url_name="cases:workflow-action",
        display_modal=True,
        modal_presentation={"size": "extra_wide"},
        disabled_state="get_workflow_action_disabled_state",
    )

    extra_actions = [
        ROW_MODAL,
        ROW_MODAL.with_options(
            text="Timeline",
            url_name="cases:timeline",
            disabled_state=None,
        ),
    ]
    ```

Use the structured version when action mechanics repeat and only text, endpoint, modal size, or disabled logic changes.

## Selection-Aware Toolbar Buttons

Use this when toolbar buttons share the same selection rules.

=== "Base Configuration API"

    ```python
    extra_buttons = [
        {
            "text": "Selected Summary (Do Not Clear)",
            "url_name": "sample:book-selected-summary",
            "needs_pk": False,
            "display_modal": True,
            "uses_selection": True,
            "clear_selection_on_success": False,
            "selection_min_count": 1,
            "selection_min_behavior": "disable",
            "selection_min_reason": "Select at least one row first.",
        },
        {
            "text": "Selected Export",
            "url_name": "sample:book-selected-export",
            "needs_pk": False,
            "display_modal": True,
            "uses_selection": True,
            "selection_min_count": 1,
            "selection_min_behavior": "disable",
            "selection_min_reason": "Select at least one row to export.",
        },
    ]
    ```

=== "Structured Declaration API"

    ```python
    from powercrud.actions import PowerButton


    SELECTED_MODAL = PowerButton(
        text="Selected Summary",
        url_name="sample:book-selected-summary",
        display_modal=True,
        uses_selection=True,
        selection_min_count=1,
        selection_min_behavior="disable",
        selection_min_reason="Select at least one row first.",
    )

    extra_buttons = [
        SELECTED_MODAL,
        SELECTED_MODAL.with_options(
            text="Selected Summary (Do Not Clear)",
            clear_selection_on_success=False,
        ),
        SELECTED_MODAL.with_options(
            text="Selected Export",
            url_name="sample:book-selected-export",
            selection_min_reason="Select at least one row to export.",
        ),
    ]
    ```

Use the structured version when the selection contract repeats and the local difference should be limited to the label, URL, or reason text.

`uses_selection=True` can render row selection controls without enabling the built-in bulk edit/delete UI.

Set `extra_button_selection_controls_disabled = True` on the view if the button uses selected rows, but this list should not show checkboxes just because of that button.

This is mainly useful when the selected rows come from somewhere else, or when the page has its own custom way to choose rows. Bulk edit and bulk delete still show checkboxes because they need them.

## What To Do Next

- Use [PowerField](powerfields.md) for the full Field Intent guide.
- Use [PowerAction and PowerButton](poweractions.md) for reusable action and button declarations.
- Use [Configuration Options](../../reference/config_options.md) when you need the exact Base Configuration API contract.
