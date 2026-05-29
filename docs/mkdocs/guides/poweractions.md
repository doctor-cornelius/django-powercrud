# PowerAction And PowerButton

`PowerAction` and `PowerButton` are small helpers for reusable `extra_actions` and `extra_buttons` declarations.

They do not replace the primitive dictionary API. Use them when related views repeat the same action mechanics and only change text, URL names, modal size, selection rules, or disabled logic.

```python
from powercrud.actions import PowerAction, PowerButton
```

## When To Use Them

Use the primitive dictionaries for one-off buttons and actions.

Use `PowerAction` or `PowerButton` when you want to name and reuse a pattern:

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

## Row Actions

Use `PowerAction` for row-level `extra_actions`.

```python
PREVIEW_ACTION = PowerAction(
    text="Description Preview",
    url_name="sample:bigbook-description-preview",
    display_modal=True,
    disabled_state="get_description_preview_disabled_state",
)

extra_actions = [
    PREVIEW_ACTION,
]

def get_description_preview_disabled_state(self, obj, request):
    if not obj.description:
        return "This book does not have a description yet."
    return None
```

`PowerAction.needs_pk` defaults to `True`, matching the normal row-action case.

## Toolbar Buttons

Use `PowerButton` for list-level `extra_buttons`.

```python
SELECTED_SUMMARY = PowerButton(
    text="Selected Summary",
    url_name="sample:bigbook-selected-summary",
    display_modal=True,
    uses_selection=True,
    selection_min_count=1,
    selection_min_behavior="disable",
    selection_min_reason="Select at least one row first.",
)

extra_buttons = [
    SELECTED_SUMMARY,
]
```

`PowerButton.needs_pk` defaults to `False`, matching the normal toolbar-button case.

## Mixing Styles

Primitive dictionaries and helper declarations may be mixed in the same list.

```python
extra_buttons = [
    PowerButton(
        text="Selected Summary",
        url_name="sample:bigbook-selected-summary",
        display_modal=True,
        uses_selection=True,
        selection_min_count=1,
        selection_min_behavior="disable",
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
