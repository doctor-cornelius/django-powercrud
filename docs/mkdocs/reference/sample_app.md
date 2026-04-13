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
    column_help_text = {
        "title": "The book title shown throughout the app.",
        "isbn_empty": "Shows whether this row currently has an ISBN value.",
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
    
    filterset_fields = ['author', 'title', 'published_date', 'isbn', 'pages', 'genres']
    dropdown_sort_options = {"author": "name"}
    inline_edit_fields = ['title', 'author', 'genres', 'published_date', 'bestseller', 'isbn', 'description']
    
    extra_buttons = [...]  # Includes a selection-aware "Selected Summary" demo
    extra_actions = [...]  # Includes a conditional "Description Preview" demo
```

The sample `BookCRUDView` uses `view_title = "My List of Books"` plus `view_instructions = "Here you can edit books"` to demonstrate the narrow heading/helper-text overrides. It also sets `column_help_text` for one field and one property so the sample list shows the new header-help tooltip pattern. That changes only the large title/header area above the table; other UI copy such as the create button still comes from the model verbose names, and both the instructions text and header help text are rendered as plain escaped text rather than HTML.

The sample form configuration now also demonstrates two contextual form-surface features:

- `form_display_fields = ["uneditable_field"]` shows the model’s non-editable field in a separate read-only `Context` block above the update form.
- `form_disabled_fields = ["isbn"]` keeps the ISBN visible on update forms but locks the input so users can see it without changing it.

`BookForm` remains the source of truth for editable inputs, while PowerCRUD layers the display-only context block and disabled-field behavior on top of that custom form.

The sample `BookCRUDView` now also demonstrates both custom action enhancements discussed in the docs:

- a selection-aware `extra_button` that opens a modal summary for the current persisted bulk selection
- a row-level `extra_action` that disables itself with a tooltip when the book has no description

These examples are intentionally simple so package users can inspect both the view config and the matching sample endpoints/templates.

The sample `BookCRUDView` also includes no-op illustrative overrides for the new sync persistence hooks:

- `persist_single_object(...)`
- `persist_bulk_update(...)`

They currently just call `super()`, but they mark the exact place where a downstream app would route validated writes through domain services while still letting PowerCRUD own validation and UI response flow.

The sample app also now includes tutorial-oriented helper classes in `sample.services` and `sample.backends`:

- `BookWriteService`
- `BookBulkUpdateService`
- `BookBulkUpdateBackend`

These are deliberately small examples used by the advanced persistence-hook guides. They are there to make the documentation more inspectable, not to change the default sample app behavior.

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

- **GenreCRUDView**: Minimal configuration example plus a sample protected row (`Protected Sample Genre`) that demonstrates handled single-delete `ValidationError` responses in the built-in modal delete flow
- **ProfileCRUDView**: OneToOneField, inline editing, bulk operations, merged nullable relation filtering on `favorite_genre`, and a static queryset rule that limits `favorite_genre` choices to genres whose names start with `S`
- **AuthorCRUDView**: Properties, filtering, template debugging, companion nullable scalar filtering on `birth_date`, and visible row-level `extra_actions` in the default button mode
- **BookCRUDView**: Async bulk editing, dependent `author -> genres` queryset scoping, `view_title` / `view_instructions` heading-area overrides, `column_help_text` header tooltips, selection-aware `extra_buttons`, and dropdown row actions that open upward for the last five rendered rows

The `Genre` sample keeps this deliberately narrow: if a row is named `Protected Sample Genre`, its `delete()` method raises `ValidationError("Protected Sample Genre exists to demonstrate handled delete refusals.")`. That lets the sample app show the framework behavior added for built-in single delete without mixing it into the busier `BookCRUDView` demo surface.

### Static queryset demo

The sample app also includes a static queryset example on `ProfileCRUDView`:

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

This makes `ProfileCRUDView` the sample app reference for static queryset rules, while `BookCRUDView` remains the reference for dynamic parent/child dependencies.

Example `BookCRUDView` action config:

```python
extra_actions_mode = "dropdown"
extra_actions_dropdown_open_upward_bottom_rows = 5

extra_buttons = [
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
    },
]
```

That lets the sample app demonstrate both selection-aware header actions and conditionally disabled row actions in the same CRUD surface.

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
- **Static Queryset Rules**: Editing a Profile only offers `favorite_genre` choices whose names start with `S`, and the same restriction carries through inline and bulk edit
- **CSS Frameworks**: Easy switching between daisyUI and Bootstrap
- **Responsive Design**: Table layouts with column width controls

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
