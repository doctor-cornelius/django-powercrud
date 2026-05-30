# Deprecations

This page tracks public APIs that still work for compatibility but are no longer the preferred path.

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
