# Permission-Aware Affordances DDMS Review Summary

## Purpose

This is a standalone summary to paste into a DDMS-focused AI review.

Question for DDMS review:

Will this proposed PowerCRUD enhancement fit DDMS's permission and workflow needs, especially around viewer-style users, action suppression, and keeping permission separate from row/workflow state?

## Proposed PowerCRUD Change

PowerCRUD would add a narrow permission-aware affordance layer.

It would not become the downstream application's authorization system. DDMS services, custom endpoints, queryset scoping, and workflow rules would still enforce their own permissions and business rules.

The change is intended to make PowerCRUD-owned UI and endpoints more truthful:

1. Hide built-in Create when the user cannot create.
2. Hide built-in Edit/Delete when the user cannot perform those operations.
3. Keep row/workflow-state disable hooks separate from permission checks.
4. Add permission-aware affordance support to `extra_buttons` / `PowerButton`.
5. Add permission-aware affordance support to `extra_actions` / `PowerAction`.

## Layers To Keep Separate

The design depends on four separate layers:

1. Screen access: can the user open this PowerCRUD list/detail screen?
2. Operation permission: can the user perform this kind of operation at all?
3. Row/workflow state: is the operation valid for this object right now?
4. Backend enforcement: does the target endpoint or service reject unauthorized or invalid attempts?

DDMS feedback is especially needed on whether this separation matches how DDMS currently uses PowerCRUD.

## Built-In Create

PowerCRUD would provide a downstream override hook:

```python
def has_power_create_permission(self, request):
    return True
```

Default is open for backward compatibility.

If the hook returns `False`:

1. Hide the Create button.
2. Deny direct access to the PowerCRUD-owned create endpoint.

There is no first-design `permission_behavior` choice for built-in Create. Permission failure hides.

## Built-In Edit And Delete

PowerCRUD would provide downstream override hooks:

```python
def has_power_update_permission(self, request, obj):
    return True

def has_power_delete_permission(self, request, obj):
    return True
```

These are permission hooks.

Existing row-state hooks keep their current meaning:

```python
def can_update_object(self, obj, request):
    return True

def can_delete_object(self, obj, request):
    return True
```

The intended composition is:

1. If `has_power_update_permission()` returns `False`, hide Edit and deny direct update access.
2. If permission passes but `can_update_object()` returns `False`, disable Edit as a row/workflow-state failure.
3. If `has_power_delete_permission()` returns `False`, hide Delete and deny direct delete access.
4. If permission passes but `can_delete_object()` returns `False`, disable Delete as a row/workflow-state failure.

There is no first-design `permission_behavior` choice for built-in Edit/Delete. Permission failure hides.

## Extra Buttons And PowerButton

PowerCRUD's Base API remains the fundamental API. New keys should work in Base API `extra_buttons` dictionaries first:

```python
extra_buttons = [
    {
        "text": "Admin Review",
        "url_name": "cases:admin-review",
        "display_modal": True,
        "permission": "cases.manage_cases",
        "permission_behavior": "hide",
    }
]
```

The structured API should expose the same capability:

```python
extra_buttons = [
    PowerButton(
        text="Admin Review",
        url_name="cases:admin-review",
        display_modal=True,
        permission="cases.manage_cases",
        permission_behavior="hide",
    )
]
```

PowerCRUD would provide an always-present resolver:

```python
def has_power_permission(self, permission, request, obj=None):
    return request.user.has_perm(permission)
```

Default behavior treats `permission` as a Django permission string.

Downstream apps can override `has_power_permission()` if they use an app-specific permission service.

For operation-specific logic, use a named method instead:

```python
extra_buttons = [
    PowerButton(
        text="Admin Review",
        url_name="cases:admin-review",
        permission_check="can_use_admin_review",
    )
]

def can_use_admin_review(self, request, obj=None):
    return request.user.is_staff
```

`permission` and `permission_check` are mutually exclusive. If both are set, PowerCRUD should raise `ImproperlyConfigured`.

Use the same `permission_check(request, obj=None)` shape for toolbar buttons and row actions. Toolbar buttons call the method with `obj=None`; row actions pass the row object.

## Extra Actions And PowerAction

The same base-API-first rule applies to row actions.

Base API:

```python
extra_actions = [
    {
        "text": "Submit",
        "url_name": "cases:submit",
        "permission": "cases.submit_case",
        "permission_behavior": "hide",
        "disabled_state": "cannot_submit_case",
    }
]
```

Structured API:

```python
extra_actions = [
    PowerAction(
        text="Submit",
        url_name="cases:submit",
        permission="cases.submit_case",
        permission_behavior="hide",
        disabled_state="cannot_submit_case",
    )
]
```

Permission and row/workflow state remain separate:

```python
def cannot_submit_case(self, obj, request):
    if obj.status != "draft":
        return "Only draft cases can be submitted."
    return None
```

Evaluation order:

1. Evaluate `permission` or `permission_check`.
2. If permission fails and `permission_behavior` is `"hide"`, hide the action immediately.
3. If permission fails and `permission_behavior` is `"disable"`, disable the action with a permission reason.
4. If permission passes, evaluate `hidden_if`.
5. If not hidden, evaluate `disabled_state`.

Permission behavior takes precedence over `hidden_if` and `disabled_state`.

The target extra action endpoint remains downstream-owned. DDMS must still enforce permission and workflow validity in the endpoint/service.

## Expected DDMS Benefits

1. Viewer-style users can see appropriate PowerCRUD screens without seeing operations they cannot perform.
2. DDMS can stop treating row/workflow hooks as permission hooks.
3. Toolbar buttons get a first-class permission affordance instead of being assembled per request in ad hoc code.
4. Extra row actions can declare user capability separately from workflow eligibility.
5. Built-in Create/Edit/Delete UI can align with backend checks for PowerCRUD-owned endpoints.
6. Custom DDMS endpoints remain DDMS-owned and still enforce their own permissions.

## First Implementation Slice

Suggested first slice:

1. Add `permission`, `permission_check`, `permission_behavior`, and `permission_denied_reason` to Base API `extra_actions`.
2. Add the same fields to `PowerAction`.
3. Add the same fields to Base API `extra_buttons`.
4. Add the same fields to `PowerButton`.
5. Add the always-present, overridable `has_power_permission()` resolver.
6. Add `has_power_create_permission()` for Create UI and backend create handling.
7. Add `has_power_update_permission()` and compose it with `can_update_object()`.
8. Add `has_power_delete_permission()` and compose it with `can_delete_object()`.
9. Add tests proving Base API and `Power*` API parity.

Deferred:

1. list/detail permission hooks
2. bulk operation permission hooks
3. field-sensitive bulk permissions
4. callable permission declarations
5. richer backend denial customization

## DDMS Review Questions

1. Does hiding permission-denied Create/Edit/Delete match DDMS viewer-style UX?
2. Does `permission_check` as a named view method fit DDMS better than callable declarations?
3. Does this preserve DDMS's current use of `hidden_if` and `disabled_state` for row/workflow state?
4. Are toolbar buttons the biggest DDMS UI gap, or are built-in actions more urgent?
5. Are there DDMS endpoints where this proposal might create a false sense of backend protection?
6. Is operation-level permission enough for the first slice, or does DDMS need field-sensitive or workflow-sensitive permission immediately?
