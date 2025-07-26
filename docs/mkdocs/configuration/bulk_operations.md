# Bulk Operations

Efficiently edit or delete multiple records at once with atomic transactions and persistent selection.

## Basic Setup

Enable bulk editing and/or deletion:

```python
class BookCRUDView(NominopolitanMixin, CRUDView):
    model = models.Book
    base_template_path = "core/base.html"
    
    # Required for bulk operations
    use_htmx = True
    use_modal = True
    
    # Enable bulk edit for specific fields
    bulk_fields = ['title', 'author', 'published_date', 'bestseller']
    
    # Enable bulk delete
    bulk_delete = True
```

!!! note "Requirements"

    Bulk operations require both `use_htmx = True` and `use_modal = True`.


??? warning "Selecting More Than 1000 Records"

    If you anticipate users selecting >= 1000 records at a time for bulk processing, you need to explicitly set the `DATA_UPLOAD_MAX_NUMBER_FIELDS` in `settings.py`. The default for this setting as per the [Django docs](https://docs.djangoproject.com/en/5.2/ref/settings/) is 1000.

    For example: `DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000`

    Currently, if the the selected records exceeds the default setting, there is no error displayed on the front end (only in the server logs) and from the user's perspective they will get a misleading message saying "No items selected for bulk edit"



## How It Works

- **Selection**: Checkboxes appear next to each record
- **Persistence**: Selected rows survive pagination and page reloads  
- **Atomic Operations**: All changes applied together or none at all
- **Modal Interface**: Bulk edit form opens in a modal dialog
- **Validation**: By default, `full_clean()` runs on each object before saving
- **Save Process**: `save()` is always called on every object after validation

## Field Types Supported

All Django field types work with bulk operations:

- **Basic fields**: CharField, DateField, BooleanField, IntegerField, etc.
- **Foreign keys**: Dropdown selection with sorting support
- **Many-to-many**: Multiple selection with replace/add/remove actions
- **OneToOne**: Single selection dropdown

## Configuration Options

### Validation Control

By default, bulk operations will call the `full_clean()` and `save()` method for every selected object. You can override to skip the `full_clean()` step.

```python
class BookCRUDView(NominopolitanMixin, CRUDView):
    model = models.Book
    base_template_path = "core/base.html"
    bulk_fields = ['title', 'author']
    
    # Skip full_clean() for better performance (default: True)
    bulk_full_clean = False
```

### Dropdown Sorting

```python
class BookCRUDView(NominopolitanMixin, CRUDView):
    model = models.Book
    base_template_path = "core/base.html"
    bulk_fields = ['author', 'publisher']
    
    dropdown_sort_options = {
        'author': 'name',        # Sort authors by name (ascending)
        'publisher': '-name',    # Sort publishers by name (descending)
    }
```

## Customization & Overrides

### Restricting Dropdown Choices

Override `get_bulk_choices_for_field()` to limit foreign key options:

```python
class BookCRUDView(NominopolitanMixin, CRUDView):
    model = models.Book
    base_template_path = "core/base.html"
    bulk_fields = ['author', 'publisher']
    
    def get_bulk_choices_for_field(self, field_name, field):
        """Restrict foreign key choices for bulk edit dropdown."""
        if field_name == 'author' and hasattr(field, "related_model"):
            # Only show active authors
            return field.related_model.objects.filter(is_active=True)
        
        return super().get_bulk_choices_for_field(field_name, field)
```

### Selection Key Customization

Customize how selections are stored:

```python
def get_bulk_selection_key_suffix(self):
    """Add custom constraints to selection persistence."""
    # Example: separate selections by user
    return f"user_{self.request.user.id}"
```

## Error Handling

All bulk operations are atomic - either all records are updated/deleted or none are. When validation fails, the form displays errors and allows correction while preserving selections.

## Examples

=== "Basic Setup"

    ```python
    class BookCRUDView(NominopolitanMixin, CRUDView):
        model = models.Book
        base_template_path = "core/base.html"
        
        # Required for bulk operations
        use_htmx = True
        use_modal = True
        
        # Enable bulk operations
        bulk_fields = ['title', 'published_date', 'bestseller', 'author', 'genres']
        bulk_delete = True
        
        # Sort dropdown options
        dropdown_sort_options = {
            'author': 'name',
            'genres': '-name',
        }
    ```

=== "Advanced Configuration"

    ```python
    class ProjectCRUDView(NominopolitanMixin, CRUDView):
        model = models.Project
        base_template_path = "core/base.html"
        
        use_htmx = True
        use_modal = True
        
        # Bulk operations
        bulk_fields = ['status', 'priority', 'assigned_to', 'due_date', 'tags']
        bulk_delete = True
        bulk_full_clean = False  # Performance optimization
        
        # Custom dropdown sorting
        dropdown_sort_options = {
            'assigned_to': 'last_name',
            'tags': 'name',
        }
        
        def get_bulk_choices_for_field(self, field_name, field):
            """Restrict choices based on user permissions."""
            if field_name == 'assigned_to':
                # Only show team members user can assign to
                return field.related_model.objects.filter(
                    teams__members=self.request.user
                ).distinct()
            
            return super().get_bulk_choices_for_field(field_name, field)
        
        def get_bulk_selection_key_suffix(self):
            """Separate selections by team."""
            return f"team_{self.request.user.current_team.id}"
    ```