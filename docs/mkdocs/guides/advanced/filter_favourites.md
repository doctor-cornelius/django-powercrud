# Saved Filter Favourites

Saved filter favourites are an optional add-on for teams that want named, reusable filter states per user.

This feature is intentionally shipped as a contrib app so projects that do not need it do not have to carry its model, migration, or UI surface.

Use this guide when you want to:

- install the favourites contrib app
- enable it on selected list views
- understand what the saved state includes
- understand how it behaves when the app is not installed

## What it saves

PowerCRUD can persist named list states per authenticated user, including:

- active filter values
- optional filter visibility
- current sort
- current page size

The saved payload intentionally does not persist the current page number.

## Installation

Add the contrib app to `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "powercrud.contrib.favourites",
]
```

Then run migrations:

```bash
python manage.py migrate
```

This step is optional. If you never install the contrib app, the rest of PowerCRUD filtering still works normally.

## Enable it on a list view

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # ...
    filter_favourites_enabled = True
```

That turns on the favourites toolbar for that list view, provided the contrib app is installed.

## Scoping

Saved favourites are scoped per:

- authenticated user
- list view identity

The view identity is derived automatically from `"<module>.<ClassName>"`.

## Behavior notes

- Anonymous users still see the toolbar when the view enables favourites, but the save, update, and delete controls remain unavailable and the UI prompts them to sign in.
- Applying a saved favourite restores optional filter visibility as well as the saved filter values.
- The current UI is intentionally compact:
    - selecting a saved favourite auto-applies it
    - the toolbar stays hidden until the filter panel is open
    - long selected favourite names are truncated in the trigger and exposed through a tooltip

## Missing-app guard

If a developer sets `filter_favourites_enabled = True` on a view but does not install `powercrud.contrib.favourites`, PowerCRUD silently disables the feature.

That means:

- no toolbar renders
- no favourites URLs are included
- no separate global setting is required to declare that favourites are available

PowerCRUD detects this directly from `apps.is_installed("powercrud.contrib.favourites")`.

## Sample app

The sample `BookCRUDView` demonstrates the feature end-to-end and is the best reference implementation in the demo project.

For the broader filtering story that favourites build on top of, see [Filtering](../filtering.md).
