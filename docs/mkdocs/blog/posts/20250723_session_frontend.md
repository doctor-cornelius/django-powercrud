---
date: 2025-07-23
categories:
  - django
  - sessions
  - bulk
  - htmx
---
# Django Sessions Bulk Selection: Frontend Implementation Analysis

The migration from client-side sessionStorage to server-side Django sessions for bulk selection encountered critical functionality issues. This document provides a comprehensive analysis of the problems and a detailed implementation plan to resolve them.
<!-- more -->

## Current Implementation Issues

After migrating from client-side sessionStorage to server-side Django sessions, several critical functionality issues emerged:

1. **Select-all functionality broken**: When clicking the "select all" header checkbox, only the header checkbox shows as checked - individual row checkboxes don't update
2. **Bulk Edit not recognizing selections**: After selecting records individually, Bulk Edit button shows error "no records have been selected"
3. **Clear Selection button non-functional**: Clear Selection button does nothing when clicked

These issues stem from architectural changes made during the migration process.

## Architectural Analysis

### Original Architecture

The original plan for migrating from client-side sessionStorage to server-side Django sessions had a clear two-phase approach:

1. **Phase 1 (Backend)**: Implement Django session methods in BulkMixin
   - ✅ Successfully implemented session storage methods
   - ✅ Added HTMX endpoints for toggle/clear operations
   - ✅ Added URL patterns for these endpoints

2. **Phase 2 (Frontend)**: Replace JavaScript with HTMX calls
   - ❌ Problematic implementation with critical functionality issues

### Debug Module Changes

During implementation, a Debug module made several unauthorized architectural changes:

1. **Added `get_context_data` method to BulkMixin (lines 44-60)**
   ```python
   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       selected_ids = self.get_selected_ids_from_session(self.request)
       context['selected_ids'] = selected_ids
       context['selected_count'] = len(selected_ids)
       # Determine if all items on the current page are selected
       if 'object_list' in context:
           current_page_ids = set(str(obj.pk) for obj in context['object_list'])
           all_selected_on_page = current_page_ids.issubset(set(selected_ids))
           some_selected_on_page = bool(current_page_ids.intersection(set(selected_ids)))
           context['all_selected'] = all_selected_on_page and len(current_page_ids) > 0
           context['some_selected'] = some_selected_on_page and not all_selected_on_page
       else:
           context['all_selected'] = False
           context['some_selected'] = False
       return context
   ```

2. **Refactored three separate view methods into a single `post` method (lines 279-328)**
   - Consolidated toggle_selection, clear_selection, and toggle_all_selection into one method
   - Used action-based routing via URL kwargs

3. **Modified HTMX targets**
   - Changed from `#bulk-actions-container` to `#filtered_results`
   - This causes excessive DOM updates and breaks checkbox state

4. **Added URL pattern for toggle-all-selection**
   - Added URL pattern but didn't update URL patterns to use the new post method
   - Created inconsistency between URL routing and view implementation

### Root Causes of Issues

1. **Architectural Inconsistency**:
   - Mismatch between URL patterns (expecting separate view methods) and implementation (using a consolidated `post` method)
   - This causes routing issues and method resolution failures

2. **HTMX Target Mismatch**:
   - The overly broad target (`#filtered_results`) causes excessive DOM updates
   - Re-rendering the entire results section disrupts checkbox state
   - This is the primary cause of the select-all functionality issue

3. **Missing Template Coordination**:
   - The `bulk_selection_status.html` partial is defined in `object_list.html` as a `partialdef`
   - But some code may be trying to reference it as a separate file

4. **Incomplete Implementation**:
   - The Debug module's changes were valuable but incompletely implemented
   - The consolidated approach requires URL pattern changes that weren't made

## Evaluation of Debug Module Changes

Despite being unauthorized, some of the Debug module's changes have architectural merit:

1. **`get_context_data` Method**: ✅ KEEP
   - Correctly calculates selection state for UI rendering
   - Provides essential context for checkbox and bulk actions display
   - Well-implemented and necessary for server-side selection state

2. **Consolidated `post` Method**: ⚠️ REFINE
   - Centralizing selection handling logic has merit
   - But was incompletely implemented, causing the current issues
   - Needs proper integration with URL patterns

3. **HTMX Target Changes**: ❌ REVERT
   - Targeting `#filtered_results` is too broad
   - Causes unnecessary re-rendering and state loss
   - Root cause of most functionality issues

4. **URL Pattern Addition**: ✅ KEEP
   - The toggle-all-selection URL pattern is necessary
   - But needs proper integration with view methods

## Recommended Solution: Refined Hybrid Approach

Based on this analysis, I recommend a hybrid approach that:

1. **Keeps valuable additions**:
   - Retain the `get_context_data` method for selection state calculation
   - Keep the `toggle_all_selection_in_session` functionality

2. **Reverts problematic changes**:
   - Return to separate view methods for each action
   - Fix the HTMX target strategy to use targeted updates

3. **Implements optimal HTMX target strategy**:
   - Use targeted updates with out-of-band swaps
   - Leverage django-template-partials for template organization

## Implementation Details

### 1. BulkMixin Class Modifications

#### 1.1. Keep the `get_context_data` Method

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    selected_ids = self.get_selected_ids_from_session(self.request)
    context['selected_ids'] = selected_ids
    context['selected_count'] = len(selected_ids)
    
    # Determine if all items on the current page are selected
    if 'object_list' in context:
        current_page_ids = set(str(obj.pk) for obj in context['object_list'])
        all_selected_on_page = current_page_ids.issubset(set(selected_ids))
        some_selected_on_page = bool(current_page_ids.intersection(set(selected_ids)))
        context['all_selected'] = all_selected_on_page and len(current_page_ids) > 0
        context['some_selected'] = some_selected_on_page and not all_selected_on_page
    else:
        context['all_selected'] = False
        context['some_selected'] = False
    return context
```

#### 1.2. Create Separate View Methods (Replace Consolidated `post` Method)

```python
def toggle_selection_view(self, request, *args, **kwargs):
    """Handle HTMX requests to toggle selection state for an individual object."""
    if not (hasattr(request, 'htmx') and request.htmx):
        return HttpResponseBadRequest("Only HTMX requests are supported.")
    
    object_id = kwargs.get(self.pk_url_kwarg)
    if not object_id:
        return HttpResponseBadRequest("Object ID not provided.")
    
    # Toggle selection in session
    selected_ids = self.toggle_selection_in_session(request, object_id)
    
    # Prepare context for response
    context = self.get_context_data()
    context['selected_ids'] = selected_ids
    
    # Return bulk actions container with out-of-band updates for select-all checkbox
    response = render(request, f"{self.templates_path}/object_list.html#bulk-actions-container", context)
    
    # Add out-of-band update for select-all checkbox if needed
    if 'object_list' in context:
        select_all_html = render_to_string(
            f"{self.templates_path}/object_list.html#select-all-checkbox", 
            context,
            request=request
        )
        response['HX-Trigger'] = json.dumps({
            'updateSelectAllCheckbox': select_all_html
        })
    
    return response

def clear_selection_view(self, request, *args, **kwargs):
    """Handle HTMX requests to clear all selections."""
    if not (hasattr(request, 'htmx') and request.htmx):
        return HttpResponseBadRequest("Only HTMX requests are supported.")
    
    # Clear selection in session
    self.clear_selection_from_session(request)
    
    # Prepare context for response
    context = self.get_context_data()
    context['selected_ids'] = []
    
    # Return bulk actions container with out-of-band updates for all checkboxes
    response = render(request, f"{self.templates_path}/object_list.html#bulk-actions-container", context)
    
    # Add out-of-band update for all checkboxes
    response['HX-Trigger'] = json.dumps({
        'clearAllCheckboxes': True,
        'updateSelectAllCheckbox': False
    })
    
    return response

def toggle_all_selection_view(self, request, *args, **kwargs):
    """Handle HTMX requests to toggle selection for all objects on the current page."""
    if not (hasattr(request, 'htmx') and request.htmx):
        return HttpResponseBadRequest("Only HTMX requests are supported.")
    
    # Get all object IDs from the current page
    queryset = self.get_queryset()
    object_ids = list(queryset.values_list('pk', flat=True))
    
    # Toggle selection for all objects
    selected_ids = self.toggle_all_selection_in_session(request, object_ids)
    
    # Prepare context for response
    context = self.get_context_data()
    context['selected_ids'] = selected_ids
    
    # Return the table body with updated checkbox states
    response = render(request, f"{self.templates_path}/object_list.html#table-body", context)
    
    # Add out-of-band update for bulk actions container
    bulk_actions_html = render_to_string(
        f"{self.templates_path}/object_list.html#bulk-actions-container", 
        context, 
        request=request
    )
    
    response['HX-Trigger'] = json.dumps({
        'updateBulkActions': bulk_actions_html
    })
    
    return response
```

### 2. Template Modifications

#### 2.1. Add New Partial Templates to object_list.html

```html
{% partialdef select_all_checkbox %}
<input type="checkbox" id="select-all-checkbox"
       class="checkbox checkbox-sm checkbox-neutral border-1 border-white"
       {% if all_selected %}checked{% endif %}
       {% if some_selected and not all_selected %}indeterminate{% endif %}
       hx-post="{{ list_view_url }}toggle-all-selection/"
       hx-target="#table-body"
       hx-swap="innerHTML">
{% endpartialdef select_all_checkbox %}

{% partialdef table_body %}
{% for object in object_list %}
<tr class="text-center hover {% if object.is_selected %}bg-base-200{% endif %}">
    {% if enable_bulk_edit %}
    <!-- Row selection checkbox -->
    <td class="py-0 align-middle">
        <input type="checkbox"
               class="checkbox checkbox-sm row-select-checkbox"
               data-id="{{ object.id }}"
               {% if object.id|stringformat:"s" in selected_ids %}checked{% endif %}
               hx-post="{{ list_view_url }}toggle-selection/{{ object.id }}/"
               hx-target="#bulk-actions-container"
               hx-swap="outerHTML">
    </td>
    {% endif %}
    
    {% for field in object.fields %}
    <td class="{% if forloop.first %}font-medium{% endif %} py-0 align-middle px-2 truncate table-column-width"
        {% if not field|safe|stringformat:"s"|first in "<" %}data-tippy-content="{{field}}"{% endif %}>
        {{ field }}
    </td>
    {% endfor %}
    <td class="text-right py-1 align-middle">
        {{ object.actions }}
    </td>
</tr>
{% endfor %}
{% endpartialdef table_body %}
```

#### 2.2. Update `list.html` to Use the New Partial Templates

```html
<table class="table {{ table_classes }} w-auto">
    <thead>
        <tr>
            {% if enable_bulk_edit %}
            <!-- Bulk selection checkbox column -->
            <th class="bg-neutral text-neutral-content text-center align-middle sticky-header w-10">
                {% partial select_all_checkbox %}
            </th>
            {% endif %}
            
            <!-- Rest of the header row -->
            <!-- ... -->
        </tr>
    </thead>
    <tbody id="table-body">
        {% partial table_body %}
    </tbody>
</table>
```

#### 2.3. Update `bulk_selection_status` Partial

```html
{% partialdef bulk_selection_status %}
<!-- Bulk actions container - show/hide based on selection count -->
<div id="bulk-actions-container" class="join {% if selected_count == 0 %}hidden{% endif %}">
    <a href="{{ list_view_url }}bulk-edit/" class="join-item btn btn-primary {{ view.get_extra_button_classes }}"
        hx-get="{{ list_view_url }}bulk-edit/" hx-target="#nominopolitanModalContent"
        onclick="nominopolitanBaseModal.showModal();">
        Bulk Edit <span id="selected-items-counter">{{ selected_count }}</span>
    </a>
    <button class="join-item btn btn-outline btn-error {{ view.get_extra_button_classes }}"
            hx-post="{{ list_view_url }}clear-selection/"
            hx-target="#bulk-actions-container"
            hx-swap="outerHTML">
        Clear Selection
    </button>
</div>
{% endpartialdef bulk_selection_status %}
```

### 3. Add JavaScript for HTMX Event Handling

```javascript
// Add to object_list.html
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // Handle checkbox updates from HTMX events
    if (evt.detail.triggerSpec && evt.detail.triggerSpec.includes('updateSelectAllCheckbox')) {
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        if (selectAllCheckbox && evt.detail.xhr.response) {
            try {
                const response = JSON.parse(evt.detail.xhr.response);
                if (response.updateSelectAllCheckbox === false) {
                    selectAllCheckbox.checked = false;
                    selectAllCheckbox.indeterminate = false;
                } else if (typeof response.updateSelectAllCheckbox === 'string') {
                    // Replace the checkbox with the new HTML
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = response.updateSelectAllCheckbox;
                    const newCheckbox = tempDiv.firstElementChild;
                    selectAllCheckbox.parentNode.replaceChild(newCheckbox, selectAllCheckbox);
                }
            } catch (e) {
                console.error('Error updating select-all checkbox:', e);
            }
        }
    }
    
    // Handle clearing all checkboxes
    if (evt.detail.triggerSpec && evt.detail.triggerSpec.includes('clearAllCheckboxes')) {
        document.querySelectorAll('.row-select-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
    }
    
    // Handle updating bulk actions container
    if (evt.detail.triggerSpec && evt.detail.triggerSpec.includes('updateBulkActions')) {
        try {
            const response = JSON.parse(evt.detail.xhr.response);
            if (typeof response.updateBulkActions === 'string') {
                const bulkActionsContainer = document.getElementById('bulk-actions-container');
                if (bulkActionsContainer) {
                    bulkActionsContainer.outerHTML = response.updateBulkActions;
                }
            }
        } catch (e) {
            console.error('Error updating bulk actions:', e);
        }
    }
});
```

### 4. URL Pattern Adjustments

Ensure the URL patterns in `url_mixin.py` match the view methods:

```python
# Add URL for toggling individual selection
urls.append(
    path(
        f"{cls.url_base}/toggle-selection/<int:{cls.lookup_url_kwarg}>/",
        cls.as_view(
            role=Role.LIST,
            http_method_names=["post"],
            template_name_suffix="_toggle_selection",
        ),
        name=f"{cls.url_base}-toggle-selection",
    )
)

# Add URL for clearing all selections
urls.append(
    path(
        f"{cls.url_base}/clear-selection/",
        cls.as_view(
            role=Role.LIST,
            http_method_names=["post"],
            template_name_suffix="_clear_selection",
        ),
        name=f"{cls.url_base}-clear-selection",
    )
)

# Add URL for toggling all selection on the current page
urls.append(
    path(
        f"{cls.url_base}/toggle-all-selection/",
        cls.as_view(
            role=Role.LIST,
            http_method_names=["post"],
            template_name_suffix="_toggle_all_selection",
        ),
        name=f"{cls.url_base}-toggle-all-selection",
    )
)
```

## HTMX Target Strategy

The optimal HTMX target strategy is critical for fixing the functionality issues:

### 1. Individual Checkbox Toggle

**What Changes**:
- The specific checkbox's checked state
- The bulk actions container visibility and selection count
- Potentially the select-all checkbox state

**Target Strategy**:
- Primary target: `#bulk-actions-container`
- Use HX-Trigger to update select-all checkbox if needed

### 2. Select-All Toggle

**What Changes**:
- All checkboxes on the current page
- The select-all checkbox state
- The bulk actions container

**Target Strategy**:
- Primary target: `#table-body` (containing all row checkboxes)
- Use HX-Trigger to update bulk actions container

### 3. Clear Selection

**What Changes**:
- All checkboxes should be unchecked
- The select-all checkbox should be unchecked
- The bulk actions container should be hidden

**Target Strategy**:
- Primary target: `#bulk-actions-container`
- Use HX-Trigger to update all checkboxes and select-all checkbox

## Additional Architectural Improvements

Beyond fixing the immediate issues, these architectural improvements would enhance the bulk selection system:

### 1. Selection State Management Class

Create a dedicated class for managing selection state:

```python
class SelectionState:
    """Manages selection state for a specific model and user session."""
    
    def __init__(self, request, storage_key):
        self.request = request
        self.storage_key = storage_key
        self._load_state()
    
    def _load_state(self):
        """Load selection state from session."""
        if 'nominopolitan_selections' not in self.request.session:
            self.request.session['nominopolitan_selections'] = {}
        self.selected_ids = self.request.session['nominopolitan_selections'].get(self.storage_key, [])
    
    def save(self):
        """Save selection state to session."""
        self.request.session['nominopolitan_selections'][self.storage_key] = self.selected_ids
        self.request.session.modified = True
    
    # Additional methods for toggle, clear, toggle_all, etc.
```

### 2. HTMX Response Builder

Create a dedicated class for building HTMX responses:

```python
class HtmxResponseBuilder:
    """Builds HTMX responses with out-of-band swaps and triggers."""
    
    def __init__(self, request, templates_path):
        self.request = request
        self.templates_path = templates_path
        self.triggers = {}
        self.oob_swaps = []
    
    # Methods for adding triggers, out-of-band swaps, etc.
    
    def build(self, primary_template, context):
        """Build the HTMX response with the primary template and all additions."""
        # Implementation
```

### 3. Cross-Page Selection Management

Enhance the selection system to handle cross-page selections more explicitly:

```python
def get_selection_stats(self, selected_ids):
    """Get selection statistics for the current view."""
    page_ids = self.get_page_object_ids()
    total_count = self.get_queryset().count()
    
    # Calculate statistics
    selected_on_page = [id for id in selected_ids if str(id) in page_ids]
    all_selected_on_page = len(selected_on_page) == len(page_ids) and len(page_ids) > 0
    some_selected_on_page = len(selected_on_page) > 0 and not all_selected_on_page
    
    return {
        'total_count': total_count,
        'selected_count': len(selected_ids),
        'page_count': len(page_ids),
        'selected_on_page_count': len(selected_on_page),
        'all_selected_on_page': all_selected_on_page,
        'some_selected_on_page': some_selected_on_page,
        'all_selected': len(selected_ids) == total_count and total_count > 0,
    }
```

### 4. Selection Validation

Add validation for selections to prevent unauthorized access:

```python
def validate_selection(self, request, selected_ids):
    """Validate that the user has permission to operate on the selected objects."""
    # Get queryset with permission filtering
    queryset = self.get_queryset()
    
    # Check if all selected IDs are in the queryset
    valid_ids = set(str(id) for id in queryset.values_list('pk', flat=True))
    selected_set = set(map(str, selected_ids))
    
    # Find invalid IDs
    invalid_ids = selected_set - valid_ids
    
    if invalid_ids:
        return False, f"Invalid selection: {', '.join(invalid_ids)}"
    
    return True, None
```

## Implementation Steps

1. **Remove the consolidated `post` method** from BulkMixin
2. **Add the three separate view methods** for toggle, clear, and toggle-all
3. **Add the new partial templates** to object_list.html
4. **Update the existing templates** to use the new partials
5. **Add the JavaScript event handlers** for HTMX events
6. **Verify URL patterns** match the view methods
7. **Test each operation** to ensure it works correctly

## Testing Plan

1. **Individual Checkbox Toggle**:
   - Click a checkbox and verify it toggles correctly
   - Verify the bulk actions container updates with the correct count
   - Verify the select-all checkbox updates to the correct state

2. **Select-All Toggle**:
   - Click the select-all checkbox and verify all checkboxes on the page toggle
   - Verify the bulk actions container updates with the correct count
   - Verify toggling again deselects all checkboxes

3. **Clear Selection**:
   - Select multiple checkboxes, then click Clear Selection
   - Verify all checkboxes are unchecked
   - Verify the bulk actions container is hidden

4. **Bulk Edit**:
   - Select multiple checkboxes, then click Bulk Edit
   - Verify the modal opens with the correct selected IDs
   - Verify bulk edit operations work correctly

5. **Filter/Sort/Pagination Preservation**:
   - Apply filters, then select checkboxes
   - Change sort order and verify selections persist
   - Navigate to another page and back, verify selections persist

## Conclusion

The migration from client-side sessionStorage to server-side Django sessions encountered issues due to architectural inconsistencies and problematic HTMX target strategies. By implementing the refined hybrid approach outlined in this document, we can fix the functionality issues while maintaining the valuable architectural improvements from the Debug module.

The key to success is using targeted HTMX updates with out-of-band swaps to ensure UI components stay in sync with the server-side selection state. This approach provides a robust solution that respects the project's architecture and constraints.


## Implementation Plan

Following the Architect's hybrid approach, here's the comprehensive task plan broken into small, manageable delegations:

### Phase 1: Revert Problematic Debug Changes

#### Delegation 1A: Restore Original Architecture
- **Task**: Remove the consolidated `post` method from BulkMixin and restore original separate view methods
- **Files**: `nominopolitan/mixins/bulk_mixin.py`
- **Documentation**: Read sections "Debug Module Changes Assessment" and "Recommended Solution" from `@/docs/mkdocs/blog/posts/20250723_session_frontend.md`
- **Testing Point**: ⚠️ **STOP FOR MANUAL TESTING** - Verify individual checkbox toggles work without errors

#### Delegation 1B: Fix HTMX Target Strategy
- **Task**: Revert HTMX targets from `#filtered_results` back to `#bulk-actions-container` in templates
- **Files**: `nominopolitan/templates/nominopolitan/daisyUI/partial/list.html`
- **Documentation**: Read "HTMX Target Strategy Analysis" section from `@/docs/mkdocs/blog/posts/20250723_session_frontend.md`
- **Testing Point**: ⚠️ **STOP FOR MANUAL TESTING** - Verify bulk actions container updates correctly

### Phase 2: Keep Valuable Additions

#### Delegation 2A: Preserve get_context_data Method
- **Task**: Ensure the `get_context_data` method added by Debug module is properly integrated and working
- **Files**: `nominopolitan/mixins/bulk_mixin.py`
- **Documentation**: Read "Debug Module Changes Assessment" section from `@/docs/mkdocs/blog/posts/20250723_session_frontend.md`
- **Testing Point**: ⚠️ **STOP FOR MANUAL TESTING** - Verify bulk actions buttons show/hide correctly on page load

### Phase 3: Implement Missing Functionality

#### Delegation 3A: Add toggle_all_selection_view Method
- **Task**: Implement the missing `toggle_all_selection_view` method in BulkMixin
- **Files**: `nominopolitan/mixins/bulk_mixin.py`
- **Documentation**: Read "Implementation Plan" section from `@/docs/mkdocs/blog/posts/20250723_session_frontend.md` and original context from `@/docs/mkdocs/blog/posts/20250722_django_sessions.md`
- **Testing Point**: ⚠️ **STOP FOR MANUAL TESTING** - Verify select-all checkbox functionality works

### Phase 4: Complete URL Configuration

#### Delegation 4A: Update URL Patterns
- **Task**: Ensure all URL patterns are properly configured for the restored separate view methods
- **Files**: `nominopolitan/mixins/url_mixin.py`
- **Documentation**: Read "URL Pattern Analysis" section from `@/docs/mkdocs/blog/posts/20250723_session_frontend.md`
- **Testing Point**: ⚠️ **STOP FOR MANUAL TESTING** - Verify all selection endpoints return 200 status codes

### Phase 5: Implement HTMX Out-of-Band Strategy

#### Delegation 5A: Add Out-of-Band Swap Support
- **Task**: Modify view methods to return HTMX out-of-band swaps for UI synchronization
- **Files**: `nominopolitan/mixins/bulk_mixin.py`
- **Documentation**: Read "HTMX Out-of-Band Swap Implementation" section from `@/docs/mkdocs/blog/posts/20250723_session_frontend.md`
- **Testing Point**: ⚠️ **STOP FOR MANUAL TESTING** - Verify checkboxes and bulk actions update simultaneously

### Phase 6: Template Updates

#### Delegation 6A: Update Template HTMX Attributes
- **Task**: Add proper HTMX attributes and IDs for out-of-band swap targeting
- **Files**: `nominopolitan/templates/nominopolitan/daisyUI/object_list.html`, `nominopolitan/templates/nominopolitan/daisyUI/partial/list.html`
- **Documentation**: Read "Template Implementation Details" section from `@/docs/mkdocs/blog/posts/20250723_session_frontend.md`
- **Testing Point**: ⚠️ **STOP FOR MANUAL TESTING** - Verify complete UI synchronization works

### Phase 7: Final Integration

#### Delegation 7A: Cleanup and Verification
- **Task**: Remove any remaining problematic code, verify all functionality works end-to-end
- **Files**: All modified files
- **Documentation**: Read "Testing Plan" section from `@/docs/mkdocs/blog/posts/20250723_session_frontend.md`
- **Testing Point**: ⚠️ **STOP FOR COMPREHENSIVE MANUAL TESTING** - Full functionality verification

### Key Instructions for All Delegations

1. **Required Reading**: Each delegation MUST read the specified sections from `@/docs/mkdocs/blog/posts/20250723_session_frontend.md` and `@/docs/mkdocs/blog/posts/20250722_django_sessions.md`

2. **Testing Stops**: When you see ⚠️ **STOP FOR MANUAL TESTING**, the delegation MUST pause and explicitly request manual testing before proceeding

3. **Small Scope**: Each delegation focuses on ONE specific aspect to avoid overwhelming context

4. **Documentation First**: Always read the architectural guidance before implementing

### Progress Tracking

- [ ] Phase 1A: Restore Original Architecture
- [ ] Phase 1B: Fix HTMX Target Strategy  
- [ ] Phase 2A: Preserve get_context_data Method
- [ ] Phase 3A: Add toggle_all_selection_view Method
- [ ] Phase 4A: Update URL Patterns
- [ ] Phase 5A: Add Out-of-Band Swap Support
- [ ] Phase 6A: Update Template HTMX Attributes
- [ ] Phase 7A: Cleanup and Verification