# List Options

List options let a user choose which data columns are visible on an opted-in list view.

Use this when a screen has more useful columns than should be shown by default. The view owner still controls the full allowed column set; users can only show or hide columns that the view already exposes.

## Minimal Setup

Declare the normal list column allow-list with `fields` and `properties`, then set `list_options_enabled = True`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = Project

    fields = [
        "reference",
        "owner",
        "status",
        "needs_attention",
        "due_date",
        "internal_notes",
    ]
    properties = ["is_overdue"]
    list_options_enabled = True
```

With that configuration, every allowed column is visible by default and users can hide or show columns through **Cols**.

To start from a narrower default/reset state, add `default_list_fields`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = Project

    fields = [
        "reference",
        "owner",
        "status",
        "needs_attention",
        "due_date",
        "internal_notes",
    ]
    properties = ["is_overdue"]
    list_options_enabled = True
    default_list_fields = [
        "reference",
        "owner",
        "status",
        "needs_attention",
        "is_overdue",
    ]
```

With that configuration:

- `fields` and `properties` define the allowed selectable data columns.
- `list_options_enabled = True` enables the **Cols** dropdown.
- `default_list_fields` defines the default visible subset. When it is omitted, every allowed column is default-visible.
- Every allowed-but-not-default column remains available through the **Cols** dropdown.
- Existing views are unchanged when both `list_options_enabled` and `default_list_fields` are unset.
- For backward compatibility, setting `default_list_fields` still enables list options even when `list_options_enabled` is omitted.

## Column Sources

`default_list_fields` can include:

- model field names listed in `fields`
- queryset annotation names listed in `fields`
- property names listed in `properties`

Queryset annotation columns follow the same contract described in [Queryset Annotation Fields](queryset_annotation_fields.md): the annotation name must match the public name used in `fields`, and the effective queryset must expose it before PowerCRUD renders the list.

Properties remain display-only. Model fields and queryset annotation fields keep their existing formatting, sorting, header help, alignment, links, and tooltips when they are visible.

## Persistence

PowerCRUD stores current list-column choices in the Django session per CRUD view.

The session state is scoped by the view's Python identity:

```text
package.module.ProjectCRUDView
```

This applies to authenticated and anonymous users. Choices survive reloads and navigation in the same browser session until the session expires or the user resets the chooser. There is no core PowerCRUD database table or migration for unnamed column choices.

For durable named list states, install the optional saved favourites contrib app. Saved favourites include visible columns alongside filters, optional filter visibility, sort, and page size for authenticated users.

## Behavior Rules

- User-selected columns are validated against the current allow-list.
- Stale session columns are dropped if a view later removes or renames a column.
- If session state becomes empty or invalid, PowerCRUD falls back to `default_list_fields`, or to every allowed column when no default subset is declared.
- Users cannot save an empty data-column table.
- Reset deletes the session state and returns to `default_list_fields`, or to every allowed column when no default subset is declared.
- Hiding the currently sorted column clears the sort and resets to page 1.
- Filtering stays independent from visible columns; a user can filter by a field that is hidden from the table.
- Row selection, row actions, bulk controls, and pagination are system columns and are not user-toggleable data columns.

## What Is Deferred

This first version is show/hide only.

Deferred behavior includes:

- URL-shareable visible-column state
- user-controlled column ordering
- export/download coupling to visible columns
- localStorage persistence
- zero-data-column tables

## Sample App

The sample `BookCRUDView` demonstrates list options on `/sample/bigbook/`.

Open the book list and use **Cols**. The default table hides some allowed columns, while the chooser can add them back for the current browser session. Try changing columns while filters, page size, sorting, inline editing, linked cells, and bulk selection are active.
