# Core Configuration

Essential settings that control field display, templates, and basic view behavior.

## Convention Over Configuration

PowerCRUD follows Django's "convention over configuration" philosophy. You only need to specify what differs from sensible defaults:

```python
# Minimum configuration - just specify your model
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    base_template_path = "core/base.html"
    # Everything else has sensible defaults
```

There are two required parameters:

- `model`. All other settings have defaults that work for most cases.
- `base_template_path` , which defaults to the inbuilt `powercrud/base.html`. But this is unlikely to be relevant to your project or app. So it's important to specify the path to your actual base template.

## Field Control

### Basic Field Selection

Control which model fields appear in your views:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    
    # Include specific fields
    fields = ["name", "owner", "status", "created_date"]
    
    # Or include all fields (default)
    fields = '__all__'
    
    # Exclude specific fields
    exclude = ["internal_notes", "debug_info"]
```

**Default**: All model fields are included if `fields` is not specified.

### Property Fields

Include model `@property` methods alongside regular fields:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    fields = ["name", "owner", "status"]
    
    # Add computed properties
    properties = ["is_overdue", "days_remaining"]
    
    # Or include all properties
    properties = '__all__'
    
    # Exclude specific properties
    properties_exclude = ["internal_calculation"]
```

!!! note "Property Display Names"

    For a property `myprop`, set `myprop.fget.short_description = "Custom Title"` in your model class to customize column headers.

### Detail View Customization

Show different fields in detail views than in list views:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    fields = ["name", "owner", "status"]  # List view
    
    # Detail view gets additional fields
    detail_fields = ["name", "owner", "status", "description", "created_date"]
    detail_properties = ["is_overdue", "progress_percentage"]
    
    # Or use shortcuts
    detail_fields = '__all__'        # All model fields
    detail_fields = '__fields__'     # Same as fields setting
    detail_properties = '__all__'    # All properties
    detail_properties = '__properties__'  # Same as properties setting
    
    # Exclude from detail view
    detail_exclude = ["internal_notes"]
    detail_properties_exclude = ["debug_info"]
```

!!! note "Defaults"

    - `detail_fields` defaults to your `fields` setting
    - `detail_properties` defaults to `None` (no properties shown)

## Template Configuration

### Base Template

Point to your project's base template:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    base_template_path = "core/base.html"  # Default: framework-specific base
```

### Template Overrides

Override PowerCRUD templates with your own:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    templates_path = "myapp/custom"  # Look in myapp/templates/myapp/custom/
```

This looks for templates in your specified path instead of the default PowerCRUD templates.

### Bootstrap Templates

Copy PowerCRUD templates to your project for customization:

```bash
# Copy all templates for an app
python manage.py pcrud_mktemplate myapp

# Copy specific model templates
python manage.py pcrud_mktemplate myapp.Project --all
python manage.py pcrud_mktemplate myapp.Project --list    # Just list view
python manage.py pcrud_mktemplate myapp.Project --form    # Just form templates
```

Templates are copied to your app's template directory following Django conventions.

## URL Configuration

### Namespacing

Organize URLs to avoid conflicts:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    namespace = "projects"  # Must match app_name in urls.py
```

???+ note "Your `urls.py` must have matching `app_name`"

    ```python
    # urls.py
    app_name = "projects"  # Must match namespace in view
    urlpatterns = [
        path("", ProjectCRUDView.as_view(), name="project"),
    ]
    ```

### Custom URL Base

Override the default URL pattern:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    url_base = "active_projects"  # Instead of default "project"
```

Useful when you have multiple CRUD views for the same model with different configurations.

## Display Enhancement

### Automatic Improvements

PowerCRUD automatically enhances display:

- **Related fields**: Shows `str(related_object)` instead of numeric IDs
- **Reactive headers**: Page titles update without reload when using HTMX
- **Responsive tables**: Column width controls and truncation with popovers

These work automatically - no configuration needed.

## Common Patterns

### Minimal Configuration
```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Book
    # Uses all defaults - shows all fields, no properties
```

### List vs Detail Fields
```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Book
    
    # Minimal list view
    fields = ["title", "author", "status"]
    
    # Comprehensive detail view
    detail_fields = '__all__'
    detail_properties = ["is_bestseller", "reading_time"]
```

### Custom Templates
```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Book
    
    # Use custom base template
    base_template_path = "library/base.html"
    
    # Use custom CRUD templates
    templates_path = "library/books"
    
    # Organize with namespace
    namespace = "library"
```

### Properties with Custom Titles
```python
# In your model
class Book(models.Model):
    title = models.CharField(max_length=200)
    pages = models.IntegerField()
    
    @property
    def reading_time(self):
        return f"{self.pages // 250} hours"
    
    # Custom column title
    reading_time.fget.short_description = "Est. Reading Time"

# In your view
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Book
    properties = ["reading_time"]  # Uses custom title
```

## Configuration Reference

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| `fields` | list/str | All model fields | Fields to show in list view |
| `exclude` | list | `[]` | Fields to exclude from list view |
| `properties` | list/str | `[]` | Properties to show in list view |
| `properties_exclude` | list | `[]` | Properties to exclude from list view |
| `detail_fields` | list/str | Same as `fields` | Fields to show in detail view |
| `detail_exclude` | list | `[]` | Fields to exclude from detail view |
| `detail_properties` | list/str | `None` | Properties to show in detail view |
| `detail_properties_exclude` | list | `[]` | Properties to exclude from detail view |
| `base_template_path` | str | Framework-specific | Path to your base template |
| `templates_path` | str | `"powercrud/{framework}"` | Path to override templates |
| `namespace` | str | `None` | URL namespace (must match urls.py) |
| `url_base` | str | Model name | Base for URL patterns |

## Related Configuration

- **Forms**: See [Form Handling](form_handling.md) for form field control
- **Styling**: See [Styling](styling.md) for visual customization
- **Advanced Features**: See [HTMX & Modals](htmx_modals.md), [Filtering](filtering.md), [Bulk Operations](bulk_operations.md)
