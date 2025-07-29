# Django PowerCRUD

**Advanced CRUD for perfectionists with deadlines. An opinionated [`Neapolitan`](https://github.com/carltongibson/neapolitan) extension, with sprinkles.**

## What is PowerCRUD?

The [`neapolitan`](https://github.com/carltongibson/neapolitan/) package gives you a solid foundation for Django CRUD views. But you still need to add filtering, bulk operations, modern UX features, and styling yourself.

PowerCRUD comes with these features built-in, specifically for user-facing CRUD interfaces. Use what you need, customize what you want.

!!! warning "Early Alpha Release"
    This is a **very early alpha** release with limited tests and documentation. Expect breaking changes. You might prefer to fork or copy what you need.

See the [full documentation](https://doctor-cornelius.github.io/django-powercrud/).

## Key Features

🎯 **Advanced CRUD Operations** - Filtering, pagination, bulk edit/delete (with async) out of the box  
⚡ **Modern Web UX** - HTMX integration, modals, and reactive updates  
🔧 **Developer Friendly** - Convention over configuration with full customization options  
🎨 **Multiple CSS Frameworks** - daisyUI/Tailwind (default) and Bootstrap 5 support  

!!! warning "Bootstrap Templates Outdated"

    Bootstrap templates are currently out of date as all recent development has focused on `daisyUI`. Once async support is finalised and tested, Bootstrap templates will either be updated or removed.


## Quick Example

Start with basic neapolitan:

```python
# Basic neapolitan
class ProjectView(CRUDView):
    model = Project
```

Add PowerCRUD for advanced features:

```python
# With PowerCRUD
class ProjectView(PowerCRUDMixin, CRUDView):
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

## Getting Started

1. **[Installation](getting_started.md#installation-dependencies)** - Install and configure in minutes
2. **[Quick Start](getting_started.md#quick-start-tutorial)** - Your first PowerCRUD view
3. **[Configuration](configuration/core_config.md)** - Explore the features

## Framework Support

- **daisyUI/Tailwind CSS** - Modern utility-first styling (default)
- **Bootstrap 5** - Production-ready components
- **Custom frameworks** - Bring your own CSS
