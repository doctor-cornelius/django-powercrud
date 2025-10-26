# Django PowerCRUD

**Advanced CRUD for perfectionists with deadlines. An opinionated extension of [Neapolitan](https://github.com/carltongibson/neapolitan).**

## What is PowerCRUD?

The [`neapolitan`](https://github.com/carltongibson/neapolitan/) package gives you a solid foundation for Django CRUD views. But you still need to add filtering, bulk operations, modern UX features, and styling yourself.

PowerCRUD comes with these features built-in, specifically for user-facing CRUD interfaces. Use what you need, customize what you want.

> ℹ️ **Status**
> 
> PowerCRUD is still evolving, but now ships with a comprehensive pytest suite (including Playwright UI smoke tests). Expect rough edges while APIs settle, and pin the package if you rely on current behaviour.

See the [full documentation](https://doctor-cornelius.github.io/django-powercrud/).

## Key Features

🎯 **Advanced CRUD Operations** - Filtering, pagination, bulk edit/delete (with async) out of the box  
⚡ **Modern Web UX** - HTMX integration, modals, and reactive updates  
🔧 **Developer Friendly** - Convention over configuration with full customization options  
🎨 **Multiple CSS Frameworks** - daisyUI/Tailwind (default) and Bootstrap 5 support  

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

See the **[Quick Start](https://doctor-cornelius.github.io/django-powercrud/getting_started/)** documentation

## Development Setup

PowerCRUD’s development environment is Docker-first. From the project root:

```bash
./runproj up          # build images, start services, enter the Django container
pytest                # run the full test suite, including Playwright smoke tests
```

Dependencies are managed with [`uv`](https://github.com/astral-sh/uv); the Docker image installs them into the system interpreter so you never need to activate a virtual environment inside the container. See the [Dockerised Development Environment guide](https://doctor-cornelius.github.io/django-powercrud/reference/dockerised_dev/) for full details.
