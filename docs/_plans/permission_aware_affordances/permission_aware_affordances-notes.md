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

This gives downstream apps one place to map PowerCRUD declarations to their permission service. It also keeps the default behavior compatible with Django permission strings.

The resolver should not assume every project uses Django model permissions directly. DDMS may want to delegate to an app-specific permission service.

### Permission Metadata On Extra Actions And Buttons

Add optional declaration fields to `PowerAction` and `PowerButton`:

```python
permission=None
permission_behavior="hide"
permission_denied_reason=None
```

Primitive dictionaries should support the same keys, because helper declarations compile to primitive dictionaries and should not become more capable than the base API.

Compatibility rule:

1. If `permission` is omitted, behavior remains exactly as it is today.
2. Existing `hidden_if`, `disabled_state`, and selection behavior remain valid.
3. Permission evaluation happens before row-state disabled-state evaluation when the behavior is hide.
4. When permission behavior is disable, row-state and permission reasons need a deterministic precedence.

Recommended precedence:

1. Permission hide removes the control before other state is evaluated.
2. Permission disable disables the control before row-state disabled logic.
3. Row-state disabled reason can remain more specific only when permission passes.

That avoids showing business-state details to users who lack the operation permission.

### Built-In CRUD Permissions

PowerCRUD-owned endpoints should have permission hooks that apply to both UI affordances and backend handling.

Possible hooks:

```python
def has_power_list_permission(self, request):
    return True

def has_power_detail_permission(self, request, obj=None):
    return True

def has_power_create_permission(self, request):
    return True

def has_power_update_permission(self, request, obj):
    return True

def has_power_delete_permission(self, request, obj):
    return True
```

The default should be open for backward compatibility.

PowerCRUD should use these hooks in both places:

1. UI rendering: Create, View, Edit, Delete affordances.
2. Backend endpoints: list, detail, create, update, delete handlers.

For update and delete, these permission hooks should compose with existing row-state hooks:

1. `has_power_update_permission(request, obj)` answers whether the user can update this kind of object.
2. `can_update_object(obj, request)` answers whether this specific row is currently updateable.
3. Both must pass for backend mutation.
4. Permission failure should normally hide the UI affordance.
5. Row-state failure should normally disable the UI affordance with an optional reason.

### Bulk Permissions

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

PowerCRUD should enforce permission hooks for endpoints it owns:

1. list
2. detail
3. create
4. update
5. delete
6. inline edit
7. bulk update
8. bulk delete
9. list options endpoints if they become permission-sensitive
10. selection endpoints if they expose sensitive scope

For these surfaces, it is reasonable and useful for the same PowerCRUD permission policy to drive both UI and backend behavior.

### Downstream-Owned Custom Surfaces

PowerCRUD can only provide UI affordance support for downstream-owned custom endpoints:

1. `extra_actions`
2. `extra_buttons`

PowerCRUD can hide or disable the button.

The downstream app must still enforce the endpoint permission and business rule.

That distinction should be explicit in public docs so developers do not confuse a hidden button with authorization.

## Why This Is Useful

### Extra Actions

Current state:

1. Row-state hooks are good.
2. Permission checks must be repeated inside action-specific hooks or local helper methods.

Benefit:

1. Actions can declare user capability directly.
2. Row-state hooks remain focused on business state.
3. Downstream apps can centralize permission interpretation in one view-level resolver.

### Extra Buttons

Current state:

1. Toolbar buttons have no generic hide or disabled-state hook.
2. Selection-aware disabling exists but is not a permission model.

Benefit:

1. Permission-aware toolbar UI becomes first-class.
2. Downstream apps no longer need to conditionally assemble `extra_buttons` for common permission cases.
3. `PowerButton` reaches parity with `PowerAction` for operation availability.

### Regular Actions

Current state:

1. Built-in Edit and Delete have row-state disable hooks.
2. Built-in actions do not have an explicit permission layer.

Benefit:

1. PowerCRUD can separate "user may update" from "this row can be updated now".
2. UI and backend behavior for PowerCRUD-owned update/delete endpoints can align.
3. Existing row-state hooks keep their job.

### Regular Buttons

Current state:

1. Create is controlled indirectly through the presence of `create_view_url`.
2. There is no `can_create` or `has_power_create_permission` hook.

Benefit:

1. Create can be hidden for users without create permission.
2. Direct create endpoint access can be rejected consistently.
3. Downstream apps avoid the `create_view_url = None` workaround.

### UI Versus Backend Protection

Current state:

1. Some UI affordances can be disabled or hidden.
2. Backend protection is inconsistent across PowerCRUD-owned surfaces and custom downstream endpoints.

Benefit:

1. PowerCRUD-owned operations can enforce permissions in both UI and backend.
2. Custom downstream endpoints still remain downstream-owned.
3. Documentation can describe the responsibility split clearly.

## Compatibility Requirements

1. Default behavior must remain open when no permission hook or permission declaration is configured.
2. Existing `hidden_if` and `disabled_state` behavior must remain unchanged.
3. Existing `can_update_object()` and `can_delete_object()` behavior must remain valid.
4. Existing `inline_edit_requires_perm` behavior must remain valid unless explicitly deprecated later.
5. Existing primitive dictionary configuration must remain valid.
6. `PowerAction` and `PowerButton` should continue compiling to primitive dictionaries.
7. Any backend denial should use an overridable response strategy so downstream apps can choose between `403`, login redirect, or custom handling.

## Documentation Requirements

Public docs should be very explicit about the layers:

1. Permission controls user capability.
2. Row-state hooks control object readiness or workflow applicability.
3. UI behavior hides or disables controls.
4. Backend enforcement is mandatory.
5. PowerCRUD enforces backend permissions only for endpoints it owns.
6. Extra action and extra button endpoints must enforce permissions downstream.

The docs should avoid implying that `hidden_if` is permission-specific. It is not. It may be, and often is, row-state specific.

## Open Questions

1. Should built-in create/update/delete permissions use one generic resolver plus named operation strings, explicit methods, or both?
2. Should missing permission always hide by default, or should built-in Edit/Delete prefer disabled behavior for discoverability?
3. What is the exact response contract for backend denial: raise `PermissionDenied`, return `HttpResponseForbidden`, or call an overridable handler?
4. Should permission hooks check Django model permissions automatically by default, or should they only return `True` until the downstream view opts in?
5. Should `permission` accept only strings, or also callables?
6. Should `permission_behavior` be accepted on built-in CRUD operations, or only on `PowerAction` and `PowerButton`?
7. Should detail/list access be included in the first slice, or should the first slice focus on mutation affordances?
8. How should permission-denied reasons interact with row-state disabled reasons when both exist?
9. Should bulk update permission be field-sensitive, or is operation-level permission enough for the first slice?

## Initial Recommendation

The enhancement is worth doing, but it should be small and staged.

Recommended first slice, if one implementation branch is used:

1. Add permission metadata and UI behavior to primitive `extra_actions` and `PowerAction`.
2. Add permission metadata and UI behavior to primitive `extra_buttons` and `PowerButton`.
3. Add `has_power_permission(permission, request, obj=None)` as the central resolver.
4. Add `has_power_create_permission(request)` and use it for Create UI and backend create handling.
5. Add `has_power_update_permission(request, obj)` and compose it with `can_update_object()`.
6. Add `has_power_delete_permission(request, obj)` and compose it with `can_delete_object()`.
7. Add focused tests proving UI and backend behavior for built-in create/update/delete.

If that is too broad once implementation starts, split it into two smaller slices:

1. First add the central resolver plus permission-aware UI for `PowerAction`, `PowerButton`, and Create.
2. Then add backend-enforced built-in update/delete permission composition.

Defer until the first contract settles:

1. list/detail permission hooks
2. bulk operation permission hooks
3. field-sensitive bulk permissions
4. richer denial response customization
5. callable permission declarations

The first slice should prove the concept across the most visible gaps without trying to redesign every access-control edge in one pass.
