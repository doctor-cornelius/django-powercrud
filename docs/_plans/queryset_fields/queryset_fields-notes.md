# Queryset Fields Notes

## Problem Summary

PowerCRUD currently treats `fields` as model fields only. Validation checks names against `model._meta.get_fields()`, and list rendering later assumes every `fields` entry can be looked up with `obj._meta.get_field(...)`.

That blocks operational list screens where the most useful columns are queryset-derived values: status health flags, mismatch booleans, counts, rollups, workflow recommendations, or other calculated values.

The current `properties` escape hatch is not enough because properties are rendered after `fields`. That means computed operational values cannot be placed exactly where the user wants them in the list scan order.

## Public API Decision

Do not add a new `queryset_fields` setting in the first version.

Use the existing `fields` and `filterset_fields` settings:

```python
class DDMActionCRUDView(PowerCRUDMixin, CRUDView):
    model = DDMAction

    queryset = DDMAction.objects.annotate(
        analytics_status_ok=Case(
            When(..., then=Value(False)),
            default=Value(True),
            output_field=BooleanField(),
        ),
    )

    fields = [
        "id",
        "a_id",
        "analytics_status_ok",
    ]

    filterset_fields = [
        "analytics_status_ok",
    ]
```

The contract is:

1. `fields` may contain model field names and queryset annotation names.
2. `filterset_fields` may contain model field names and queryset annotation names.
3. Annotation names must match the public names used in PowerCRUD config.
4. Annotation fields are read-only list/filter/sort fields.
5. Annotation fields are not valid for `form_fields`, `inline_edit_fields`, or `bulk_fields`.
6. `properties` keep their existing behaviour and remain separate from annotation-backed first-class fields.

## Queryset Annotations In Plain Terms

A Django queryset is the database query before it is run:

```python
DDMAction.objects.all()
```

`annotate()` adds calculated columns to each returned row:

```python
DDMAction.objects.annotate(
    analytics_status_ok=Case(..., output_field=BooleanField()),
)
```

After that, each returned object can be read like it has an extra attribute:

```python
action.analytics_status_ok
```

PowerCRUD can inspect the queryset to discover that `analytics_status_ok` exists and that Django considers it a boolean value.

## Why Not `queryset_fields` For Version 1

The first version does not need a separate declaration if the annotation uses the same public name as the configured column.

This works:

```python
queryset = DDMAction.objects.annotate(
    analytics_status_ok=Case(..., output_field=BooleanField()),
)

fields = ["id", "analytics_status_ok"]
filterset_fields = ["analytics_status_ok"]
```

This should fail with pure introspection:

```python
queryset = DDMAction.objects.annotate(
    _analytics_status_ok=Case(..., output_field=BooleanField()),
)

fields = ["id", "analytics_status_ok"]
```

PowerCRUD cannot safely infer that `_analytics_status_ok` is intended to back the public column `analytics_status_ok`. The first-version answer is to annotate with the public name:

```python
queryset = DDMAction.objects.annotate(
    analytics_status_ok=Case(..., output_field=BooleanField()),
)
```

Alias mapping and richer metadata are out of scope for this feature. If a queryset value is intended to be a PowerCRUD field, the annotation name should be the public name used in `fields` and `filterset_fields`.

## Use `annotate()`

Use `annotate()` for PowerCRUD fields.

`annotate()` adds a calculated value to each returned object, which makes it suitable for display as a list cell.

Do not support other queryset expression APIs in this feature. Version 1 should document `annotate()` as the supported path.

## Type Inference And `output_field`

PowerCRUD should use queryset introspection for mechanics:

1. Label fallback from the annotation name.
2. Display formatting from the annotation `output_field`.
3. Sort expression from the public annotation name.
4. Filter widget and filter class from the annotation `output_field`.

For simple expressions, Django may expose enough type information automatically. For complex expressions, users should provide an explicit `output_field`.

Examples:

```python
analytics_status_ok=Case(
    When(..., then=Value(False)),
    default=Value(True),
    output_field=BooleanField(),
)
```

```python
open_issue_count=Count("blocking_issues", output_field=IntegerField())
```

If PowerCRUD cannot infer a usable type for a requested annotation filter, it should raise a clear configuration error asking for an explicit `output_field`.

## Timing Decision

Timing is solvable with two-stage validation.

Class-level querysets can be inspected during view initialization:

```python
class DDMActionCRUDView(PowerCRUDMixin, CRUDView):
    queryset = DDMAction.objects.annotate(
        analytics_status_ok=Case(..., output_field=BooleanField()),
    )
```

PowerCRUD can inspect:

```python
self.queryset.query.annotations
```

without evaluating the queryset.

Request-time querysets need deferred validation:

```python
def get_queryset(self):
    return super().get_queryset().annotate(
        analytics_status_ok=Case(..., output_field=BooleanField()),
    )
```

At `__init__`, `self.request` may not exist yet. PowerCRUD should validate model fields early and defer unresolved non-model names until the effective queryset is available during the request.

## Filtering Direction

Generated `filterset_fields` should support annotation names when the annotation has usable type metadata.

Candidate mapping:

1. `BooleanField` to `BooleanFilter` with the existing boolean-select UI.
2. `CharField` and `TextField` to `CharFilter(lookup_expr="icontains")`.
3. Integer, decimal, and float fields to `NumberFilter`.
4. `DateField` to `DateFilter`.
5. `TimeField` to `TimeFilter`.
6. Unknown supported scalar fields to the current fallback text filter only when safe.

Custom `filterset_class` remains unchanged and continues to take precedence over generated filters.

## Sorting Direction

Annotation-backed `fields` should be sortable by default using the public annotation name:

```text
?sort=analytics_status_ok
```

PowerCRUD should translate that to:

```python
queryset.order_by("analytics_status_ok", "pk")
```

`column_sort_fields_override` should remain available when a view needs a different sort expression.

## Rendering Direction

List rendering should stop assuming every `fields` entry is a model field.

For model fields, keep the existing model-field rendering path.

For annotation fields:

1. Read the value with `getattr(obj, field_name)`.
2. Format booleans with the existing tick/cross display.
3. Format dates consistently with model date fields.
4. Use the existing alignment, help text, semantic tooltip, and link hooks where applicable.

Annotation fields should be treated as field cells, not property cells, because they are in `fields` order and represent first-class list/query columns.

## Backwards Compatibility

This should be additive.

Existing views with only model fields keep current behaviour. Existing `properties` keep their current ordering and rendering. Existing custom filtersets keep their current behaviour. Existing invalid names still fail, but error messages should say the name is not a model field or queryset annotation.

Editable configuration remains intentionally stricter. Annotation fields are read-only and should not become valid for forms, inline editing, or bulk editing.

## Product Value

This feature makes PowerCRUD substantially stronger for operational screens, dashboards, and triage queues.

It supports:

1. Workflow health booleans.
2. Status mismatch indicators.
3. Annotated counts and rollups.
4. SLA or priority calculations.
5. Source-system recommendation flags.
6. Query-efficient display values that should filter and sort like normal columns.

The major user-facing win is that these values can appear exactly where the developer places them in `fields`, rather than being appended after model fields through `properties`.

## Out Of Scope

This feature should stay narrow.

Out of scope:

1. A new `queryset_fields` setting.
2. Mapping one public column name to a differently named annotation.
3. Supporting non-`annotate()` queryset expressions as PowerCRUD fields.
4. Making Python-only `@property` values first-class fields unless backed by a matching queryset annotation name.
