# Permission-Aware Affordances

Permission-aware affordances let a user open a PowerCRUD screen without seeing operations they are not allowed to use.

This is an affordance and PowerCRUD-owned endpoint feature. It is not a replacement for your application's authorization layer.

## The Four Layers

Keep these concerns separate:

1. Screen access: can the user open the list or detail view?
2. Operation permission: can the user perform this kind of operation at all?
3. Row or workflow state: is the operation valid for this object right now?
4. Backend enforcement: does the endpoint or service reject direct unauthorized attempts?

PowerCRUD helps with operation affordances. For PowerCRUD-owned create, detail, update, delete, inline-update, bulk update, and bulk delete endpoints, it also enforces the matching built-in permission hooks.

For custom `extra_actions` and `extra_buttons`, PowerCRUD can hide or disable the UI affordance. The endpoint is yours, so it must still enforce its own permission and business rules.

## Built-In Create, Detail, Edit, And Delete

Use the built-in hooks when the standard PowerCRUD-owned operations should be available only to some users.

```python
class CaseCRUDView(PowerCRUDMixin, CRUDView):
    def has_power_create_permission(self, request):
        return request.user.has_perm("cases.add_case")

    def has_power_detail_permission(self, request, obj):
        return request.user.has_perm("cases.view_case")

    def has_power_update_permission(self, request, obj):
        return request.user.has_perm("cases.change_case")

    def has_power_delete_permission(self, request, obj):
        return request.user.has_perm("cases.delete_case")
```

When these hooks return `False`:

- Create is removed from the list toolbar.
- Built-in Detail/View, Edit, and Delete are removed from row actions.
- Direct PowerCRUD create, detail, update, delete, and inline-update requests are rejected.

The default implementation returns `True`, so existing views remain open unless you override the hooks.

`has_power_detail_permission()` covers the built-in Detail/View row action and PowerCRUD-owned detail endpoint only. It is not a whole-screen list-access hook, and it does not authorize arbitrary linked fields or downstream custom detail-like endpoints.

You may also override the denial response:

```python
def handle_power_permission_denied(self, request, operation, obj=None):
    return HttpResponseForbidden(f"You cannot {operation} cases.")
```

## Built-In Bulk Update And Bulk Delete

Use the bulk hooks when PowerCRUD-owned bulk operations should be available only to some users.

```python
class CaseCRUDView(PowerCRUDMixin, CRUDView):
    def has_power_bulk_update_permission(self, request):
        return request.user.has_perm("cases.change_case")

    def has_power_bulk_delete_permission(self, request):
        return request.user.has_perm("cases.delete_case")
```

When these hooks return `False`:

- bulk update fields and Apply Changes are removed from the bulk modal
- the bulk delete section is removed from the bulk modal
- the bulk modal is denied entirely when neither bulk operation is permitted
- direct PowerCRUD bulk update and bulk delete submissions are rejected
- row selection controls are hidden when no permitted bulk operation or permitted selection-aware extra button needs them

The hooks are operation-level. `bulk_fields` remains the allow-list for which fields may be bulk edited.

## Extra Row Actions

Base API `extra_actions` dictionaries and `PowerAction` support the same permission fields.

??? example "Base API and Structured API"

    === "Base API"

        ```python
        extra_actions = [
            {
                "text": "Send for Approval",
                "url_name": "cases:send-for-approval",
                "permission_check": "can_send_for_approval",
                "permission_behavior": "hide",
                "disabled_state": "get_send_for_approval_disabled_state",
            },
        ]

        def can_send_for_approval(self, request, obj=None):
            return CasePermissionService.can_manage_cases(request.user)

        def get_send_for_approval_disabled_state(self, obj, request):
            if obj.status != "draft":
                return "Only draft cases can be sent for approval."
            return None
        ```

    === "Structured API"

        ```python
        PowerAction(
            text="Send for Approval",
            url_name="cases:send-for-approval",
            permission_check="can_send_for_approval",
            permission_behavior="hide",
            disabled_state="get_send_for_approval_disabled_state",
        )

        def can_send_for_approval(self, request, obj=None):
            return CasePermissionService.can_manage_cases(request.user)

        def get_send_for_approval_disabled_state(self, obj, request):
            if obj.status != "draft":
                return "Only draft cases can be sent for approval."
            return None
        ```

Permission is checked before `hidden_if` and `disabled_state`. This keeps capability checks separate from row or workflow state.

## Extra Toolbar Buttons

Base API `extra_buttons` dictionaries and `PowerButton` use the same permission fields.

??? example "Base API and Structured API"

    === "Base API"

        ```python
        extra_buttons = [
            {
                "text": "Selected Summary",
                "url_name": "cases:selected-summary",
                "uses_selection": True,
                "selection_min_count": 1,
                "selection_min_behavior": "disable",
                "selection_min_reason": "Select at least one case first.",
                "permission_check": "can_use_selected_summary",
                "permission_behavior": "hide",
            },
        ]

        def can_use_selected_summary(self, request, obj=None):
            return CasePermissionService.can_manage_cases(request.user)
        ```

    === "Structured API"

        ```python
        PowerButton(
            text="Selected Summary",
            url_name="cases:selected-summary",
            uses_selection=True,
            selection_min_count=1,
            selection_min_behavior="disable",
            selection_min_reason="Select at least one case first.",
            permission_check="can_use_selected_summary",
            permission_behavior="hide",
        )

        def can_use_selected_summary(self, request, obj=None):
            return CasePermissionService.can_manage_cases(request.user)
        ```

Permission is checked before selection-state disabling. If permission fails with the default hide behavior, the button is removed instead of showing a disabled selection prompt.

!!! tip "Permission fields"

    Use one of these per custom action or button:

    - `permission`: a Django permission string resolved by `has_power_permission(permission, request, obj=None)`.
    - `permission_check`: a named view method with signature `permission_check(request, obj=None)`.

    Do not set both on the same declaration.

    Optional behavior fields:

    - `permission_behavior`: `"hide"` or `"disable"`. Defaults to `"hide"`.
    - `permission_denied_reason`: tooltip text used only when `permission_behavior = "disable"`.

    The default `has_power_permission(...)` delegates to `request.user.has_perm(permission)`. Override it if your project uses a different permission service.

## Hide Versus Disable

Use hide for permission failure:

- the user cannot create this model
- the user cannot edit or delete this row type
- the user cannot run an approval operation at all

Use disable for row or workflow state:

- the user can approve cases, but this case is not ready
- the user can edit, but this row is locked
- the user can run a selected-row action, but no rows are selected

This is why `hidden_if`, `disabled_state`, `can_update_object()`, and `can_delete_object()` remain row or workflow-state hooks. They should compose with permission checks, not replace them.

## Backend Responsibility

PowerCRUD enforces permission hooks only for operations it owns:

- standard create
- standard detail
- standard update
- standard delete
- inline update
- bulk update
- bulk delete

Custom `extra_actions` and `extra_buttons` call downstream endpoints. Hiding or disabling those controls makes the UI truthful, but the endpoint must still enforce permission directly.

```python
@permission_required("cases.send_for_approval")
def send_for_approval(request, pk):
    ...
```

or:

```python
def send_for_approval(request, pk):
    if not CasePermissionService.can_manage_cases(request.user):
        return HttpResponseForbidden()
    ...
```

## Sample App Demo

The sample app includes viewer and manager users in the runtime login menu.

On `/sample/bigbook/`:

- viewer users can open the list but do not see built-in Create, Detail/View, Edit, Delete, the permission-hidden row action, or the permission-hidden toolbar button
- manager users see those affordances
- row and selection state can still disable controls after permission passes

The `/sample/powerfield-book/` view mirrors the same behavior through `PowerAction` and `PowerButton`.
