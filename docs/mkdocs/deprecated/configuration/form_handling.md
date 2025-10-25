# Form Handling

Configure form field selection, validation, and styling for create/edit operations.

## Basic Form Field Control

### Auto-Generated Forms
By default, powercrud creates forms automatically from your model:

```python
class AuthorCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Author
    # No form_fields specified = editable fields from detail_fields
    # No detail_fields specified = uses fields
    # No fields specified = all model fields
```

### Specify Form Fields
Control which fields appear in forms:

```python
class AuthorCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Author
    
    # Include specific fields
    form_fields = ["name", "bio", "birth_date"]
    
    # Or use shortcuts
    form_fields = '__all__'      # All editable model fields
    form_fields = '__fields__'   # Only editable fields from 'fields' attribute
    
    # Exclude specific fields
    form_fields_exclude = ["created_date", "modified_date"]
```

!!! note "Default Behavior"

    If not specified, `form_fields` defaults to editable fields from your resolved `detail_fields`.

### Field Selection Priority
Form fields are resolved in this order:

1. **Custom `form_class`** (if specified) - Takes precedence over everything
2. **`form_fields`** - Explicit field list
3. **Default** - Editable fields from `detail_fields`

## Custom Form Classes

When you need more control than auto-generation provides:

```python
# forms.py
class AuthorForm(forms.ModelForm):
    class Meta:
        model = models.Author
        fields = ['name', 'bio', 'birth_date']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

# views.py
class AuthorCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Author
    form_class = AuthorForm  # This overrides form_fields
```

## HTML5 Widgets

Auto-generated forms include HTML5 widgets for better UX:

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Book
    form_fields = ["title", "author", "published_date"]
    # published_date automatically gets type="date" widget
```

**Automatic HTML5 widgets:**

- `DateField` → `<input type="date">`
- `DateTimeField` → `<input type="datetime-local">`
- `TimeField` → `<input type="time">`

## Dropdown Sorting

Control how dropdown options are sorted in forms:

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Book
    form_fields = ["title", "author", "genres"]
    
    dropdown_sort_options = {
        "author": "name",          # Sort authors by name (ascending)
        "genres": "-name",         # Sort genres by name (descending)
    }
```

!!! note

    Dropdown sorting also applies to [filtering](filtering.md) and [bulk operations](bulk_operations.md).

## Crispy Forms Integration

Crispy Forms styling is automatically enabled if installed:

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Book
    form_fields = ["title", "author", "published_date"]
    
    use_crispy = True  # Default: True if crispy-forms is installed
```

!!! note "Automatic Configuration"

    powercrud automatically configures crispy forms to work with HTMX and modals by setting `form_tag = False` and `disable_csrf = True`.

### Custom Crispy Configuration
If you need different crispy settings:

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Book
    form_class = BookForm  # Define your own FormHelper in the form class
    
    def _apply_crispy_helper(self, form_class):
        # Skip automatic crispy configuration
        return form_class
```

## Integration with Other Features

### HTMX & Modals
Forms automatically integrate with HTMX and modals when enabled. See [HTMX & Modals](htmx_modals.md) for configuration details.

### Bulk Operations
Form field configuration affects bulk edit operations. See [Bulk Operations](bulk_operations.md) for details on `bulk_fields` and bulk form behavior.

### Filtering
Dropdown sorting configuration applies to filter dropdowns. See [Filtering](filtering.md) for filtering-specific configuration.

## Examples

=== "Basic Configuration"

    ```python
    class GenreCRUDView(PowerCRUDMixin, CRUDView):
        model = models.Genre
        
        # Simple form configuration
        form_fields = ["name", "description"]
        form_fields_exclude = ["created_date"]
    ```

=== "Advanced Configuration"

    ```python
    class BookCRUDView(PowerCRUDMixin, CRUDView):
        model = models.Book
        
        # Custom form class for complex validation
        form_class = forms.BookForm
        
        # Dropdown sorting (applies to forms, filters, bulk operations)
        dropdown_sort_options = {
            "author": "name",
            "genres": "name"
        }
    ```

=== "Profile with Relationships"

    ```python
    class ProfileCRUDView(PowerCRUDMixin, CRUDView):
        model = models.Profile
        
        # Include related fields
        form_fields = ["author", "nickname", "favorite_genre"]
        
        # Sort related dropdowns
        dropdown_sort_options = {
            "author": "name",
            "favorite_genre": "name"
        }
        
        # Crispy forms styling
        use_crispy = True
    ```

=== "Custom Form with Widgets"

    ```python
    # forms.py
    class BookForm(forms.ModelForm):
        class Meta:
            model = models.Book
            fields = ['title', 'author', 'genres', 'published_date', 'pages']
            widgets = {
                'published_date': forms.DateInput(attrs={'type': 'date'}),
                'pages': forms.NumberInput(attrs={'min': 1}),
                'genres': forms.CheckboxSelectMultiple(),
            }

    # views.py
    class BookCRUDView(PowerCRUDMixin, CRUDView):
        model = models.Book
        form_class = BookForm
    ```

## Configuration Reference

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| `form_fields` | list/str | Editable fields from `detail_fields` | Fields to include in forms |
| `form_fields_exclude` | list | `[]` | Fields to exclude from forms |
| `form_class` | ModelForm | Auto-generated | Custom form class (overrides form_fields) |
| `use_crispy` | bool | `True` if installed | Enable crispy forms styling |
| `dropdown_sort_options` | dict | `{}` | Sort options for dropdown fields |
