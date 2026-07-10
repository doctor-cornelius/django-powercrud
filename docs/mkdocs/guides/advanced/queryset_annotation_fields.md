# Queryset Annotation Fields

This guide is about the queryset declaration side of annotation-backed list fields: how to declare annotations so PowerCRUD can discover them, type them, render them, sort them, and generate filters for them.

For the general filtering workflow, keep using [Filtering](../filtering.md). For a short copyable pattern, see [Annotated Operational Columns](recipes.md#annotated-operational-columns).

## The Minimal Contract

PowerCRUD supports queryset annotation fields when all of these are true:

- the value is declared with Django `annotate(...)`
- the annotation name is the same public name used in PowerCRUD config
- the annotation expression exposes a useful `output_field`
- the name is used on read-only list/filter surfaces, not editable form surfaces

```python
from django.db.models import BooleanField, Case, Value, When


class BookQueueCRUDView(PowerCRUDMixin, CRUDView):
    model = Book

    def get_queryset(self):
        """Attach the exact public annotation name used below."""
        return super().get_queryset().annotate(
            long_book=Case(
                When(pages__gte=400, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    fields = ["title", "author", "pages", "long_book", "published_date"]
    filterset_fields = ["author", "long_book", "pages"]
    default_filterset_fields = ["author", "long_book"]
```

`long_book` is now a first-class list/filter/sort column, but it is still not a model field.

## Static Queryset Declarations

Class-level querysets are the easiest declaration to reason about:

```python
class BookQueueCRUDView(PowerCRUDMixin, CRUDView):
    model = Book

    queryset = Book.objects.select_related("author").annotate(
        long_book=Case(
            When(pages__gte=400, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    )

    fields = ["title", "author", "long_book"]
    filterset_fields = ["author", "long_book"]
```

PowerCRUD can inspect `queryset.query.annotations` during view setup without evaluating the queryset.

Use this shape when the annotation does not depend on the request, user, permissions, query parameters, or runtime context.

## Request-Time Queryset Declarations

Use `get_queryset()` when the annotation depends on request-time context or when you already build the queryset dynamically:

```python
class CaseQueueCRUDView(PowerCRUDMixin, CRUDView):
    model = Case

    def get_queryset(self):
        """Annotate after the parent queryset has been built."""
        queryset = super().get_queryset()
        return queryset.annotate(
            needs_review=Case(
                When(status="blocked", then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    fields = ["reference", "status", "needs_review"]
    filterset_fields = ["status", "needs_review"]
```

At initialization time, `request` may not exist yet. PowerCRUD therefore validates unresolved non-model names once the effective queryset exists for the request.

## Name Matching

The annotation name is the public column name.

This works:

```python
queryset = Book.objects.annotate(
    long_book=Case(..., output_field=BooleanField()),
)

fields = ["title", "long_book"]
filterset_fields = ["long_book"]
```

This does not:

```python
queryset = Book.objects.annotate(
    _long_book=Case(..., output_field=BooleanField()),
)

fields = ["title", "long_book"]
filterset_fields = ["long_book"]
```

PowerCRUD does not infer that `_long_book` is meant to back `long_book`. There is no alias/source-name mapping in this feature.

## Type Declarations With `output_field`

PowerCRUD uses the annotation expression's `output_field` to choose display and generated-filter behavior.

Boolean example:

```python
long_book=Case(
    When(pages__gte=400, then=Value(True)),
    default=Value(False),
    output_field=BooleanField(),
)
```

Number example:

```python
from django.db.models import Count


genre_count=Count("genres", distinct=True)
```

Text example:

```python
from django.db.models import CharField, Value
from django.db.models.functions import Concat


display_reference=Concat(
    "author__name",
    Value(" / "),
    "title",
    output_field=CharField(),
)
```

For simple expressions, Django may infer the output field. For `Case`, `Value`, mixed-type expressions, and anything ambiguous, declare it explicitly.

If PowerCRUD cannot infer a usable type for a generated annotation filter, it raises a configuration error asking for `output_field`.

## Generated Filter Mapping

When an annotation name appears in `filterset_fields`, PowerCRUD maps its `output_field` like a model field:

- `BooleanField` becomes a boolean select.
- `CharField` and `TextField` become text filters with `icontains`.
- integer, decimal, and float fields become number filters.
- `DateField` becomes a date input.
- `TimeField` becomes a time input.

Relation output fields are not generated as annotation filters. Use a real model relation field or a custom `filterset_class` for that.

If `filterset_class` is set, it takes precedence and PowerCRUD does not generate filters from `filterset_fields`.

## Sorting

Annotation columns sort by the public annotation name:

```text
?sort=long_book
?sort=-long_book
```

PowerCRUD adds secondary `pk` ordering for stable pagination.

Use `column_sort_fields_override` only when the visible annotation column should sort by a different expression:

```python
column_sort_fields_override = {
    "long_book": "-pages",
}
```

Most annotation columns do not need an override.

## Display And Editability

Annotation fields are read-only field cells:

- valid in `fields`
- valid in `filterset_fields`
- valid in `default_filterset_fields`
- valid in `column_help_text`
- valid in `column_alignments`
- valid in `column_value_formats` when the annotation has an inferable `DateField`, `TimeField`, or `DateTimeField` `output_field`
- valid in `list_cell_tooltip_fields`
- valid in `link_fields`
- invalid in `form_fields`
- invalid in `inline_edit_fields`
- invalid in `bulk_fields`

Mixing editable model fields and read-only annotation fields is fine:

```python
fields = ["title", "pages", "long_book"]
inline_edit_fields = ["pages"]
```

The model field `pages` can be edited inline. The annotation field `long_book` remains read-only.

## Workable Declaration

```python
class ActionQueueCRUDView(PowerCRUDMixin, CRUDView):
    model = Action

    def get_queryset(self):
        return super().get_queryset().annotate(
            analytics_status_ok=Case(
                When(analytics_status="ok", then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    fields = ["reference", "analytics_status_ok", "created_at"]
    filterset_fields = ["analytics_status_ok"]
    inline_edit_fields = []
    bulk_fields = []
```

Why it works:

- `analytics_status_ok` is declared by `annotate(...)`.
- The same name appears in `fields` and `filterset_fields`.
- The annotation has `output_field=BooleanField()`.
- The annotation is not used as an editable field.

## Non-Workable Declarations

Different private source name:

```python
queryset = Action.objects.annotate(_analytics_status_ok=Case(...))
fields = ["analytics_status_ok"]
```

Missing annotation:

```python
fields = ["analytics_status_ok"]
```

Annotation in editable config:

```python
fields = ["analytics_status_ok"]
inline_edit_fields = ["analytics_status_ok"]
```

Ambiguous generated filter type:

```python
queryset = Action.objects.annotate(analytics_status_ok=Value(None))
filterset_fields = ["analytics_status_ok"]
```

Use `output_field` when the annotation should be filterable.

## Sample App

The sample app includes `AnnotatedBookCRUDView` at:

```text
/sample/annotated-book/
```

The top navigation labels it **Annotated Books**. It demonstrates a `long_book` boolean annotation, generated filtering, annotation sorting, `pages` as an inline-editable model field, and `long_book` as a read-only annotation field.
