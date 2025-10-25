# 07. Customisation tips

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
- `get_context_data` for injecting extra template data.

Full API details live in the reference, but these are the most common overrides.

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
    ]

    extra_actions = [
        {
            "url_name": "projects:clone",
            "text": "Clone",
            "needs_pk": True,
            "htmx_target": "#powercrudModalContent",
            "display_modal": True,
        },
    ]
```

Button dictionaries support additional keys (HTMX targets, extra attributes)—see the reference for the full schema.

---

## 4. Integrate with other workflows

- **Signals or admin** – Import the same async helpers ([Section 03](./03_async_manager.md)) to queue work or enforce locks outside PowerCRUD.
- **Notifications** – Override `async_task_lifecycle` in your manager to send emails/slack messages on `fail`/`complete`.
- **Audit logging** – Hook into lifecycle events or override CRUD methods to push entries to your logging system.

---

## 5. Useful references

- [Configuration options](../reference/config_options.md) – complete list of view settings and defaults.
- [Management commands](../reference/mgmt_commands.md) – template copy, Tailwind safelist, async cleanup.
- [Sample app](../reference/sample_app.md) – full working example you can mine for patterns.

---

## Next steps

You now have the full toolkit: core CRUD, synchronous and async bulk operations, reusable async helpers, dashboards, styling, and customisation. Refer back to the guides as needed and keep the reference section handy for specific settings or commands. Happy shipping!
