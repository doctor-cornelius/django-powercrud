# HTMX & Modals

Configure HTMX integration and modal dialogs for enhanced user interactions.

## Installation & Dependencies

Add to your `settings.py`:

```python
INSTALLED_APPS = [
    ...
    "django_htmx",
    ...
]
```

**Frontend requirements:**

- HTMX JavaScript library
- Popper.js (for table truncation popovers)

## Feature Dependencies

| Feature | Requires HTMX | Requires Modals |
|---------|:-------------:|:---------------:|
| Reactive page loads | ✓ | |
| Reactive pagination | ✓ | |
| Table sorting without page reload | ✓ | |
| Modal dialogs for CRUD | ✓ | ✓ |
| Bulk operations | ✓ | ✓ |

## Modal Configuration

The default modal is defined in `object_list.html` with:

- **Modal ID**: `powercrudBaseModal`
- **Content target**: `powercrudModalContent`

To use your own modal, override these settings:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    use_htmx = True
    use_modal = True
    
    modal_id = "myCustomModal"        # Your modal's ID
    modal_target = "myModalContent"   # Your content target ID (no # prefix)
```

## Basic Configuration

### Enable HTMX
```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    use_htmx = True
```

### Enable Modals
```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    use_htmx = True   # Required
    use_modal = True  # All CRUD actions open in modals
```

## Advanced Configuration

### HTMX Target
Control where HTMX responses are rendered:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    use_htmx = True
    
    # Override default target (default: '#content')
    default_htmx_target = '#main-content'
```

### HTMX Triggers
HTMX triggers fire custom JavaScript events after server responses, enabling client-side reactions like notifications, UI updates, or data refreshes:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    use_htmx = True
    
    # Single trigger - fires 'projectUpdated' event
    hx_trigger = 'projectUpdated'
    
    # Multiple triggers with data - useful for notifications, counters, etc.
    hx_trigger = {
        'dataChanged': None,              # Simple event
        'showMessage': 'Record updated',  # Event with string data
        'updateCount': 42                 # Event with numeric data
    }
```

Catch these events with JavaScript:

```javascript
document.addEventListener('showMessage', function(e) {
    // e.detail.value contains 'Record updated'
    showNotification(e.detail.value);
});
```

### Modal Customization
Override default modal configuration:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    use_htmx = True
    use_modal = True
    
    # Custom modal ID (default: "powercrudBaseModal")
    modal_id = "projectModal"
    
    # Custom content target (default: "powercrudModalContent")
    modal_target = "projectModalContent"
```

## Configuration Reference

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| `use_htmx` | bool | `None` | Enable HTMX for reactive updates |
| `use_modal` | bool | `None` | Enable modal dialogs for CRUD operations |
| `default_htmx_target` | str | `'#content'` | Default target for HTMX responses |
| `hx_trigger` | str/dict | `None` | Custom HTMX triggers for responses |
| `modal_id` | str | `"powercrudBaseModal"` | ID of modal container |
| `modal_target` | str | `"powercrudModalContent"` | Target for modal content |

## Examples

### Basic Setup
```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Book
    use_htmx = True
    use_modal = True
    
    # Standard configuration
    filterset_fields = ["author", "genre"]
    bulk_fields = ["status", "author"]
    paginate_by = 25
```

### Custom Modal Integration
```python
class TaskCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Task
    use_htmx = True
    use_modal = True
    
    # Use existing modal in your base template
    modal_id = "appModal"
    modal_target = "appModalContent"
    
    # Custom triggers for your frontend
    hx_trigger = {
        'taskUpdated': None,
        'showNotification': 'Task saved'
    }
```