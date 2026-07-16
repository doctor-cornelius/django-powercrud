# Deprecations

This page tracks public APIs that still work for compatibility but are no longer the preferred path.

## Legacy Modal Class Settings

!!! warning "Deprecated: raw modal class settings"

    `modal_classes`, `modal_box_classes`, `modal_body_classes`, `bulk_modal_box_classes`, and per-trigger `modal_box_classes` are deprecated and targeted for removal in v1.0. Explicit use emits `FutureWarning`.

These settings expose DaisyUI, Tailwind, Bootstrap, or application-specific class strings directly. They remain available only for existing framework-specific customisations and cannot promise a portable visual outcome across template packs.

Use the semantic portable mapping instead:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    use_htmx = True
    use_modal = True
    modal_presentation = {
        "size": "wide",
        "max_height": "viewport",
        "scroll": "body",
        "vertical_alignment": "center",
    }
    bulk_modal_presentation = {"size": "extra_wide"}
```

Modal `extra_actions`, `extra_buttons`, `PowerAction`, `PowerButton`, modal `link_fields`, and hook-returned modal links may set a partial `modal_presentation` mapping. Do not combine a presentation mapping with the corresponding legacy class option; PowerCRUD raises a configuration error rather than choosing one silently.

## Legacy Extra-Action Disabled Hooks

!!! warning "Deprecated: `disabled_if` and `disabled_reason` on `extra_actions`"

    The paired `disabled_if` / `disabled_reason` row-action hooks are deprecated and targeted for removal in v1.0.

    ```python
    extra_actions = [
        {
            "url_name": "cases:case-preview",
            "text": "Preview",
            "disabled_if": "is_preview_disabled",
            "disabled_reason": "get_preview_disabled_reason",
        },
    ]
    ```

Use `disabled_state` instead. It keeps the enabled/disabled decision and reason text in one hook:

```python
extra_actions = [
    {
        "url_name": "cases:case-preview",
        "text": "Preview",
        "disabled_state": "get_preview_disabled_state",
    },
]

def get_preview_disabled_state(self, obj, request):
    if not obj.ready_for_preview:
        return "Preview is available after the case is ready."
    return None
```

Use `hidden_if` separately when the action is not applicable and should not render for a row.

## Legacy List-Cell Tooltip Hook

!!! warning "Deprecated: `list_cell_tooltip_fields` as a list"

    The legacy list form is deprecated and targeted for removal before v1.0.

    ```python
    list_cell_tooltip_fields = ["owner", "display_status"]

    def get_list_cell_tooltip(self, obj, field_name, *, is_property, request=None):
        if field_name == "owner":
            return f"{obj.owner.email} ({obj.owner.team.name})"
        if field_name == "display_status":
            return obj.status_explanation
        return None
    ```

Use the field-to-hook mapping instead:

```python
list_cell_tooltip_fields = {
    "owner": "get_owner_tooltip",
    "display_status": "get_display_status_tooltip",
}

def get_owner_tooltip(self, obj, request=None):
    return f"{obj.owner.email} ({obj.owner.team.name})"

def get_display_status_tooltip(self, obj, request=None):
    return obj.status_explanation
```

PowerField declarations should use `tooltip_hook`:

```python
PowerField(
    "owner",
    default_list=True,
    tooltip_hook="get_owner_tooltip",
)
```

Do not mix the list form and mapping form in one `list_cell_tooltip_fields` declaration. Mixed shapes are invalid configuration.
