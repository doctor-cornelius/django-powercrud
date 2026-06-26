# Hooks Reference

This page is the canonical reference for PowerCRUD's main public override points. Use the guides for workflow examples and setup, and use this page when you want to answer practical questions such as "where do I override this?" or "which hook should I use for this behavior?".

This is a curated reference for the public hooks most downstream projects are expected to use. It does not try to inventory every internal extension point.

If you want step-by-step walkthroughs rather than contracts, start with the advanced guides:

- [Persistence Hooks](../guides/advanced/persistence_hooks_sync.md)
- [Async Bulk Persistence](../guides/advanced/persistence_hooks_async_bulk.md)

??? info "Hook quick reference"

    | Hook | Purpose |
    |------|---------|
    | `get_queryset()` | Use this when you want to change which records the view works with in the first place, such as scoping rows to the current user, tenant, or workflow state. |
    | `get_context_data()` | Use this only when the template needs extra data that does not already come from PowerCRUD, such as a help panel, extra summary values, or feature flags for custom UI. |
    | `get_list_cell_tooltip()` | Deprecated generic hook for legacy `list_cell_tooltip_fields = [...]` declarations. Prefer field-specific hooks through `list_cell_tooltip_fields = {"field": "hook"}`. |
    | `get_list_cell_link()` | Use this when a rendered list cell should navigate somewhere conditionally, or when the narrow declarative `link_fields` config is not expressive enough. |
    | `get_filter_queryset_for_field()` | Use this when a filter-form dropdown should not show every possible related record, for example when you only want active owners, visible categories, or tenant-scoped choices. |
    | `get_filter_favourite_user()` | Use this when initial saved-favourite list context should read favourites for a different user than `request.user`. |
    | `get_field_queryset_dependencies()` | Use this when you want to refine, filter, or inspect the declarative `field_queryset_dependencies` metadata before PowerCRUD applies it to forms or derives inline dependency wiring. |
    | `persist_single_object()` | Use this when you want PowerCRUD to keep form validation and response handling, but you want the actual save to go through your own application service or domain write logic. |
    | `persist_bulk_update()` | Use this when you want PowerCRUD to keep the bulk UI and normalized payload handling, but you want the actual multi-row update to go through your own bulk service or orchestration code. |
    | `get_bulk_choices_for_field()` | Use this when a bulk-edit form dropdown should offer a narrower or more carefully ordered set of choices than the default related queryset. |
    | `get_bulk_selection_key_suffix()` | Use this when PowerCRUD's default bulk selection storage is too broad and you want selections kept separate by user, tenant, tab, or another context value. |
    | `has_power_permission()` | Resolve `permission="app.codename"` declarations on custom actions and buttons. |
    | `has_power_create_permission()` | Decide whether the request may use PowerCRUD-owned create handling. |
    | `has_power_detail_permission()` | Decide whether the request may use PowerCRUD-owned detail handling for a row. |
    | `has_power_update_permission()` | Decide whether the request may use PowerCRUD-owned update handling for a row. |
    | `has_power_delete_permission()` | Decide whether the request may use PowerCRUD-owned delete handling for a row. |
    | `has_power_bulk_update_permission()` | Decide whether the request may use PowerCRUD-owned bulk update handling. |
    | `has_power_bulk_delete_permission()` | Decide whether the request may use PowerCRUD-owned bulk delete handling. |
    | `handle_power_permission_denied()` | Customize the response for denied PowerCRUD-owned create, detail, update, delete, inline-update, bulk update, or bulk delete requests. |
    | `can_update_object()` | Use this when some rows should keep the built-in Edit action visible but disabled, for example workflow-owned rows, canonical records, or objects that should stay read-only on a per-row basis. |
    | `get_update_disabled_reason()` | Use this with `can_update_object()` when you want disabled Edit and inline affordances to explain why the row cannot be edited. |
    | `can_delete_object()` | Use this when some rows should keep the built-in Delete action visible but disabled, for example canonical records, workflow-owned rows, or rows that should remain undeletable except to privileged users. |
    | `get_delete_disabled_reason()` | Use this with `can_delete_object()` when you want the disabled built-in Delete action to explain why the row cannot be deleted. |
    | `inline_edit_allowed` | Use this when some rows should stay read-only inline even though inline editing is enabled for the view overall, for example archived or workflow-locked records. |
    | `is_inline_row_locked()` | Use this when your project has custom lock rules and the default async-conflict check is not the whole story. |
    | `get_inline_lock_details()` | Use this when the UI needs richer information about why a row is locked, such as the task, user, or message associated with the lock. |
    | `async_task_lifecycle()` | Use this when you want async tasks to trigger project-specific side effects such as dashboard rows, audit entries, notifications, or cleanup logic. |
    | `BulkUpdatePersistenceBackend.persist_bulk_update()` | Use this when async bulk update needs to go through app-level write orchestration without depending on a live CRUD view instance. |
    | `resolve_bulk_update_persistence_backend()` | Resolve the configured import path into a concrete bulk update persistence backend instance. |
    | `AsyncManager.resolve_manager()` | This lets workers and completion hooks find the same manager class your launch site configured, so custom lifecycle behavior stays consistent outside the request. |

---

## Adopting persistence hooks

If your project already customizes PowerCRUD writes, use these hooks to move away from internal save-path overrides.

Migration guide:

- If you currently override `form_valid()` only to control the write, move that write logic into `persist_single_object()`.
- If you currently override inline save internals only to control the write, move that write logic into the same `persist_single_object()` hook.
- If you currently override sync bulk internals such as `bulk_edit_process_post()` or `_perform_bulk_update()` only to route updates through app code, move that write logic into `persist_bulk_update()`.
- If you currently customize async bulk update by patching worker code or forking `powercrud.tasks.bulk_update_task`, move that write logic into a `BulkUpdatePersistenceBackend` and configure `bulk_update_persistence_backend_path`.

Keep the older override only when it is doing something broader than persistence, such as:

- changing validation rules
- changing request/response flow
- changing template context or UI behavior

Upgrade notes:

- `persist_single_object()` covers normal create/update forms and inline row update, but not delete flows.
- `persist_bulk_update()` is the sync bulk-update hook only. Bulk delete remains separate.
- `BulkUpdatePersistenceBackend` is the async bulk-update hook for writes. It is not a general-purpose `AsyncManager` save hook.
- When `bulk_update_persistence_backend_path` is configured, the default sync bulk-update path also uses that same backend so sync and async bulk update can share one write path.
- Live CRUD view instances are not passed into async workers.
- Built-in single delete now redisplays cleanly when `model.delete()` raises `ValidationError`, but delete still has no persistence hook equivalent to `persist_single_object()`.

---

## View lifecycle and queryset hooks

### `get_queryset()`

- Purpose: Use this when you want to change which records the view works with in the first place, such as scoping rows to the current user, tenant, or workflow state.
- When it is called: During list rendering and any flow that depends on the view queryset.
- Signature: `def get_queryset(self)`
- Default behavior: Calls the parent `get_queryset()` first, so the usual Neapolitan behavior still applies. That means an explicit class `queryset` is still respected, otherwise PowerCRUD falls back to `model._default_manager.all()`. PowerCRUD then applies sort handling and adds a stable secondary `pk` sort.
- Return contract: A queryset for the current view.
- Important note: If you override this, call `super().get_queryset()` unless you intentionally want to replace PowerCRUD's default sort behavior too.
- Related docs: [Setup & Core CRUD basics](../guides/setup_core_crud.md), [Customisation tips](../guides/advanced/customisation_tips.md)

### `get_context_data()`

- Purpose: Use this only when the template needs extra data that does not already come from PowerCRUD, such as a help panel, extra summary values, or feature flags for custom UI.
- When it is called: During template rendering for the list, detail, and form flows.
- Signature: `def get_context_data(self, **kwargs)`
- Default behavior: Extends the parent context; other PowerCRUD mixins also add their own context here, such as `form_display_items` and bulk-selection metadata.
- Return contract: A `dict` for template rendering.
- Important note: If you are not customizing templates or adding custom page data, you can ignore this hook.
- Short example:

    ```python
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["help_panel_title"] = "Project tools"
        return context
    ```

- Related docs: [Forms](../guides/forms.md), [Customisation tips](../guides/advanced/customisation_tips.md)

### `get_list_cell_tooltip()`

- Purpose: Legacy generic hook for semantic tooltip text that comes from the current row.
- When it is called: During list-row rendering, but only when `list_cell_tooltip_fields` uses the deprecated list form.
- Signature: `def get_list_cell_tooltip(self, obj, field_name, *, is_property, request=None)`
- Default behavior: Returns `None`, so no semantic list-cell tooltip is shown.
- Key arguments:
    - `obj`: The current row object.
    - `field_name`: The rendered field or property name for the current cell.
    - `is_property`: `True` when the cell comes from `properties`, otherwise `False`.
    - `request`: The current request when available.
- Return contract: A plain string tooltip, or `None` when no semantic tooltip should be shown for that cell.
- Important note: Prefer `list_cell_tooltip_fields = {"field": "get_field_tooltip"}` with field-specific hooks. The list form shown below is deprecated and targeted for removal before v1.0.
- Important note: PowerCRUD only calls this hook for configured names that are actually rendered in the list. Configured names not present in the current list are ignored silently.
- Important note: Semantic list-cell tooltips take precedence over the fallback overflow tooltip for the same cell, but existing blocked-inline tooltip states still win when the row is not editable inline.
- Important note: Returned text may contain newline characters. PowerCRUD preserves those as multiple displayed lines for hook-backed semantic list-cell tooltips only.
- Deprecated example:

    !!! warning "Deprecated list form"

        ```python
        list_cell_tooltip_fields = ["status", "has_invoice"]

        def get_list_cell_tooltip(self, obj, field_name, *, is_property, request=None):
            if field_name == "status":
                return obj.status_explanation
            if field_name == "has_invoice":
                return "Invoice attached" if obj.has_invoice else "Invoice missing"
            return None
        ```

- Related docs: [Setup & Core CRUD basics](../guides/setup_core_crud.md), [Deprecations](deprecations.md), [Sample app overview](sample_app.md)

### `get_list_cell_link()`

- Purpose: Use this when a rendered list cell should navigate somewhere conditionally, or when the narrow declarative `link_fields` config is not expressive enough.
- When it is called: During list-row rendering for non-inline-editable cells.
- Signature: `def get_list_cell_link(self, obj, field_name, value, *, is_property, request=None)`
- Default behavior: Returns `None`, so PowerCRUD falls back to `link_fields` when configured.
- Key arguments:
    - `obj`: The current row object.
    - `field_name`: The rendered field or property name for the current cell.
    - `value`: The already-resolved display value for the cell.
    - `is_property`: `True` when the cell comes from `properties`, otherwise `False`.
    - `request`: The current request when available.
- Return contract:
    - return a dict with at least `url` to link that cell
    - return `None` to allow declarative `link_fields` fallback
    - return `False` to suppress declarative `link_fields` for that cell
- Supported dict keys:
    - `url` (required)
    - `open_in`, `title`, `rel`, `classes`, `modal_box_classes` (optional)
- Important note: Inline-editable cells are never linked. Inline click-to-edit always wins, even if the hook or `link_fields` would otherwise provide a link.
- Important note: This hook can override or suppress declarative config row by row. That overlap is intentional and does not generate warnings.
- Important note: Omitted `open_in` values use the view's optional `list_cell_link_default_open_in`. If the view omits that option too, PowerCRUD assumes `"new"`. Use `"current"` for a same-page anchor or `"modal"` for the normal PowerCRUD modal flow. If modal support is off, PowerCRUD keeps the link as a normal anchor.
- Important note: `modal_box_classes` is only used with `open_in = "modal"`. It replaces the shared modal box classes for that clicked cell, so keep the default viewport-height classes when you only want to change width.
- Short example:

    ```python
    link_fields = {
        "owner": "crm:owner-detail",
    }

    def get_list_cell_link(self, obj, field_name, value, *, is_property, request=None):
        if field_name == "status" and obj.status_report_url:
            return {
                "url": obj.status_report_url,
                "title": "Open external status report",
                "open_in": "new",
            }
        if field_name == "reference_code":
            return {
                "url": self.safe_reverse("projects:project-detail", kwargs={"pk": obj.pk}),
                "open_in": "modal",
                "modal_box_classes": (
                    "modal-box flex max-h-[calc(100dvh-2rem)] "
                    "w-11/12 max-w-5xl flex-col"
                ),
            }
        if field_name == "owner" and request and not request.user.has_perm("crm.view_owner"):
            return False
        return None
    ```

- Related docs: [Setup & Core CRUD basics](../guides/setup_core_crud.md), [Configuration options](./config_options.md)

### `get_filter_queryset_for_field()`

- Purpose: Use this when a filter-form dropdown should not show every possible related record, for example when you only want active owners, visible categories, or tenant-scoped choices.
- When it is called: While building the filter form dropdown choices for related fields in `filterset_fields`.
- Signature: `def get_filter_queryset_for_field(self, field_name, model_field)`
- Default behavior: Starts from the related model queryset, applies any configured filter rules, then applies dropdown ordering.
- Return contract: A queryset of allowed choices for the filter field.
- Important note: This affects filter UI dropdowns, not edit-form dropdowns and not bulk-edit dropdowns.
- Short example:

    ```python
    def get_filter_queryset_for_field(self, field_name, model_field):
        queryset = super().get_filter_queryset_for_field(field_name, model_field)
        if field_name == "owner":
            return queryset.filter(active=True)
        return queryset
    ```

- Related docs: [Forms](../guides/forms.md), [Customisation tips](../guides/advanced/customisation_tips.md)

### `get_filter_favourite_user()`

- Purpose: Choose the user whose saved favourites should be loaded while rendering a PowerCRUD list view.
- When it is called: During list context building when the optional favourites contrib app is enabled.
- Signature: `def get_filter_favourite_user(self, request)`
- Default behavior: Delegates to the package-level saved-favourite user resolver, which uses `request.user` unless `POWERCRUD_SETTINGS["FILTER_FAVOURITE_USER_RESOLVER"]` is configured.
- Return contract: A Django user object, or a falsey/anonymous value when favourites should behave as unavailable for management.
- Important note: This view hook affects the CRUDView render path. The save, apply, update, and delete endpoints are shared function views, so use `FILTER_FAVOURITE_USER_RESOLVER` when custom ownership must apply end to end.
- Related docs: [Saved Favourites](../guides/advanced/filter_favourites.md#ownership-resolver), [Configuration options](./config_options.md#settings-configuration)

### `get_field_queryset_dependencies()`

- Purpose: Use this when you want to refine, filter, or inspect the declarative `field_queryset_dependencies` metadata before PowerCRUD applies it to forms or derives inline dependency wiring.
- When it is called: While finalizing regular forms and inline forms, and while deriving inline dependent-field metadata.
- Signature: `def get_field_queryset_dependencies(self, *, available_fields=None, warn_on_unavailable=True)`
- Default behavior: Normalizes the configured `field_queryset_dependencies`, drops unavailable child/parent fields, validates `filter_by` mappings, and preserves only usable static/dynamic rules.
- Return contract: A dict keyed by child field name, with normalized dependency metadata.
- Important note: This is the shared config path behind regular form queryset scoping and inline dependent-field refreshes. Static queryset rules from the same config are also reused by bulk edit dropdowns, but dynamic parent/child rules are not.
- Related docs: [Forms](../guides/forms.md#dependent-form-fields), [Configuration options](./config_options.md#dependent-queryset-scoping)

---

## Persistence hooks

### `persist_single_object()`

- Purpose: Use this when you want PowerCRUD to keep form validation and response handling, but you want the actual save to go through your own application service or domain write logic.
- When it is called: After validation succeeds for the standard form save path and the inline row save path.
- Signature: `def persist_single_object(self, *, form, mode, instance=None)`
- Key arguments:
    - `form`: The validated Django form.
    - `mode`: Currently `"form"` or `"inline"`.
    - `instance`: The bound object reference supplied by the caller.
- Default behavior: Calls `form.save()`.
- Return contract: The saved model instance. PowerCRUD stores it on `self.object`.
- Important note: If your override bypasses `form.save()`, your override owns any required `form.save_m2m()` handling.
- Short example:

    ```python
    def persist_single_object(self, *, form, mode, instance=None):
        book = form.save(commit=False)
        book = BookWriteService().save(book=book, mode=mode)
        form.instance = book
        form.save_m2m()
        return book
    ```

- Related docs: [Forms](../guides/forms.md#persisting-validated-standard-forms), [Inline editing](../guides/inline_editing.md#persisting-validated-inline-rows), [Customisation tips](../guides/advanced/customisation_tips.md)

### `persist_bulk_update()`

- Purpose: Use this when you want PowerCRUD to keep the bulk UI and normalized payload handling, but you want the actual multi-row update to go through your own bulk service or orchestration code.
- When it is called: After PowerCRUD has validated the bulk operation request and normalized the sync bulk payload.
- Signature: `def persist_bulk_update(self, *, queryset, fields_to_update, field_data, progress_callback=None)`
- Key arguments:
    - `queryset`: The objects selected for update.
    - `fields_to_update`: The normalized list of chosen bulk-edit fields.
    - `field_data`: The normalized field payload built from the request.
    - `progress_callback`: Optional callback used by callers that want per-record progress updates.
- Default behavior: Delegates to PowerCRUD's standard sync bulk update implementation.
- Return contract: A result dict with `success`, `success_records`, and `errors`.
    - `success`: `True` when the bulk operation completed without handled errors.
    - `success_records`: Count of updated rows on success. In the built-in transactional path this is `0` when validation fails, because the batch is rolled back.
    - `errors`: A list of `(label, messages)` tuples. `label` is a generic scope such as a field name or `"general"`, and `messages` is a list of user-displayable strings.
- Important note: This is still the sync view hook. Async bulk update uses a worker-safe backend contract instead. If `bulk_update_persistence_backend_path` is configured and you do not override this hook yourself, the default sync implementation delegates to that same backend so sync and async can share one write path.
- Important note: When `errors` is non-empty, PowerCRUD re-renders the bulk edit modal with those handled errors instead of treating the result as a server failure.
- Short example:

    ```python
    def persist_bulk_update(
        self,
        *,
        queryset,
        fields_to_update,
        field_data,
        progress_callback=None,
    ):
        return ProjectBulkUpdateService().apply(
            queryset=queryset,
            fields_to_update=fields_to_update,
            field_data=field_data,
        )
    ```

- Handled validation-error example:

    ```python
    def persist_bulk_update(
        self,
        *,
        queryset,
        fields_to_update,
        field_data,
        progress_callback=None,
    ):
        errors = [("status", ["Closed records cannot be bulk-reopened."])]
        return {
            "success": False,
            "success_records": 0,
            "errors": errors,
        }
    ```

- Related docs: [Bulk editing (synchronous)](../guides/bulk_edit_sync.md#routing-sync-bulk-updates-through-one-hook), [Customisation tips](../guides/advanced/customisation_tips.md)

---

## Bulk selection and bulk form hooks

### `get_bulk_choices_for_field()`

- Purpose: Use this when a bulk-edit form dropdown should offer a narrower or more carefully ordered set of choices than the default related queryset.
- When it is called: While building the bulk-edit form dropdown choices for related fields.
- Signature: `def get_bulk_choices_for_field(self, field_name, field)`
- Default behavior: Starts from all related objects, applies declarative static queryset rules for the field, then applies `order_by` metadata from `field_queryset_dependencies` or falls back to dropdown sort config.
- Return contract: A queryset of choices, or `None` when the field is not relation-backed.
- Important note: Yes, this relates to `field_queryset_dependencies`, but only partially. Bulk edit reuses `static_filters` and `order_by` from that config. It does not use `depends_on` and `filter_by`, because a bulk edit operation does not have one current parent form value to drive a child queryset.
- Short example:

    ```python
    def get_bulk_choices_for_field(self, field_name, field):
        queryset = super().get_bulk_choices_for_field(field_name, field)
        if field_name == "owner" and queryset is not None:
            return queryset.filter(active=True)
        return queryset
    ```

- Related docs: [Bulk editing (synchronous)](../guides/bulk_edit_sync.md#dropdowns-choices), [Customisation tips](../guides/advanced/customisation_tips.md)

### `get_bulk_selection_key_suffix()`

- Purpose: Use this when PowerCRUD's default bulk selection storage is too broad and you want selections kept separate by user, tenant, tab, or another context value.
- When it is called: Whenever PowerCRUD reads or writes the session-backed bulk selection key.
- Signature: `def get_bulk_selection_key_suffix(self) -> str`
- Default behavior: Returns an empty string.
- Return contract: A string suffix appended to the session storage key.
- Short example:

    ```python
    def get_bulk_selection_key_suffix(self):
        return f"user_{self.request.user.pk}"
    ```

- Related docs: [Bulk editing (synchronous)](../guides/bulk_edit_sync.md#4-selection-persistence), [Customisation tips](../guides/advanced/customisation_tips.md)

---

## Permission hooks

### `has_power_permission()`

- Purpose: Resolve `permission="app.codename"` declarations on `extra_actions`, `PowerAction`, `extra_buttons`, and `PowerButton`.
- When it is called: During row-action and toolbar-button rendering when a declaration uses `permission`.
- Signature: `def has_power_permission(self, permission, request, obj=None)`
- Default behavior: Calls `request.user.has_perm(permission)` when a user is available.
- Return contract: Truthy allows the affordance; falsy applies the declaration's permission behavior.
- Important note: `obj` is the row object for row actions and `None` for toolbar buttons.
- Related docs: [Permission-Aware Affordances](../guides/advanced/permission_aware_affordances.md), [PowerAction and PowerButton Reference](poweractions.md)

### `has_power_create_permission()`

- Purpose: Decide whether the request may use PowerCRUD-owned create handling.
- When it is called: While building list context for the Create affordance, before rendering the create form, and before processing create submissions.
- Signature: `def has_power_create_permission(self, request)`
- Default behavior: Returns `True`.
- Return contract: Truthy allows Create; falsy hides Create and rejects direct PowerCRUD create requests.
- Related docs: [Permission-Aware Affordances](../guides/advanced/permission_aware_affordances.md)

### `has_power_detail_permission()`

- Purpose: Decide whether the request may use PowerCRUD-owned detail handling for a row.
- When it is called: During built-in Detail/View rendering and after object resolution before rendering the PowerCRUD detail endpoint.
- Signature: `def has_power_detail_permission(self, request, obj)`
- Default behavior: Returns `True`.
- Return contract: Truthy allows Detail/View; falsy hides built-in Detail/View and rejects direct PowerCRUD detail requests.
- Important note: This is a standard operation hook, not whole-screen list access and not authorization for arbitrary linked fields or custom detail-like endpoints.
- Related docs: [Permission-Aware Affordances](../guides/advanced/permission_aware_affordances.md)

### `has_power_update_permission()`

- Purpose: Decide whether the request may use PowerCRUD-owned update handling for a row.
- When it is called: During built-in Edit rendering, before rendering or processing update forms, and before inline update rendering or saving.
- Signature: `def has_power_update_permission(self, request, obj)`
- Default behavior: Returns `True`.
- Return contract: Truthy allows update to continue into row-state checks; falsy hides built-in Edit and rejects direct PowerCRUD update and inline-update requests.
- Important note: Use `can_update_object()` for row or workflow state after permission passes.
- Related docs: [Permission-Aware Affordances](../guides/advanced/permission_aware_affordances.md), [Inline editing](../guides/inline_editing.md)

### `has_power_delete_permission()`

- Purpose: Decide whether the request may use PowerCRUD-owned delete handling for a row.
- When it is called: During built-in Delete rendering, before rendering delete confirmation, and before delete execution.
- Signature: `def has_power_delete_permission(self, request, obj)`
- Default behavior: Returns `True`.
- Return contract: Truthy allows delete to continue into row-state checks; falsy hides built-in Delete and rejects direct PowerCRUD delete requests.
- Important note: Use `can_delete_object()` for row or workflow state after permission passes.
- Related docs: [Permission-Aware Affordances](../guides/advanced/permission_aware_affordances.md)

### `has_power_bulk_update_permission()`

- Purpose: Decide whether the request may use PowerCRUD-owned bulk update handling.
- When it is called: While building list selection controls, before rendering the bulk modal, and before processing bulk update submissions.
- Signature: `def has_power_bulk_update_permission(self, request)`
- Default behavior: Returns `True`.
- Return contract: Truthy allows configured bulk update; falsy hides bulk update fields and rejects direct PowerCRUD bulk update submissions.
- Important note: `bulk_fields` remains the configured field allow-list. Use this hook for operation permission, not field-sensitive permission.
- Related docs: [Permission-Aware Affordances](../guides/advanced/permission_aware_affordances.md), [Bulk editing (synchronous)](../guides/bulk_edit_sync.md)

### `has_power_bulk_delete_permission()`

- Purpose: Decide whether the request may use PowerCRUD-owned bulk delete handling.
- When it is called: While building list selection controls, before rendering the bulk modal, and before processing bulk delete submissions.
- Signature: `def has_power_bulk_delete_permission(self, request)`
- Default behavior: Returns `True`.
- Return contract: Truthy allows configured bulk delete; falsy hides bulk delete controls and rejects direct PowerCRUD bulk delete submissions.
- Related docs: [Permission-Aware Affordances](../guides/advanced/permission_aware_affordances.md), [Bulk editing (synchronous)](../guides/bulk_edit_sync.md)

### `handle_power_permission_denied()`

- Purpose: Customize the response returned when a PowerCRUD-owned operation is denied by one of the built-in permission hooks.
- When it is called: For denied direct create, detail, update, delete, inline-update, bulk update, and bulk delete requests.
- Signature: `def handle_power_permission_denied(self, request, operation, obj=None)`
- Default behavior: Returns `HttpResponseForbidden(f"{operation} is not permitted.")`.
- Return contract: A Django response.
- Related docs: [Permission-Aware Affordances](../guides/advanced/permission_aware_affordances.md)

## Standard action guard hooks

### `can_update_object()`

- Purpose: Use this when permitted users should keep the built-in Edit action visible but disabled for row or workflow-state reasons.
- When it is called: During standard row-action rendering for the built-in Edit action, and while evaluating whether a row may enter inline edit mode.
- Signature: `def can_update_object(self, obj, request)`
- Default behavior: Returns `True`, so built-in Edit and inline editing remain available unless a downstream override blocks the row.
- Return contract: Truthy to allow row updates, falsy to disable the built-in Edit action and block inline editing for that row.
- Important note: This is the broad row-level update policy hook. It does not replace `inline_edit_fields`, which still controls which fields are inline-editable on the screen, and it does not replace `inline_edit_allowed()`, which remains available as an extra inline-only restriction.
- Short example:

    ```python
    def can_update_object(self, obj, request):
        return not obj.is_workflow_owned
    ```

- Related docs: [Inline editing hooks](#inline-editing-hooks), [Sample app overview](sample_app.md)

### `get_update_disabled_reason()`

- Purpose: Use this with `can_update_object()` when you want disabled Edit and inline affordances to explain why the row cannot be edited.
- When it is called: During standard row-action rendering, and while preparing inline blocked-row affordances when `can_update_object()` disables the row.
- Signature: `def get_update_disabled_reason(self, obj, request)`
- Default behavior: Returns `None`.
- Return contract: A plain string tooltip, or `None` when no explanation should be shown.
- Important note: Existing lock-based action blocking still takes precedence when a row is already blocked by PowerCRUD's lock metadata.
- Short example:

    ```python
    def get_update_disabled_reason(self, obj, request):
        if not self.can_update_object(obj, request):
            return "Workflow-owned rows cannot be edited."
        return None
    ```

- Related docs: [Sample app overview](sample_app.md)

### `can_delete_object()`

- Purpose: Use this when permitted users should keep the built-in Delete action visible but disabled for row or workflow-state reasons.
- When it is called: During standard row-action rendering for the built-in Delete action.
- Signature: `def can_delete_object(self, obj, request)`
- Default behavior: Returns `True`, so the built-in Delete action remains enabled unless a downstream override blocks it.
- Return contract: Truthy to allow the built-in Delete action, falsy to render it disabled.
- Important note: This controls the pre-click UI affordance only. It does not replace server-side protection. If `delete()` still raises `ValidationError`, PowerCRUD's handled single-delete refusal flow remains the safety net.
- Short example:

    ```python
    def can_delete_object(self, obj, request):
        return not obj.is_canonical
    ```

- Related docs: [Customisation tips](../guides/advanced/customisation_tips.md), [Sample app overview](sample_app.md)

### `get_delete_disabled_reason()`

- Purpose: Use this with `can_delete_object()` when you want the disabled built-in Delete action to explain why the row cannot be deleted.
- When it is called: During standard row-action rendering, only when the built-in Delete action is disabled by `can_delete_object()`.
- Signature: `def get_delete_disabled_reason(self, obj, request)`
- Default behavior: Returns `None`.
- Return contract: A plain string tooltip, or `None` when no explanation should be shown.
- Important note: Existing lock-based action blocking still takes precedence when a row is already blocked by PowerCRUD's lock metadata.
- Short example:

    ```python
    def get_delete_disabled_reason(self, obj, request):
        if not self.can_delete_object(obj, request):
            return "Canonical records cannot be deleted."
        return None
    ```

- Related docs: [Sample app overview](sample_app.md)

---

## Inline editing hooks

### `inline_edit_allowed`

- Purpose: Use this when some rows should stay read-only inline even though inline editing is enabled for the view overall, for example archived or workflow-locked records.
- When it is called: During inline row rendering and again before accepting an inline save.
- Signature: `inline_edit_allowed(obj, request)`
- Default behavior: If unset, rows follow the standard inline permission and lock checks only.
- Return contract: Truthy to allow inline editing for that row, falsy to block it.
- Important note: This is an inline-only restriction layer. It does not replace `can_update_object()`, which is the broader row-level update policy hook used by both the built-in Edit action and inline editing.
- Short example:

    ```python
    def inline_edit_allowed(obj, request):
        return obj.status != "archived"
    ```

- Related docs: [Inline editing](../guides/inline_editing.md#3-respect-locks-and-permissions), [Configuration options](./config_options.md)

### `is_inline_row_locked()`

- Purpose: Use this when your project has custom lock rules and the default async-conflict check is not the whole story.
- When it is called: While evaluating whether a row can enter or remain in inline edit mode.
- Signature: `def is_inline_row_locked(self, obj) -> bool`
- Default behavior: Uses async conflict-checking helpers when available and returns `False` otherwise.
- Return contract: `True` when the row should be treated as locked.
- Related docs: [Inline editing](../guides/inline_editing.md#3-respect-locks-and-permissions), [Async architecture & reference](./async.md)

### `get_inline_lock_details()`

- Purpose: Use this when the UI needs richer information about why a row is locked, such as the task, user, or message associated with the lock.
- When it is called: When PowerCRUD builds row payloads or lock feedback for inline editing.
- Signature: `def get_inline_lock_details(self, obj) -> dict[str, Any]`
- Default behavior: Returns metadata derived from the async manager cache when available, otherwise an empty dict.
- Return contract: A dict describing the current lock state for the row.
- Related docs: [Inline editing](../guides/inline_editing.md#3-respect-locks-and-permissions), [Async architecture & reference](./async.md)

Inline row persistence itself does not use a separate hook. It routes through [`persist_single_object()`](#persist_single_object).

Inline dependent-field refreshes also do not use a separate inline-only hook. Declare the dependency once in `field_queryset_dependencies`; PowerCRUD applies that rule to regular forms and derives the inline dependency wiring automatically through [`get_field_queryset_dependencies()`](#get_field_queryset_dependencies).

Related docs:

- [Forms: Dependent form fields](../guides/forms.md#dependent-form-fields)
- [Configuration options: Dependent queryset scoping](./config_options.md#dependent-queryset-scoping)

---

## Async hooks and extension points

### `async_task_lifecycle()`

- Purpose: Use this when you want async tasks to trigger project-specific side effects such as dashboard rows, audit entries, notifications, or cleanup logic.
- When it is called: By the async manager and completion flow as task status changes.
- Signature: `def async_task_lifecycle(self, event, task_name, **kwargs)`
- Default behavior: `AsyncManager` provides a no-op hook; downstream manager subclasses can persist dashboard rows, notify users, or record audit data.
- Important note: This is the hook to call an external webhook or notification service if your project needs that. PowerCRUD does not ship webhook delivery, retry/backoff, dead-letter handling, or replay logic as built-in features.
- Return contract: No return value is required.
- Short example:

    ```python
    class NotificationsAsyncManager(AsyncManager):
        def async_task_lifecycle(self, event, task_name, **kwargs):
            if event == "fail":
                report_error(task_name, kwargs.get("result"))
    ```

- Related docs: [Async Manager](../guides/async_manager.md#5-lifecycle-hooks), [Async architecture & reference](./async.md)

### `BulkUpdatePersistenceBackend.persist_bulk_update()`

- Purpose: Use this when async bulk update needs to go through app-level write orchestration without depending on a live CRUD view instance.
- When it is called: By the async bulk worker, and by the default sync bulk path as well when `bulk_update_persistence_backend_path` is configured.
- Signature: `def persist_bulk_update(self, *, queryset, bulk_fields, fields_to_update, field_data, context, progress_callback=None)`
- Key arguments:
    - `queryset`: The objects selected for update.
    - `bulk_fields`: The resolved allow-list of configured bulk-edit fields.
    - `fields_to_update`: The field names requested for this operation.
    - `field_data`: The normalized bulk payload built from the request.
    - `context`: Plain execution context describing whether the operation is running in `"sync"` or `"async"` mode, plus task and user metadata where available.
    - `progress_callback`: Optional callback for per-record progress updates.
- Default behavior: `DefaultBulkUpdatePersistenceBackend` preserves the built-in PowerCRUD bulk update implementation.
- Return contract: A result dict with `success`, `success_records`, and `errors`.
- Short example:

    ```python
    class ProjectBulkUpdateBackend(BulkUpdatePersistenceBackend):
        def persist_bulk_update(
            self,
            *,
            queryset,
            bulk_fields,
            fields_to_update,
            field_data,
            context,
            progress_callback=None,
        ):
            return ProjectBulkUpdateService().apply(
                queryset=queryset,
                fields_to_update=fields_to_update,
                field_data=field_data,
                mode=context.mode,
                task_name=context.task_name,
                progress_callback=progress_callback,
            )
    ```

- Related docs: [Bulk editing (async)](../guides/bulk_edit_async.md), [Async architecture & reference](./async.md), [Configuration options](./config_options.md)

### `resolve_bulk_update_persistence_backend()`

- Purpose: Resolve the configured import path into a concrete bulk update persistence backend instance.
- When it is called: By PowerCRUD's sync bulk path and async bulk worker when backend configuration is present.
- Signature: `resolve_bulk_update_persistence_backend(backend_path, *, config=None)`
- Default behavior: Returns `DefaultBulkUpdatePersistenceBackend` when no backend path is configured.
- Related docs: [Bulk editing (async)](../guides/bulk_edit_async.md), [Async architecture & reference](./async.md)

### `AsyncManager.resolve_manager()`

- Purpose: This lets workers and completion hooks find the same manager class your launch site configured, so custom lifecycle behavior stays consistent outside the request.
- When it is called: During async task execution and completion handling.
- Signature: `AsyncManager.resolve_manager(manager_class_path, config=None)`
- Default behavior: Resolves the configured manager class path and falls back to `AsyncManager` if resolution fails.
- Related docs: [Async Manager](../guides/async_manager.md), [Async architecture & reference](./async.md)

Keep the full async operational detail in the dedicated async docs:

- [Async Manager](../guides/async_manager.md)
- [Async architecture & reference](./async.md)
