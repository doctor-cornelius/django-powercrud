# Permission-Aware Affordances Plan

## Status

- [x] Phase A implementation added.
- [x] Focused Phase A-C container tests passed.
- [x] Phase B implementation added.
- [x] Phase C implementation added.
- [x] Phase D implementation added.
- [x] Phase E1 focused behavior tests added.
- [x] Phase E2 public documentation added.
- [x] Phase F bulk permission hooks added.
- [x] Built-in Detail permission follow-up added.
- [x] DDMS validation captured in notes.
- [x] DDMS caveats captured in notes.

## Next

- [ ] Continue Phase G deferred follow-up register.

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

## Phase F: Bulk Permission Hooks

1. [x] Add PowerCRUD-owned bulk permission hooks.
    1. [x] Add `has_power_bulk_update_permission(request)`.
    2. [x] Add `has_power_bulk_delete_permission(request)`.
2. [x] Apply hooks to bulk UI and backend handling.
    1. [x] Hide bulk update controls when update permission fails.
    2. [x] Hide bulk delete controls when delete permission fails.
    3. [x] Deny the bulk modal when neither bulk operation is permitted.
    4. [x] Deny direct bulk update/delete submissions before validation, async queueing, persistence, or delete execution.
3. [x] Keep selection controls tied to visible permitted operations.
    1. [x] Hide row selection controls when no permitted bulk operation or permitted selection-aware button needs them.
    2. [x] Preserve selection-aware extra button behavior when its own permission passes.

## Phase G: Deferred Follow-Up Register

1. [x] Add the narrow built-in Detail operation permission hook.
    1. [x] Add `has_power_detail_permission(request, obj)`.
    2. [x] Hide the built-in Detail/View row action when the hook denies.
    3. [x] Deny the PowerCRUD-owned detail endpoint after object resolution.
    4. [x] Keep broader list/screen access hooks deferred.
2. [ ] Keep wider permission surfaces deferred.
    1. [ ] Defer list/screen-access permission hooks.
    2. [ ] Defer field-sensitive permissions.
    3. [ ] Defer callable permission declarations.
