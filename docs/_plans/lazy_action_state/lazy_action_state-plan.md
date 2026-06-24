# Lazy Action State Plan

## Status

- [x] Initial planning folder created.
- [ ] API contract not implemented.
- [ ] Runtime endpoints not implemented.
- [ ] Public docs not updated.

## Next

1. Review the proposed contract before implementation.

## Phase A: Lock The Scope

1. [ ] Define lazy row-action state as dropdown-only for the first slice.
    1. [ ] Support lazy `disabled_state` for row `extra_actions`.
    2. [ ] Keep eager `hidden_if` behavior.
    3. [ ] Keep visible-button row actions on the existing eager path.
2. [ ] Define lazy list-cell tooltips as field-level opt-in.
    1. [ ] Add a lazy/eager mode alongside each tooltip hook.
    2. [ ] Preserve eager tooltip behavior by default.
    3. [ ] Keep tooltip content display-only, not validation authority.

## Phase B: Add Row-Action Lazy State

1. [ ] Add Base API and `PowerAction` config.
    1. [ ] Add a mode flag for lazy disabled-state evaluation.
    2. [ ] Add optional fallback/loading text.
    3. [ ] Validate unsupported lazy button-mode combinations.
2. [ ] Add the row/action state endpoint.
    1. [ ] Resolve one object and one configured row action.
    2. [ ] Return current enabled/disabled state and reason.
    3. [ ] Preserve permission and row-state precedence.

## Phase C: Add Lazy Cell Tooltips

1. [ ] Extend tooltip config.
    1. [ ] Support `PowerField(..., tooltip_mode="lazy")`.
    2. [ ] Support primitive rich tooltip config per field.
    3. [ ] Validate invalid tooltip config shapes.
2. [ ] Add the tooltip content endpoint.
    1. [ ] Resolve one object and one configured field/property.
    2. [ ] Call the configured tooltip hook on demand.
    3. [ ] Return empty content cleanly when no tooltip applies.

## Phase D: Frontend And UX

1. [ ] Hydrate lazy row-action state when the row `More` menu opens.
2. [ ] Hydrate lazy cell tooltip content on hover and focus.
3. [ ] Preserve keyboard and screen-reader behavior for both paths.
4. [ ] Avoid duplicate requests during repeated open/hover events.

## Phase E: Tests, Sample, Docs

1. [ ] Add focused unit tests for config and endpoint behavior.
2. [ ] Add browser coverage for dropdown hydration and lazy tooltip hydration.
3. [ ] Add a small sample app demonstration.
4. [ ] Update Base API, `PowerAction`, `PowerField`, and tooltip docs.
