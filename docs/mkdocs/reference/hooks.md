# Hooks Reference

This page is the canonical reference for PowerCRUD's main public override points. Use the guides for workflow examples and setup, and use this page when you want to answer practical questions such as "where do I override this?" or "which hook should I use for this behavior?".

This is a curated reference for the public hooks most downstream projects are expected to use. It does not try to inventory every internal extension point.

If you want step-by-step walkthroughs rather than contracts, start with the advanced guides:

- [Persistence Hooks for Real Write Logic](../guides/advanced/persistence_hooks_sync.md)
- [Async Bulk Persistence Without Surprises](../guides/advanced/persistence_hooks_async_bulk.md)

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

---

## View lifecycle and queryset hooks

### `get_queryset()`

- Purpose: Use this when you want to change which records the view works with in the first place, such as scoping rows to the current user, tenant, or workflow state.
- When it is called: During list rendering and any flow that depends on the view queryset.
- Signature: `def get_queryset(self)`
- Default behavior: Calls the parent `get_queryset()` first, so the usual Neapolitan behavior still applies. That means an explicit class `queryset` is still respected, otherwise PowerCRUD falls back to `model._default_manager.all()`. PowerCRUD then applies sort handling and adds a stable secondary `pk` sort.
- Return contract: A queryset for the current view.
- Important note: If you override this, call `super().get_queryset()` unless you intentionally want to replace PowerCRUD's default sort behavior too.
- Related docs: [Setup & Core CRUD basics](../guides/setup_core_crud.md), [Customisation tips](../guides/customisation_tips.md)

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

- Related docs: [Forms](../guides/forms.md), [Customisation tips](../guides/customisation_tips.md)

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

- Related docs: [Forms](../guides/forms.md), [Customisation tips](../guides/customisation_tips.md)

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

- Related docs: [Forms](../guides/forms.md#persisting-validated-standard-forms), [Inline editing](../guides/inline_editing.md#persisting-validated-inline-rows), [Customisation tips](../guides/customisation_tips.md)

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
- Important note: This is still the sync view hook. Async bulk update uses a worker-safe backend contract instead. If `bulk_update_persistence_backend_path` is configured and you do not override this hook yourself, the default sync implementation delegates to that same backend so sync and async can share one write path.
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

- Related docs: [Bulk editing (synchronous)](../guides/bulk_edit_sync.md#routing-sync-bulk-updates-through-one-hook), [Customisation tips](../guides/customisation_tips.md)

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

- Related docs: [Bulk editing (synchronous)](../guides/bulk_edit_sync.md#dropdowns-choices), [Customisation tips](../guides/customisation_tips.md)

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

- Related docs: [Bulk editing (synchronous)](../guides/bulk_edit_sync.md#4-selection-persistence), [Customisation tips](../guides/customisation_tips.md)

---

## Inline editing hooks

### `inline_edit_allowed`

- Purpose: Use this when some rows should stay read-only inline even though inline editing is enabled for the view overall, for example archived or workflow-locked records.
- When it is called: During inline row rendering and again before accepting an inline save.
- Signature: `inline_edit_allowed(obj, request)`
- Default behavior: If unset, rows follow the standard inline permission and lock checks only.
- Return contract: Truthy to allow inline editing for that row, falsy to block it.
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
