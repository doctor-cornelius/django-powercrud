# Permission-Aware Affordances Plan

## Status

- [x] Phase A implementation added.
- [ ] Focused container test run pending; `powercrud_django_dev` was not running.
- [x] DDMS validation captured in notes.

## Next

- [ ] Run focused Phase A tests once the Django container is running.

## Phase A: Lock The API Contract

1. [x] Define the base dictionary contract for permission-aware affordances.
    1. [x] Add `permission` as a permission-string field.
    2. [x] Add `permission_check` as a named view-method field.
    3. [x] Add `permission_behavior` with default hide behavior.
    4. [x] Add `permission_denied_reason` for disabled permission failures.
2. [x] Lock validation and resolver behavior.
    1. [x] Raise `ImproperlyConfigured` when `permission` and `permission_check` are both set.
    2. [x] Standardize `permission_check(request, obj=None)`.
    3. [x] Add the overridable `has_power_permission(permission, request, obj=None)` resolver.

## Phase B: Extra Actions And PowerAction

1. [ ] Add permission-aware affordances to primitive `extra_actions`.
    1. [ ] Apply permission checks before `hidden_if`.
    2. [ ] Apply permission checks before `disabled_state`.
2. [ ] Add matching fields to `PowerAction`.
    1. [ ] Preserve primitive dictionary parity.
    2. [ ] Preserve existing row/workflow-state hook behavior.

## Phase C: Extra Buttons And PowerButton

1. [ ] Add permission-aware affordances to primitive `extra_buttons`.
    1. [ ] Support permission hiding.
    2. [ ] Support permission disabling.
    3. [ ] Preserve existing selection behavior.
2. [ ] Add matching fields to `PowerButton`.
    1. [ ] Preserve primitive dictionary parity.
    2. [ ] Keep toolbar-button endpoint enforcement downstream-owned.

## Phase D: Built-In Create Edit Delete

1. [ ] Add built-in mutation permission hooks.
    1. [ ] Add `has_power_create_permission(request)`.
    2. [ ] Add `has_power_update_permission(request, obj)`.
    3. [ ] Add `has_power_delete_permission(request, obj)`.
2. [ ] Apply the hooks to PowerCRUD-owned UI and endpoints.
    1. [ ] Hide Create/Edit/Delete when permission fails.
    2. [ ] Deny direct endpoint access when permission fails.
    3. [ ] Keep row-state disabling separate through `can_update_object()` and `can_delete_object()`.

## Phase E: Tests And Documentation

1. [ ] Add focused behavior tests.
    1. [ ] Prove primitive API and `Power*` API parity.
    2. [ ] Prove permission precedence over row-state hooks.
    3. [ ] Prove PowerCRUD-owned backend denial.
2. [ ] Update public docs.
    1. [ ] Document permission versus row/workflow state.
    2. [ ] Document downstream-owned endpoint responsibilities.
    3. [ ] Document DDMS-style usage examples.

## Phase F: Deferred Follow-Up Register

1. [ ] Track bulk permissions as the likely next gap.
    1. [ ] Defer bulk update/delete hooks from the first slice.
    2. [ ] Note downstream viewer screens should disable bulk controls until hooks exist.
2. [ ] Keep wider permission surfaces deferred.
    1. [ ] Defer list/detail permission hooks.
    2. [ ] Defer field-sensitive permissions.
    3. [ ] Defer callable permission declarations.
