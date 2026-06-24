# Lazy Action State Plan

## Status

- [x] Initial planning folder created.
- [x] Phase A row-action scope locked.
- [x] Phase A API and UX decisions locked.
- [x] Lazy cell tooltips deferred from the first implementation slice.
- [x] Row-action API contract implemented.
- [x] Row-action runtime endpoint implemented.
- [x] Public docs updated for the row-action slice.
- [ ] Lazy cell tooltip implementation remains deferred.

## Next

1. Revisit Phase C lazy cell tooltips when the row-action slice is accepted.

## Phase A: Lock The Scope

1. [x] Define lazy row-action state as dropdown-only for the first slice.
    1. [x] Support lazy `disabled_state` for row `extra_actions`.
    2. [x] Keep eager `hidden_if` behavior.
    3. [x] Keep eager permission checks.
    4. [x] Keep visible-button row actions on the existing eager path.
    5. [x] Keep final action endpoints responsible for server-side revalidation.
2. [x] Defer lazy list-cell tooltips from the first implementation slice.
    1. [x] Keep the likely future shape as field-level opt-in.
    2. [x] Preserve eager tooltip behavior by default.
    3. [x] Keep tooltip content display-only, not validation authority.
3. [x] Confirm remaining first-slice API and UX decisions.
    1. [x] Use `disabled_state_mode="lazy"` as the public config.
    2. [x] Hydrate all lazy action states for the row in one request when `More` opens.
    3. [x] Wait for lazy state before opening the dropdown.
    4. [x] Reject lazy row-action state outside dropdown mode.
    5. [x] Disable unresolved lazy actions with a generic unavailable message when state resolution fails.

## Phase B: Add Row-Action Lazy State

1. [x] Add Base API and `PowerAction` config.
    1. [x] Add a mode flag for lazy disabled-state evaluation.
    2. [x] Use the locked generic fallback message for unresolved lazy state.
    3. [x] Validate unsupported lazy button-mode combinations.
2. [x] Add the row/action state endpoint.
    1. [x] Resolve one object and all configured lazy row actions.
    2. [x] Return current hidden/enabled/disabled state and reason.
    3. [x] Preserve permission and row-state precedence.

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

1. [x] Hydrate lazy row-action state when the row `More` menu opens.
2. [ ] Hydrate lazy cell tooltip content on hover and focus.
3. [ ] Preserve keyboard and screen-reader behavior for the deferred tooltip path.
4. [x] Avoid duplicate row-action state requests during repeated opens.

## Phase E: Tests, Sample, Docs

1. [x] Add focused unit tests for config and endpoint behavior.
2. [ ] Add browser coverage for dropdown hydration and lazy tooltip hydration.
    1. [x] Cover dropdown row-action hydration and failure fallback.
    2. [ ] Cover deferred lazy tooltip hydration.
3. [x] Add a small sample app demonstration.
4. [ ] Update Base API, `PowerAction`, `PowerField`, and tooltip docs.
    1. [x] Update Base API and `PowerAction` docs for row-action lazy state.
    2. [ ] Update `PowerField` and tooltip docs when Phase C is implemented.
