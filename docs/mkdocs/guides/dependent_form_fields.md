# Dependent Form Fields

Use `field_queryset_dependencies` when the available choices in one form field should depend on the current value of another form field.

Typical examples:

- the available `genres` depend on the selected `author`
- the available `rooms` depend on the selected `building`
- the available `assets` depend on the selected `asset_type`

PowerCRUD applies the same rule to:

- regular create/update forms
- inline row editing forms

For complex business rules, permission-aware filtering, or bespoke queryset logic, keep using a custom `form_class` or view override.

---

## The setting

`field_queryset_dependencies` is the public setting for dependent queryset scoping.

Use it to describe:

- which child field is being restricted
- which parent field or fields it depends on
- how parent values map into queryset filters on the child field
- what to do when the parent value is empty
- how to order the resulting child queryset

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

Inline dependency wiring is derived automatically from this setting. There is no separate inline dependency configuration to maintain.

---

## Mental Model

Think of each dependency as having three parts:

- a **child field**, which is the field whose choices should change
- one or more **parent fields**, whose current values drive the child queryset
- a **queryset mapping**, which says how the parent values should be applied to the child field's queryset

For the example above:

- `genres` is the child field
- `author` is the parent field
- `authors` is the queryset lookup used on the `Genre` queryset

In plain English, the example means:

> “Show genre choices that belong to the selected author. If no author is selected yet, still show all genres.”

---

## Line By Line

Given:

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

This is what each line means:

- `field_queryset_dependencies = { ... }` turns on dependent queryset behavior for one or more fields.
- `"genres": { ... }` says that `genres` is the child form field being restricted.
- `"depends_on": ["author"]` says that `author` is the parent field PowerCRUD must watch and read from.
- `"filter_by": {"authors": "author"}` is the key mapping: left-hand side, `authors`, is the queryset lookup to apply to the child queryset; right-hand side, `author`, is the form field name to read the value from.
- `"order_by": "name"` sorts the remaining child choices by `name` after filtering.
- `"empty_behavior": "all"` leaves the child queryset unfiltered instead of returning no options when the parent value is empty.

So this configuration effectively produces:

```python
Genre.objects.filter(authors=<selected author>).order_by("name")
```

If there is no selected author yet, PowerCRUD keeps the full `Genre` queryset because `empty_behavior` is `"all"`.

---

## General Shape

```python
field_queryset_dependencies = {
    "child_field_name": {
        "depends_on": ["parent_field_name"],
        "filter_by": {"child_queryset_lookup": "parent_field_name"},
        "order_by": "some_field",
        "empty_behavior": "none" | "all",
    }
}
```

Read this as:

> “Restrict `child_field_name` by applying `child_queryset_lookup=<value of parent_field_name>` to the child field queryset.”

---

## How `filter_by` Works

This is the part that usually needs the clearest explanation.

`filter_by` maps:

- left-hand side: queryset lookup on the child field's queryset model
- right-hand side: parent form field name

Example:

```python
"filter_by": {"authors": "author"}
```

Read that as:

> “Filter the child queryset by `authors`, using the current value of the form field `author`.”

That is why the lookup is `authors` and not `author` in the sample app:

- the child field is `genres`
- the queryset behind that field is a `Genre` queryset
- the relation from `Genre` back to `Author` is `Genre.authors`

So PowerCRUD filters the child queryset like:

```python
Genre.objects.filter(authors=selected_author)
```

The general rule is:

- left side = where to filter on the child queryset
- right side = where to get the value from in the form

---

## Supported Keys

### `depends_on`

List of parent form fields that drive the child queryset.

```python
"depends_on": ["author"]
```

Meaning:

> “This child field depends on the current value of `author`.”

Rules:

- each entry must be a form field name
- every parent referenced by `filter_by` must also appear here
- for inline refreshes, the parent field must also be inline-editable

### `filter_by`

Mapping of child queryset lookups to parent form field names.

```python
"filter_by": {"authors": "author"}
```

Meaning:

> “Apply `authors=<value of author>` to the child queryset.”

Use this for straightforward equality-style filtering.

If a parent can provide multiple values, use a lookup ending in `__in`.

### `order_by`

Optional ordering applied after filtering.

```python
"order_by": "name"
```

Meaning:

> “After restricting the queryset, sort the remaining choices by `name`.”

### `empty_behavior`

Controls what happens when a required parent value is empty.

```python
"empty_behavior": "none"
```

Supported values:

- `"none"` returns no child choices until the parent field has a value.
- `"all"` leaves the child queryset unfiltered when the parent field is empty.

Use `"none"` when the unrestricted child list would be noisy, misleading, or too large.

Use `"all"` when the unrestricted list is still useful and reasonably sized.

---

## Value Resolution Order

When PowerCRUD resolves a parent field value, it checks in this order:

1. bound form data
2. the current instance
3. initial form values

That matters because:

- edit forms can render correctly from the saved instance
- inline editing can use the user's current unsaved row values
- validation re-renders keep the same restriction logic

---

## Regular Forms Vs Inline Forms

`field_queryset_dependencies` is shared across both editing modes.

Regular create/update forms:

- the child queryset is scoped on initial render
- the child queryset is scoped again on POST and validation re-render
- regular forms are not automatically refreshed in the browser when the parent changes

Inline editing:

- the same child queryset rule is used
- PowerCRUD derives the dependency wiring automatically
- when the user changes the parent field inline, PowerCRUD rebuilds only the dependent child widget and swaps it back into the row

This means you declare the business rule once in `field_queryset_dependencies`, and PowerCRUD reuses it everywhere.

---

## Worked Example: Sample App `Book.author -> Book.genres`

The sample app uses:

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

## Migrating Older Inline-Only Dependency Patterns

If your project previously relied on an older inline-only dependency pattern, replace it with a full `field_queryset_dependencies` declaration:

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
- automatic inline refresh wiring

Older inline-only dependency config is ignored.

---

## When To Fall Back To `form_class`

Use `field_queryset_dependencies` when the rule is simple and declarative.

Fall back to `form_class`, `get_form()`, or other view overrides when you need:

- permission-aware queryset logic
- tenant-specific logic
- computed business rules that do not map cleanly to form fields
- custom joins or complex query construction
- non-queryset widget behavior

That is the intended boundary of this feature.
