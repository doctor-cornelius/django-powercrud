---
date: 2025-08-25
categories:
  - development
  - features
---
# Inline Table Editing - What's Already Available

Exploring what powercrud already provides for implementing inline table editing with HTMX.

<!-- more -->

## Inline Table Editing Design Pattern

The flow for this is along these lines:

- icon or other trigger to enable edit of a row (could just be user clicks the row)
- `htmx` swaps in a partial of the row setup for editing (eg with `hx-post`, different `html` elements, a new 'save' icon, etc). This is probably wrapped in a `<form>` tag. 
- user edits and clicks the save icon for the row, or saves on every field change, etc
- form errors shown inline (on the row) if validation fails
- if `form_valid()` then swap in the edited row with non-edit `html` elements for display only.

## Field Type Introspection and HTML Mapping

Powercrud already has robust model field introspection that maps Django field types to appropriate HTML elements and display formats.

### Display Rendering (Read-Only)

The [`object_list()` template tag](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/templatetags/powercrud.py#L154) performs comprehensive field introspection for table display:

- **M2M Fields**: Joins related object names with commas
- **Boolean Fields**: Renders as tick/cross SVG icons
- **Date Fields**: Formats as dd/mm/yyyy
- **Related Fields**: Displays the string representation of related objects
- **Other Types**: Falls back to Django's `value_to_string()`

The [`object_detail()` template tag](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/templatetags/powercrud.py#L118) handles both model fields and properties, using appropriate methods for relations vs non-relations.

### Form Rendering (Editable)

The [`FormMixin.get_form_class()`](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/mixins/form_mixin.py#L107) method dynamically generates ModelForms with appropriate widgets:

- **Date Fields**: HTML5 `<input type="date">`
- **DateTime Fields**: HTML5 `<input type="datetime-local">`
- **Time Fields**: HTML5 `<input type="time">`
- **Other Fields**: Django's default widget mapping (ModelChoiceField → select, BooleanField → checkbox, etc.)

Additional features include:
- Dropdown sorting for related fields via `dropdown_sort_options`
- Crispy Forms integration when available
- Automatic field validation and filtering

## Framework-Aware Styling

The project includes a pattern for applying CSS framework-specific attributes through [`HtmxMixin.get_framework_styles()`](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/mixins/htmx_mixin.py#L25).

The 'filter_attrs' section demonstrates how different input types get daisyUI classes:
- Text inputs: `input input-bordered input-sm`
- Selects: `select select-bordered select-sm`
- Multi-selects: Custom sizing and styling
- Date/time inputs: Appropriate type attributes plus styling

This pattern could be extended to provide consistent styling for inline edit controls.

## Two Implementation Approaches

### Option 1: Dynamic Form Class (Recommended)

This approach leverages the existing form generation infrastructure:

**Advantages:**

- Reuses [`FormMixin.get_form_class()`](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/mixins/form_mixin.py#L107) for widget selection
- Inherits HTML5 input types for date/time fields
- Gets crispy forms integration automatically
- Benefits from existing dropdown sorting functionality
- HTMX lifecycle already handled for success/error cases

**Existing Integration Points:**

- Form success handling in [`FormMixin.form_valid()`](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/mixins/form_mixin.py#L197)
- Error handling in [`FormMixin.form_invalid()`](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/mixins/form_mixin.py#L277)
- HTMX partial rendering in [`HtmxMixin.render_to_response()`](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/mixins/htmx_mixin.py#L255)
- Existing daisyUI form templates for consistency

### Option 2: Template Tag

This would create a new template tag for inline row editing:

**Advantages:**

- More direct control over HTML output
- Can follow patterns from existing [`object_list()`](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/templatetags/powercrud.py#L154) tag
- Potentially simpler for basic use cases

**Implementation Notes:**

- Would need to recreate field-to-widget mapping logic
- Should reuse framework styling patterns from `get_framework_styles()`
- Would need custom HTMX attribute handling

## Existing Assets to Leverage

### Field and Property Management

- [`CoreMixin._get_all_fields()`](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/mixins/core_mixin.py#L239) - Get all model fields
- [`CoreMixin._get_all_editable_fields()`](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/mixins/core_mixin.py#L249) - Filter to editable fields
- Field/property configuration processing in [`CoreMixin.__init__()`](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/mixins/core_mixin.py#L83)

### Template Structure

- [daisyUI list partial](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/templates/powercrud/daisyUI/partial/list.html) - Current table rendering
- [daisyUI object_list](https://github.com/doctor-cornelius/django-powercrud/blob/main/src/powercrud/templates/powercrud/daisyUI/object_list.html) - HTMX targets and containers

### HTMX Infrastructure

- Partial swapping and retargeting mechanisms already in place
- Success/error trigger handling established
- URL push/replace logic implemented

## What's Missing?

The main gap is a dedicated "inline row editor" component that can:

- Swap a display row for an editable row on demand
- Apply appropriate daisyUI classes to form controls
- Handle HTMX form submission and response
- Revert to display mode on success/cancel

Everything else needed for inline editing (field introspection, widget selection, styling patterns, and HTMX plumbing) already exists in the codebase and can be reused.
