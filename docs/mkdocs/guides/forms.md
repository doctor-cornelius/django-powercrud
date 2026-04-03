# Forms

After [Setup & Core CRUD basics](./setup_core_crud.md), the next step is understanding how PowerCRUD builds and enhances forms. This guide brings the form-related settings into one place:

- auto-generated forms vs custom `form_class`
- `form_fields` and `form_fields_exclude`
- `form_display_fields` and `form_disabled_fields`
- `field_queryset_dependencies` for dependent dropdowns
- how those same dependency rules carry across to inline editing

---

## Mental model

PowerCRUD has two layers for forms:

1. Form construction
2. Runtime enhancements applied after the form exists

When you do **not** set `form_class`, PowerCRUD generates a `ModelForm` for you and uses parameters such as `form_fields` and `form_fields_exclude` to decide which editable fields belong on that form.

When you **do** set `form_class`, that custom Django form becomes the source of truth for editable form fields. In that case, `form_fields` and `form_fields_exclude` no longer shape the editable form.

Runtime enhancements still apply after the custom form is built. That includes:

- `form_display_fields`
- `form_disabled_fields`
- `field_queryset_dependencies`
- `dropdown_sort_options`
- `searchable_selects`
- `use_crispy`

???+ note "Relationship Between form_class and PowerCRUD Form Parameters"

    `form_class` replaces PowerCRUD's editable form generation.

    If you configure a custom `form_class`, do not also rely on `form_fields` or `form_fields_exclude` to shape the editable form. Those parameters only matter when PowerCRUD is generating the form class for you.

    Runtime PowerCRUD features still apply after the custom form is built.

---

## Shaping an auto-generated form

Use `form_fields` when you want PowerCRUD to generate the form and you want to control which editable fields appear and in what order.

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = Book
    form_fields = ["title", "author", "genres", "published_date", "isbn"]
```

Key rules:

- `form_fields` only applies to auto-generated forms
- `form_fields` can only include editable model fields
- `form_fields = "__fields__"` mirrors the resolved list fields
- `form_fields = "__all__"` includes every editable model field

Use `form_fields_exclude` when you want to start from the automatic selection and remove a few fields:

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = Book
    form_fields = "__all__"
    form_fields_exclude = ["created_by", "updated_at"]
```

That is usually the cleanest path when most fields belong on the form and only a few should be hidden.

---

## Using a custom form_class

Use `form_class` when the form needs real Django form behavior that goes beyond declarative field selection.

Typical reasons:

- custom validation
- custom widgets
- field-level cleaning
- queryset logic that does not fit the declarative dependency API
- form-specific behavior that should live in the form layer

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = Book
    form_class = forms.BookForm
```

With that in place:

- `form_class` decides the editable form fields
- `form_fields` and `form_fields_exclude` no longer shape the editable form
- PowerCRUD still applies runtime helpers such as `form_disabled_fields` and `field_queryset_dependencies`

---

## Persisting validated standard forms

Once the form is valid, PowerCRUD routes the standard create/update write through `persist_single_object(...)`:

For the canonical contract, see the [Hooks reference](../reference/hooks.md#persist_single_object).

If you want a fuller walkthrough of how to route validated saves through an app service, see [Persistence Hooks for Real Write Logic](advanced/persistence_hooks_sync.md).

```python
def persist_single_object(self, *, form, mode, instance=None):
    return form.save()
```

For the standard object form flow:

- `mode` is `"form"`
- `instance` is the bound `form.instance`
- the return value becomes `self.object`

Use this hook when your app wants PowerCRUD to keep validation, modal handling, and HTMX response logic, but wants the actual write to pass through an application service.

Example:

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    def persist_single_object(self, *, form, mode, instance=None):
        book = form.save(commit=False)
        book = BookWriteService().save(book=book, mode=mode)
        form.instance = book
        form.save_m2m()
        return book
```

Important:

- If you call `form.save()` directly, Django handles the normal `ModelForm` save path.
- If you bypass `form.save()` and build your own persistence flow, your override owns any required `form.save_m2m()` handling.
- The same public hook name is also used by inline editing, so downstream code can centralize single-object write orchestration.

---

## Showing contextual read-only fields

Use `form_display_fields` when users need to see contextual model values while editing, but those values are not editable form inputs.

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = Book
    form_display_fields = ["uneditable_field"]
```

This is the right setting for:

- model fields with `editable=False`
- reference identifiers the user should see but never edit
- contextual values that help the user understand what they are editing

Behavior:

- PowerCRUD renders these values in a separate read-only `Context` area above update forms
- they are not editable inputs
- they are not submitted with the form
- they are hidden on create forms because there is no saved instance to display yet
- they remain the right place for `editable=False` model fields that you want users to see in normal edit flows, instead of trying to place those fields in `form_fields`, `inline_edit_fields`, or `bulk_fields`

---

## Showing real form fields as disabled

Use `form_disabled_fields` when a field should still appear as a real form control, but users should not change it.

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = Book
    form_disabled_fields = ["isbn"]
```

Behavior:

- the field remains visible on update forms
- PowerCRUD disables the Django form field, not just the widget
- submitted tampering is ignored and the existing instance value is preserved
- this applies to update forms only, not create forms or inline editing

This solves a different problem from `form_display_fields`:

- `form_display_fields` shows a contextual value, not a form input
- `form_disabled_fields` keeps a real form input visible but locked

---

## Combining editable, disabled, and display-only fields

These parameters can work together cleanly:

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = Book
    form_class = forms.BookForm
    form_display_fields = ["uneditable_field"]
    form_disabled_fields = ["isbn"]
```

In that example:

- `BookForm` defines the editable form fields
- `uneditable_field` is shown separately for context
- `isbn` stays on the actual form but is disabled

This gives users more context without forcing you to build a bespoke template.

---

## Dependent form fields

Use `field_queryset_dependencies` when the available choices in one form field should depend on the current value of another form field, or when a queryset-backed field should always be restricted by a fixed rule.

Typical examples:

- the available `genres` depend on the selected `author`
- the available `rooms` depend on the selected `building`
- the available `assets` depend on the selected `asset_type`

PowerCRUD applies the same rule to:

- regular create/update forms
- inline row editing forms

!!! note "Bulk edit and static rules"

    Static queryset rules declared via `static_filters` also apply to bulk edit dropdowns.

    Dynamic parent/child dependency rules still apply only to regular and inline forms, because bulk selections may contain rows with different parent values.

    If you override `get_bulk_choices_for_field()`, that override takes full control for bulk and PowerCRUD does not re-apply declarative static filters afterwards.

For complex business rules, permission-aware filtering, or bespoke queryset logic, keep using a custom `form_class` or view override.

### The setting

`field_queryset_dependencies` is the public setting for dependent queryset scoping.

Use it to describe:

- which child field is being restricted
- which parent field or fields it depends on
- which fixed queryset filters should always apply
- how parent values map into queryset filters on the child field
- what to do when the parent value is empty
- how to order the resulting child queryset

Example:

```python
field_queryset_dependencies = {
    "genres": {
        "static_filters": {"is_active": True},
        "depends_on": ["author"],
        "filter_by": {"authors": "author"},
        "order_by": "name",
        "empty_behavior": "all",
    }
}
```

Inline dependency wiring is derived automatically from this setting. There is no separate inline dependency configuration to maintain.

### Mental model

Think of each dependency as having four parts:

- a **child field**, which is the field whose choices should change
- an optional **static restriction**, which always applies to the child queryset
- one or more **parent fields**, whose current values drive the child queryset
- a **queryset mapping**, which says how the parent values should be applied to the child field's queryset

For the example above:

- `genres` is the child field
- `author` is the parent field
- `authors` is the queryset lookup used on the `Genre` queryset

In plain English, the example means:

> “Show genre choices that belong to the selected author. If no author is selected yet, still show all genres.”

### Line by line

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

- `field_queryset_dependencies = { ... }` turns on dependent queryset behavior for one or more fields
- `"genres": { ... }` says that `genres` is the child form field being restricted
- `"depends_on": ["author"]` says that `author` is the parent field PowerCRUD must watch and read from
- `"filter_by": {"authors": "author"}` is the key mapping: left-hand side, `authors`, is the queryset lookup to apply to the child queryset; right-hand side, `author`, is the form field name to read the value from
- `"order_by": "name"` sorts the remaining child choices by `name` after filtering
- `"empty_behavior": "all"` leaves the child queryset unfiltered instead of returning no options when the parent value is empty

So this configuration effectively produces:

```python
Genre.objects.filter(authors=<selected author>).order_by("name")
```

If there is no selected author yet, PowerCRUD keeps the full `Genre` queryset because `empty_behavior` is `"all"`.

### General shape

```python
field_queryset_dependencies = {
    "child_field_name": {
        "static_filters": {"always_on_lookup": "value"},
        "depends_on": ["parent_field_name"],
        "filter_by": {"child_queryset_lookup": "parent_field_name"},
        "order_by": "some_field",
        "empty_behavior": "none" | "all",
    }
}
```

Read this as:

> “Restrict `child_field_name` by applying `child_queryset_lookup=<value of parent_field_name>` to the child field queryset.”

### How filter_by works

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

### Supported keys

#### depends_on

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

#### static_filters

Mapping of fixed queryset lookups that should always apply to the child field.

```python
"static_filters": {"side__in": ["analytics", "both"]}
```

Meaning:

> “Always restrict the child queryset using these fixed filters, even when no parent field is involved.”

Use this for static dropdown subsets such as status dictionaries, scoped reference tables, or side-specific exclusion reasons.

Static filters apply to:

- regular create/update forms
- inline row editing forms
- bulk edit dropdowns, unless `get_bulk_choices_for_field()` is overridden

#### filter_by

Mapping of child queryset lookups to parent form field names.

```python
"filter_by": {"authors": "author"}
```

Meaning:

> “Apply `authors=<value of author>` to the child queryset.”

Use this for straightforward equality-style filtering.

If a parent can provide multiple values, use a lookup ending in `__in`.

#### order_by

Optional ordering applied after filtering.

```python
"order_by": "name"
```

Meaning:

> “After restricting the queryset, sort the remaining choices by `name`.”

#### empty_behavior

Controls what happens when a required parent value is empty.

```python
"empty_behavior": "none"
```

Supported values:

- `"none"` returns no child choices until the parent field has a value
- `"all"` leaves the child queryset unfiltered when the parent field is empty

Use `"none"` when the unrestricted child list would be noisy, misleading, or too large.

Use `"all"` when the unrestricted list is still useful and reasonably sized.

### Value resolution order

When PowerCRUD resolves a parent field value, it checks in this order:

1. bound form data
2. the current instance
3. initial form values

That matters because:

- edit forms can render correctly from the saved instance
- inline editing can use the user's current unsaved row values
- validation re-renders keep the same restriction logic

### Static-only example

```python
field_queryset_dependencies = {
    "reconciliation_exclude_reason": {
        "static_filters": {
            "side__in": [
                ReconciliationSide.ANALYTICS,
                ReconciliationSide.BOTH,
            ],
        },
        "order_by": "sort_order",
    }
}
```

This means:

- regular forms only show analytics-or-both exclusion reasons
- inline forms use the same restricted queryset
- bulk edit dropdowns use the same restricted queryset

No `depends_on` or `filter_by` block is required when the rule is fully static.

### Regular forms vs inline forms

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

### Worked example: sample app Book.author -> Book.genres

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
- [Sample application](../reference/sample_app.md)

### Migrating older inline-only dependency patterns

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

## When to fall back to form_class

Use PowerCRUD's declarative form settings when the behavior is simple and repetitive.

Fall back to `form_class`, `get_form()`, or view overrides when you need:

- permission-aware queryset logic
- tenant-specific logic
- computed business rules that do not map cleanly to form fields
- custom joins or complex query construction
- custom validation
- non-queryset widget behavior

That is the intended boundary of the declarative form API.
