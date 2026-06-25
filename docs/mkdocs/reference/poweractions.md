# PowerAction and PowerButton Reference

`PowerAction` and `PowerButton` live in `powercrud.actions`.

```python
from powercrud.actions import PowerAction, PowerButton
```

They are plain Python declarations. PowerCRUD compiles them to the same Base API dictionaries used by `extra_actions` and `extra_buttons`.

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
    hidden_if=None,
    hidden_if_mode=None,
    disabled_state=None,
    disabled_state_mode=None,
    disabled_if=None,
    disabled_reason=None,
    permission=None,
    permission_check=None,
    permission_behavior=None,
    permission_denied_reason=None,
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
| `hidden_if` | `None` | Boolean hook name that hides this row action when true. |
| `hidden_if_mode` | `None` | `None` or `"eager"` evaluates `hidden_if` during list rendering. `"lazy"` resolves it when a dropdown row action's `More` menu opens. |
| `disabled_state` | `None` | Single disabled-state hook name. |
| `disabled_state_mode` | `None` | `None` or `"eager"` evaluates `disabled_state` during list rendering. `"lazy"` resolves it when a dropdown row action's `More` menu opens. |
| `disabled_if` | `None` | Deprecated legacy disabled boolean hook name. Use `disabled_state` instead. |
| `disabled_reason` | `None` | Deprecated legacy disabled reason hook name. Use `disabled_state` instead. |
| `permission` | `None` | Django permission string resolved through `has_power_permission(permission, request, obj=obj)`. |
| `permission_check` | `None` | Named view method with signature `permission_check(request, obj=None)`. |
| `permission_behavior` | `None` | `"hide"` or `"disable"` when permission fails. `None` behaves as `"hide"`. |
| `permission_denied_reason` | `None` | Tooltip/help text used only when `permission_behavior="disable"`. |

`to_dict()` returns the base `extra_actions` dictionary. `with_options(...)` returns a new `PowerAction` with selected values changed.

Any constructor parameter in the table above can be passed to `with_options(...)`.

```python
ROW_MODAL = PowerAction(
    text="Workflow Action",
    url_name="cases:workflow-action",
    display_modal=True,
    modal_box_classes="modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-5xl flex-col",
    hidden_if="should_hide_workflow_action",
    hidden_if_mode="lazy",
    disabled_state="get_workflow_action_disabled_state",
    disabled_state_mode="lazy",
    permission_check="can_run_workflow_action",
    permission_behavior="hide",
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
    clear_selection_on_success=False,
    selection_min_count=0,
    selection_min_behavior="allow",
    selection_min_reason=None,
    permission=None,
    permission_check=None,
    permission_behavior=None,
    permission_denied_reason=None,
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
| `clear_selection_on_success` | `False` | Clear the persisted selection after a successful HTMX request. Ignored unless `uses_selection=True`. |
| `selection_min_count` | `0` | Minimum selected-row count required. |
| `selection_min_behavior` | `"allow"` | `"allow"` keeps the button clickable; `"disable"` disables it below the minimum. |
| `selection_min_reason` | `None` | Disabled tooltip/help text when the selected count is too low. |
| `permission` | `None` | Django permission string resolved through `has_power_permission(permission, request, obj=None)`. |
| `permission_check` | `None` | Named view method with signature `permission_check(request, obj=None)`. |
| `permission_behavior` | `None` | `"hide"` or `"disable"` when permission fails. `None` behaves as `"hide"`. |
| `permission_denied_reason` | `None` | Tooltip/help text used only when `permission_behavior="disable"`. |

`to_dict()` returns the base `extra_buttons` dictionary. `with_options(...)` returns a new `PowerButton` with selected values changed.

Any constructor parameter in the table above can be passed to `with_options(...)`.

`uses_selection=True` can render row selection controls even when the view has no built-in bulk edit/delete configuration.

Set `clear_selection_on_success=True` only when the button's successful HTMX request consumes the current selection. Leave it off for summary or preview modals that merely read the selected rows.

Set `extra_button_selection_controls_disabled = True` on the view if the button uses selected rows, but this list should not show checkboxes just because of that button.

This is mainly useful when the selected rows come from somewhere else, or when the page has its own custom way to choose rows. Bulk edit and bulk delete still show checkboxes because they need them.

```python
SELECTED_MODAL = PowerButton(
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
- `PowerAction.hidden_if` must be a method-name string when set.
- `PowerAction.hidden_if_mode` must be `"eager"` or `"lazy"` when set, and `"lazy"` requires `hidden_if`.
- `PowerAction.disabled_state` cannot be combined with `disabled_if` or `disabled_reason`.
- `PowerAction.disabled_state_mode` must be `"eager"` or `"lazy"` when set, and `"lazy"` requires `disabled_state`.
- Lazy hidden and disabled state are supported for dropdown row actions. Base dictionaries use the same `hidden_if_mode` and `disabled_state_mode` keys.
- `PowerAction.disabled_if` and `PowerAction.disabled_reason` are deprecated and targeted for removal in v1.0.
- `PowerAction.disabled_reason` requires `disabled_if`; use `disabled_state` for the single-hook contract.
- `PowerAction` and `PowerButton` cannot combine `permission` with `permission_check`.
- `permission_behavior`, when set, must be `"hide"` or `"disable"`.
- `permission_denied_reason` is only used by disabled permission failures.
- `PowerButton.selection_min_behavior` must be `"allow"` or `"disable"`.
- `PowerButton` cannot combine `uses_selection=True` with `needs_pk=True`.
- `PowerButton.clear_selection_on_success` is ignored unless `uses_selection=True`.

Base dictionaries remain valid and are still the underlying Action API. `PowerAction` and `PowerButton` are for reuse, defaults, and early validation.

See [Permission-Aware Affordances](../guides/advanced/permission_aware_affordances.md) for the distinction between permission checks, row state, and backend enforcement. See [Lazy Evaluation](../guides/advanced/lazy_evaluation.md) for deferring expensive row-action state until the row menu opens.
