# PowerAction and PowerButton

`PowerAction` and `PowerButton` are Structured Declaration API objects for reusable `extra_actions` and `extra_buttons` declarations.

They do not replace the Base API dictionary shape. Use them when related views repeat the same action mechanics and only change text, URL names, modal size, selection rules, or disabled logic.

```python
from powercrud.actions import PowerAction, PowerButton
```

## When To Use PowerActions And PowerButtons

Use Base API dictionaries for one-off buttons and actions.

Use `PowerAction` or `PowerButton` when you want to name and reuse a pattern:

??? example "Base API and Structured API"

    === "Base API"

        ```python
        extra_actions = [
            {
                "text": "Workflow Action",
                "url_name": "cases:workflow-action",
                "needs_pk": True,
                "display_modal": True,
                "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-5xl flex-col",
                "hidden_if": "should_hide_workflow_action",
                "disabled_state": "get_workflow_action_disabled_state",
            },
            {
                "text": "Timeline",
                "url_name": "cases:timeline",
                "needs_pk": True,
                "display_modal": True,
                "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-5xl flex-col",
            },
        ]
        ```

    === "PowerAction"

        ```python
        ROW_MODAL = PowerAction(
            text="Workflow Action",
            url_name="cases:workflow-action",
            display_modal=True,
            modal_box_classes="modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-5xl flex-col",
            hidden_if="should_hide_workflow_action",
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

That keeps the repeated mechanics in one declaration and leaves each view focused on the user operation.

Any constructor option can be changed in a derived declaration by passing it to `with_options(...)`.

## PowerActions

Use `PowerAction` for row-level `extra_actions`.

`PowerAction` also supports `disabled_state` for row actions that should stay visible but unavailable with a reason.

It also supports permission affordance fields. Use those for user capability, and keep `hidden_if` / `disabled_state` for row or workflow state.

```python
ROW_PREVIEW = PowerAction(
    text="Description Preview",
    url_name="sample:book-description-preview",
    display_modal=True,
    permission_check="can_preview_description",
    permission_behavior="hide",
    hidden_if="should_hide_description_preview",
    hidden_if_mode="lazy",
    disabled_state="get_description_preview_disabled_state",
    disabled_state_mode="lazy",
)

extra_actions = [
    ROW_PREVIEW,
    ROW_PREVIEW.with_options(
        text="Timeline",
        url_name="sample:book-timeline",
        disabled_state=None,
    ),
]

def should_hide_description_preview(self, obj, request):
    return obj.archived

def get_description_preview_disabled_state(self, obj, request):
    if not obj.description:
        return "This book does not have a description yet."
    return None

def can_preview_description(self, request, obj=None):
    return request.user.has_perm("sample.preview_book_description")
```

`PowerAction.needs_pk` defaults to `True`, matching the normal row-action case.

## PowerButtons

Use `PowerButton` for list-level `extra_buttons`.

??? example "Base API and Structured API"

    === "Base API"

        ```python
        extra_buttons = [
            {
                "text": "Selected Summary",
                "url_name": "sample:book-selected-summary",
                "needs_pk": False,
                "display_modal": True,
                "uses_selection": True,
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

    === "PowerButton"

        ```python
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
                text="Selected Export",
                url_name="sample:book-selected-export",
                selection_min_reason="Select at least one row to export.",
            ),
        ]
        ```

`PowerButton.needs_pk` defaults to `False`, matching the normal toolbar-button case.

`PowerButton` supports the same permission affordance fields as `PowerAction`.

```python
PowerButton(
    text="Selected Summary",
    url_name="sample:book-selected-summary",
    display_modal=True,
    uses_selection=True,
    selection_min_count=1,
    selection_min_behavior="disable",
    selection_min_reason="Select at least one row first.",
    permission_check="can_use_selected_summary",
    permission_behavior="hide",
)

def can_use_selected_summary(self, request, obj=None):
    return request.user.has_perm("sample.view_selected_summary")
```

`uses_selection=True` can render row selection controls even when the view has no built-in bulk edit/delete configuration.

Set `extra_button_selection_controls_disabled = True` on the view if the button uses selected rows, but this list should not show checkboxes just because of that button.

This is mainly useful when the selected rows come from somewhere else, or when the page has its own custom way to choose rows. Bulk edit and bulk delete still show checkboxes because they need them.

## Mixing Styles

Base dictionaries and structured declarations may be mixed in the same list.

```python
SELECTED_MODAL = PowerButton(
    text="Selected Summary",
    url_name="sample:book-selected-summary",
    display_modal=True,
    uses_selection=True,
    selection_min_count=1,
    selection_min_behavior="disable",
)

extra_buttons = [
    SELECTED_MODAL,
    SELECTED_MODAL.with_options(
        text="Selected Export",
        url_name="sample:book-selected-export",
    ),
    {
        "url_name": "home",
        "text": "Home",
        "button_class": "btn-success",
        "needs_pk": False,
        "display_modal": False,
        "htmx_target": "content",
    },
]
```

PowerCRUD compiles structured declarations to Base API dictionaries before rendering.

This is different from `PowerField`: a view inheritance chain must choose either Base API Field Intent attributes or `power_fields`. `PowerAction` and `PowerButton` are list entries, so they can safely sit beside dictionaries in `extra_actions` and `extra_buttons`.

## PowerAction Disabled State

For row actions, prefer `disabled_state` when one hook can decide both disabled state and reason.

```python
def get_preview_disabled_state(self, obj, request):
    if not obj.description:
        return "Add a description before previewing."
    return None
```

Return a non-empty string to disable the action and show that string as the reason. Return `None`, `False`, or an empty string to keep the action enabled.

Set `hidden_if_mode="lazy"` for a dropdown row action when the row relevance hook is expensive. Set `disabled_state_mode="lazy"` when the exact disabled reason is expensive. Lazy hidden mode requires `hidden_if`, lazy disabled mode requires `disabled_state`, and neither mode is supported for visible button-mode row actions. See [Lazy Evaluation](../advanced/lazy_evaluation.md) for the Base API and Structured API lazy patterns together.

The older `disabled_if` and `disabled_reason` pair still works for compatibility, but it is deprecated and targeted for removal in v1.0. Do not combine those legacy hooks with `disabled_state` on one action.

Use `hidden_if` when the row action is not applicable and should not render. Use `disabled_state` when the action is applicable but unavailable and the user benefits from a reason.

Use `permission_check` or `permission` when the user is not allowed to perform the operation at all. Permission checks run before `hidden_if` and `disabled_state`; the default permission behavior is to hide the action.

## Reference

See [Choosing an API Style](index.md), [Structured API Recipes](recipes.md), [Permission-Aware Affordances](../advanced/permission_aware_affordances.md), and [PowerAction and PowerButton Reference](../../reference/poweractions.md) for constructor parameters, defaults, and validation rules.
