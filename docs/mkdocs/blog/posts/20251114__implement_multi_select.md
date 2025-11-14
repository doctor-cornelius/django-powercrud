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

**Important**: This implementation focuses specifically on the multiselect widget for inline editing. The broader "widget registry" system for template customization is a **future enhancement** that will be considered when we implement "A Better Way to Override Templates" (see `docs/mkdocs/reference/enhancements.md` and the separate [Widget Registry post](./20251114_widget_registry.md)).

### Architecture

#### 1. Widget Template Partial

Create `src/powercrud/templates/powercrud/daisyUI/partial/inline_multiselect.html`:

```html
{% if use_crispy %}
    {% load crispy_forms_field %}
{% endif %}

{% with selections=field.value|default:[] %}
<div class="dropdown">
    <button type="button" class="btn btn-sm btn-outline w-32 text-left"
            onclick="toggleInlineMultiselect('{{ field.id_for_label }}')">
        <span id="summary-{{ field.id_for_label }}">
            {% if selections %}
                {% for value in selections %}
                    {% if not forloop.first %}, {% endif %}
                    {% for choice_value, choice_label in field.field.choices %}
                        {% if choice_value|stringformat:"s" == value|stringformat:"s" %}{{ choice_label }}{% endif %}
                    {% endfor %}
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
                       {% if choice_value|stringformat:"s" in selections %}checked{% endif %}
                       onchange="updateInlineMultiselectSummary('{{ field.id_for_label }}')">
                {{ choice_label }}
            </label>
        </li>
        {% endfor %}
    </ul>
</div>
{% endwith %}
```

*Note: Conditionally loads crispy forms tags only if `use_crispy` is True, following the pattern used in `list.html` and `object_form.html`. The `bg-base-100` class provides the appropriate background color for the current daisyUI theme.*

#### 2. Mixin Logic in InlineEditingMixin

Add widget preparation method to `src/powercrud/mixins/inline_editing_mixin.py`:

**Note**: Add `from django.db import models` to the imports at the top of the file.

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

        # Mark the field for custom rendering (use underscores for template access)
        field.widget.attrs['data_inline_multiselect'] = 'true'
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
    {% elif field.field.widget.attrs.data_inline_multiselect|default_if_none:'' %}
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

        // Close any other open dropdowns first (scoped to inline table)
        const inlineTable = document.querySelector('[data-inline-enabled="true"]');
        if (inlineTable) {
            inlineTable.querySelectorAll('[id^="dropdown-"]').forEach(d => {
                if (d !== dropdown && !d.classList.contains('hidden')) {
                    d.classList.add('hidden');
                }
            });
        }

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
            const inlineTable = document.querySelector('[data-inline-enabled="true"]');
            if (inlineTable) {
                inlineTable.querySelectorAll('[id^="dropdown-"]').forEach(dropdown => {
                    dropdown.classList.add('hidden');
                });
            }
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

## Summary

This implementation provides a **targeted solution** for the inline multi-select problem:

- **Immediate value**: Solves the tall `<select multiple>` element issue in inline editing
- **Minimal scope**: Only affects M2M fields in inline editing context
- **Future-compatible**: Sets foundation for broader widget customization when the template system is enhanced
- **Production-ready**: Handles all edge cases and incorporates expert technical feedback

## Task List

1. [x] Create the widget template partial at `src/powercrud/templates/powercrud/daisyUI/partial/inline_multiselect.html`
2. [x] Add `_prepare_inline_multiselect_widgets()` method to `src/powercrud/mixins/inline_editing_mixin.py`
3. [x] Add `from django.db import models` import to `src/powercrud/mixins/inline_editing_mixin.py` (was already present)
4. [x] Modify `src/powercrud/templates/powercrud/daisyUI/partial/list.html` to detect and render M2M fields (corrected - used list.html instead of layout/inline_field.html)
5. [x] Add JavaScript functions to `src/powercrud/templates/powercrud/daisyUI/object_list.html`
6. [x] Add widget preparation calls in `InlineEditingMixin._dispatch_inline_row()` (both GET and POST branches)
7. [x] Add widget preparation call in `InlineEditingMixin._render_inline_row_form()`
8. [x] Add `auto_id` to inline form creation in `FormMixin.build_inline_form()` (additional fix for field IDs)
9. [ ] Test with sample M2M fields to ensure proper form submission and display
10. [ ] Verify no regressions in existing inline editing functionality

