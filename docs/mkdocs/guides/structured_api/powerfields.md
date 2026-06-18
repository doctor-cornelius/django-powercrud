# PowerField

PowerField is the Structured Declaration API for Field Intent.

It is not a contrib app, and it is not a replacement product API. It is a structured declaration layer over the Base Configuration API attributes such as `fields`, `detail_fields`, `form_fields`, `inline_edit_fields`, `bulk_fields`, `default_list_fields`, `field_labels`, `column_help_text`, `list_cell_tooltip_fields`, and `link_fields`.

Use it when the same field participates in several places and the Base Configuration API starts to repeat the same names across many lists and dictionaries.

```python
from powercrud.powerfields import PowerField, PowerOverride
```

## The Rule

Each view inheritance chain must use one Field Intent style:

- Base Configuration API Field Intent attributes, or
- `power_fields`.

Do not mix them in one view or inheritance chain. Surface, Presentation, Action, Selection, Bulk Operation, Async, and Styling settings remain normal class attributes alongside `power_fields`.

That means this is fine:

```python
class BookView(PowerCRUDAsyncMixin, CRUDView):
    model = Book
    namespace = "sample"
    use_htmx = True
    use_modal = True

    power_fields = [
        PowerField("title", default_list=True, form=True),
    ]
```

But this is not:

```python
class BookView(PowerCRUDAsyncMixin, CRUDView):
    model = Book
    fields = ["title", "author"]

    power_fields = [
        PowerField("title", inline=True),
    ]
```

## Why Use It

Base configuration is direct and remains the baseline. PowerField is useful when one field has repeated intent:

??? example "Base Configuration API vs PowerField"

    === "Base Configuration API"

        ```python
        fields = ["title", "author"]
        detail_fields = ["title", "author"]
        form_fields = ["title", "author"]
        inline_edit_fields = ["title"]
        bulk_fields = ["title"]
        default_list_fields = ["title", "author"]
        list_cell_tooltip_fields = {
            "title": "get_title_tooltip",
        }
        field_labels = {
            "title": "DDMS Execution Owner",
        }
        ```

    === "PowerField"

        ```python
        power_fields = [
            PowerField(
                "title",
                detail=True,
                form=True,
                inline=True,
                bulk=True,
                default_list=True,
                label="DDMS Execution Owner",
                tooltip_hook="get_title_tooltip",
            ),
            PowerField(
                "author",
                detail=True,
                form=True,
                default_list=True,
            ),
        ]
        ```

PowerField compiles to the same base configuration before PowerCRUD registers feature URLs, validates config, and builds runtime behaviour.

## Declaration Style

Prefer one `PowerField` entry per field.

```python
PowerField(
    "title",
    default_list=True,
    tooltip_hook="get_title_tooltip",
    form=True,
    inline=True,
    bulk=True,
)
```

That is the main readability win: the field's participation is visible in one place.

`default_list=True` also adds the field to the underlying list allow-list. For property-backed columns, combine it with `property=True`.

Start with the boolean kwargs for field roles. Add dict kwargs such as `column={...}`, `link={...}`, or `queryset_dependencies={...}` only when that field needs richer list-column, link, or choice-scoping behaviour.

PowerCRUD also supports repeating a field across multiple declarations. The compiler merges and de-duplicates the generated base lists, so this works:

```python
PowerField("title", default_list=True, tooltip_hook="get_title_tooltip")
PowerField("title", form=True)
PowerField("title", inline=True, bulk=True)
```

Use that grouped-by-dimension style only when the ordering of separate base lists matters more than seeing each field in one place. For most views, the one-entry-per-field style is easier to reason about.

## Reusing Declarations

Use `with_options(...)` when related views share most of a field declaration but need one or two local changes.

```python
ACTION_STATUS = PowerField(
    "status",
    default_list=True,
    tooltip_hook="get_status_tooltip",
    bulk=True,
)


class ActionCRUDView(PowerCRUDMixin, CRUDView):
    model = Action
    power_fields = [
        ACTION_STATUS,
    ]


class ActionReviewCRUDView(PowerCRUDMixin, CRUDView):
    model = Action
    power_fields = [
        ACTION_STATUS.with_options(bulk=False),
    ]
```

`with_options(...)` returns a new `PowerField`. The original declaration is unchanged, and the copied declaration is validated the same way as a directly constructed `PowerField`.

## Broad List And Detail Defaults

Use `PowerOverride` when you want a broad base sentinel such as `fields = "__all__"` or `detail_fields = "__all__"`.

```python
power_fields = [
    PowerOverride(list="__all__", detail="__all__"),
    PowerField("description", exclude={"list": True}),
]
```

This is explicit. In PowerField mode, absent dimensions do not fall through to the legacy base defaults. If you want broad defaults, opt into them with `PowerOverride`.

??? example "Broad defaults with one list exclude"

    === "Base Configuration API"

        ```python
        fields = "__all__"
        exclude = ["description"]
        detail_fields = "__all__"
        ```

    === "PowerField"

        ```python
        power_fields = [
            PowerOverride(list="__all__", detail="__all__"),
            PowerField("description", exclude={"list": True}),
        ]
        ```

## List Columns, Properties, Help, Links, And Tooltips

Field Intent can also include list-column defaults, properties, header help, semantic tooltip hooks, and declarative links.

??? example "Book list columns"

    === "Base Configuration API"

        ```python
        fields = "__all__"
        properties = ["isbn_empty", "a_really_long_property_header_for_title"]
        default_list_fields = [
            "title",
            "author",
            "published_date",
            "pages",
            "isbn_empty",
        ]
        column_help_text = {
            "pages": "Demo link: opens this book detail in the current page.",
            "isbn_empty": "Shows whether this row currently has an ISBN value.",
        }
        field_labels = {
            "isbn_empty": "ISBN Missing",
        }
        list_cell_tooltip_fields = {
            "pages": "get_pages_tooltip",
            "isbn_empty": "get_isbn_empty_tooltip",
        }
        link_fields = {
            "pages": {
                "view_name": "sample:bigbook-detail",
                "open_in": "current",
            },
        }
        ```

    === "PowerField"

        ```python
        power_fields = [
            PowerOverride(list="__all__"),
            PowerField("title", default_list=True),
            PowerField("author", default_list=True),
            PowerField("published_date", default_list=True),
            PowerField(
                "pages",
                default_list=True,
                tooltip_hook="get_pages_tooltip",
                column={
                    "help_text": (
                        "Demo link: opens this book detail in the current page."
                    ),
                },
                link={
                    "view_name": "sample:bigbook-detail",
                    "open_in": "current",
                },
            ),
            PowerField(
                "isbn_empty",
                property=True,
                default_list=True,
                label="ISBN Missing",
                tooltip_hook="get_isbn_empty_tooltip",
                column={
                    "help_text": "Shows whether this row currently has an ISBN value.",
                },
            ),
            PowerField(
                "a_really_long_property_header_for_title",
                property=True,
            ),
        ]
        ```

`tooltip_hook="..."` maps the visible list cell to a row-specific hook. The hook must exist on the view and returns plain text or `None`.

```python
def get_pages_tooltip(self, obj, request=None):
    return f"Page count: {obj.pages}"
```

Use `column={"help_text": "..."}` for column-header help. Use `tooltip_hook="..."` only for row-specific list-cell tooltips.

`link={...}` accepts the same metadata supported by base `link_fields`. There is no `link=True` shorthand because PowerCRUD needs the link target metadata.

## Forms And Custom Form Classes

PowerField can declare generated form intent with `form=True`, display-only context fields with `form_display=True`, and disabled inputs with `form_disabled=True`.

??? example "Generated form fields"

    === "Base Configuration API"

        ```python
        form_fields = [
            "title",
            "author",
            "published_date",
            "isbn",
            "pages",
            "description",
        ]
        form_display_fields = ["uneditable_field"]
        form_disabled_fields = ["isbn"]
        ```

    === "PowerField"

        ```python
        power_fields = [
            PowerField("title", form=True),
            PowerField("author", form=True),
            PowerField("published_date", form=True),
            PowerField("isbn", form=True, form_disabled=True),
            PowerField("pages", form=True),
            PowerField("description", form=True),
            PowerField("uneditable_field", form_display=True),
        ]
        ```

If the view sets `form_class`, that custom form class remains the runtime source of truth for editable inputs. PowerField form declarations still compile at class-time, but runtime `form_fields` is cleared in the same way as base `form_fields` when `form_class` is configured.

Use this pattern when you want PowerField to document the intended surface while a custom `ModelForm` controls the actual editable form fields.

## Inline, Bulk, And Dependent Choices

Inline and bulk participation stays explicit. Queryset dependencies can be attached to the field that owns the constrained choices.

```python
power_fields = [
    PowerField("title", inline=True, bulk=True),
    PowerField("published_date", inline=True, bulk=True),
    PowerField("bestseller", inline=True, bulk=True),
    PowerField(
        "genres",
        inline=True,
        bulk=True,
        queryset_dependencies={
            "depends_on": ["author"],
            "filter_by": {"authors": "author"},
            "order_by": "name",
            "empty_behavior": "all",
        },
    ),
]
```

Bulk operation flags such as `bulk_delete`, `bulk_async`, and `bulk_min_async_records` are not Field Intent. Keep them as ordinary class attributes.

## Ordering

PowerField preserves declaration order for each base list it generates.

If different surfaces need different field order, repeat the field in separate dimension-specific declarations.

```python
power_fields = [
    PowerField("title", default_list=True),
    PowerField("author", default_list=True),
    PowerField("published_date", default_list=True),
    PowerField("title", inline=True),
    PowerField("published_date", inline=True),
]
```

PowerCRUD de-duplicates each generated base list while preserving first occurrence.

## What PowerField Does Not Cover

PowerField covers Field Intent only.

Keep these as normal view configuration:

- `filterset_fields` and `default_filterset_fields`
- `bulk_delete`, `bulk_full_clean`, `bulk_async`, and other bulk operation flags
- `extra_buttons`, `extra_actions`, and action hooks
- `use_htmx`, `use_modal`, modal settings, and template paths
- table classes, button classes, widths, and other styling options

## Sample App

The sample app includes `PowerFieldBookCRUDView`, visible as **PowerField Books**.

It is a sibling of the base `BookCRUDView`, not a subclass. The backend tests compare its resolved base Field Intent config against `BookCRUDView`, with intentional differences for the clearer PowerField list allow-list and self-contained route names.

See [Choosing an API Style](index.md), [Sample app overview](../../reference/sample_app.md), and the [PowerField reference](../../reference/powerfields.md) for the full API contract.
