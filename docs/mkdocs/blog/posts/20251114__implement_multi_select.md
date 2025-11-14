---
date: 2025-11-14
categories:
  - styles
  - inline
  - enhancement
---
# Implementing Inline Multi-Select

This article is the plan to implement the "Roll Your Own" inline multi-select element assessed in [this post](./20251113_multi_select.md).
<!-- more -->
## Design

### Overview

We'll implement a custom inline multi-select widget that replaces the tall `<select multiple>` element with a single-row dropdown containing checkboxes. This maintains table row height while providing full multi-selection functionality.

**Important**: This implementation focuses specifically on the multiselect widget for inline editing. The broader "widget registry" system described later in this document is a **future enhancement** that will be considered when we implement "A Better Way to Override Templates" (see `docs/mkdocs/reference/enhancements.md`).

### Architecture

#### 1. Widget Template Partial

Create `src/powercrud/templates/powercrud/daisyUI/partial/inline_multiselect.html`:

```html
{% if use_crispy %}
    {% load crispy_forms_field %}
{% endif %}

<div class="dropdown">
    <button type="button" class="btn btn-sm btn-outline w-32 text-left"
            onclick="toggleInlineMultiselect('{{ field.id_for_label }}')">
        <span id="summary-{{ field.id_for_label }}">
            {% if field.value %}
                {% for value in field.value %}
                    {% if forloop.first %}{{ value }}{% else %}, {{ value }}{% endif %}
                {% endfor %}
            {% else %}
                Select items
            {% endif %}
        </span>
    </button>
    <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-[1] w-52 p-2 shadow hidden"
        id="dropdown-{{ field.id_for_label }}">
        {% for choice_value, choice_label in field.field.choices %}
        <li>
            <label class="cursor-pointer">
                <input type="checkbox" class="checkbox checkbox-sm"
                       name="{{ field.html_name }}" value="{{ choice_value }}"
                       {% if choice_value|stringformat:"s" in field.value %}checked{% endif %}
                       onchange="updateInlineMultiselectSummary('{{ field.id_for_label }}')">
                {{ choice_label }}
            </label>
        </li>
        {% endfor %}
    </ul>
</div>
```

*Note: Conditionally loads crispy forms tags only if `use_crispy` is True, following the pattern used in `list.html` and `object_form.html`. The `bg-base-100` class provides the appropriate background color for the current daisyUI theme.*

#### 2. Mixin Logic in InlineEditingMixin

Add widget preparation method to `src/powercrud/mixins/inline_editing_mixin.py`:

```python
def _prepare_inline_multiselect_widgets(self, form):
    """Convert M2M fields to use custom inline multiselect rendering."""
    if not form:
        return

    for field_name, field in form.fields.items():
        # Check if this is a ManyToMany field
        try:
            model_field = self.model._meta.get_field(field_name)
        except Exception:
            continue

        if not isinstance(model_field, models.ManyToManyField):
            continue

        # Mark the field for custom rendering
        field.widget.attrs['data-inline-multiselect'] = 'true'
        # Ensure we have choices available for template rendering
        if hasattr(field, 'choices') and not field.choices:
            # Use the form field's queryset to avoid extra queries
            queryset = getattr(field, 'queryset', None)
            if queryset is not None:
                field.choices = [(obj.pk, str(obj)) for obj in queryset]
            else:
                # Fallback to related model if no queryset set
                related_model = model_field.remote_field.model
                field.choices = [(obj.pk, str(obj)) for obj in related_model.objects.all()]
```

#### 3. Template Logic in layout/inline_field.html

Modify `src/powercrud/templates/powercrud/daisyUI/layout/inline_field.html` to detect and render M2M fields:

```html
{% load crispy_forms_field %}

{% if field.is_hidden %}
    {{ field }}
{% else %}
    {% if field|is_checkbox %}
        <div id="div_{{ field.auto_id }}" class="form-control w-full md:w-auto items-center gap-2{% if wrapper_class %} {{ wrapper_class }}{% endif %}">
            {% crispy_field field 'class' 'checkbox checkbox-sm' %}
            <label for="{{ field.id_for_label }}" class="text-sm font-medium">
                {{ field.label }}
            </label>
        </div>
    {% elif field.field.widget.attrs|get:'data-inline-multiselect' %}
        <!-- Custom multiselect for M2M fields -->
        {% include "powercrud/daisyUI/partial/inline_multiselect.html" %}
    {% else %}
        <div id="div_{{ field.auto_id }}"{% if wrapper_class %} class="{{ wrapper_class }}"{% endif %}>
            <label for="{{ field.id_for_label }}" class="sr-only">
                {{ field.label }}
            </label>
            {% if field.errors %}
                {% crispy_field field 'class' 'input input-bordered input-sm w-full' 'placeholder' field.label %}
                <p class="text-error text-xs mt-1">{{ field.errors|join:", " }}</p>
            {% else %}
                {% crispy_field field 'class' 'input input-bordered input-sm w-full' 'placeholder' field.label %}
            {% endif %}
        </div>
    {% endif %}
{% endif %}
```

#### 4. JavaScript in object_list.html

Add interaction functions to the `<script>` section in `src/powercrud/templates/powercrud/daisyUI/object_list.html`:

```javascript
// Inline multiselect functions - wrapped in IIFE to prevent redefinition
(function() {
    if (window.powercrudMultiselectInitialized) return;
    window.powercrudMultiselectInitialized = true;

    function toggleInlineMultiselect(fieldId) {
        const dropdown = document.getElementById('dropdown-' + fieldId);
        const trigger = dropdown.previousElementSibling;

        // Close any other open dropdowns first
        document.querySelectorAll('[id^="dropdown-"]').forEach(d => {
            if (d !== dropdown && !d.classList.contains('hidden')) {
                d.classList.add('hidden');
            }
        });

        // Get trigger position relative to viewport
        const rect = trigger.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const spaceBelow = viewportHeight - rect.bottom;
        const spaceAbove = rect.top;

        // Remove existing direction classes
        const container = dropdown.parentElement;
        container.classList.remove('dropdown-bottom', 'dropdown-top');

        // Decide direction: if less than 200px below AND more space above than below, drop up
        const minSpaceNeeded = 200; // Minimum space for dropdown
        if (spaceBelow < minSpaceNeeded && spaceAbove > spaceBelow) {
            container.classList.add('dropdown-top');
        } else {
            container.classList.add('dropdown-bottom');
        }

        // Toggle visibility
        dropdown.classList.toggle('hidden');
    }

    function updateInlineMultiselectSummary(fieldId) {
        const dropdown = document.getElementById('dropdown-' + fieldId);
        const checkboxes = dropdown.querySelectorAll('input[type="checkbox"]:checked');
        const selectedLabels = Array.from(checkboxes).map(cb => {
            const label = cb.closest('li')?.querySelector('label');
            return label ? label.textContent.trim() : '';
        }).filter(label => label);

        const summary = document.getElementById('summary-' + fieldId);
        if (selectedLabels.length > 0) {
            summary.textContent = selectedLabels.join(', ');
        } else {
            summary.textContent = 'Select items';
        }
    }

    // Close dropdowns when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.dropdown')) {
            document.querySelectorAll('[id^="dropdown-"]').forEach(dropdown => {
                dropdown.classList.add('hidden');
            });
        }
    });

    // Export functions to global scope
    window.toggleInlineMultiselect = toggleInlineMultiselect;
    window.updateInlineMultiselectSummary = updateInlineMultiselectSummary;
})();
```

#### 5. Integration Point

Call widget preparation in `InlineEditingMixin._dispatch_inline_row()` before validation:

```python
def _dispatch_inline_row(self, request, *args, **kwargs):
    # ... existing code ...
    obj = self.get_object()

    should_render_display = request.GET.get("inline_display") or request.POST.get("inline_display")

    auth_state = self._evaluate_inline_state(obj, request)
    if auth_state["status"] != "ok":
        return self._build_inline_guard_response(obj, auth_state)

    if should_render_display:
        # ... existing code ...
    elif request.method == "POST":
        lock_state = self._evaluate_inline_state(obj, request)
        if lock_state["status"] != "ok":
            return self._build_inline_guard_response(obj, lock_state)

        form = self.build_inline_form(instance=obj, data=request.POST, files=request.FILES)
        self._prepare_inline_number_widgets(form)
        self._prepare_inline_multiselect_widgets(form)  # Add this line - before validation
        self._preserve_inline_raw_data(form, request.POST)
        # ... rest of method
    else:
        # GET request
        form = self.build_inline_form(instance=obj)
        self._prepare_inline_number_widgets(form)
        self._prepare_inline_multiselect_widgets(form)  # Add this line
        # ... rest of method
```

Also call in `InlineEditingMixin._render_inline_row_form()` for consistency:

```python
def _render_inline_row_form(self, obj, form=None, error_summary: str | None = None) -> str:
    row_payload = self._build_inline_row_payload(obj)
    inline_form = form or self.build_inline_form(instance=obj)
    self._prepare_inline_number_widgets(inline_form)
    self._prepare_inline_multiselect_widgets(inline_form)  # Add this line
    # ... rest of method
```

### Key Benefits

- **Template-based**: Widget HTML lives in a reusable partial
- **Mixin-integrated**: Logic in `InlineEditingMixin` where it belongs
- **Persistent JS**: Functions in `object_list.html` that survives HTMX swaps
- **Conditional rendering**: Only applies to M2M fields in inline context
- **Template inheritance**: Uses existing `layout/inline_field.html` structure

### Form Processing

The existing form processing in `InlineEditingMixin._dispatch_inline_row()` already handles multiple values correctly via `request.POST.getlist(field_name)`, so no changes needed there.

### Current Widget System Integration

The implementation extends powercrud's existing widget system rather than replacing it.

#### FormMixin.get_form_class() Current Behavior

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

#### Extended Framework-Agnostic Widget System

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

#### Future: Framework-Agnostic Widget Registry

**Note**: The comprehensive widget registry system described below is **future enhancement work** that will be considered when implementing "A Better Way to Override Templates" (see `docs/mkdocs/reference/enhancements.md`). For now, we're implementing the multiselect widget as a specialized solution.

### Conceptual Design (For Future Implementation)

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

### Widget Configuration Properties

#### Required Properties
- **`contexts`**: Array of contexts where widget applies (`['inline', 'modal', 'all']`)
- **`template`**: Path to widget template partial
- **`classes`**: Dict of CSS class names for widget elements

#### Optional Properties
- **`description`**: Human-readable description of the widget
- **`dependencies`**: Array of required JS/CSS dependencies
- **`config`**: Widget-specific configuration options
- **`field_types`**: Override which Django field types this applies to (rarely needed)

### Context Specification

Widgets can specify where they apply:

- **`'inline'`**: Only in inline editing (table rows)
- **`'modal'`**: Only in modal forms
- **`'all'`**: Everywhere the field type appears
- **`'list'`**: In list views (future use)

### Implementation Guide for Template Packs

#### Step 1: Identify Customization Opportunities

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

#### Step 2: Create Widget Templates

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

#### Step 3: Add JavaScript Functions

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

#### Step 4: Handle Template Loading

Ensure your widget templates load required tags:

```html
{% if use_crispy %}
    {% load crispy_forms_field %}
{% endif %}
<!-- Your widget HTML here -->
```

### Validation and Error Handling

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

### Best Practices for Template Packs

#### 1. Start Minimal
```python
# Don't try to customize everything at once
'widgets': {
    'ManyToManyField': {...},  # Most impactful
    # Add others incrementally
}
```

#### 2. Follow Framework Conventions
```python
# Use your framework's naming conventions
'classes': {
    'container': 'myframework-dropdown',
    'trigger': 'myframework-btn myframework-btn-outline',
    # Not 'btn btn-outline' (Bootstrap/DaisyUI classes)
}
```

#### 3. Handle Edge Cases
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

#### 4. Test Across Contexts
```python
# Ensure widgets work in all specified contexts
'ManyToManyField': {
    'contexts': ['inline', 'modal'],  # Test both
    # ...
}
```

### Migration Path for Existing Template Packs

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

### Future Widget Types

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


