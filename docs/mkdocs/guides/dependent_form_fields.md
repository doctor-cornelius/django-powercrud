# Dependent Form Fields

Use declarative dependent queryset scoping when one selectable child field should be restricted by the value of another form field.

This feature is primarily for straightforward cases such as:

- “Asset type choices depend on the selected property”
- “Genre choices depend on the selected author”
- “Subcategory choices depend on the selected category”

PowerCRUD applies the same rule to:

- regular create/update forms
- inline row editing forms

For complex business rules, permission-aware filtering, or bespoke queryset logic, keep using a custom `form_class` or view override.

---

## The two settings

### `field_queryset_dependencies`

This is the primary declaration.

Use it to describe:

- which child field is being restricted
- which parent field or fields it depends on
- how parent values map into queryset filters on the child field

Example:

```python
field_queryset_dependencies = {
    "genres": {
        "depends_on": ["author"],
        "filter_by": {"authors": "author"},
        "order_by": "name",
        "empty_behavior": "all",
    }
}
```

### `inline_field_dependencies`

This is now an inline-only override layer.

Most projects no longer need it.

Keep it only when you need inline-specific metadata such as:

- a custom dependency endpoint name
- an inline-only `depends_on` override

Example:

```python
inline_field_dependencies = {
    "genres": {
        "endpoint_name": "sample:book-inline-dependency",
    }
}
```

If you define `field_queryset_dependencies` but omit `inline_field_dependencies`, PowerCRUD derives the inline dependency wiring automatically.

---

## How `filter_by` works

This is the part that most users need spelled out.

`filter_by` maps:

- left-hand side: queryset lookup on the child field's queryset model
- right-hand side: parent form field name

General shape:

```python
field_queryset_dependencies = {
    "child_field": {
        "depends_on": ["parent_field"],
        "filter_by": {"child_queryset_lookup": "parent_field"},
    }
}
```

Read that as:

> “When the user changes `parent_field`, restrict `child_field` choices by filtering its queryset with `child_queryset_lookup=<value of parent_field>`.”

### Example 1: many-to-many lookup

```python
field_queryset_dependencies = {
    "genres": {
        "depends_on": ["author"],
        "filter_by": {"authors": "author"},
    }
}
```

Meaning:

- `genres` is the child form field
- `author` is the parent form field
- `authors` is the lookup on the `Genre` queryset

So PowerCRUD effectively narrows the genres queryset like:

```python
Genre.objects.filter(authors=<selected author>)
```

### Example 2: foreign key lookup

```python
field_queryset_dependencies = {
    "cmms_asset": {
        "depends_on": ["cmms_property_asset_type_override"],
        "filter_by": {
            "property_asset_type_override": "cmms_property_asset_type_override",
        },
        "empty_behavior": "none",
    }
}
```

Meaning:

- `cmms_asset` is the child field being restricted
- `cmms_property_asset_type_override` is the parent field the user selects
- `property_asset_type_override` is the lookup on the `cmms_asset` field queryset

So PowerCRUD effectively narrows the queryset like:

```python
Asset.objects.filter(
    property_asset_type_override=<selected cmms_property_asset_type_override>
)
```

### Example 3: multiple parent fields

```python
field_queryset_dependencies = {
    "room": {
        "depends_on": ["building", "level"],
        "filter_by": {
            "building": "building",
            "level": "level",
        },
        "empty_behavior": "none",
    }
}
```

PowerCRUD applies all valid mappings, so the child queryset becomes more specific as more parent values are available.

---

## Supported keys

### `depends_on`

List of parent form fields that drive the child queryset.

```python
"depends_on": ["author"]
```

Rules:

- each entry must be a form field name
- for inline refresh, the parent field must also be inline-editable
- for `filter_by`, every referenced parent must also appear in `depends_on`

### `filter_by`

Mapping of child queryset lookups to parent form field names.

```python
"filter_by": {"authors": "author"}
```

Rules:

- keys are lookup names used against the child field queryset
- values are parent form field names
- use this for simple equality-style filtering

### `order_by`

Optional ordering applied to the child queryset after filtering.

```python
"order_by": "name"
```

### `empty_behavior`

Controls what happens when the needed parent value is empty.

```python
"empty_behavior": "none"
```

Supported values:

- `"none"`: return no child choices until the parent value is available
- `"all"`: leave the child queryset unfiltered when the parent value is empty

Use `"none"` when an unrestricted dropdown would be noisy or misleading.

Use `"all"` when the unfiltered list is still useful and reasonably sized.

---

## Value resolution order

When PowerCRUD decides how to filter the child queryset, it resolves parent values in this order:

1. bound form data
2. the current instance
3. initial form values

That matters because:

- regular edit forms can scope correctly on initial page load from the instance
- inline refreshes can use the user’s current unsaved row values
- validation re-renders preserve the same restriction logic

---

## Regular forms vs inline forms

`field_queryset_dependencies` is shared across both editing modes.

Regular create/update forms:

- the child queryset is scoped on render
- the child queryset is scoped again on POST / validation re-render
- regular forms are not auto-refreshed in the browser when the parent changes

Inline editing:

- the same child queryset rule is used
- dependency wiring is derived automatically from `field_queryset_dependencies`
- when the user changes the parent field inline, PowerCRUD rebuilds the child widget and swaps it into the row

This is why `field_queryset_dependencies` is the primary setting and `inline_field_dependencies` is only an override layer.

---

## Worked example: sample app `Book.author -> Book.genres`

The sample app uses this configuration:

```python
field_queryset_dependencies = {
    "genres": {
        "depends_on": ["author"],
        "filter_by": {"authors": "author"},
        "order_by": "name",
        "empty_behavior": "all",
    }
}
```

Why this works:

- `genres` is the child field the user edits
- `author` is the parent field the user chooses
- `Genre` records are related to `Author` records through `Genre.authors`
- so the child queryset lookup is `authors`, not `author`

In practice:

- the normal Book create/edit form only shows genres allowed for the selected author
- inline Book editing uses the same restriction
- when the user changes `author` inline, PowerCRUD refreshes the `genres` widget immediately

`BookForm` still exists in the sample app, but only for form-specific concerns such as keeping `genres` optional.

See also:

- [Inline editing](./inline_editing.md)
- [Sample Application](../reference/sample_app.md)

---

## Migrating old inline-only configs

Old pattern:

```python
inline_field_dependencies = {
    "cmms_asset": {
        "depends_on": ["cmms_property_asset_type_override"],
    }
}
```

This only tells inline editing which parent field should trigger a refresh. It does not declare the shared queryset rule.

New pattern:

```python
field_queryset_dependencies = {
    "cmms_asset": {
        "depends_on": ["cmms_property_asset_type_override"],
        "filter_by": {
            "property_asset_type_override": "cmms_property_asset_type_override",
        },
        "empty_behavior": "none",
    }
}
```

That one declaration now gives you:

- regular form queryset restriction
- inline form queryset restriction
- derived inline dependency refresh wiring

If you still need an inline-only override, layer it on top:

```python
inline_field_dependencies = {
    "cmms_asset": {
        "endpoint_name": "myapp:custom-inline-dependency",
    }
}
```

---

## When to fall back to `form_class`

Use `field_queryset_dependencies` when the rule is simple and declarative.

Fall back to `form_class`, `get_form()`, or other view overrides when you need:

- permission-aware queryset logic
- tenant-specific logic
- computed business rules that do not map cleanly to form fields
- custom joins or complex query construction
- non-queryset widget behavior

That is the intended boundary of this feature.
