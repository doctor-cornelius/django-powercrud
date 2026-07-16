# PowerField Design Brief

## Context

django-powercrud is a Django CRUD framework where views are configured via class attributes. The current API requires declaring field participation across multiple separate primitive lists, which is verbose and error-prone. PowerField is a planned helper to collapse that repetition into a single per-field declaration.

## The Problem

A single field can currently appear in up to seven separate declarations:

```python
fields = ["status", ...]
column_help_text = {"status": "..."}
list_cell_tooltip_fields = ["status"]
form_fields = ["status"]
inline_edit_fields = ["status"]
bulk_fields = ["status"]
field_queryset_dependencies = {"status": {...}}
```

PowerField collapses this to a single declaration per field.

---

## Scope

PowerField covers **Field Intent** only — the concept bucket from the config audit. This maps to the following primitives:

1. `fields`
2. `properties`
3. `exclude`
4. `properties_exclude`
5. `detail_fields`
6. `detail_properties`
7. `detail_exclude`
8. `detail_properties_exclude`
9. `form_fields`
10. `form_fields_exclude`
11. `form_display_fields`
12. `form_disabled_fields`
13. `inline_edit_fields`
14. `field_queryset_dependencies`
15. `column_help_text`
16. `column_alignments`
17. `list_cell_tooltip_fields`
18. `link_fields`
19. `default_list_fields`

**Explicitly out of scope:**
- Filter participation (`filterset_fields`, `default_filterset_fields`) — Surface concept
- `column_sort_fields_override` — Surface concept
- `bulk_delete`, `bulk_full_clean`, `bulk_async` etc. — Bulk Operation concept
- Async, action, presentation, and styling config

---

## API Shape

`power_fields` is a list containing an optional `PowerOverride` (at most one, must be first) followed by any number of `PowerField` instances:

```python
power_fields = [
    PowerOverride(detail="__all__", form="__all__"),
    PowerField("status",
        inline=True,
        bulk=True,
        column={"help_text": "Current status.", "alignment": "center"},
        exclude={"form": True, "detail": True},
    ),
    PowerField("exclude_reason",
        form=True,
        inline=True,
        tooltip=True,
        default_list=True,
        queryset_dependencies={...},
    ),
    PowerField("notes",
        inline=True,
        exclude={"bulk": True},  # bulk not declared anyway — silent
    ),
]
```

---

## PowerField

A plain Python class, not a Django field. One instance per field declaring that field's full participation intent.

### Kwargs

Boolean flat kwargs for simple participation:

- `inline=True` — include in `inline_edit_fields`
- `bulk=True` — include in `bulk_fields`
- `form=True` — include in `form_fields`
- `form_display=True` — include in `form_display_fields`
- `form_disabled=True` — include in `form_disabled_fields`
- `tooltip=True` — include in `list_cell_tooltip_fields`
- `detail=True` — include in `detail_fields`
- `list=True` — include in `fields`
- `default_list=True` — include in `default_list_fields`
- `property=True` — include in `properties`
- `detail_property=True` — include in `detail_properties`

Dict kwargs for concepts with genuine sub-options:

- `column={"help_text": "...", "alignment": "center"}` — drives `column_help_text` and `column_alignments`
- `queryset_dependencies={...}` — drives `field_queryset_dependencies`
- `link={...}` — include in `link_fields` using the same metadata dict supported by the primitive `link_fields` API

### Tooltip and link behaviour

`tooltip=True` registers the field in `list_cell_tooltip_fields`. Tooltip *content* still lives in `get_list_cell_tooltip()` as today. PowerField handles registration; the hook handles content.

`link={...}` writes the supplied metadata to `link_fields[field_name]`. The dict must follow the same primitive `link_fields` contract, for example `{"view_name": "library:author-detail", "pk_attr": "author_id", "open_in": "modal"}`. There is no `link=True` shorthand because it would not provide enough information to build a declarative link. Row-specific links still belong in `get_list_cell_link()` as today.

### Primitive extraction helpers

`PowerField` should expose a small method for extracting the primitive API contribution for one field. The exact method name can be settled during implementation, but the contract should be simple:

```python
PowerField("status", list=True, form=True, inline=True).to_primitive_fragment()
```

returns a fragment shaped like:

```python
{
    "fields": ["status"],
    "form_fields": ["status"],
    "inline_edit_fields": ["status"],
}
```

Dict-backed declarations contribute mapping fragments:

```python
PowerField(
    "status",
    column={"help_text": "Current status.", "alignment": "center"},
    link={"view_name": "workflow:status-detail", "open_in": "modal"},
).to_primitive_fragment()
```

returns a fragment shaped like:

```python
{
    "column_help_text": {"status": "Current status."},
    "column_alignments": {"status": "center"},
    "link_fields": {
        "status": {"view_name": "workflow:status-detail", "open_in": "modal"},
    },
}
```

The aggregate compiler then combines `PowerOverride` defaults and all `PowerField` fragments into one normalized primitive config object. Tests should be able to assert both the individual fragment output and the aggregate primitive lists/dicts.

### The `exclude` dict

`exclude` is a dict of dimensions to explicitly suppress:

```python
PowerField("status",
    inline=True,
    exclude={"form": True, "detail": True},
)
```

**Three rules for `exclude`:**

1. **`exclude` beats `PowerOverride`** — if `PowerOverride` declares `form="__all__"` but this field has `exclude={"form": True}`, the field is excluded from form. Exclude always wins over a view-level override.

2. **`exclude` on an undeclared dimension is silent** — if the field wasn't going to be included in that dimension anyway, the exclude is quietly ignored. No error.

3. **`exclude` and explicit include on the same dimension raises `ImproperlyConfigured`** — with a clear message identifying the field and dimension:

```
ImproperlyConfigured: PowerField "status" declares both
form=True and exclude={"form": True}. Use one or the other.
```

---

## PowerOverride

An optional view-level entry that sets broad dimension declarations, accepting the same sentinel values as the primitive API.

```python
PowerOverride(detail="__all__", form="__all__", bulk=None)
```

### Rules

- At most one `PowerOverride` per view — `ImproperlyConfigured` if multiple declared
- Must be the first entry in `power_fields` if present
- Accepted values per dimension match primitive API — `"__all__"`, `None`, sentinel strings
- Where a `PowerOverride` dimension is declared, field-level `PowerField` declarations for that same dimension are subordinate — unless the field declares `exclude` for that dimension, in which case exclude wins
- `PowerOverride` is optional — most views will not need it
- Primary use case is exploration and development, e.g. `detail="__all__"` while getting familiar with a model

### Possible public shape

The current proposed public shape keeps `PowerOverride` as the optional first item in `power_fields`:

```python
power_fields = [
    PowerOverride(detail="__all__", form="__all__"),
    PowerField("status", inline=True),
]
```

An alternate implementation could expose the same idea as a separate class attribute:

```python
power_field_defaults = PowerOverride(detail="__all__", form="__all__")
power_fields = [
    PowerField("status", inline=True),
]
```

That separate attribute is not required, but it may be cleaner internally because the resolver can treat broad dimension defaults and per-field declarations as different inputs instead of giving special meaning to the first list element. If the first-entry list shape remains the public API, the implementation can still normalize it internally into separate defaults and field declarations before compiling primitive config.

---

## Coexistence Rule

**Per-view, pick one style. No mixing.**

If `power_fields` is declared alongside any primitive Field Intent attribute on the same view, raise `ImproperlyConfigured` immediately with a clear message identifying the conflicting primitive declarations. This is consistent with how `ConfigMixin.__init__` already handles misconfiguration aggressively.

There is no escape hatch. If PowerField does not yet support something you need, use the primitive API for the whole view. Migrate views one at a time — each view is unambiguously one style or the other.

---

## Precedence Summary

From highest to lowest:

1. `exclude` on a `PowerField` — always wins
2. Explicit participation declared on a `PowerField` — e.g. `form=True`
3. `PowerOverride` view-level dimension declaration — e.g. `form="__all__"`
4. Absence — field simply not included in that dimension

---

## Independent Declaration and Reuse

`power_fields` lists can be defined independently and imported, addressing repetition across related views:

```python
# shared_fields.py
ASSET_FIELDS = [
    PowerOverride(detail="__all__"),
    PowerField("status", inline=True, bulk=True,
        column={"help_text": "Current status."}
    ),
    PowerField("exclude_reason", inline=True, form=True, tooltip=True,
        queryset_dependencies={...},
    ),
]

# views.py
class AnalyticsAssetCRUDView(AbstractBasePowerCRUDView):
    power_fields = ASSET_FIELDS

class CMMSAssetCRUDView(AbstractBasePowerCRUDView):
    power_fields = ASSET_FIELDS
```

Subclassing `PowerField` is valid for domain-specific field types with standard flag combinations:

```python
class ReconciliationField(PowerField):
    def __init__(self, name, **kwargs):
        super().__init__(name, inline=True, bulk=True, tooltip=True, **kwargs)
```

---

## Inheritance Between Views

A view inheritance chain may use primitive Field Intent config or PowerField Field Intent config, not both.

A subclass declaring its own `power_fields` replaces the parent's `power_fields` entirely for that view. No merging — replacement only. A subclass can freely define its own `power_fields` without reasoning about what the parent declared.

### Primitive parent classes

PowerField mode is view-local, but inherited primitive Field Intent config still matters.

If a base class declares primitive Field Intent attributes such as `fields`, `form_fields`, `inline_edit_fields`, `bulk_fields`, `list_cell_tooltip_fields`, or `default_list_fields`, a subclass should not also declare `power_fields`. That would mix two sources of truth across the inheritance chain and make it unclear whether PowerField replaces, extends, or overrides inherited primitive config.

The conflict check should inspect the class MRO for primitive Field Intent declarations, not only the subclass `__dict__`. A subclass may inherit shared Surface, Presentation, Action, Selection, Bulk Operation, Async, and Styling config from a primitive base class, but it may not inherit primitive Field Intent config and then declare `power_fields`.

If a project wants a PowerField-ready base class, move shared field declarations into reusable `power_fields` lists or `PowerField` subclasses instead of primitive parent attributes.

Do not support implicit bridging:

1. A primitive child class should not partially override compiled `power_fields` from a parent.
2. A PowerField child class should not silently replace, merge, or suppress primitive Field Intent config inherited from a parent.

If later projects show real demand for mixed inheritance, add it as an explicit named bridge rather than implicit behaviour. For example, a future option could deliberately say "replace inherited primitive Field Intent config with this view's `power_fields`", but that is out of scope.

---

## Internal Compile Target

PowerField declarations compile to the existing primitive attributes (`fields`, `form_fields`, `inline_edit_fields`, `bulk_fields`, etc.) before any existing PowerCRUD machinery consumes those attributes.

This must happen earlier than ordinary `ConfigMixin.__init__` validation because some PowerCRUD behaviour is decided at class/URL-registration time:

1. Bulk-edit URLs are registered from class-level `bulk_fields` / `bulk_delete`.
2. Inline-edit URLs are registered from class-level `inline_edit_fields`.
3. List-options URLs are registered from class-level `default_list_fields` / `list_options_enabled`.

The implementation target is therefore:

```text
primitive class attrs -> normalized primitive config -> existing validation/resolution
power_fields          -> normalized primitive config -> existing validation/resolution
```

Existing primitive views must keep their current behaviour. The standardisation goal is not to change the legacy API; it is to make primitive config and PowerField config pass through one normalized internal representation before URL registration, validation, and runtime helpers read it.

PowerField compilation should also run early enough that downstream base classes which normalize primitive config before `super().__init__()` see ordinary primitive attributes. A DDMS-style base class that removes a raw list column or adds a tooltip field should not need to know whether a child view used primitives or PowerField, provided that the inheritance-boundary rules above are respected.

The conflict check (PowerField + primitive Field Intent config in the same inheritance chain) also runs before compilation and raises `ImproperlyConfigured` immediately.

---

## PowerField Defaults Versus Legacy Defaults

Legacy primitive config keeps its existing sensible fallbacks. For example, omitted or empty primitive `fields` can resolve to all model fields, and omitted or empty primitive `form_fields` can fall back from detail fields.

PowerField mode should not inherit those implicit fallbacks accidentally. In PowerField mode, absence means the field is not included in that dimension unless:

1. A `PowerField` explicitly includes it, for example `PowerField("status", form=True)`.
2. A `PowerOverride` explicitly opts a whole dimension into a primitive sentinel, for example `PowerOverride(form="__all__")` or `PowerOverride(detail="__all__")`.

This preserves legacy defaults for existing primitive views while making PowerField views explicit by default. `PowerOverride` is the deliberate escape hatch for broad sensible defaults during exploration or for views where the old sentinel behaviour is genuinely wanted.

Examples:

```python
# Explicit-only PowerField mode: only the named dimensions are populated.
power_fields = [
    PowerField("status", list=True, form=True),
]
```

```python
# Broad defaults are still available, but they are opt-in and visible.
power_fields = [
    PowerOverride(list="__all__", detail="__all__", form="__all__"),
    PowerField("status", inline=True, bulk=True),
]
```

The compiler should emit explicit primitive values for PowerField mode so the legacy resolver does not mistake "not declared" for "please apply the old fallback". For example, if no PowerField or PowerOverride declares `form`, the compiled primitive `form_fields` should represent "no generated form fields" rather than falling through to the legacy form-field default.

---

## Implementation Notes

- `PowerField` and `PowerOverride` are plain Python classes, not Django fields
- `power_fields` is a new class attribute on `ConfigMixin`
- Processing happens before URL registration and before `_configure_fields()` and related methods run
- PowerField writes to existing primitive attributes, or an internal normalized primitive-config object, so downstream validation runs unchanged
- Existing views using primitive declarations continue to work unchanged — PowerField is purely additive
- The conflict check must inspect the relevant class MRO for primitive Field Intent declarations, not only `cls.__dict__`
- Error messages must always identify the specific field name and dimension involved
- `bulk_delete` and other Bulk Operation flags remain as primitive declarations alongside `power_fields` without triggering the coexistence error — they are a different concept bucket
