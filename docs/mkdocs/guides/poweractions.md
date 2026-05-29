# PowerAction And PowerButton

`PowerAction` and `PowerButton` are small helpers for reusable `extra_actions` and `extra_buttons` declarations.

They do not replace the primitive dictionary API. Use them when related views repeat the same action mechanics and only change text, URL names, modal size, selection rules, or disabled logic.

```python
from powercrud.actions import PowerAction, PowerButton
```

## When To Use Them

Use the primitive dictionaries for one-off buttons and actions.

Use `PowerAction` or `PowerButton` when you want to name and reuse a pattern:

??? example "Primitive API vs PowerAction"

    === "Primitive"

        ```python
        extra_actions = [
            {
                "text": "Workflow Action",
                "url_name": "cases:workflow-action",
                "needs_pk": True,
                "display_modal": True,
                "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-5xl flex-col",
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

Any constructor option can be changed in a derived helper by passing it to `with_options(...)`.

## Row Actions

Use `PowerAction` for row-level `extra_actions`.

```python
ROW_PREVIEW = PowerAction(
    text="Description Preview",
    url_name="sample:book-description-preview",
    display_modal=True,
    disabled_state="get_description_preview_disabled_state",
)

extra_actions = [
    ROW_PREVIEW,
    ROW_PREVIEW.with_options(
        text="Timeline",
        url_name="sample:book-timeline",
        disabled_state=None,
    ),
]

def get_description_preview_disabled_state(self, obj, request):
    if not obj.description:
        return "This book does not have a description yet."
    return None
```

`PowerAction.needs_pk` defaults to `True`, matching the normal row-action case.

## Toolbar Buttons

Use `PowerButton` for list-level `extra_buttons`.

??? example "Primitive API vs PowerButton"

    === "Primitive"

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

## Mixing Styles

Primitive dictionaries and helper declarations may be mixed in the same list.

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

PowerCRUD compiles helpers to primitive dictionaries before rendering.

## Disabled State

For row actions, prefer `disabled_state` when one hook can decide both disabled state and reason.

```python
def get_preview_disabled_state(self, obj, request):
    if not obj.description:
        return "Add a description before previewing."
    return None
```

Return a non-empty string to disable the action and show that string as the reason. Return `None`, `False`, or an empty string to keep the action enabled.

The older `disabled_if` and `disabled_reason` pair still works. Do not combine those legacy hooks with `disabled_state` on one action.

## Reference

See [PowerAction And PowerButton Reference](../reference/poweractions.md) for constructor parameters, defaults, and validation rules.
