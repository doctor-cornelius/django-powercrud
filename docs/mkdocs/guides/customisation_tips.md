# Customisation tips

Once the basics are in place you may want to tailor templates, extend mixins, or integrate PowerCRUD into broader workflows. This chapter rounds up the common tweaks and points to deeper references.

---

## 1. Copy and tweak templates

Use the management command to copy PowerCRUD templates into your app:

```bash
# Copy entire structure
python manage.py pcrud_mktemplate myapp --all

# Just the CRUD templates for a model
python manage.py pcrud_mktemplate myapp.Project --all

# Specific pieces
python manage.py pcrud_mktemplate myapp.Project --list
python manage.py pcrud_mktemplate myapp.Project --form
```

Templates land in `myapp/templates/myapp/…` mirroring PowerCRUD’s layout. Override only what you need; remove a copied file to fall back to the default.

---

## 2. Extend mixins and views

Because PowerCRUD leans on mixins, you can override behaviour by subclassing:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs
```

Useful hooks:

- `get_queryset`, `get_filter_queryset_for_field`.
- `get_bulk_choices_for_field`, `get_bulk_selection_key_suffix`.
- `persist_single_object` for validated standard form and inline writes.
- `persist_bulk_update` for synchronous bulk update writes.
- `get_context_data` for injecting extra template data.

If your sync bulk service needs to reject the batch with a user-facing validation message, return the standard handled bulk result payload instead of raising an unhandled exception. See [Bulk editing (synchronous)](bulk_edit_sync.md#handling-validation-errors-in-persist_bulk_update).

Use the [Hooks reference](../reference/hooks.md) for the canonical hook contracts and signatures.

If you want a more guided explanation of when persistence hooks are worth using, start with the [Advanced Guides](advanced/index.md), especially [Persistence Hooks for Real Write Logic](advanced/persistence_hooks_sync.md) and [Async Bulk Persistence Without Surprises](advanced/persistence_hooks_async_bulk.md).

### Persistence hooks

Use the sync persistence hooks when your app needs validated PowerCRUD inputs but wants business write orchestration to live in an app service rather than in several separate view overrides.

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    def persist_single_object(self, *, form, mode, instance=None):
        project = super().persist_single_object(
            form=form,
            mode=mode,
            instance=instance,
        )
        ProjectAuditService().record_save(project=project, mode=mode)
        return project

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

Notes:

- `persist_single_object(...)` is used by both the normal form save path and inline row save path.
- `mode` is currently `"form"` or `"inline"`.
- If you bypass `form.save()` in `persist_single_object(...)`, your override owns any required `form.save_m2m()` handling.
- `persist_bulk_update(...)` is sync bulk-update only in this release. Bulk delete and async bulk persistence remain separate follow-up concerns.
- The full hook contract now lives in the [Hooks reference](../reference/hooks.md).

### Migrating older write overrides

If an existing downstream project is overriding internal methods only to take control of persistence, move that logic onto the public hooks instead:

- move standard form-save write logic from `form_valid()` into `persist_single_object(...)`
- move inline write logic from inline-save internals into the same `persist_single_object(...)`
- move sync bulk-update write logic from bulk internals into `persist_bulk_update(...)`
- move async bulk-update write logic out of worker patches and into `BulkUpdatePersistenceBackend` plus `bulk_update_persistence_backend_path`

Keep the older override only when it also changes validation, response handling, or another non-persistence part of the flow.

---

## 3. Custom buttons & actions

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    extra_buttons = [
        {
            "url_name": "projects:new",
            "text": "New project",
            "button_class": "btn-primary",
            "display_modal": True,
        },
        {
            "url_name": "projects:selected-summary",
            "text": "Selected summary",
            "display_modal": True,
            "uses_selection": True,
            "selection_min_count": 1,
            "selection_min_behavior": "disable",
        },
    ]

    extra_actions = [
        {
            "url_name": "projects:clone",
            "text": "Clone",
            "needs_pk": True,
            "htmx_target": "#powercrudModalContent",
            "display_modal": True,
            "disabled_if": "is_clone_disabled",
            "disabled_reason": "get_clone_disabled_reason",
        },
    ]
```

Button dictionaries support additional keys such as selection-aware thresholds, while row actions can now use named disable hooks. See the reference for the full schema.

---

## 4. Integrate with other workflows

- **Signals or admin** – Import the same async helpers ([Async Manager](./async_manager.md)) to queue work or enforce locks outside PowerCRUD.
- **Notifications** – Override `async_task_lifecycle` in your manager to send emails/slack messages on `fail`/`complete`.
- **Audit logging** – Hook into lifecycle events or override CRUD methods such as `persist_single_object(...)` / `persist_bulk_update(...)` to push entries to your logging system.

---

## 5. Useful references

- [Configuration options](../reference/config_options.md) – complete list of view settings and defaults.
- [Hooks reference](../reference/hooks.md) – canonical contracts for the main public override points.
- [Management commands](../reference/mgmt_commands.md) – template copy, Tailwind safelist, async cleanup.
- [Sample app](../reference/sample_app.md) – full working example you can mine for patterns.

---

## Next steps

You now have the full toolkit: core CRUD, synchronous and async bulk operations, reusable async helpers, dashboards, styling, and customisation. Refer back to the guides as needed and keep the reference section handy for specific settings or commands. Happy shipping!
