# Filtering

PowerCRUD's filtering support now has enough moving parts that it deserves its own guide rather than living only inside the basic setup walkthrough.

Use this page when you want to understand:

- the normal `filterset_fields` path
- the default vs optional filter split
- null helpers and filter visibility
- how custom `filterset_class` interacts with the rest of the filtering UX

For the raw configuration matrix, see [Configuration Options](../reference/config_options.md#filter-controls).

## Start with generated filters

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    use_htmx = True
    filterset_fields = ["owner", "status", "created_date"]
    default_filterset_fields = ["owner", "status"]
```

What happens by default:

- With no `filterset_fields`, the view renders the list immediately and ignores any query parameters except `page`, `page_size`, and `sort`.
- Setting `filterset_fields` automatically builds a `django-filter` `FilterSet` for those fields, including sensible widgets based on field type and optional HTMX attributes if `use_htmx` is True.
- Leave `default_filterset_fields` unset to keep the current behavior and show every allowed filter immediately.
- Set `default_filterset_fields` to a smaller subset when some filters should be visible by default and the rest should stay behind the built-in `Add filter` control.
- Once an optional filter is shown, it stays visible until the user explicitly removes it, even if its current value is empty.
- PowerCRUD persists optional filter visibility through the reserved `visible_filters` query parameter, so shared URLs can still open the same optional filters explicitly.
- When HTMX is enabled, PowerCRUD also remembers optional filter visibility in browser-local storage for the current list route. That browser-local state restores the same optional filters on later refreshes or revisits without preserving any filter values.

## Default vs optional filters

`default_filterset_fields` is the key to the more compact filter layout.

- Treat `filterset_fields` or the effective fields from `filterset_class` as the full set of allowed filters.
- Treat `default_filterset_fields` as the subset visible on first render.
- Everything allowed but not included in `default_filterset_fields` becomes optional and is exposed through the built-in `Add filter` control.

Example:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    filterset_fields = [
        "owner",
        "status",
        "created_date",
        "priority",
        "customer",
    ]
    default_filterset_fields = ["owner", "status"]
```

In that example:

- `owner` and `status` are visible immediately
- `created_date`, `priority`, and `customer` remain allowed filters
- users can reveal those optional filters as needed through `Add filter`

PowerCRUD validates `default_filterset_fields` against the effective bound filter names, not only against raw model field names.

## Null helpers

Nullable auto-generated filters behave differently by field type:

- Nullable `ForeignKey` and `OneToOneField` filters keep a single dropdown and add an `Empty only` option near the top.
- Nullable scalar filters such as `CharField`, `TextField`, `DateField`, `TimeField`, `IntegerField`, `DecimalField`, `FloatField`, and `BooleanField` gain a separate companion `... is empty` boolean select.
- Companion null controls are rendered immediately after their parent auto-generated filter field in the form.

Use `filter_null_fields_exclude` when you want to opt specific generated filters out of those helpers.

- Use original field names from `filterset_fields`, for example `["birth_date", "favorite_genre"]`.
- Do not use generated companion names such as `birth_date__isnull`.
- Excluding a nullable scalar field suppresses the companion `... is empty` control.
- Excluding a nullable relation field suppresses the merged `Empty only` option.

Example:

```python
filterset_fields = ["owner", "published_date", "status"]
default_filterset_fields = ["owner"]
filter_null_fields_exclude = ["status"]
```

In that configuration:

- `owner` stays visible by default and keeps one dropdown with `Empty only`
- `published_date` remains allowed, starts hidden, and gains a separate `Published date is empty` companion filter when added
- `status` remains allowed but gets no built-in null helper

## Filterset parameters on the generated path

Use these when you are on the auto-generated `filterset_fields` path:

- Use `filter_queryset_options` or `dropdown_sort_options` to scope or sort the choices in generated dropdowns.
- Toggle `m2m_filter_and_logic = True` if many-to-many filters must match all selected values instead of the default OR behavior.
- With `searchable_selects = True` (default), filter select widgets are Tom Select-enhanced: single-selects become searchable dropdowns and M2M filters become searchable multi-select controls.

Auto-generated text filters use `icontains` by default. There is no separate declarative setting to change that lookup expression field by field. If you need custom lookup behavior such as `iexact`, `startswith`, or range-style filters, switch to a custom `filterset_class`.

## Sorting behavior

Sorting is wired into the table headers.

- Clicking a column toggles `?sort=field` and `?sort=-field` on the URL.
- PowerCRUD applies that ordering server-side and always adds a secondary `pk` sort so pagination stays stable.
- Properties can be sorted too, as long as the property name is listed in `properties`.
- Direct relation columns such as `author` sort by `author__name` automatically when the related model has a concrete `name` field.

If a column should sort by something else, configure `column_sort_fields_override`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    column_sort_fields_override = {
        "owner": "owner__email",
        "customer": "customer__code",
    }
```

`column_sort_fields_override` is an override map, not an exhaustive declaration. If a sortable list field is not present, PowerCRUD falls back to the normal default for that field.

## Custom filtersets

If you need hand-crafted filters, switch to a custom `filterset_class`.

???+ note "filterset_fields vs filterset_class"

    `filterset_fields` and `filterset_class` are alternative strategies.

    If you set `filterset_class`, it takes precedence and PowerCRUD does not auto-generate filters from `filterset_fields`.

    These settings only shape the auto-generated `filterset_fields` path:

    - `filter_queryset_options`
    - `filter_null_fields_exclude`
    - `m2m_filter_and_logic`
    - filter-side `dropdown_sort_options`

    These behaviors still apply to both generated and custom filtersets after the filterset exists:

    - `default_filterset_fields`
    - `searchable_selects`
    - HTMX widget attrs when `use_htmx = True` and the custom filterset exposes `setup_htmx_attrs()`

    For custom filtersets, the recommended pattern is still to subclass `HTMXFilterSetMixin` when you want reactive filtering.

`default_filterset_fields` still works with a custom filterset. Validation happens against the effective filter names exposed by the bound form, including custom declared filter names.

If you want a generated text filter to use a different lookup than the default `icontains`, move that filter into a custom `filterset_class`.

## HTMX and page behavior

HTMX is optional but recommended.

- When enabled, filter submissions post back to the list endpoint and the results replace the list region without a full reload.
- Pagination automatically resets to page 1 after each filter submit.
- Optional filter visibility is also remembered in browser-local storage for the current list route, without preserving actual filter values.

## Optional saved favourites

Saved filter favourites build on top of the filtering system, but they live in an optional contrib app and have their own installation and persistence concerns.

See [Saved Filter Favourites](advanced/filter_favourites.md).
