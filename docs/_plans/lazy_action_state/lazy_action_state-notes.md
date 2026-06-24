# Lazy Action State Notes

## Intent

This plan covers opt-in lazy evaluation for expensive row-action disabled state and expensive list-cell tooltip content.

The goal is to avoid doing business-heavy work for every visible row during list render when most actions and tooltips are never opened.

## Current Problem

PowerCRUD currently renders row actions eagerly. For each visible row, configured row actions may call permission checks, `hidden_if`, and `disabled_state` before the user interacts with the action.

That is fine for cheap checks. It becomes expensive when downstream callbacks call services, inspect related objects, summarize child records, or build detailed disabled reasons.

List-cell semantic tooltips can have the same cost shape if a tooltip hook does non-trivial work for every visible row.

## Settled Direction

1. Lazy row-action state is useful for PowerCRUD.
2. The first row-action implementation should be dropdown-only.
3. Visible row-action buttons should keep the current eager behavior in the first slice.
4. `hidden_if` should stay eager because hidden means the action should not exist for that row.
5. `disabled_state` is the best lazy row-action target because the action exists, but the precise disabled reason can be resolved when needed.
6. Final action endpoints must still revalidate before mutation.
7. Lazy cell tooltips should be field-level, not a global list.

## Locked Phase A Scope

First implementation slice:

1. Add lazy evaluation only for row-action `disabled_state`.
2. Apply it only to `extra_actions_mode = "dropdown"`.
3. Keep `hidden_if` eager.
4. Keep permission checks eager.
5. Keep visible-button row actions eager.
6. Keep the default behavior eager.
7. Require the final action endpoint to revalidate before mutation.

Explicitly deferred:

1. Lazy `hidden_if`.
2. Lazy visible row-action buttons.
3. Lazy cell tooltip implementation.
4. Any generic lazy state system beyond row-action disabled state.

Future tooltip direction, if resumed later:

1. Field-level opt-in, likely through `PowerField(..., tooltip_mode="lazy")`.
2. Rich primitive config beside the hook.
3. Display-only content, not validation or permission logic.

## Proposed Row-Action API Shape

Accepted public config:

```python
PowerAction(
    text="Close",
    url_name="case-close",
    display_modal=True,
    disabled_state="get_close_disabled_state",
    disabled_state_mode="lazy",
)
```

Primitive equivalent:

```python
extra_actions = [
    {
        "text": "Close",
        "url_name": "case-close",
        "display_modal": True,
        "disabled_state": "get_close_disabled_state",
        "disabled_state_mode": "lazy",
    },
]
```

Default should remain eager.

## Locked Phase A API And UX Decisions

1. Public config is `disabled_state_mode="lazy"`.
2. Lazy state hydration is one row-level request when the user opens `More`.
3. The request returns state for all lazy actions in that row dropdown.
4. PowerCRUD waits for lazy state before opening the dropdown.
5. While waiting, the `More` trigger should expose a loading or busy state.
6. Lazy row-action state outside dropdown mode is invalid configuration.
7. If lazy state resolution fails, unresolved lazy actions render disabled with a generic unavailable message.

Reasoning:

1. `disabled_state_mode="lazy"` reads beside `disabled_state` and leaves room for future modes.
2. One row-level request avoids a request per action and matches the user intent of opening that row's menu.
3. Waiting before opening avoids temporary false states and dropdown flicker.
4. Rejecting button mode is clearer than silently falling back to eager behavior.
5. Disabling unresolved actions is safer than hiding them or leaving them enabled after validation failed.

## Proposed Tooltip API Shape

Preferred `PowerField` shape:

```python
PowerField(
    "status",
    list=True,
    tooltip_hook="get_status_tooltip",
    tooltip_mode="lazy",
)
```

Primitive current shape should remain valid and eager:

```python
list_cell_tooltip_fields = {
    "status": "get_status_tooltip",
}
```

Primitive rich shape:

```python
list_cell_tooltip_fields = {
    "status": {
        "hook": "get_status_tooltip",
        "mode": "lazy",
        "loading_text": "Loading...",
        "empty_text": None,
    },
}
```

## Plan Phases

### Phase A: Lock The Scope

The first implementation should avoid a broad lazy-state system. Keep the boundary narrow: lazy disabled-state for dropdown row actions only.

Do not make `hidden_if` lazy in the first slice. If an action is truly not applicable, showing it briefly and then removing it would weaken the current row-action contract.

Lazy cell tooltips remain a worthwhile later feature, but they should not be mixed into the first implementation PR.

The remaining Phase A decisions are now locked:

1. Use `disabled_state_mode="lazy"`.
2. Fetch all lazy action states for the row in one request.
3. Wait for state before opening the dropdown.
4. Raise a validation error for lazy state outside dropdown mode.
5. Disable unresolved lazy actions with a generic unavailable message if state resolution fails.

### Phase B: Add Row-Action Lazy State

Dropdown mode is the clean first target because the user has already expressed intent by opening `More`. PowerCRUD can hydrate the current state for that row's extra actions before showing or finalizing the menu contents.

Button mode is deferred because all actions are already visible. A lazy button-mode design would need a separate UX decision for whether the button appears enabled, disabled, or neutral before validation.

### Phase C: Add Lazy Cell Tooltips

Tooltip laziness should live beside the tooltip hook because cost varies per field. A separate global `lazy_list_cell_tooltip_fields` setting would split one concept across two places.

Lazy tooltip content is display-only. It must not become a permission or workflow validation path.

### Phase D: Frontend And UX

Frontend behavior should request state only when the user opens the relevant row-action dropdown or hovers/focuses the relevant tooltip trigger.

The implementation should cache or coalesce repeated requests enough to avoid duplicate work during normal open/close or hover/focus cycles.

### Phase E: Tests, Sample, Docs

Tests should prove that eager behavior remains the default, lazy callbacks are not called during initial list render, and lazy endpoints call only the requested row/action or row/field hook.

Docs should keep Base API dictionaries visible as the primitive contract and show matching `PowerAction` / `PowerField` examples.
