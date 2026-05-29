# PowerAction and PowerButton Reference

`PowerAction` and `PowerButton` live in `powercrud.actions`.

```python
from powercrud.actions import PowerAction, PowerButton
```

They are plain Python declarations. PowerCRUD compiles them to the same base dictionaries used by `extra_actions` and `extra_buttons`.

## PowerAction

Use `PowerAction` inside `extra_actions` for row-level actions.

```python
PowerAction(
    text,
    url_name,
    *,
    needs_pk=True,
    button_class=None,
    htmx_target=None,
    display_modal=None,
    modal_box_classes=None,
    hx_post=False,
    lock_sensitive=False,
    refresh_list_on_modal_close=False,
    disabled_state=None,
    disabled_if=None,
    disabled_reason=None,
)
```

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `text` | required | Visible row action label. |
| `url_name` | required | Django URL name for the row action endpoint. |
| `needs_pk` | `True` | Include the current row primary key in the URL. |
| `button_class` | `None` | Styling class used when actions render as visible buttons. |
| `htmx_target` | `None` | Custom HTMX target for non-modal or custom-target flows. |
| `display_modal` | `None` | `True` opens in a modal. `None` preserves the base row-action fallback behavior. |
| `modal_box_classes` | `None` | Replacement modal box classes for this modal action. |
| `hx_post` | `False` | Render the action as an HTMX POST. |
| `lock_sensitive` | `False` | Disable the action under PowerCRUD row-lock logic. |
| `refresh_list_on_modal_close` | `False` | Refresh the list when this modal closes. |
| `disabled_state` | `None` | Single disabled-state hook name. |
| `disabled_if` | `None` | Legacy disabled boolean hook name. |
| `disabled_reason` | `None` | Legacy disabled reason hook name. |

`to_dict()` returns the base `extra_actions` dictionary. `with_options(...)` returns a new `PowerAction` with selected values changed.

Any constructor parameter in the table above can be passed to `with_options(...)`.

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
        modal_box_classes="modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-7xl flex-col",
        disabled_state=None,
    ),
]
```

## PowerButton

Use `PowerButton` inside `extra_buttons` for toolbar-level buttons.

```python
PowerButton(
    text,
    url_name,
    *,
    needs_pk=False,
    button_class=None,
    htmx_target=None,
    display_modal=False,
    modal_box_classes=None,
    refresh_list_on_modal_close=False,
    extra_attrs=None,
    extra_class_attrs=None,
    uses_selection=False,
    selection_min_count=0,
    selection_min_behavior="allow",
    selection_min_reason=None,
)
```

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `text` | required | Visible toolbar button label. |
| `url_name` | required | Django URL name for the button endpoint. |
| `needs_pk` | `False` | Usually stays `False` because toolbar buttons are not row actions. |
| `button_class` | `None` | Styling class for the button. |
| `htmx_target` | `None` | Custom HTMX target for non-modal or custom-target flows. |
| `display_modal` | `False` | Open the response in the standard modal target. |
| `modal_box_classes` | `None` | Replacement modal box classes for this modal button. |
| `refresh_list_on_modal_close` | `False` | Refresh the list when this modal closes. |
| `extra_attrs` | `None` | Raw HTML attributes appended to the button element. |
| `extra_class_attrs` | `None` | Extra CSS classes appended after the standard button classes. |
| `uses_selection` | `False` | Endpoint should operate on the current persisted PowerCRUD selection. |
| `selection_min_count` | `0` | Minimum selected-row count required. |
| `selection_min_behavior` | `"allow"` | `"allow"` keeps the button clickable; `"disable"` disables it below the minimum. |
| `selection_min_reason` | `None` | Disabled tooltip/help text when the selected count is too low. |

`to_dict()` returns the base `extra_buttons` dictionary. `with_options(...)` returns a new `PowerButton` with selected values changed.

Any constructor parameter in the table above can be passed to `with_options(...)`.

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
        modal_box_classes="modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-7xl flex-col",
        selection_min_reason="Select at least one row to export.",
    ),
]
```

## Validation Rules

`PowerAction` and `PowerButton` validate declaration shape before PowerCRUD renders them.

- `text` and `url_name` must be non-empty strings.
- Boolean parameters must be `True`, `False`, or `None` where the constructor explicitly allows `None`.
- `PowerAction.disabled_state` cannot be combined with `disabled_if` or `disabled_reason`.
- `PowerAction.disabled_reason` requires `disabled_if`; use `disabled_state` for the single-hook contract.
- `PowerButton.selection_min_behavior` must be `"allow"` or `"disable"`.
- `PowerButton` cannot combine `uses_selection=True` with `needs_pk=True`.

Base dictionaries remain valid and are still the underlying Action API. `PowerAction` and `PowerButton` are for reuse, defaults, and early validation.
