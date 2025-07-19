# Filtering & Sorting

Add powerful filtering and sorting capabilities to your CRUD views with automatic form generation and HTMX integration.

## Basic Filtering Setup

### Simple Filtering

Enable filtering by specifying which fields should be filterable:

```python
class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    base_template_path = "core/base.html"
    fields = ["name", "owner", "status", "created_date"]
    
    # Enable filtering on specific fields
    filterset_fields = ["owner", "status", "created_date"]
```

This automatically generates filter forms with appropriate widgets:

- **Foreign Key fields**: Dropdown selection
- **Choice fields**: Dropdown selection  
- **Date fields**: Date input widgets
- **Text fields**: Text input for contains/icontains lookup

### HTMX Integration

When `use_htmx = True`, filters update results reactively without page reloads:

```python
class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    base_template_path = "core/base.html"
    use_htmx = True
    filterset_fields = ["owner", "status", "created_date"]
```

### Custom Filterset Class

For advanced filtering, provide your own filterset class:

```python
import django_filters
from nominopolitan.mixins import HTMXFilterSetMixin

class ProjectFilterSet(HTMXFilterSetMixin, django_filters.FilterSet):
    class Meta:
        model = models.Project
        fields = ["owner", "status", "created_date"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setup HTMX attributes for reactive filtering
        self.setup_htmx_attrs()

class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    base_template_path = "core/base.html"
    filterset_class = ProjectFilterSet
    use_htmx = True
```

## Table Sorting

Tables support clickable column headers for sorting:

### Basic Usage

Sorting is enabled by default for all displayed fields:

```python
class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    base_template_path = "core/base.html"
    fields = ["name", "owner", "status", "created_date"]
    use_htmx = True  # For reactive sorting without page reloads
```

### Sorting Behavior

- **Click any column header** to sort by that field
- **Click again** to reverse sort direction
- **Unsorted by default** - first click sorts ascending
- **Secondary sort** by primary key ensures stable pagination
- **Visual indicators** show current sort direction using Hero Icons

### URL Parameters

Sorting uses URL parameters that can be bookmarked:
- `?sort=name` - Sort by name (ascending)
- `?sort=-name` - Sort by name (descending)

## Advanced Filtering Options

### Filter Queryset Options

Restrict which options appear in filter dropdowns:

```python
class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    base_template_path = "core/base.html"
    filterset_fields = ["owner", "status", "category"]
    
    filter_queryset_options = {
        # Only show specific owner in dropdown
        'owner': {'name': 'Nancy Wilson'},
        
        # Only show categories containing "urgent"
        'category': {'name__icontains': 'urgent'},
        
        # Only show active statuses
        'status': {'is_active': True},
    }
```

### Filter Sort Options

!!! note "Foreign Key Fields Only"

    This only affects foreign key fields with dropdown options. Other field types will ignore sort options without error.

Control how dropdown options are sorted for foreign key fields:

```python
class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    base_template_path = "core/base.html"
    filterset_fields = ["owner", "category", "priority"]
    
    filter_sort_options = {
        'owner': 'name',        # Sort owners by name (ascending)
        'category': '-name',    # Sort categories by name (descending)
        'priority': '-order',   # Sort priorities by order field (descending)
    }
```

### Many-to-Many Filter Logic

Control M2M filter logic. The default logic is `AND` (all selected options must match); this can be overridden to use `OR` logic (any selected option must match).

```python
class BookCRUDView(NominopolitanMixin, CRUDView):
    model = models.Book
    base_template_path = "core/base.html"
    filterset_fields = ["authors", "genres"]
    
    # Use AND logic for M2M filters (default is OR)
    m2m_filter_and_logic = True
```

## Customization & Overrides

### Restricting Filter Options

Override `get_filter_queryset_for_field()` to restrict available options for specific filter fields:

```python
class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    base_template_path = "core/base.html"
    filterset_fields = ["owner", "status"]
    
    def get_queryset(self):
        """Restrict main queryset to current user's projects."""
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)
    
    def get_filter_queryset_for_field(self, field_name, model_field):
        """Restrict filter options to match main queryset restrictions."""
        qs = super().get_filter_queryset_for_field(field_name, model_field)
        
        if field_name == 'owner':
            # Only show current user in owner dropdown
            qs = qs.filter(id=self.request.user.id)
        elif field_name == 'category':
            # Only show categories used by current user's projects
            qs = qs.filter(projects__owner=self.request.user).distinct()
            
        return qs
```

**Method Parameters**:

- `field_name` (str): The name of the field being filtered
- `model_field`: The actual Django model field instance (e.g., ForeignKey, CharField)

## Complete Examples

=== "Basic Project Filtering"

    ```python
    class ProjectCRUDView(NominopolitanMixin, CRUDView):
        model = models.Project
        base_template_path = "core/base.html"
        fields = ["name", "owner", "status", "created_date"]
        
        # Enable filtering and sorting
        filterset_fields = ["owner", "status", "created_date"]
        use_htmx = True
        
        # Customize filter options
        filter_sort_options = {
            'owner': 'name',
            'status': 'priority',
        }
    ```

=== "Advanced Book Filtering"

    ```python
    class BookCRUDView(NominopolitanMixin, CRUDView):
        model = models.Book
        base_template_path = "core/base.html"
        fields = ["title", "author", "genres", "published_date"]
        
        # Advanced filtering setup
        filterset_fields = ["author", "genres", "published_date"]
        use_htmx = True
        
        # M2M filter with AND logic
        m2m_filter_and_logic = True
        
        # Restrict and sort filter options
        filter_queryset_options = {
            'author': {'is_active': True},
            'genres': {'name__icontains': 'fiction'},
        }
        
        filter_sort_options = {
            'author': 'name',
            'genres': '-popularity',
        }
        
        def get_filter_queryset_for_field(self, field_name, model_field):
            """Further restrict filter options based on user permissions."""
            qs = super().get_filter_queryset_for_field(field_name, model_field)
            
            if field_name == 'author' and not self.request.user.is_staff:
                # Non-staff users only see public authors
                qs = qs.filter(is_public=True)
                
            return qs
    ```

=== "Custom Filterset Integration"

    ```python
    import django_filters
    from nominopolitan.mixins import HTMXFilterSetMixin

    class ProjectFilterSet(HTMXFilterSetMixin, django_filters.FilterSet):
        # Custom filter with choices
        priority = django_filters.ChoiceFilter(
            choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')],
            empty_label="Any Priority"
        )
        
        # Date range filter
        created_date = django_filters.DateRangeFilter()
        
        class Meta:
            model = models.Project
            fields = ["owner", "status", "priority", "created_date"]
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Setup HTMX attributes for reactive filtering
            self.setup_htmx_attrs()

    class ProjectCRUDView(NominopolitanMixin, CRUDView):
        model = models.Project
        base_template_path = "core/base.html"
        filterset_class = ProjectFilterSet
        use_htmx = True
    ```
