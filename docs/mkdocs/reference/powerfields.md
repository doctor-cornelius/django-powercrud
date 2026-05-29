# PowerField Reference

PowerField is a core helper for declaring Field Intent. It compiles to the existing primitive PowerCRUD configuration attributes before URL registration, validation, and runtime helpers consume config.

Import it from:

```python
from powercrud.powerfields import PowerField, PowerOverride
```

## View Attribute

Set `power_fields` on a PowerCRUD view:

```python
power_fields = [
    PowerOverride(list="__all__", detail="__all__"),
    PowerField("title", default_list=True, form=True, inline=True),
]
```

Accepted value: `None` or a list containing zero or one `PowerOverride` followed by `PowerField` declarations.

If a `PowerOverride` is present, it must be the first item.

## PowerField

`PowerField` is a plain Python declaration, not a Django model field.

```python
PowerField(
    name,
    *,
    inline=False,
    bulk=False,
    form=False,
    form_display=False,
    form_disabled=False,
    tooltip=False,
    detail=False,
    list=False,
    default_list=False,
    property=False,
    detail_property=False,
    column=None,
    queryset_dependencies=None,
    link=None,
    exclude=None,
)
```

### Boolean Kwargs

| Kwarg | Primitive target | Meaning |
|-------|------------------|---------|
| `list=True` | `fields` | Include the name in list fields. |
| `property=True` | `properties` | Include the name in list properties. |
| `detail=True` | `detail_fields` | Include the name in detail fields. |
| `detail_property=True` | `detail_properties` | Include the name in detail properties. |
| `form=True` | `form_fields` | Include the name in generated form fields. |
| `form_display=True` | `form_display_fields` | Show the field as display-only form context. |
| `form_disabled=True` | `form_disabled_fields` | Disable the input on update forms. |
| `inline=True` | `inline_edit_fields` | Include the editable model field in inline editing. |
| `bulk=True` | `bulk_fields` | Include the editable model field in bulk editing. |
| `default_list=True` | `default_list_fields` | Include the name in the default visible list columns. |
| `tooltip=True` | `list_cell_tooltip_fields` | Register the visible list cell for semantic tooltip lookup. |

### Dict Kwargs

| Kwarg | Primitive target | Meaning |
|-------|------------------|---------|
| `column={"help_text": "..."}` | `column_help_text` | Add header help text for the rendered field or property. |
| `column={"alignment": "center"}` | `column_alignments` | Override rendered body-cell alignment. |
| `queryset_dependencies={...}` | `field_queryset_dependencies` | Attach declarative queryset scoping for form, inline, and bulk choices. |
| `link={...}` | `link_fields` | Attach a declarative list-cell link using the primitive `link_fields` metadata contract. |

`link` must be a metadata dict. There is no `link=True` shorthand.

### Copying With Changes

Use `with_options(**changes)` to derive a new declaration from an existing `PowerField`:

```python
ACTION_STATUS = PowerField(
    "status",
    list=True,
    default_list=True,
    tooltip=True,
    bulk=True,
)

ACTION_STATUS_NO_BULK = ACTION_STATUS.with_options(bulk=False)
```

The original declaration is unchanged. The copied declaration is validated like a direct `PowerField(...)` call, so unsupported option names raise `TypeError` and invalid include/exclude combinations raise `ValueError`.

## PowerOverride

`PowerOverride` sets broad primitive sentinel values for a whole dimension.

```python
PowerOverride(
    list="__all__",
    detail="__all__",
    form="__all__",
    bulk=None,
)
```

| Kwarg | Primitive target |
|-------|------------------|
| `list` | `fields` |
| `detail` | `detail_fields` |
| `form` | `form_fields` |
| `bulk` | `bulk_fields` |

Use `PowerOverride` when you intentionally want a broad primitive sentinel in PowerField mode.

```python
power_fields = [
    PowerOverride(list="__all__", detail="__all__"),
    PowerField("description", exclude={"list": True}),
]
```

## Exclude

`exclude` is a dict keyed by PowerField dimension name:

```python
PowerField("description", exclude={"list": True})
```

Supported exclude dimensions:

| Exclude key | Primitive target |
|-------------|------------------|
| `list` | `exclude` |
| `property` | `properties_exclude` |
| `detail` | `detail_exclude` |
| `detail_property` | `detail_properties_exclude` |
| `form` | `form_fields_exclude` |

Rules:

- exclude wins over a matching `PowerOverride`;
- exclude on an undeclared dimension is ignored;
- declaring include and exclude for the same field/dimension is invalid.

## Validation Rules

PowerCRUD validates PowerField declarations early.

- `power_fields` must be a list or tuple.
- Entries must be `PowerField` or `PowerOverride` instances.
- At most one `PowerOverride` is allowed.
- `PowerOverride` must be the first entry if present.
- A `PowerField` name must be a non-empty string.
- A field cannot be explicitly included and excluded from the same dimension.

Invalid `power_fields` config raises `ImproperlyConfigured` when PowerCRUD resolves class config.

## Coexistence And Inheritance

A view inheritance chain can use primitive Field Intent or PowerField Field Intent, not both.

Primitive Field Intent config includes attributes such as `fields`, `properties`, `detail_fields`, `detail_properties`, `form_fields`, `form_display_fields`, `form_disabled_fields`, `inline_edit_fields`, `bulk_fields`, `default_list_fields`, `list_cell_tooltip_fields`, `column_help_text`, `column_alignments`, `field_queryset_dependencies`, and `link_fields`.

Non-Field-Intent settings can still be inherited or declared normally. For example, `model`, `namespace`, `base_template_path`, `use_htmx`, `use_modal`, `filterset_fields`, `bulk_delete`, `extra_actions`, and table classes remain ordinary view config.

A PowerField child can inherit PowerField config from a PowerField parent. A primitive child can inherit primitive Field Intent from a primitive parent. Mixing the two styles in one chain is rejected.

## Form Class Behaviour

When `form_class` is set, the custom form class remains the runtime source of truth for editable form inputs.

That rule is the same for primitive `form_fields` and PowerField-generated `form_fields`. PowerField form declarations can still be visible in class-time compiled config, but runtime `form_fields` is cleared once `form_class` is configured.

Use `form_display=True` and `form_disabled=True` when you want PowerCRUD to layer display-only context or disabled-field behaviour around a custom form.

## Primitive Extraction

PowerField declarations expose primitive fragments for testing and inspection:

```python
PowerField("title", list=True, form=True, inline=True).to_primitive_fragment()
```

returns:

```python
{
    "fields": ["title"],
    "form_fields": ["title"],
    "inline_edit_fields": ["title"],
}
```

Aggregate compilation is handled by `compile_powerfields(...)`.

```python
from powercrud.powerfields import compile_powerfields

compile_powerfields([
    PowerOverride(list="__all__"),
    PowerField("description", exclude={"list": True}),
])
```

returns a primitive config fragment:

```python
{
    "fields": "__all__",
    "exclude": ["description"],
}
```

Most application code should declare `power_fields` on the view and let PowerCRUD compile it.
