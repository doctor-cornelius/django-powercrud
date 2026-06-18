# Choosing an API Style

PowerCRUD has two supported API styles.

The **Base Configuration API** uses class attributes, hooks, lists, and dictionaries directly. It is the underlying contract, and it remains the best place to start when learning a feature or configuring a one-off view.

The **Structured Declaration API** uses `PowerField`, `PowerAction`, and `PowerButton` to group repeated intent into reusable declaration objects. Structured declarations compile back to the same base configuration, so both styles use the same runtime behavior.

## When To Use The Base Configuration API

Use the Base Configuration API when:

- you are building your first PowerCRUD view;
- the view has only a few fields, buttons, or actions;
- you want the most direct mapping to the configuration reference;
- you are using hooks or dictionaries that are clearer inline.

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = Book

    fields = ["title", "author", "status"]
    form_fields = ["title", "author", "status"]
    inline_edit_fields = ["status"]
    bulk_fields = ["status"]
```

This is already declarative: you state the configured columns and capabilities, and PowerCRUD builds the forms, tables, URLs, validation, and HTMX behavior.

## When To Use The Structured Declaration API

Use the Structured Declaration API when repeated field or action intent starts to obscure the view.

```python
from powercrud.powerfields import PowerField


STATUS_FIELD = PowerField(
    "status",
    default_list=True,
    form=True,
    inline=True,
    bulk=True,
)


class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = Book

    power_fields = [
        PowerField("title", default_list=True, form=True),
        PowerField("author", default_list=True, form=True),
        STATUS_FIELD,
    ]
```

This keeps related intent close to the thing it describes. The `status` field's list, form, inline, and bulk roles are visible in one declaration instead of being repeated across several class attributes.

## Important Style Rules

`PowerField` is exclusive for Field Intent within a view inheritance chain. Choose one style for field intent:

- Base Configuration API attributes such as `fields`, `properties`, `detail_fields`, `form_fields`, `inline_edit_fields`, `bulk_fields`, `field_labels`, `column_help_text`, `list_cell_tooltip_fields`, and `link_fields`; or
- `power_fields` using `PowerField` and optional `PowerOverride`.

Do not mix those Field Intent styles in the same view inheritance chain.

`PowerAction` and `PowerButton` are different. They can be mixed with base dictionaries inside `extra_actions` and `extra_buttons`.

```python
extra_actions = [
    ROW_PREVIEW,
    {
        "url_name": "library:book-history",
        "text": "History",
        "display_modal": True,
    },
]
```

## What To Read Next

- [PowerField](powerfields.md) for structured field intent.
- [PowerAction and PowerButton](poweractions.md) for reusable row actions and toolbar buttons.
- [Structured API Recipes](recipes.md) for side-by-side base and structured examples.
- [Configuration Options](../../reference/config_options.md) for the Base Configuration API reference.
