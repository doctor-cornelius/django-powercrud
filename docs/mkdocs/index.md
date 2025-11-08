# Home

**Advanced CRUD for perfectionists with deadlines. An opinionated extension of [`Neapolitan`](https://github.com/carltongibson/neapolitan).**

## What is powercrud?

The [`neapolitan`](https://github.com/carltongibson/neapolitan/) package gives you a solid foundation for Django CRUD views. But you still need to add filtering, bulk operations, modern UX features, and styling yourself.

powercrud comes with these features built-in, specifically for user-facing CRUD interfaces. Use what you need, customize what you want.

!!! info "Project status"
    PowerCRUD is still evolving, but now ships with a full pytest suite (including Playwright smoke tests). Expect breaking changes while APIs settle, and pin the package if you rely on current behaviour.

## Key Features

🎯 **Advanced CRUD Operations** - Filtering, pagination, bulk edit/delete (with async) out of the box  
⚡ **Modern Web UX** - HTMX integration, modals, and reactive updates  
🔧 **Developer Friendly** - Convention over configuration with full customization options  
🎨 **Multiple CSS Frameworks** - `daisyUI` with `tailwindcss` (default) and Bootstrap 5 support  

!!! warning "Bootstrap5 Templates Outdated"

    Bootstrap templates are currently out of date as all recent development has focused on `daisyUI`. Once async support is finalised and tested, Bootstrap templates will either be updated or removed.

## Start Here

- First time? Begin with [Getting Started](guides/getting_started.md) for installation and prerequisites, then continue with [Setup & Core CRUD basics](guides/setup_core_crud.md).
- Already up and running? Jump straight to the chapter that matches what you need next in the “Guides” section of the sidebar.

## Quick Example

Start with basic neapolitan:

```python
# Basic neapolitan
class ProjectView(CRUDView):
    model = Project
```

Add powercrud for advanced features:

```python
# With powercrud
class ProjectView(powercrudMixin, CRUDView):
    model = Project
    fields = ["name", "owner", "status"]
    base_template_path = "core/base.html"
    
    # Modern features
    use_htmx = True
    use_modal = True
    
    # Advanced filtering
    filterset_fields = ["owner", "status", "created_date"]
    
    # Bulk operations
    bulk_fields = ["status", "owner"]
    bulk_delete = True
    
    # Enhanced display
    properties = ["is_overdue", "days_remaining"]
```

See the **[Getting Started](guides/getting_started.md)** section for more details.
