# Power Actions Notes

## Intent

This plan covers small helper declarations for the existing `extra_actions` and `extra_buttons` APIs.

The goal is to make repeated row-action and toolbar-button mechanics easier to reuse without replacing the current primitive dictionary contract.

## Current Problem

`extra_actions` and `extra_buttons` are readable for one-off actions. They become noisy when several workflow screens repeat the same mechanics:

1. Row action opens a modal.
2. Row action needs the current row primary key.
3. Row action has the same disabled hook and disabled reason hook.
4. Toolbar button opens a modal.
5. Toolbar button operates on the current selection.
6. Toolbar button should disable until at least one row is selected.

In those cases, the business operation is often just the `text` and `url_name`, while the repeated PowerCRUD wiring dominates the view.

## Proposed Shape

Add two lightweight declarations:

1. `PowerAction` for row-level `extra_actions`.
2. `PowerButton` for toolbar-level `extra_buttons`.

Both should accept the same public parameters as the current dictionaries and compile to the same dictionaries before rendering.

Example:

```python
CASE_ROW_MODAL = PowerAction(
    text="Workflow Action",
    url_name="ddms:ddmcase-workflow-action-single",
    needs_pk=True,
    display_modal=True,
    button_class="btn-accent",
    modal_box_classes=CASE_WORKFLOW_ACTION_MODAL_BOX_CLASSES,
    disabled_state="get_manual_case_workflow_action_disabled_state",
)

extra_actions = [
    CASE_ROW_MODAL,
    CASE_ROW_MODAL.with_options(
        text="Timeline",
        url_name="ddms:ddmcase-timeline",
    ),
]
```

## Product Decision

Start with plain constructor parameters matching the existing primitive API.

Do not start with extra constructor helpers such as `PowerAction.modal(...)` or `PowerButton.selection_modal(...)`. They may be useful later, but the first value is reuse, validation, and `with_options(...)`, not a new vocabulary.

## Disabled State

The existing row-action disabled API has two related keys:

```python
disabled_if="is_manual_case_workflow_action_disabled",
disabled_reason="get_manual_case_workflow_action_disabled_reason",
```

They are close enough that the new helper should support a single hook:

```python
disabled_state="get_manual_case_workflow_action_disabled_state"
```

The proposed hook contract is:

```python
def get_manual_case_workflow_action_disabled_state(self, obj, request):
    if not obj.can_take_workflow_action:
        return "Workflow action is not available for this case."
    return None
```

Return meaning:

1. `None`, `False`, or an empty string means enabled.
2. A non-empty string means disabled, and the string is the disabled reason.

This should be added to the primitive `extra_actions` dictionary API as well as `PowerAction`. Otherwise the helper becomes more capable than the primitive contract.

Legacy `disabled_if` and `disabled_reason` should remain valid. A single action should not mix `disabled_state` with the legacy pair.

## Design Rules

1. Existing dictionary config must keep working.
2. Mixed lists should work during migration.
3. `PowerAction` should only target `extra_actions`.
4. `PowerButton` should only target `extra_buttons`.
5. `with_options(...)` should return a new declaration.
6. The declarations should be immutable if practical.
7. The renderer should continue consuming normalized dictionaries.

## Main Benefit

The helper is not mainly about shortening one action. One action as a dictionary is fine.

The helper is valuable when a project can define a small reusable action primitive and vary it across related workflow views.

## Sample App

Add the first sample to the existing PowerField sample view.

That keeps the demonstration focused: Power helpers can compose in one view, and `PowerField` does not create a separate mode that excludes action and button helpers.

Keep the sample small:

1. One reusable `PowerAction` with `with_options(...)`.
2. One reusable `PowerButton` only if it clearly shows selected-row toolbar reuse.
3. No broad workflow demo in the sample app.

## Open Questions

1. Should `PowerAction` default `needs_pk` to `True`, or should it preserve the current primitive default explicitly?
2. Should `PowerButton` default `needs_pk` to `False`, or should callers always set it?
3. Should invalid row-only keys on `PowerButton`, or button-only keys on `PowerAction`, fail immediately?
4. Should `to_dict()` be public, or should compilation stay internal?
