# Permission-Aware Affordances Notes

## Intent

This planning slice captures the permission-related diagnosis and design direction for PowerCRUD action affordances.

The useful enhancement is not to make PowerCRUD the downstream application's complete authorization system. The useful enhancement is to give PowerCRUD a consistent way to apply permission decisions to the UI affordances and backend handlers that PowerCRUD owns, while keeping business services and custom endpoints responsible for their own final enforcement.

## Problem Summary

Downstream applications such as DDMS need users who can open a PowerCRUD list or detail screen but cannot run every operation visible on that screen.

The conceptual model has four separate layers:

1. View or screen access: can the user open this list or detail view?
2. Operation permission: can the user perform this kind of operation at all?
3. Row or workflow state: is this operation valid for this object right now?
4. Backend enforcement: does the endpoint or service reject unauthorized or invalid attempts?

PowerCRUD currently has some good row-state hooks, but it does not provide one coherent permission contract across built-in CRUD actions, extra row actions, toolbar buttons, bulk operations, and inline editing.

## Current Behavior

### Evidence Anchors

The diagnosis is grounded in the current PowerCRUD and Neapolitan flow:

1. The list template renders Create only when `create_view_url` is present.
2. Neapolitan exposes CRUD operations by registered role and URL reversal. It does not provide model-permission filtering for those roles.
3. Built-in View/Edit/Delete row actions are rendered from reversible URLs. Edit and Delete then pass through PowerCRUD's disabled-state resolver.
4. PowerCRUD's standard-action disabled resolver calls `can_update_object()` and `can_delete_object()`, but those hooks default open and are not Django permission checks by default.
5. Inline edit already composes row lock state, `can_update_object()`, optional `inline_edit_requires_perm`, and optional `inline_edit_allowed()`.
6. Extra toolbar buttons currently derive disabled state from selection state only; they do not have generic permission, `hidden_if`, or `disabled_state` handling.
7. Bulk operations validate configured fields and whether bulk delete is enabled, but do not have per-user permission hooks.

### Built-In Create

The list template shows the Create button when `create_view_url` is present.

That URL is present when the create route can be reversed. It is not currently filtered by a Django `add` permission check inside PowerCRUD.

Practical effect:

1. If the downstream app does not register the create URL, the Create button is hidden.
2. If the create URL exists but the current user lacks model or view create permission, PowerCRUD still shows the button unless downstream code clears or suppresses `create_view_url`.
3. The create endpoint itself does not have a PowerCRUD-owned permission hook today.

Relevant current surfaces:

1. `src/powercrud/templates/powercrud/daisyUI/object_list.html`
2. `src/powercrud/mixins/url_mixin.py`
3. Neapolitan `Role.CREATE.maybe_reverse(...)`

### Built-In Edit

The built-in Edit action is rendered when the update URL can be reversed.

PowerCRUD can disable it through `can_update_object(obj, request)` and explain it through `get_update_disabled_reason(obj, request)`.

That hook is currently best understood as a row-state affordance hook. Its default returns `True`, and it does not automatically check Django `change` permission.

Important limitation:

1. The row UI affordance can be disabled through `can_update_object()`.
2. Inline editing also respects `can_update_object()`.
3. The regular update form endpoint does not currently use `can_update_object()` as backend authorization before rendering or saving the form.

### Built-In Delete

Delete mirrors Edit in broad shape.

PowerCRUD can disable the built-in Delete row action through `can_delete_object(obj, request)` and explain it through `get_delete_disabled_reason(obj, request)`.

PowerCRUD also catches `ValidationError` raised by the model delete operation and redisplays it cleanly.

Important limitation:

1. The row UI affordance can be disabled through `can_delete_object()`.
2. Direct delete endpoint protection still depends on downstream checks or model/service refusal.
3. The current hook is row-state oriented, not an automatic Django `delete` permission check.

### Inline Editing

Inline editing has the strongest current permission-related behavior.

It checks:

1. inline editing is enabled
2. the row is not locked
3. `can_update_object(obj, request)` allows the row
4. optional `inline_edit_requires_perm`
5. optional `inline_edit_allowed(obj, request)`

This is a good precedent for composing a broad update permission with row-state and inline-only restrictions.

### Extra Row Actions

`PowerAction` and primitive `extra_actions` support:

1. `hidden_if`
2. `disabled_state`
3. legacy `disabled_if` and `disabled_reason`

These hooks receive the row object and request.

They are adequate for row-state and workflow-state logic. In DDMS they are already used that way, and they should not be replaced by a permission abstraction.

Current limitation:

1. Permission checks can be repeated inside each `hidden_if` or `disabled_state` method.
2. There is no declarative operation-permission field on the action itself.
3. Extra action endpoints are downstream-owned, so PowerCRUD can improve affordances but cannot be the complete backend enforcement layer for those custom endpoints.

### Extra Toolbar Buttons

`PowerButton` and primitive `extra_buttons` support toolbar/modal/selection mechanics, including selection thresholds.

They do not currently have generic `hidden_if` or `disabled_state` equivalents.

This is the largest UI-affordance gap in the current action/button surface.

Current limitation:

1. Downstream projects can conditionally assemble `extra_buttons` per request, but that is ad hoc.
2. Selection-aware disabling exists, but permission-aware disabling or hiding does not.
3. Extra button endpoints are downstream-owned, so PowerCRUD can improve affordances but cannot guarantee backend enforcement for custom endpoints.

### Bulk Operations

Bulk edit and bulk delete are driven by configuration:

1. `bulk_fields`
2. `bulk_delete`
3. derived `bulk_edit_enabled`
4. derived `bulk_delete_enabled`

Bulk update validates submitted fields against configured `bulk_fields`.

Current limitation:

1. There is no first-class per-user permission hook for showing or denying bulk update.
2. There is no first-class per-user permission hook for showing or denying bulk delete.
3. Bulk delete only checks whether the operation is enabled by configuration before processing.

## Downstream Workarounds Available Today

There are viable downstream approaches now, but they are inconsistent.

For DDMS or similar downstream apps:

1. Hide Create by overriding `get_context_data()` and setting `create_view_url = None` when the user lacks create permission.
2. Disable built-in Edit by overriding `can_update_object(obj, request)` and optionally `get_update_disabled_reason(obj, request)`.
3. Disable built-in Delete by overriding `can_delete_object(obj, request)` and optionally `get_delete_disabled_reason(obj, request)`.
4. Hide or disable extra row actions with `hidden_if` and `disabled_state`.
5. Handle toolbar buttons by conditionally assembling `extra_buttons` for the request, or accepting a visible button with downstream backend denial.
6. Enforce backend permissions with downstream view mixins, decorators, dispatch checks, queryset scoping, and service-layer checks.

These workarounds are good enough that DDMS should not be blocked on a PowerCRUD change.

They are still a signal that PowerCRUD has room for a small coherent permission-affordance API.

## Design Principle

Permission hooks and row-state hooks must remain separate.

Permission asks:

1. Is this user allowed to perform this operation type at all?

Row state asks:

1. Is this operation valid for this object right now?
2. Is this object locked?
3. Is this workflow state eligible?
4. Are required prerequisites missing?

UI behavior asks:

1. Should this control be hidden?
2. Should this control be disabled?
3. Should PowerCRUD show a reason?

Backend enforcement asks:

1. Should the request be rejected even if the user reaches the endpoint directly?

The enhancement should compose these layers. It should not collapse `hidden_if`, `disabled_state`, `can_update_object()`, or `can_delete_object()` into permission checks.

Example desired composition:

```python
PowerAction(
    text="Send for Approval",
    url_name="cases:send-for-approval",
    permission="cases.submit_case",
    hidden_if="hide_when_not_in_draft_state",
    disabled_state="get_submission_disabled_reason",
)
```

In that example:

1. `permission` is user capability.
2. `hidden_if` is row or workflow applicability.
3. `disabled_state` is row or workflow readiness.
4. The downstream endpoint still validates the operation before mutation.

## UI Behavior Recommendation

The default response to a missing permission should be to hide the control.

Reasoning:

1. If the user lacks permission entirely, the operation is not part of their usable interface.
2. Showing a disabled control is often noise.
3. Showing permission-denied controls can leak irrelevant capability information.

Disabled with a reason should be used when the user generally has the capability but the operation is not valid right now.

Examples:

1. User can approve cases, but this case is not ready: disable and explain.
2. User can edit cases, but this row is locked: disable and explain.
3. User can submit a workflow action, but required fields are missing: disable and explain.

For permission failure:

1. User cannot create this model: hide Create.
2. User cannot approve cases at all: hide Approve.
3. User cannot use an admin toolbar button: hide the button.

Suggested default:

```python
permission_behavior = "hide"
```

Optional override:

```python
PowerButton(
    text="Admin Review",
    url_name="cases:admin-review",
    permission="cases.manage_cases",
    permission_behavior="disable",
)
```

The explicit disable behavior can be useful in admin or training interfaces, but it should not be the default.

## Recommended Enhancement Shape

### API Layering Requirement

The base API remains the fundamental API.

Any permission-aware affordance feature should be available first through the primitive dictionaries that PowerCRUD already accepts. The structured `Power*` APIs should expose the same capability as a clearer, typed declaration layer that compiles down to the base API.

Practical requirement:

1. Add the new keys to the primitive action/button dictionaries.
2. Add matching fields to `PowerAction` and `PowerButton`.
3. Keep the semantics identical between the base API and the structured API.
4. Do not make `PowerAction` or `PowerButton` more capable than the primitive API.
5. Document the primitive API as the underlying contract, with `Power*` as the preferred ergonomic wrapper.

This changes the design emphasis slightly: implementation should start by proving the base dictionary behavior, then wire the structured declarations through it.

### Core Permission Resolver

Add a small view-level permission resolver that downstream projects can override.

Possible shape:

```python
def has_power_permission(self, permission, request, obj=None):
    if not permission:
        return True
    user = getattr(request, "user", None)
    return bool(user and user.has_perm(permission))
```

Possible disabled reason hook:

```python
def get_power_permission_disabled_reason(self, permission, request, obj=None):
    return None
```

This hook should always exist. The default implementation should interpret `permission` as a Django permission string and call `request.user.has_perm(permission)`.

Downstream apps can override it when they do not use plain Django permissions. DDMS may want to delegate to an app-specific permission service.

### Permission Metadata On Extra Actions And Buttons

Add optional declaration fields to primitive action/button dictionaries and to `PowerAction` and `PowerButton`:

```python
permission=None
permission_check=None
permission_behavior="hide"
permission_denied_reason=None
```

`permission` and `permission_check` have separate meanings:

1. `permission` is a permission string. By default, PowerCRUD checks it through `has_power_permission(permission, request, obj=None)`.
2. `permission_check` is a named view method for projects that want operation-specific logic instead of a permission string.
3. `permission` and `permission_check` are mutually exclusive. If both are configured, PowerCRUD should raise `ImproperlyConfigured` during configuration validation.

Suggested method signatures:

```python
def can_use_admin_review(self, request, obj=None):
    return request.user.is_staff

def can_submit_case(self, request, obj=None):
    return (
        obj is not None
        and request.user.has_perm("cases.submit_case")
        and obj.owner == request.user
    )
```

Use the same `permission_check(request, obj=None)` shape for toolbar buttons and row actions. Toolbar buttons call the method with `obj=None`; row actions pass the row object.

Compatibility rule:

1. If both `permission` and `permission_check` are omitted, behavior remains exactly as it is today.
2. If both `permission` and `permission_check` are configured, raise `ImproperlyConfigured`.
3. Existing `hidden_if`, `disabled_state`, and selection behavior remain valid.
4. Permission evaluation happens before row-state disabled-state evaluation when the behavior is hide.
5. When permission behavior is disable, row-state and permission reasons need a deterministic precedence.

Recommended precedence:

1. Permission hide removes the control before other state is evaluated.
2. Permission disable disables the control before row-state disabled logic.
3. Row-state disabled reason can remain more specific only when permission passes.

That avoids showing business-state details to users who lack the operation permission.

### Built-In CRUD Permissions

PowerCRUD-owned endpoints should have permission hooks that apply to both UI affordances and backend handling.

Phase D should stay focused on mutation operations:

```python
def has_power_create_permission(self, request):
    return True

def has_power_update_permission(self, request, obj):
    return True

def has_power_delete_permission(self, request, obj):
    return True
```

The default should be open for backward compatibility.

PowerCRUD should use these hooks in both places:

1. UI rendering: Create, Edit, and Delete affordances.
2. Backend endpoints: create, update, and delete handlers.

For the first design, built-in Create, Edit, and Delete do not need a per-control `permission_behavior` setting. If the relevant permission hook returns `False`, the UI affordance should be hidden. Backend access should be denied for direct requests.

For update and delete, these permission hooks should compose with existing row-state hooks:

1. `has_power_update_permission(request, obj)` answers whether the user can update this kind of object.
2. `can_update_object(obj, request)` answers whether this specific row is currently updateable.
3. Both must pass for backend mutation.
4. Permission failure should normally hide the UI affordance.
5. Row-state failure should normally disable the UI affordance with an optional reason.

Backend handling order matters:

1. Create permission can be checked before form rendering because it does not need an object.
2. Update and delete permission must be checked after object resolution because the hooks receive `obj`.
3. Update permission failure should deny before form rendering and before persistence.
4. Delete permission failure should deny before confirmation handling and before delete execution.

List/detail permission hooks remain deferred. DDMS already owns screen access through its own view-level permission mechanisms, and this PowerCRUD slice should not expand into general screen authorization.

### Bulk Permissions

Bulk permissions are likely the next gap after the first mutation/action slice.

Add explicit bulk permission hooks because bulk operations are PowerCRUD-owned endpoints.

Possible hooks:

```python
def has_power_bulk_update_permission(self, request):
    return True

def has_power_bulk_delete_permission(self, request):
    return True
```

PowerCRUD should use these hooks in both places:

1. UI rendering: bulk edit controls, bulk delete controls, selection affordances where relevant.
2. Backend handling: bulk edit modal GET, bulk update POST, bulk delete POST.

Bulk field validation remains separate and still mandatory.

DDMS feedback confirmed that operation-level permission is enough for the first implementation slice, but viewer-accessible DDMS screens must not expose bulk edit/delete controls. If bulk hooks are deferred, DDMS should explicitly disable bulk edit/delete on viewer-accessible views or keep those screens read-only until PowerCRUD has bulk permission hooks.

### Inline Editing Permissions

Inline editing should compose the new update permission hook with the existing inline checks.

Proposed order:

1. inline editing is enabled
2. object exists
3. row is not locked
4. `has_power_update_permission(request, obj)` passes
5. `can_update_object(obj, request)` passes
6. `inline_edit_requires_perm` passes if configured
7. `inline_edit_allowed(obj, request)` passes if configured

There is an open design question about whether `inline_edit_requires_perm` should be retained as a legacy convenience once `has_power_update_permission()` exists. The conservative answer is to retain it and document precedence.

## Backend Enforcement Boundary

The backend enforcement boundary differs by surface.

### PowerCRUD-Owned Surfaces

PowerCRUD should enforce permission hooks for endpoints it owns, where those hooks exist:

1. create
2. update
3. delete
4. inline edit if it is brought under the update hook
5. bulk update when bulk permission hooks are added
6. bulk delete when bulk permission hooks are added
7. list/detail if those hooks are added later
8. list options endpoints if they become permission-sensitive
9. selection endpoints if they expose sensitive scope

For these surfaces, it is reasonable and useful for the same PowerCRUD permission policy to drive both UI and backend behavior.

### Downstream-Owned Custom Surfaces

PowerCRUD can only provide UI affordance support for downstream-owned custom endpoints:

1. `extra_actions`
2. `extra_buttons`

PowerCRUD can hide or disable the button.

The downstream app must still enforce the endpoint permission and business rule.

That distinction should be explicit in public docs so developers do not confuse a hidden button with authorization.

## Main Benefits

1. Create becomes truthful.
    - Scope: add a create-permission hook and use it for both the Create button and the create endpoint.
    - Attack: keep the default open, and only hide or deny when the downstream view opts in.
    - Downstream benefit: apps stop using `create_view_url = None` as an ad hoc permission workaround.
2. Edit and Delete get a real permission layer.
    - Scope: add permission hooks separate from `can_update_object()` and `can_delete_object()`.
    - Attack: check permission first, then row-state eligibility.
    - Downstream benefit: apps can express "this user cannot edit" separately from "this row is locked".
3. Toolbar buttons become first-class.
    - Scope: add permission, hide, and disabled affordance support to the primitive button API and `PowerButton`.
    - Attack: bring toolbar buttons closer to the row-action model without changing existing behavior when unset.
    - Downstream benefit: apps stop conditionally assembling toolbars per user in one-off code.
4. Extra row actions become cleaner.
    - Scope: add optional permission metadata to primitive row actions and `PowerAction`.
    - Attack: let permission describe user capability while `hidden_if` and `disabled_state` keep describing row or workflow state.
    - Downstream benefit: apps avoid repeating permission checks inside every row-state hook.
5. PowerCRUD-owned backend behavior aligns with the UI.
    - Scope: enforce permission hooks only on endpoints PowerCRUD owns, such as create, update, delete, inline edit, and later bulk operations.
    - Attack: use the same permission policy for UI affordances and backend handling where PowerCRUD controls both.
    - Downstream benefit: built-in CRUD actions do not rely on hidden buttons as their only protection.
6. Downstream-owned endpoints stay downstream-owned.
    - Scope: for extra actions and extra buttons, PowerCRUD improves the UI affordance only.
    - Attack: document clearly that target views and services still enforce their own permissions.
    - Downstream benefit: callers get better UI consistency without a false promise that PowerCRUD is now the application authorization system.
7. The change stays compatible with both APIs.
    - Scope: enable the primitive/base API first, then expose the same fields through `PowerAction` and `PowerButton`.
    - Attack: make `Power*` declarations compile to the same primitive keys and semantics.
    - Downstream benefit: existing dictionary users and structured-API users get the same capability.

## DDMS Validation

DDMS review confirmed that this enhancement fits the DDMS model.

Key validation points:

1. Hiding permission-denied Create, Edit, and Delete matches DDMS viewer-style UX.
2. Disabled affordances should remain for row/workflow-state problems, not for users who can never perform the operation.
3. `permission_check` as a named view method fits DDMS well because DDMS can wrap `DDMSPermissionService` methods locally.
4. The important semantic split is:
    - `permission` / `permission_check` = user capability
    - `hidden_if` = row/action relevance
    - `disabled_state` = row/workflow-state reason
5. Toolbar buttons are the biggest immediate DDMS UI gap, but built-in Create/Edit/Delete also matter once viewer users can open broader PowerCRUD screens.
6. PowerCRUD hiding an extra action or extra button must not be treated as backend protection for custom DDMS endpoints.
7. Operation-level permission is enough for the first slice; field-sensitive permission can wait.
8. Bulk operations are the likely next gap for viewer-accessible screens.
9. Built-in update/delete backend checks must happen after object resolution and before form rendering, persistence, or delete execution.
10. DDMS timeline GET/POST handling is downstream-specific. If viewers can see timelines but cannot add comments, DDMS must split or guard timeline POST separately from PowerCRUD affordance work.

DDMS-style usage:

```python
PowerAction(
    text="Send for Approval",
    url_name="ddms:ddmcase-send-for-approval-single",
    permission_check="can_send_for_approval",
    permission_behavior="hide",
    disabled_state="get_submit_for_approval_disabled_reason",
)

def can_send_for_approval(self, request, obj=None):
    return DDMSPermissionService.can_manage_cases(request.user)
```

The target endpoint still needs its DDMS permission decorator or equivalent service check.

## Plan Phases

### Phase A: Lock The API Contract

Phase A implementation added the shared permission fields, structured API parity, primitive config validation, and the default resolver. Focused tests were added, but the required container test command could not run because `powercrud_django_dev` was not running.

### Phase B: Extra Actions And PowerAction

Phase B made permission metadata active for row extra actions.

Implemented behavior:

1. `permission` and `permission_check` are evaluated before `hidden_if` and `disabled_state`.
2. Permission failure with default `permission_behavior="hide"` omits the action.
3. Permission failure with `permission_behavior="disable"` renders the action disabled and uses `permission_denied_reason`.
4. Row-state hooks still run after permission passes.
5. Permission failure does not evaluate or reveal row/workflow-state reasons.
6. The sample app now has viewer and manager login controls so the behavior can be seen in the primitive Books view and the `PowerAction` PowerField Books view.
7. The sample description-preview endpoint still enforces its own permission check because it is downstream-owned from PowerCRUD's perspective.

Verification:

1. `./runproj exec ./runtests --pytest src/tests/test_templatetags_powercrud.py src/sample/tests/test_permission_affordance_demo.py src/tests/test_poweractions.py src/tests/test_core_phase1.py`
2. Result: 225 passed.

### Phase C: Extra Buttons And PowerButton

Phase C made permission metadata active for toolbar extra buttons.

Implemented behavior:

1. `permission` and `permission_check` are evaluated before selection state.
2. Permission failure with default `permission_behavior="hide"` omits the button.
3. Permission failure with `permission_behavior="disable"` renders the button disabled and uses `permission_denied_reason`.
4. Selection-state disabling still runs after permission passes.
5. Permission failure does not evaluate or reveal selection-state disabled reasons.
6. Disabled toolbar buttons remain hoverable for semantic tooltips while `aria-disabled="true"` and the frontend click guard prevent action execution.
7. The sample app now shows the selected-summary toolbar button as manager-only in the primitive Books view and the `PowerButton` PowerField Books view.
8. The sample selected-summary endpoint still enforces its own permission check because it is downstream-owned from PowerCRUD's perspective.

Verification:

1. `./runproj exec ./runtests --pytest src/tests/test_templatetags_powercrud.py src/sample/tests/test_permission_affordance_demo.py src/tests/test_core_phase1.py src/tests/test_poweractions.py`
2. Result: 233 passed.

### Phase D: Built-In Create Edit Delete

Phase D can move forward without reworking Phases A-C.

Notes for implementation:

1. Keep default permissions open for backward compatibility.
2. Hide built-in Create/Edit/Delete on permission failure.
3. Deny direct create access before form rendering or persistence.
4. Resolve the object before update/delete permission checks.
5. Deny direct update/delete access before form rendering, persistence, or delete execution.
6. Keep `can_update_object()` and `can_delete_object()` as row/workflow-state hooks, evaluated only after permission passes for UI composition.

### Phase E: Tests And Documentation

### Phase F: Deferred Follow-Up Register

Deferred items remain unchanged:

1. Bulk permission hooks are still the likely next gap after Phase D.
2. List/detail permission hooks remain deferred.
3. Field-sensitive permissions remain deferred.
4. Callable permission declarations remain deferred.
5. DDMS timeline GET/POST behavior remains downstream-owned.

## Compatibility Requirements

1. Default behavior must remain open when no permission hook or permission declaration is configured.
2. Existing `hidden_if` and `disabled_state` behavior must remain unchanged.
3. Existing `can_update_object()` and `can_delete_object()` behavior must remain valid.
4. Existing `inline_edit_requires_perm` behavior must remain valid unless explicitly deprecated later.
5. Existing primitive dictionary configuration must remain valid.
6. New affordance keys must be available through primitive dictionary configuration.
7. `PowerAction` and `PowerButton` should continue compiling to primitive dictionaries.
8. `PowerAction` and `PowerButton` must not expose permission behavior that the primitive dictionaries cannot express.
9. `permission` and `permission_check` must be mutually exclusive in both primitive dictionaries and `Power*` declarations.
10. Any backend denial should use an overridable response strategy so downstream apps can choose between `403`, login redirect, or custom handling.

## Documentation Requirements

Public docs should be very explicit about the layers:

1. Permission controls user capability.
2. Row-state hooks control object readiness or workflow applicability.
3. UI behavior hides or disables controls.
4. Backend enforcement is mandatory.
5. PowerCRUD enforces backend permissions only for endpoints it owns.
6. Extra action and extra button endpoints must enforce permissions downstream.
7. `permission` is for permission strings, while `permission_check` is for named view methods.
8. `permission_behavior` takes precedence over `hidden_if` and `disabled_state`; those row-state hooks still run only after permission passes or after permission is converted to a disabled affordance.
9. Built-in update/delete direct-route checks happen after object lookup and before form rendering, persistence, or delete execution.
10. DDMS-style timeline concerns are downstream-owned and not solved by PowerCRUD action affordances.

The docs should avoid implying that `hidden_if` is permission-specific. It is not. It may be, and often is, row-state specific.

## Open Questions

1. What is the exact response contract for backend denial: raise `PermissionDenied`, return `HttpResponseForbidden`, or call an overridable handler?
2. Should detail/list access be included in the first slice, or should the first slice focus on mutation affordances?

Settled direction:

1. Built-in Create, Edit, and Delete use explicit hooks and hide their UI affordance when the hook returns `False`.
2. `permission_behavior` is for custom action/button affordances, not for built-in Create, Edit, and Delete in the first design.
3. `permission` is a permission string checked through the always-present, overridable `has_power_permission()` resolver.
4. `permission_check` is the named-method alternative.
5. `permission` and `permission_check` are mutually exclusive; setting both should raise `ImproperlyConfigured`.
6. Permission behavior takes precedence over `hidden_if` and `disabled_state`.
7. Callable permission declarations are deferred; named methods are enough for the first design.
8. `permission_check` should use one signature everywhere: `permission_check(request, obj=None)`.
9. Operation-level permission is enough for the first slice; field-sensitive permission is deferred.
10. Bulk permission hooks are a likely follow-up, and viewer-accessible downstream views should disable bulk controls until those hooks exist.
11. Completed Phases A-C do not need rework based on the latest DDMS feedback.

## Initial Recommendation

The enhancement is worth doing, but it should be small and staged.

Recommended first slice, if one implementation branch is used:

1. Add permission metadata and UI behavior to primitive `extra_actions`.
2. Add matching permission metadata and UI behavior to `PowerAction`.
3. Add permission metadata and UI behavior to primitive `extra_buttons`.
4. Add matching permission metadata and UI behavior to `PowerButton`.
5. Add `has_power_permission(permission, request, obj=None)` as the central resolver.
6. Add `has_power_create_permission(request)` and use it for Create UI and backend create handling.
7. Add `has_power_update_permission(request, obj)` and compose it with `can_update_object()`.
8. Add `has_power_delete_permission(request, obj)` and compose it with `can_delete_object()`.
9. Add focused tests proving base API and `Power*` API parity, plus UI and backend behavior for built-in create/update/delete.

If that is too broad once implementation starts, split it into two smaller slices:

1. First add the central resolver plus permission-aware UI for primitive actions/buttons, `PowerAction`, `PowerButton`, and Create.
2. Then add backend-enforced built-in update/delete permission composition.

Defer until the first contract settles:

1. list/detail permission hooks
2. bulk operation permission hooks
3. field-sensitive bulk permissions
4. richer denial response customization
5. callable permission declarations

The first slice should prove the concept across the most visible gaps without trying to redesign every access-control edge in one pass.
