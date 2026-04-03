# Hooks Reference

This page is the canonical reference for PowerCRUD's main public override points. Use the guides for workflow examples and setup, and use this page when you want to answer practical questions such as "where do I override this?" or "which hook should I use for this behavior?".

This is a curated reference for the public hooks most downstream projects are expected to use. It does not try to inventory every internal extension seam.

If you want step-by-step walkthroughs rather than contracts, start with the advanced guides:

- [Persistence Hooks for Real Write Logic](../guides/advanced/persistence_hooks_sync.md)
- [Async Bulk Persistence Without Surprises](../guides/advanced/persistence_hooks_async_bulk.md)

---

## View lifecycle and queryset hooks

### `get_queryset()`

- Purpose: Use this when you want to change which records the view works with in the first place, such as scoping rows to the current user, tenant, or workflow state.
- When it is called: During list rendering and any flow that depends on the view queryset.
- Signature: `def get_queryset(self)`
- Default behavior: Calls the parent queryset, applies PowerCRUD sort handling, and adds a stable secondary `pk` sort.
- Return contract: A queryset for the current view.
- Related docs: [Setup & Core CRUD basics](../guides/setup_core_crud.md), [Customisation tips](../guides/customisation_tips.md)

### `get_context_data()`

- Purpose: Use this when the template needs extra data that does not already come from PowerCRUD, such as a help panel, extra summary values, or feature flags for custom UI.
- When it is called: During template rendering for the list, detail, and form flows.
- Signature: `def get_context_data(self, **kwargs)`
- Default behavior: Extends the parent context; `FormMixin` also injects `form_display_items`.
- Return contract: A `dict` for template rendering.
- Short example:

    ```python
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["help_panel_title"] = "Project tools"
        return context
    ```

- Related docs: [Forms](../guides/forms.md), [Customisation tips](../guides/customisation_tips.md)

### `get_filter_queryset_for_field()`

- Purpose: Use this when a filter dropdown should not show every possible related record, for example when you only want active owners, visible categories, or tenant-scoped choices.
- When it is called: While building filter form dropdowns for related fields.
- Signature: `def get_filter_queryset_for_field(self, field_name, model_field)`
- Default behavior: Starts from the related model queryset, applies any configured filter rules, then applies dropdown ordering.
- Return contract: A queryset of allowed choices for the filter field.
- Short example:

    ```python
    def get_filter_queryset_for_field(self, field_name, model_field):
        queryset = super().get_filter_queryset_for_field(field_name, model_field)
        if field_name == "owner":
            return queryset.filter(active=True)
        return queryset
    ```

- Related docs: [Forms](../guides/forms.md), [Customisation tips](../guides/customisation_tips.md)

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

- Purpose: Use this when a bulk-edit dropdown should offer a narrower or more carefully ordered set of choices than the default related queryset.
- When it is called: While building bulk-edit choices for related fields.
- Signature: `def get_bulk_choices_for_field(self, field_name, field)`
- Default behavior: Starts from all related objects, applies declarative static queryset rules for the field, then applies dependency or dropdown ordering metadata.
- Return contract: A queryset of choices, or `None` when the field is not relation-backed.
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

---

## Async hooks and extension points

### `async_task_lifecycle()`

- Purpose: Use this when you want async tasks to trigger project-specific side effects such as dashboard rows, audit entries, notifications, or cleanup logic.
- When it is called: By the async manager and completion flow as task status changes.
- Signature: `def async_task_lifecycle(self, event, task_name, **kwargs)`
- Default behavior: `AsyncManager` provides a no-op hook; downstream manager subclasses can persist dashboard rows, notify users, or record audit data.
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

- Purpose: This is the async extension seam that lets workers and completion hooks find the same manager class your launch site configured, so custom lifecycle behavior stays consistent outside the request.
- When it is called: During async task execution and completion handling.
- Signature: `AsyncManager.resolve_manager(manager_class_path, config=None)`
- Default behavior: Resolves the configured manager class path and falls back to `AsyncManager` if resolution fails.
- Related docs: [Async Manager](../guides/async_manager.md), [Async architecture & reference](./async.md)

Keep the full async operational detail in the dedicated async docs:

- [Async Manager](../guides/async_manager.md)
- [Async architecture & reference](./async.md)
