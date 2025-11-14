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

### Architecture

#### 1. Widget Template Partial

Create `src/powercrud/templates/powercrud/daisyUI/partial/inline_multiselect.html`:

```html
{% if use_crispy %}
    {% load crispy_forms_field %}
{% endif %}

<div class="dropdown">
    <div tabindex="0" role="button" class="btn btn-sm btn-outline w-32 text-left"
         onclick="toggleInlineMultiselect('{{ field.id_for_label }}')">
        <span id="summary-{{ field.id_for_label }}">Selected: {{ field.value|length }}</span>
    </div>
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
        model_field = getattr(self.model, field_name, None)
        if not model_field or not hasattr(model_field, 'many_to_many') or not model_field.many_to_many:
            continue

        # Mark the field for custom rendering
        field.widget.attrs['data-inline-multiselect'] = 'true'
        # Ensure we have choices available for template rendering
        if hasattr(field, 'choices') and not field.choices:
            # Populate choices from related model if not already set
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
    {% elif field.field.widget.attrs.data-inline-multiselect %}
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
function toggleInlineMultiselect(fieldId) {
    const dropdown = document.getElementById('dropdown-' + fieldId);
    const trigger = dropdown.previousElementSibling;

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
    const checkboxes = dropdown.querySelectorAll('input[type="checkbox"]');
    const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
    const summary = document.getElementById('summary-' + fieldId);
    summary.textContent = `Selected: ${checkedCount}`;
}
```

#### 5. Integration Point

Call widget preparation in `InlineEditingMixin._render_inline_row_form()`:

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

### UX Behavior

- Single-row height maintained in table
- Dropdown expands downward by default
- Automatically switches to upward expansion when insufficient viewport space below (< 200px) and more space available above
- Checkboxes allow multiple selection
- Summary shows count of selected items
- Form submits all selected values as array


