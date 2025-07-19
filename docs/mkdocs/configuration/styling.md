# Styling Configuration

Configure visual appearance and styling for your Nominopolitan views.

## Framework Selection

### Supported Frameworks

Choose from built-in framework support:

```python
# settings.py
NOMINOPOLITAN_CSS_FRAMEWORK = 'daisyui'    # Default (with Tailwind CSS v4)
NOMINOPOLITAN_CSS_FRAMEWORK = 'bootstrap5'  # Alternative
```

**Available frameworks:**

- **daisyUI v5** (default) - Modern utility-first styling with Tailwind CSS v4
- **Bootstrap 5** - Production-ready component library
- **Custom** - Bring your own framework

## Basic Styling

### Table Classes

Add CSS classes to your tables:

```python
class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    table_classes = 'table-striped table-hover'  # Added to base 'table' class
```

### Button Classes

Style action and extra buttons:

```python
class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    
    # Style buttons that appear for each record (edit, delete, etc.)
    action_button_classes = 'btn-sm btn-outline'
    
    # Style additional buttons at the top of the page
    extra_button_classes = 'btn-sm btn-primary'
```

### Dropdown Sorting

Control how options are sorted in dropdowns:

```python
class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    
    dropdown_sort_options = {
        "owner": "name",           # Sort by name (ascending)
        "category": "-name",       # Sort by name (descending)
        "priority": "-order",      # Sort by order field (descending)
    }
```

This affects dropdowns in filters, edit forms, and bulk edit forms.

## Advanced Table Styling

### Column Width Control

Control how table columns are sized:

```python
class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    
    # Maximum column width in characters (default: 25)
    table_max_col_width = 30
    
    # Minimum width for column headers when they wrap (default: same as max)
    table_header_min_wrap_width = 15
```

!!! note "Text Truncation"

    When text exceeds `table_max_col_width`, it's truncated with a popover showing the full text.

    **Requirements**: `popper.js` must be installed for truncation popovers to work.

### Table Height Control

Control the maximum height of data tables:

```python
class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    
    # Height of other page elements in pixels (default: 0)
    table_pixel_height_other_page_elements = 100
    
    # Max height as percentage of remaining viewport (default: 70)
    table_max_height = 80
```

This creates a scrollable table with calculated max height:
```css
max-height: calc((100vh - 100px) * 80 / 100);
```

### Table Sorting

Tables automatically support clickable column sorting:

```python
class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    use_htmx = True  # Enable reactive sorting without page reload
```

**Sorting behavior:**

- Click column headers to sort (starts unsorted)
- Click again to reverse sort direction
- Always includes secondary sort by primary key for stable pagination
- Visual indicators using Hero Icons (built-in, no installation needed)

## Tailwind CSS Integration

If using daisyUI or custom Tailwind-based framework, ensure Tailwind detects Nominopolitan's classes.

### Method 1: Package Source (Recommended)

Add Nominopolitan's package path to your `tailwind.css`:

```css
@import "tailwindcss";
@source "/path/to/your/site-packages/nominopolitan";
```

**Find your package path:**

```bash
python manage.py shell
>>> import django_nominopolitan 
>>> print(django_nominopolitan.__path__)
['/usr/local/lib/python3.12/site-packages/nominopolitan']
```

### Method 2: Safelist Generation

Generate a safelist of Tailwind classes:

```python
# settings.py
NM_TAILWIND_SAFELIST_JSON_LOC = 'config/templates/nominopolitan/'
```

```bash
# Generate safelist
python manage.py nm_extract_tailwind_classes --pretty
```

Use in your `tailwind.config.js`:
```javascript
module.exports = {
  content: [
    // your content paths
  ],
  safelist: require('./config/templates/nominopolitan/nominopolitan_tailwind_safelist.json')
}
```

### Management Command: Extract Tailwind Classes

Generate a safelist of Tailwind classes used by Nominopolitan which can be picked up by the `tailwindcss` tree-shaking process.

```bash
# Basic usage (requires NM_TAILWIND_SAFELIST_JSON_LOC setting)
python manage.py nm_extract_tailwind_classes

# With options
python manage.py nm_extract_tailwind_classes --pretty --output ./config/
```

**Command options:**

- `--pretty`: Format output for readability
- `--output PATH`: Specify custom output location (overrides settings)

## Custom CSS Framework

Implementing a custom CSS framework is a substantial undertaking that requires recreating templates and providing complete style configurations.

!!! warning
    **This is major work** - you're essentially rebuilding the entire template system.

### Complete Implementation Steps

**1. Configure Your Framework**

```python
# settings.py
NOMINOPOLITAN_CSS_FRAMEWORK = 'bulma'  # Your framework name
```

**2. Install Your Framework**

- Add CSS/JS files to your base template
- Include any JavaScript dependencies (for modals, dropdowns, etc.)
- If using crispy forms, install appropriate crispy template packs for your framework
- Ensure all framework-specific JavaScript is loaded before Nominopolitan interactions

**3. Create Custom Templates**
```bash
# Copy all templates to customize with your CSS classes
python manage.py nm_mktemplate myapp --all
```

You'll need to update these templates with your framework's classes:

- `object_list.html` - Main list view
- `object_form.html` - Form styling  
- `object_detail.html` - Detail view layout
- `object_confirm_delete.html` - Delete confirmation
- `partial/list.html` - Table structure and styling
- `partial/bulk_edit_form.html` - Bulk operations form
- `partial/filters.html` - Filter form styling
- `partial/pagination.html` - Pagination controls
- `crispy_partials.html` - Crispy forms integration (if using crispy forms)

**4. Override Framework Styles**

The `get_framework_styles()` method must return a complete configuration dictionary. Your framework configuration must include all required components:

**Required Components:**

- `base` - Base CSS class applied to all buttons
- `actions` - Dictionary containing CSS classes for View/Edit/Delete buttons
- `extra_default` - Default CSS class for extra buttons
- `modal_attrs` - HTML attributes to trigger your framework's modal system
- `filter_attrs` - Complete dictionary for all filter field types:
    - `text` - Text input styling
    - `select` - Dropdown select styling
    - `multiselect` - Multi-select dropdown styling (must include 'size' and 'style' for height)
    - `date` - Date input styling (must include 'type': 'date')
    - `number` - Number input styling (must include 'step': 'any')
    - `time` - Time input styling (must include 'type': 'time')
    - `default` - Fallback styling for other field types

These components are used throughout both the template tags and HTMX mixins, so all keys must be present and properly configured for your framework.

**5. Test All Functionality**

- Verify tables render correctly
- Test filtering and sorting
- Confirm modal interactions work
- Check bulk operations interface
- Validate pagination controls
- Test form submissions and validation

## Common Styling Patterns

=== "Basic Table Styling"

    ```python
    class BookCRUDView(NominopolitanMixin, CRUDView):
        model = models.Book
        table_classes = 'table-striped table-hover'
        action_button_classes = 'btn-sm'
    ```

=== "Responsive Tables"

    ```python
    class BookCRUDView(NominopolitanMixin, CRUDView):
        model = models.Book
        
        # Control column width and wrapping
        table_max_col_width = 25
        table_header_min_wrap_width = 15
        
        # Control table height
        table_pixel_height_other_page_elements = 120  # Account for nav, etc.
        table_max_height = 75  # 75% of remaining space
    ```

=== "Sorted Dropdowns"

    ```python
    class BookCRUDView(NominopolitanMixin, CRUDView):
        model = models.Book
        
        # Sort all dropdowns consistently
        dropdown_sort_options = {
            "author": "last_name",
            "genre": "name",
            "publisher": "-name",  # Descending
        }
    ```

=== "Custom Framework Example"

    ```python
    class BookCRUDView(NominopolitanMixin, CRUDView):
        model = models.Book
        templates_path = "myapp/bulma"  # Custom Bulma templates
        
        # Custom styling
        table_classes = 'table is-striped is-hoverable'
        action_button_classes = 'button is-small'
        extra_button_classes = 'button is-primary'
        
        def get_framework_styles(self):
            styles = super().get_framework_styles()
            styles['framework'] = 'bulma'
            styles['table'] = 'table'
            styles['button'] = 'button'
            return styles
    ```

## Configuration Reference

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| `table_classes` | str | `''` | Additional CSS classes for tables |
| `action_button_classes` | str | `''` | Additional CSS classes for action buttons |
| `extra_button_classes` | str | `''` | Additional CSS classes for extra buttons |
| `table_max_col_width` | int | `25` | Maximum column width in characters |
| `table_header_min_wrap_width` | int | Same as max | Minimum width for wrapped headers |
| `table_pixel_height_other_page_elements` | int | `0` | Height of other page elements (px) |
| `table_max_height` | int | `70` | Max table height as % of remaining viewport |
| `dropdown_sort_options` | dict | `{}` | Sort options for dropdown fields |

## Framework Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `NOMINOPOLITAN_CSS_FRAMEWORK` | `'daisyui'` | CSS framework choice |
| `NM_TAILWIND_SAFELIST_JSON_LOC` | `None` | Location for Tailwind safelist file |

## Related Configuration

- **Table display**: See [Core Configuration](core_config.md) for field control
- **Interactive features**: See [HTMX & Modals](htmx_modals.md) for reactive styling
- **Form styling**: See [Form Handling](form_handling.md) for form-specific styling