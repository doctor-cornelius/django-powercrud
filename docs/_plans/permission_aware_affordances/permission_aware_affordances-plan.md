# Permission-Aware Affordances Plan

## Status

- [x] Phase A implementation added.
- [x] Focused Phase A-C container tests passed.
- [x] Phase B implementation added.
- [x] Phase C implementation added.
- [x] Phase D implementation added.
- [x] Phase E1 focused behavior tests added.
- [x] Phase E2 public documentation added.
- [x] DDMS validation captured in notes.
- [x] DDMS caveats captured in notes.

## Next

- [ ] Start Phase F deferred follow-up register.

## Phase A: Lock The API Contract

1. [x] Define the Base API dictionary contract for permission-aware affordances.
    1. [x] Add `permission` as a permission-string field.
    2. [x] Add `permission_check` as a named view-method field.
    3. [x] Add `permission_behavior` with default hide behavior.
    4. [x] Add `permission_denied_reason` for disabled permission failures.
2. [x] Lock validation and resolver behavior.
    1. [x] Raise `ImproperlyConfigured` when `permission` and `permission_check` are both set.
    2. [x] Standardize `permission_check(request, obj=None)`.
    3. [x] Add the overridable `has_power_permission(permission, request, obj=None)` resolver.

## Phase B: Extra Actions And PowerAction

1. [x] Add permission-aware affordances to Base API `extra_actions`.
    1. [x] Apply permission checks before `hidden_if`.
    2. [x] Apply permission checks before `disabled_state`.
2. [x] Add matching fields to `PowerAction`.
    1. [x] Preserve Base API dictionary parity.
    2. [x] Preserve existing row/workflow-state hook behavior.
3. [x] Add a simple sample-app demonstration.
    1. [x] Add sample viewer and manager login controls.
    2. [x] Show permission-hidden preview actions in Base API and `PowerAction` examples.
    3. [x] Keep downstream-owned endpoint enforcement explicit.

## Phase C: Extra Buttons And PowerButton

1. [x] Add permission-aware affordances to Base API `extra_buttons`.
    1. [x] Support permission hiding.
    2. [x] Support permission disabling.
    3. [x] Preserve existing selection behavior.
2. [x] Add matching fields to `PowerButton`.
    1. [x] Preserve Base API dictionary parity.
    2. [x] Keep toolbar-button endpoint enforcement downstream-owned.
3. [x] Add a simple sample-app demonstration.
    1. [x] Show permission-hidden selected-summary buttons in Base API and `PowerButton` examples.
    2. [x] Preserve selection-state disabling after permission passes.
    3. [x] Keep downstream-owned endpoint enforcement explicit.

## Phase D: Built-In Create Edit Delete

1. [x] Add built-in mutation permission hooks.
    1. [x] Add `has_power_create_permission(request)`.
    2. [x] Add `has_power_update_permission(request, obj)`.
    3. [x] Add `has_power_delete_permission(request, obj)`.
2. [x] Apply the hooks to PowerCRUD-owned UI and endpoints.
    1. [x] Hide Create/Edit/Delete when permission fails.
    2. [x] Deny direct create access before form rendering or persistence.
    3. [x] Resolve objects before update/delete permission checks.
    4. [x] Deny direct update/delete access before form rendering, persistence, or delete execution.
    5. [x] Keep row-state disabling separate through `can_update_object()` and `can_delete_object()`.

## Phase E: Tests And Documentation

1. [x] Add focused behavior tests.
    1. [x] Prove Base API and `Power*` API parity.
    2. [x] Prove permission precedence over row-state hooks.
    3. [x] Prove PowerCRUD-owned backend denial.
2. [x] Update public docs.
    1. [x] Document permission versus row/workflow state.
    2. [x] Document downstream-owned endpoint responsibilities.
    3. [x] Document DDMS-style usage examples.

## Phase F: Deferred Follow-Up Register

1. [ ] Track bulk permissions as the likely next gap.
    1. [ ] Defer bulk update/delete hooks from the first slice.
    2. [ ] Note downstream viewer screens should disable bulk controls until hooks exist.
2. [ ] Keep wider permission surfaces deferred.
    1. [ ] Defer list/detail permission hooks.
    2. [ ] Defer field-sensitive permissions.
    3. [ ] Defer callable permission declarations.
    4. [ ] Keep DDMS timeline GET/POST handling downstream-owned.
