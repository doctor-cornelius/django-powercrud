# Sample Application

## Overview

The `sample` app provides a comprehensive demonstration of django-powercrud features using a realistic book/author management system. It serves as both a testing environment during development and a reference implementation for developers learning the package.

## Models

The sample app includes four interconnected models that showcase different relationship types and field configurations:

=== "Author"

    - Basic fields: `name`, `bio`, `birth_date`
    - Many-to-many: `genres` relationship used to constrain inline Book genre choices
    - Properties: `has_bio`, `property_birth_date` 
    - Demonstrates property display in list/detail views

=== "Book"  

    - Core fields: `title`, `author` (ForeignKey), `published_date`, `isbn`, `pages`
    - Many-to-many: `genres` relationship
    - Advanced features: 
    - `isbn_empty` GeneratedField for complex database expressions
    - `uneditable_field` for testing non-editable fields
    - Custom `clean()` and `save()` methods
    - Delayed `delete()` method for async testing
    - Properties with custom display names
    - Unique constraint on `title` + `author`

=== "Genre"

    - Simple model: `name`, `description`, `numeric_string`
    - Custom validation in `clean()` method
    - Guarded demo row for built-in Delete disable hooks
    - Protected demo row for handled single-delete refusal UX
    - Used for many-to-many relationships and filtering

=== "Profile"

    - OneToOneField to Author (tests 1:1 relationships)
    - ForeignKey to Genre (tests optional relationships)
    - Demonstrates related field handling in forms/filters

## CRUD Views

Each model has a dedicated CRUD view demonstrating different powercrud features:

### BookCRUDView - Full Feature Demo

```python
from powercrud.mixins import PowerCRUDAsyncMixin


class BookCRUDView(PowerCRUDAsyncMixin, CRUDView):
    # Comprehensive configuration showing:
    view_title = "My List of Books"
    view_instructions = "Here you can edit books"
    view_help = {
        "summary": "About this feature demo",
        "details": (
            "This Books screen demonstrates many PowerCRUD features in one place."
            "\n\n"
            "Use it to inspect list options, inline editing, saved filter favourites, "
            "bulk actions, async workflows, modal links, external links, selection-aware "
            "toolbar actions, and guarded update behaviour."
        ),
        "color": "info",
    }
    column_help_text = {
        "title": "The book title shown throughout the app.",
        "pages": "Demo link: opens this book detail in the current page.",
        "isbn": "Demo link: opens an external ISBN reference in a new tab or window.",
        "isbn_empty": "Shows whether this row currently has an ISBN value.",
        "a_really_long_property_header_for_title": (
            "Demo link: opens the related author detail in a larger PowerCRUD modal."
        ),
    }
    list_cell_tooltip_fields = ["title", "pages", "isbn_empty"]
    list_cell_link_default_open_in = "modal"
    list_options_enabled = True
    default_list_fields = [
        "title",
        "author",
        "published_date",
        "pages",
        "bestseller",
        "isbn",
        "genres",
        "isbn_empty",
        "a_really_long_property_header_for_title",
    ]
    link_fields = {
        "a_really_long_property_header_for_title": {
            "view_name": "sample:author-detail",
            "pk_attr": "author_id",
            "modal_box_classes": (
                "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 "
                "max-w-6xl flex-col"
            ),
        },
        "pages": {
            "view_name": "sample:bigbook-detail",
            "open_in": "current",
        },
        "isbn": {
            "url": "https://www.isbn-international.org/content/what-isbn",
            "open_in": "new",
        },
    }
    form_class = BookForm
    form_display_fields = ["uneditable_field"]
    form_disabled_fields = ["isbn"]
    field_queryset_dependencies = {
        "genres": {
            "depends_on": ["author"],
            "filter_by": {"authors": "author"},
            "order_by": "name",
            "empty_behavior": "all",
        }
    }
    bulk_fields = ['title', 'published_date', 'bestseller', 'pages', 'author', 'genres']
    bulk_delete = True
    bulk_async = True
    
    filterset_fields = ['author', 'title', 'published_date', 'isbn', 'pages', 'description', 'genres']
    default_filterset_fields = ['author', 'title', 'published_date']
    filter_favourites_enabled = True
    dropdown_sort_options = {"author": "name"}
    inline_edit_fields = ['title', 'author', 'genres', 'published_date', 'bestseller', 'description']
    
    extra_buttons = [...]  # Includes a selection-aware "Selected Summary" demo
    extra_actions = [...]  # Includes a conditional "Description Preview" demo

    def get_list_cell_tooltip(self, obj, field_name, *, is_property, request=None):
        if field_name == "title":
            return f"{obj.author}\n{obj.pages} pages"
        if field_name == "pages":
            return f"Page count: {obj.pages}"
        if field_name == "isbn_empty":
            return (
                "This book does not currently have an ISBN."
                if obj.isbn_empty
                else f"ISBN: {obj.isbn}"
            )
        return None
```

The sample `BookCRUDView` uses `view_title = "My List of Books"` plus `view_instructions = "Here you can edit books"` to demonstrate the narrow heading/helper-text overrides. It also sets `view_help` to demonstrate collapsed screen-level guidance with a one-line summary, escaped paragraph text, a subtle `info` colour tint, and table-aligned width. The `column_help_text` mapping covers one field and one property so the sample list shows the header-help tooltip pattern; on linked demo columns, the header help explicitly says whether the link opens in the current page, a new tab/window, or the PowerCRUD modal. `list_cell_tooltip_fields` plus `get_list_cell_tooltip(...)` demonstrates semantic field-level tooltips on the inline-editable `title`, the visible non-inline `pages` field, and the boolean-like `isbn_empty` property cell. The sample `title` tooltip intentionally uses a newline so the demo shows multiline semantic list-cell tooltip rendering, while header-help tooltips and other tooltip surfaces keep their normal single-line behavior. That changes only the list surface above and inside the table; other UI copy such as the create button still comes from the model verbose names, and the instructions text, collapsed screen help, header help text, and semantic cell tooltip text are all rendered as plain escaped text rather than HTML.

The same sample view now also demonstrates list-cell linking through the narrow declarative `link_fields` API. The live sample uses the non-inline property column `a_really_long_property_header_for_title` so the screen can keep its primary `title` and `author` columns reserved for inline-edit and dependency demos. That is deliberate: PowerCRUD never turns inline-editable cells into links. The sample sets `list_cell_link_default_open_in = "modal"` and uses the dict form with `pk_attr = "author_id"` plus `modal_box_classes`, so that existing non-inline link opens the related author detail through a noticeably larger PowerCRUD modal when the sample page is running with modal support. In views that omit `list_cell_link_default_open_in`, PowerCRUD assumes `"new"`. The sample links `pages` to the current book detail with explicit `open_in = "current"`, and keeps `isbn` out of `inline_edit_fields` so that visible field can link to a static external ISBN reference with explicit `open_in = "new"`.

The same sample view now also demonstrates progressive filter visibility:

- `author`, `title`, and `published_date` are visible by default through `default_filterset_fields`
- `isbn`, `pages`, `description`, and `genres` remain allowed filters but start hidden
- the Add filter control reveals those optional filters on demand without changing the underlying filterset contract

The same sample view now also demonstrates list options:

- `list_options_enabled = True` enables **Cols**, while `default_list_fields` keeps the initial book table narrower than the full allowed column set
- users can open **Cols** and add allowed hidden columns such as `uneditable_field`
- the current column choice is scoped to the browser session and the `BookCRUDView`
- reset returns the table to the declared `default_list_fields`

The sample `BookCRUDView` also demonstrates the optional saved-favourites contrib app:

- `filter_favourites_enabled = True` turns on the toolbar for this list
- saved favourites persist the current filters, optional filter visibility, sort, page size, and visible columns for the signed-in user, scoped to the list view's derived identity
- the sample project mounts `include("powercrud.urls", namespace="powercrud")`, which is required for the optional favourites endpoints

See [Filtering](../guides/filtering.md) for the core filter behavior and [Saved Favourites](../guides/advanced/filter_favourites.md) for the optional contrib add-on.

### AnnotatedBookCRUDView - Queryset Annotation Columns

The sample app includes a focused list-only view at `/sample/annotated-book/` for queryset-backed list/filter fields.

```python
from django.db.models import BooleanField, Case, Value, When


class AnnotatedBookCRUDView(PowerCRUDAsyncMixin, CRUDView):
    model = Book
    url_base = "annotated-book"

    queryset = Book.objects.select_related("author").annotate(
        long_book=Case(
            When(pages__gte=400, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    )
    fields = ["title", "author", "pages", "long_book", "published_date"]
    list_options_enabled = True
    default_list_fields = ["title", "author", "pages", "published_date"]
    filterset_fields = ["author", "long_book", "pages"]
    default_filterset_fields = ["author", "long_book"]
    inline_edit_fields = ["pages"]
    bulk_fields = []
```

The `long_book` column is not a model field. It is the public queryset annotation name, and PowerCRUD uses that same name in `fields`, generated filters, sorting, header help, cell tooltips, and list-column selection. The sample sets `list_options_enabled = True` and keeps `long_book` out of `default_list_fields` so it appears as an optional selectable column in the **Cols** control. The sample makes the real `pages` model field inline-editable while keeping `long_book` out of inline edit and bulk edit config because annotation fields are read-only. See [Queryset Annotation Fields](../guides/advanced/queryset_annotation_fields.md) for the declaration details behind this sample.

The sample frontend now also shows the downstream tooltip-styling path. In [`src/config/static/css/app.custom.css`](../../../src/config/static/css/app.custom.css), the sample app actively overrides `--pc-tooltip-bg` and `--pc-tooltip-fg` to use daisyUI's primary semantic tokens, while PowerCRUD itself keeps neutral tooltip defaults. The sample Vite entry imports that file after `powercrud/css/powercrud.css`, so readers can inspect the real app-level override pattern rather than only reading about it in the styling guide.

The sample form configuration now also demonstrates two contextual form-surface features:

- `form_display_fields = ["uneditable_field"]` shows the model’s non-editable field in a separate read-only `Context` block above the update form.
- `form_disabled_fields = ["isbn"]` keeps the ISBN visible on update forms but locks the input so users can see it without changing it.

`BookForm` remains the source of truth for editable inputs, while PowerCRUD layers the display-only context block and disabled-field behavior on top of that custom form.

The sample `BookCRUDView` now also demonstrates both custom action enhancements discussed in the docs:

- a selection-aware `extra_button` that opens a modal summary for the current persisted bulk selection
- a row-level `extra_action` that disables itself with a tooltip when the book has no description
- an opt-in modal `extra_action` using `refresh_list_on_modal_close=True` to refresh the current list when its modal is closed
- per-trigger modal sizing on a modal list-cell link, a modal `extra_button`, and modal `extra_actions` through `modal_box_classes`
- semantic field-level list-cell tooltips on the inline `title`, non-inline `pages`, and `isbn_empty` property columns
- session-backed list-column choices through **Cols**
- declarative list-cell linking on `pages` (`current`), visible `isbn` (`new`), and the non-inline `Really Long Title` property column (`modal`)
- an active sample app-level tooltip theme override through `--pc-tooltip-bg` / `--pc-tooltip-fg`
- a guarded row (`Guarded Sample Book`) that disables the built-in Edit action and inline editing before the user can start an update
- a bulk-validation demo row (`Bulk Validation Sample Book`) that re-renders the bulk edit modal for sync bulk updates and fails the async task for queued bulk updates when a sample bulk rule is violated

These examples are intentionally simple so package users can inspect both the view config and the matching sample endpoints/templates.

The sample `BookCRUDView` also includes illustrative persistence-hook wiring:

- `persist_single_object(...)`
- `persist_bulk_update(...)`
- `bulk_update_persistence_backend_path = "sample.backends.BookBulkUpdateBackend"`

The single-object hook stays intentionally thin. For bulk updates, the sync hook and the async backend both route through `BookBulkUpdateService`, so the same sample validation rule applies in either execution mode.

The sample app also now includes tutorial-oriented helper classes in `sample.services` and `sample.backends`:

- `BookWriteService`
- `BookBulkUpdateService`
- `BookBulkUpdateBackend`

These are deliberately small examples used by the advanced persistence-hook guides. They are there to make the documentation more inspectable, and `BookBulkUpdateBackend` is now also wired into the sample `BookCRUDView` so the async bulk example is real rather than purely illustrative.

### Inline dependency demo

The sample app now includes a concrete inline dependency example:

- `Book.author` is the parent field.
- `Book.genres` is the dependent field.
- Allowed genre choices come from `Author.genres`, not from historical book rows.

`field_queryset_dependencies` is the primary declaration for this rule, so the same queryset restriction applies to regular forms and inline editing. `BookForm` stays in place only for form-specific tweaks such as keeping `genres` optional when an author has no allowed genres.

Worked configuration:

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

How to read that:

- `genres` is the child field being restricted
- `author` is the parent form field the user changes
- `authors` is the queryset lookup on `Genre`

So the child queryset is effectively narrowed as if PowerCRUD were doing:

```python
Genre.objects.filter(authors=<selected author>).order_by("name")
```

That same rule applies in two places:

- the normal Book create/edit form
- inline editing on the Books list

When the user changes `author` inline, PowerCRUD posts the current row data to the dependency endpoint, rebuilds the `genres` widget through the same form pipeline, and swaps the refreshed widget back into the row.

### Other Views

- **GenreCRUDView**: Minimal configuration example plus two focused delete demos: a guarded row (`Guarded Sample Genre`) that disables the built-in Delete action before click, and a protected row (`Protected Sample Genre`) that demonstrates handled single-delete `ValidationError` responses after submit
- **ProfileCRUDView**: OneToOneField, the sample app's column-alignment demo (`status` centered, `priority_band` right-aligned, `favorite_genre` left-aligned), inline editing, bulk operations, merged nullable relation filtering on `favorite_genre`, and a static queryset rule that limits `favorite_genre` choices to genres whose names start with `S`
- **AuthorCRUDView**: Properties, filtering, template debugging, companion nullable scalar filtering on `birth_date`, the sample app's red inline-edit highlight accent demo, and visible row-level `extra_actions` in the default button mode
- **BookCRUDView**: Async bulk editing, dependent `author -> genres` queryset scoping, `view_title` / `view_instructions` / `view_help` heading-area overrides, `column_help_text` header tooltips, list options through **Cols**, semantic field-level list-cell tooltips on inline and non-inline columns, declarative modal and external list-cell link demos, selection-aware `extra_buttons` in the top toolbar overflow menu, dropdown row actions that open upward for the last five rendered rows, and a guarded sample row for built-in Edit and inline update guards

The `Genre` sample keeps these delete demos deliberately narrow:

- If a row is named `Guarded Sample Genre`, `GenreCRUDView.can_delete_object(...)` returns `False` and the built-in Delete action renders disabled with a tooltip reason before the modal opens.
- If a row is named `Protected Sample Genre`, its `delete()` method raises `ValidationError("Protected Sample Genre exists to demonstrate handled delete refusals.")`.

That lets the sample app show both layers of the product story on the same lightweight CRUD surface:

- pre-click Delete disablement
- post-click handled delete refusal

The `Book` sample includes a separate update-guard demo on the busier inline-editing screen:

- If a row is titled `Guarded Sample Book`, `BookCRUDView.can_update_object(...)` returns `False`.
- The built-in Edit action renders disabled with a tooltip reason.
- Inline-editable cells stay visible but render as disabled affordances with the same reason, so the sample shows both update surfaces together on a screen that already exercises inline editing.

The same `Book` screen now also includes a bulk-validation demo:

- If a selected row is titled `Bulk Validation Sample Book`, `BookBulkUpdateService` rejects a sample bulk `bestseller=true` update.
- If the selection stays below `bulk_min_async_records`, PowerCRUD re-renders the bulk edit modal with the handled error payload instead of treating the result as a server failure.
- If the selection reaches the async threshold, the queued task fails instead and the sample async dashboard shows the failure state.
- That makes `BookCRUDView` the sample app reference for shared sync/async bulk persistence wiring plus the current difference between sync modal errors and async task-level failures.

### ProfileCRUDView alignment and queryset demo

`ProfileCRUDView` is the sample app reference for two smaller-but-practical list customizations:

- mixed per-column list alignment through `column_alignments`
- static queryset rules shared across normal forms, inline editing, and bulk edit choices

The view uses three list columns to demonstrate the alignment feature in a way that is easy to inspect on screen:

- `status` is a short categorical value and is centered
- `priority_band` is a short categorical value and is right-aligned
- `favorite_genre` is ordinary text and is kept left-aligned

Current sample config:

```python
column_alignments = {
    "status": "center",
    "priority_band": "right",
    "favorite_genre": "left",
}
```

That same screen also keeps those fields in inline editing and bulk editing, so the sample shows how alignment overrides behave across the main list display states without moving the feature onto the much busier `Book` screen.

`Profile` also carries the static queryset demo for `favorite_genre`:

```python
field_queryset_dependencies = {
    "favorite_genre": {
        "static_filters": {"name__startswith": "S"},
        "order_by": "name",
    }
}
```

How to read that:

- `favorite_genre` is the field being restricted
- `static_filters` applies a fixed queryset rule with no parent field involved
- `order_by` keeps the remaining choices sorted predictably

That same static rule is reused in three places:

- the normal Profile create/edit form
- inline editing on the Profiles list
- the bulk edit dropdown for `favorite_genre`

This makes `ProfileCRUDView` the sample app reference for static queryset rules and mixed list alignment overrides, while `BookCRUDView` remains the reference for dynamic parent/child dependencies.

Example `BookCRUDView` action config:

```python
extra_actions_mode = "dropdown"
extra_buttons_mode = "dropdown"
extra_actions_dropdown_open_upward_bottom_rows = 5

extra_buttons = [
    {
        "url_name": "home",
        "text": "Home in Modal!",
        "display_modal": True,
        "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-3xl flex-col",
    },
    {
        "url_name": "sample:bigbook-selected-summary",
        "text": "Selected Summary",
        "display_modal": True,
        "uses_selection": True,
        "selection_min_count": 1,
        "selection_min_behavior": "disable",
    },
]

extra_actions = [
    {
        "url_name": "sample:bigbook-description-preview",
        "text": "Description Preview",
        "needs_pk": True,
        "display_modal": True,
        "disabled_if": "is_description_preview_disabled",
        "disabled_reason": "get_description_preview_disabled_reason",
        "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-5xl flex-col",
    },
]
```

That lets the sample app demonstrate selection-aware header actions, conditionally disabled row actions, and per-trigger modal sizing in the same CRUD surface. `Selected Summary` intentionally uses the view default modal width, while `Home in Modal!` shows a header-button override. The `modal_box_classes` entries are full replacement strings: they keep the default viewport-height classes and add per-trigger width classes for those specific modal calls.

## Management Commands

=== "Creating Test Data"

    ```bash
    # Create default authors (25) and books (50)
    ./manage.py create_sample_data

    # Create 100 authors and 1000 books
    ./manage.py create_sample_data --authors 100 --books 1000

    # Create 500 books with an average of 5 books per author
    ./manage.py create_sample_data --books 500 --books-per-author 5
    ```

    Generates realistic sample data:

    - Random author names and bios
    - Book titles, descriptions, publication dates, and ISBNs
    - Progress feedback during creation
    - Allows control over the distribution of books per author using `--books-per-author`.

=== "Clearing Test Data"

    ```bash
    ./manage.py clear_sample_data --all        # Delete everything
    ./manage.py clear_sample_data --books      # Books only
    ./manage.py clear_sample_data --authors    # Authors only (cascades to books)
    ```

    Safety features:

    - Only works when `DEBUG=True`
    - Handles protected foreign key relationships
    - Provides clear feedback on deletion counts

## Forms & Filters

### Custom Forms

- **BookForm**: Date widgets, field selection, crispy forms integration, and form-specific tweaks while `field_queryset_dependencies` handles the shared `author -> genres` queryset rule
- **AuthorForm**: Demonstrates form customization patterns

### Advanced Filtering  

- **BookFilterSet**: HTMX integration, custom widget attributes
- **AuthorFilterSet**: Inherits from `HTMXFilterSetMixin` for reactive filtering
- Shows crispy forms layout integration

## Development Use Cases

### Feature Testing

- **Bulk Operations**: Test edit/delete on multiple books with validation
- **Async Processing**: Book deletion includes artificial delay for async testing  
- **Complex Relationships**: M2M genres, ForeignKey authors, OneToOne profiles
- **Field Types**: Generated fields, boolean displays, date formatting

### UI/UX Testing

- **Modal Interactions**: All CRUD operations in modals
- **HTMX Features**: Reactive filtering, pagination, form updates
- **Inline Dependencies**: Changing a Book author inline immediately refreshes the allowed genre choices derived from the shared form dependency config
- **Inline Validation Errors**: Clear a Book title inline and save to see the row stay open with field-level error text and a field popover
- **Static Queryset Rules**: Editing a Profile only offers `favorite_genre` choices whose names start with `S`, and the same restriction carries through inline and bulk edit
- **CSS Frameworks**: Easy switching between daisyUI and Bootstrap
- **Responsive Design**: Table layouts with column width controls

### Manual Inline Error Repro

Use the Book list to inspect the inline validation UI:

1. Open `/sample/bigbook/`.
2. Click the inline edit affordance on a book title.
3. Clear the title field.
4. Click **Save**.

Expected result: the row remains in edit mode, the title field is marked invalid, and a forced-visible popover says `This field is required.`. The inline error text remains in the markup as an accessibility/fallback message but is visually hidden while the popover is active.

To check inline searchable selects on the same screen, click the `author` inline-edit affordance. The field should focus and open the dropdown.

### Configuration Examples

- **Property Display**: Custom property names and formatting
- **Field Exclusions**: Hide sensitive/internal fields  
- **Custom Actions**: Additional buttons and row-level actions, including dropdown-style overflow for `extra_actions`
- **Sorting & Filtering**: Advanced queryset manipulation

## Getting Started

1. **Run migrations:**

   ```bash
   ./manage.py migrate
   ```

2. **Create sample data:**

   ```bash
   ./manage.py create_sample_data
   ```

3. **Access the views:**

   - Books: http://localhost:8001/sample/bigbook/
   - Authors: http://localhost:8001/sample/author/
   - Genres: http://localhost:8001/sample/genre/
   - Profiles: http://localhost:8001/sample/profile/

4. **Test features:**

   - Try bulk edit operations on books
   - Use filtering and sorting
   - Test modal create/edit/delete
   - Open a Book row inline, change `author`, and confirm `genres` refreshes immediately without saving
   - Experiment with different page sizes

## How to try the inline dependency demo

1. Open the Books list at `/sample/bigbook/`.
2. Edit an Author and assign one or more genres to that author.
3. Open a Book edit form in a modal and confirm the genres dropdown only shows genres for that author.
4. Open a Book row in inline mode.
5. Change the Book author.
6. Re-open the Book genres control before saving.
7. Confirm the available genres now match the selected author’s `genres` relation.

## How to adapt this pattern downstream

If your project used an older inline-only dependency pattern, the sample app demonstrates the preferred replacement:

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

The key point is that `filter_by` maps:

- queryset lookup on the child field's queryset model
- to parent form field name

Inline refresh wiring is derived automatically from this declaration.

The browser regression for this flow lives in [test_inline_dependencies.py](/home/mfo/projects/packages/django_powercrud/src/tests/playwright/test_inline_dependencies.py).

## Development Notes

The sample app is designed to be:

- **Comprehensive**: Covers all major powercrud features
- **Realistic**: Uses believable domain models and relationships  
- **Educational**: Clear examples of configuration patterns
- **Extensible**: Easy to add new models or features for testing

When developing new powercrud features, add corresponding examples to the sample app to ensure comprehensive testing coverage.
