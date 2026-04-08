---
date: 2025-11-14
categories:
  - enhancement
  - styles
  - templates
---
# Future Enhancement: Widget Registry for Template Extension

This is an idea for a customisable widget registry for template packs.
<!-- more -->

## Current Widget System Integration

The implementation extends powercrud's existing widget system rather than replacing it.

### FormMixin.get_form_class() Current Behavior

Currently, `FormMixin.get_form_class()` handles widgets in a basic way:

```python
def get_form_class(self):
    # Configure HTML5 input widgets for date/time fields
    widgets = {}
    for field in self.model._meta.get_fields():
        if isinstance(field, db_models.DateField):
            widgets[field.name] = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        elif isinstance(field, db_models.DateTimeField):
            widgets[field.name] = forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
        # ... similar for TimeField

    form_class = modelform_factory(self.model, fields=self.form_fields, widgets=widgets)
```

This is a **static, hardcoded** system that only handles specific Django field types.

### Extended Framework-Agnostic Widget System

The new system extends this with framework-specific custom widgets:

```python
def get_form_class(self):
    # ... existing date/time widget logic ...
    widgets = self._get_basic_widgets()

    # NEW: Apply framework-specific custom widgets
    framework_widgets = self._get_framework_widgets()
    widgets.update(framework_widgets)

    form_class = modelform_factory(self.model, fields=self.form_fields, widgets=widgets)

    # NEW: Mark fields for custom template rendering
    self._mark_fields_for_custom_rendering(form_class)
```

### Future: Framework-Agnostic Widget Registry

**Note**: The comprehensive widget registry system described below is **future enhancement work** that will be considered when implementing "A Better Way to Override Templates" (see `docs/mkdocs/reference/enhancements.md`). For now, we're implementing the multiselect widget as a specialized solution.

## Conceptual Design (For Future Implementation)

A framework-agnostic widget registry would allow template packs to provide custom widgets for specific Django field types in specific contexts, providing a clean API for framework-specific implementations.

**For the current multiselect implementation, we skip this registry and implement the widget directly as a special case in the inline editing system.**

```python
# Future API - NOT implemented now
def get_framework_styles(self):
    return {
        'frameworkName': {
            'widgets': {
                'ManyToManyField': {
                    'contexts': ['inline'],
                    'template': 'powercrud/frameworkName/partial/inline_multiselect.html',
                    'classes': {...}
                }
            }
        }
    }
```

## Widget Configuration Properties

### Required Properties
- **`contexts`**: Array of contexts where widget applies (`['inline', 'modal', 'all']`)
- **`template`**: Path to widget template partial
- **`classes`**: Dict of CSS class names for widget elements

### Optional Properties
- **`description`**: Human-readable description of the widget
- **`dependencies`**: Array of required JS/CSS dependencies
- **`config`**: Widget-specific configuration options
- **`field_types`**: Override which Django field types this applies to (rarely needed)

## Context Specification

Widgets can specify where they apply:

- **`'inline'`**: Only in inline editing (table rows)
- **`'modal'`**: Only in modal forms
- **`'all'`**: Everywhere the field type appears
- **`'list'`**: In list views (future use)

## Implementation Guide for Template Packs

### Step 1: Identify Customization Opportunities

```python
# In your framework's HtmxMixin subclass
class MyFrameworkHtmxMixin(HtmxMixin):
    def get_framework_styles(self):
        return {
            'myFramework': {
                'widgets': {
                    # Start with the most impactful customizations
                    'ManyToManyField': self._get_multiselect_config(),
                    'DateTimeField': self._get_datetime_config(),
                }
            }
        }
```

### Step 2: Create Widget Templates

Create `powercrud/myFramework/partial/inline_multiselect.html`:

```html
{% comment %}Custom multi-select widget for MyFramework{% endcomment %}
<div class="{{ classes.container|default:'dropdown' }}">
    <button type="button" class="{{ classes.trigger|default:'btn btn-sm' }}"
            onclick="toggleMyFrameworkMultiselect('{{ field.id_for_label }}')">
        <span id="summary-{{ field.id_for_label }}">
            {% if field.value %}{{ field.value|length }} selected{% else %}Select items{% endif %}
        </span>
    </button>
    <div class="{{ classes.menu|default:'menu' }} hidden" id="dropdown-{{ field.id_for_label }}">
        {% for choice_value, choice_label in field.field.choices %}
        <label class="cursor-pointer">
            <input type="checkbox" class="{{ classes.checkbox|default:'checkbox' }}"
                   name="{{ field.html_name }}" value="{{ choice_value }}"
                   {% if choice_value|stringformat:"s" in field.value %}checked{% endif %}
                   onchange="updateMyFrameworkSummary('{{ field.id_for_label }}')">
            {{ choice_label }}
        </label>
        {% endfor %}
    </div>
</div>
```

### Step 3: Add JavaScript Functions

In your framework's `object_list.html`, add widget-specific functions:

```javascript
// MyFramework multiselect functions
function toggleMyFrameworkMultiselect(fieldId) {
    const dropdown = document.getElementById('dropdown-' + fieldId);
    // Framework-specific toggle logic
    dropdown.classList.toggle('hidden');
}

function updateMyFrameworkSummary(fieldId) {
    const dropdown = document.getElementById('dropdown-' + fieldId);
    const checkboxes = dropdown.querySelectorAll('input[type="checkbox"]:checked');
    const summary = document.getElementById('summary-' + fieldId);
    summary.textContent = `${checkboxes.length} selected`;
}
```

### Step 4: Handle Template Loading

Ensure your widget templates load required tags:

```html
{% if use_crispy %}
    {% load crispy_forms_field %}
{% endif %}
<!-- Your widget HTML here -->
```

## Validation and Error Handling

The system validates widget definitions:

```python
def _validate_widget_config(self, widget_config, field_type):
    """Validate widget configuration for a field type."""
    required = ['contexts', 'template', 'classes']
    for prop in required:
        if prop not in widget_config:
            raise ValueError(f"Widget for {field_type} missing required property: {prop}")

    if not isinstance(widget_config['contexts'], list):
        raise ValueError(f"Widget contexts for {field_type} must be a list")

    # Validate context values
    valid_contexts = {'inline', 'modal', 'all', 'list'}
    for context in widget_config['contexts']:
        if context not in valid_contexts:
            raise ValueError(f"Invalid context '{context}' for {field_type} widget")
```

## Best Practices for Template Packs

### 1. Start Minimal
```python
# Don't try to customize everything at once
'widgets': {
    'ManyToManyField': {...},  # Most impactful
    # Add others incrementally
}
```

### 2. Follow Framework Conventions
```python
# Use your framework's naming conventions
'classes': {
    'container': 'myframework-dropdown',
    'trigger': 'myframework-btn myframework-btn-outline',
    # Not 'btn btn-outline' (Bootstrap/DaisyUI classes)
}
```

### 3. Handle Edge Cases
```python
# Consider empty states, loading states, error states
<span id="summary-{{ field.id_for_label }}">
    {% if field.value %}
        {{ field.value|length }} selected
    {% else %}
        Select {{ field.label|default:'items' }}
    {% endif %}
</span>
```

### 4. Test Across Contexts
```python
# Ensure widgets work in all specified contexts
'ManyToManyField': {
    'contexts': ['inline', 'modal'],  # Test both
    # ...
}
```

## Migration Path for Existing Template Packs

Existing template packs continue working unchanged:

```python
# Before: No widgets section
def get_framework_styles(self):
    return {
        'myFramework': {
            # Existing style configurations
            'actions': {...},
            'filter_attrs': {...},
        }
    }

# After: Add widgets section (optional)
def get_framework_styles(self):
    return {
        'myFramework': {
            # Existing configurations unchanged
            'actions': {...},
            'filter_attrs': {...},

            # New: Optional widgets section
            'widgets': {
                'ManyToManyField': {...},
            }
        }
    }
```

## Future Widget Types

This system supports future customizations:

- **`FileField`**: Drag-and-drop upload widgets
- **`JSONField`**: Code editors with syntax highlighting
- **`ForeignKey`**: Enhanced relationship pickers
- **`DecimalField`**: Currency inputs with formatting

Each follows the same pattern: Django field type → context specification → template + classes.

## Summary

This document outlines a **targeted implementation** for inline multi-select widgets that:

1. **Delivers immediate value** - Solves the tall `<select multiple>` problem for inline editing
2. **Uses existing patterns** - Extends current widget system without major architectural changes
3. **Sets foundation for future** - The conceptual registry design provides a roadmap for broader widget customization
4. **Incorporates expert feedback** - Addresses technical issues identified in the AI review

The implementation focuses on the specific use case while maintaining compatibility with future enhancements when "A Better Way to Override Templates" is developed.

#### Complete Integration Flow

1. **`FormMixin.get_form_class()`** - Creates form with basic widgets + framework custom widgets
2. **`InlineEditingMixin._prepare_inline_multiselect_widgets()`** - Marks M2M fields for custom rendering
3. **Template logic** in `layout/inline_field.html` - Checks for custom rendering flags and uses appropriate templates
4. **Framework styles** in `HtmxMixin.get_framework_styles()` - Provides widget definitions

### UX Behavior

- Single-row height maintained in table
- Dropdown expands downward by default
- Automatically switches to upward expansion when insufficient viewport space below (< 200px) and more space available above
- Checkboxes allow multiple selection
- Summary shows comma-separated selected item labels (e.g., "Fiction, Mystery, Adventure") or "Select items" when empty
- Clicking outside closes any open dropdown
- Only one dropdown open at a time
- Form submits all selected values as array

### Future Extensibility

This system supports future custom widgets for other constrained contexts:

- **Rich text editors** for TextField in modal forms
- **Date range pickers** for date fields
- **Color pickers** for color fields
- **File upload widgets** with drag-and-drop

Each would follow the same pattern: Django field type key → context specification → template + classes.


