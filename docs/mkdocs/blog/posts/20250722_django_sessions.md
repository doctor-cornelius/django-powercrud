---
date: 2025-07-22
categories:
- django
- sessions
- bulk
---
# Migration from sessionStorage to Django Sessions for Bulk Selection

The current bulk selection system uses browser `sessionStorage` which prevents server-side manipulation of selected items. We need to migrate to Django sessions to enable backend control over selection state.
<!-- more -->

## Why This Change?

**Client-Side Only Storage**: Selection state is trapped in the browser and cannot be manipulated from the server

- No way to programmatically add/remove items from selection
- Cannot implement server-side business logic for selection constraints  
- No persistence across different devices/browsers for the same user
- Selection state lost if user opens new tab/window

**Backend Integration Issues**: 

- Conflict detection systems cannot access current selection state
- Cannot implement selection-based business rules
- No audit trail of selection changes
- Cannot pre-populate selections based on server logic

## Current sessionStorage Implementation

### Frontend (Templates & JavaScript)

**object_list.html**:

- `getStorageKey()` - Returns storage key from Django template variable
- `getSelectedIds()` - Retrieves selected IDs from browser sessionStorage
- `saveSelectedIds(ids)` - Stores selected IDs in browser sessionStorage
- `toggleRowSelection(checkbox)` - Handles individual checkbox changes
- `toggleAllSelection(checked)` - Handles select-all checkbox
- `clearSelection()` - Removes all selections from sessionStorage
- `updateSelectionUI()` - Updates checkboxes and bulk actions based on stored state

**partial/list.html**:

- Checkbox `data-id` attributes for JavaScript selection handling
- `onchange="toggleRowSelection(this)"` handlers on row checkboxes
- `onchange="toggleAllSelection(this.checked)"` on select-all checkbox

### Backend (Python)

**bulk_mixin.py**:

- `get_storage_key()` - Generates unique storage key for model/suffix combination
- `get_bulk_selection_key_suffix()` - Provides suffix for storage key customization  
- `bulk_edit()` - Receives selected IDs via POST/GET parameters from frontend
- Template context includes `storage_key` for JavaScript to use

**Current Flow**: Backend generates storage key → Frontend JavaScript uses key for sessionStorage → User selections stored in browser → Form submission sends selected IDs back to backend

## Simple Solution

Move selection storage from browser `sessionStorage` to Django sessions. This is straightforward since we already have the infrastructure.

The migration will change this to: Backend generates key → Backend stores selections in Django session → HTMX updates sync frontend with backend state → Backend has direct access to current selections.

### What Changes

**Backend (bulk_mixin.py)**: Add methods to get/set selection from Django sessions

```python
def get_selected_ids_from_session(self, request):
  """Get selected IDs for current model from Django session"""
  key = self.get_storage_key()
  selections = request.session.get('powercrud_selections', {})
  return selections.get(key, [])

def save_selected_ids_to_session(self, request, ids):
  """Save selected IDs for current model to Django session"""
  if 'powercrud_selections' not in request.session:
      request.session['powercrud_selections'] = {}
    
  key = self.get_storage_key()
  request.session['powercrud_selections'][key] = ids
  request.session.modified = True
```

**Frontend**: Replace JavaScript sessionStorage calls with HTMX requests to update server state

**Templates**: Render checkboxes based on server session state instead of JavaScript state

## Implementation Tasks

### ✅ Phase 1: Backend Session Support

1. ✅ **Add session methods to BulkMixin**

     - Add `get_selected_ids_from_session(request)` method
     - Add `save_selected_ids_to_session(request, ids)` method
     - Add `toggle_selection(request, obj_id)` method
     - Add `clear_selection(request)` method

2. ✅ **Update bulk_edit method**

     - Check session for selected IDs if not in POST data
     - Maintain backward compatibility with existing POST approach
     - Update context to include session-based selected state

### Phase 2: HTMX Integration

3. **Add selection management views**

     - Add `toggle_selection_view` method to handle HTMX checkbox toggles
     - Add `clear_selection_view` method for clear button
     - Return partial template updates for selection status

4. **Update templates**

     - Replace JavaScript sessionStorage calls with HTMX attributes on checkboxes
     - Update checkbox rendering to show server session state
     - Keep existing JavaScript as fallback for non-HTMX scenarios
     - Selection status partial for bulk actions container
     - Checkbox state partial for individual row updates

### Phase 3: Testing and Cleanup. **Test migration**

     - Test selection persistence across page loads
     - Test bulk operations with session-stored selections
     - Verify fallback behavior works
     - Test with multiple models/suffixes

6. **Documentation**

     - Update docs with session backend requirements
     - Add configuration notes about Django sessions
     - Document new server-side selection capabilities

!!! warning "Implementation Notes"

   - disregard all bootstrap5 templates. bootstrap5 is deprecated at the moment. ONLY work on daisyUI templates
   - we will eventually be removing the current sessionStorage approach completely, including all relevant javascript related to selection, deselection of id's but not other js
   - I do not want to see extra css styles added if possible. We are using daisyUI v5 and tailwindcss v4. It should be possible if customisation is needed to use preferably daisyUI and if not tailwindcss classes
   - do not mess up the extensive work done to ensure persistence of filtering, sort, page size and page number params detailed in [this document](./20250711_filter_preservation.md)

## Django Session Backend

**No Redis Required**: Django sessions work with database backend by default

```python
# Default Django session settings (no changes needed)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Uses database
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = False
```

## Benefits

- **Server Control**: Backend can manipulate selection state programmatically
- **Persistence**: Selections survive browser restarts and tab switches  
- **Reliability**: No loss of selections on page refresh
- **Integration**: Works with existing Django session infrastructure

That's it. Simple migration, real benefits, no rocket science.

## Phase 2 Implementation Details

### Current sessionStorage Analysis

**JavaScript Functions to Replace (object_list.html lines 412-513)**:
- `getStorageKey()` - Returns storage key from Django template variable
- `getSelectedIds()` - Retrieves selected IDs from browser sessionStorage
- `saveSelectedIds(ids)` - Stores selected IDs in browser sessionStorage
- `toggleRowSelection(checkbox)` - Handles individual checkbox changes
- `toggleAllSelection(checked)` - Handles select-all checkbox
- `clearSelection()` - Removes all selections from sessionStorage
- `updateSelectionUI()` - Updates checkboxes and bulk actions based on stored state

**Template Integration Points**:
- **object_list.html**: Bulk actions container (lines 98-108), selection restoration (lines 451-458)
- **partial/list.html**: Checkbox onchange handlers (lines 52, 101), data-id attributes (line 99)

**Current Flow**:
1. User clicks checkbox → `toggleRowSelection()` → sessionStorage update → `updateSelectionUI()`
2. Page navigation/filtering → `updateSelectionUI()` restores state from sessionStorage
3. Bulk edit → JavaScript reads sessionStorage → sends IDs to server
4. Success → `clearSelection()` removes from sessionStorage

### Backend Session Infrastructure (✅ Complete)

**BulkMixin Methods**:
- `get_selected_ids_from_session(request)` - Get selected IDs from Django session
- `save_selected_ids_to_session(request, ids)` - Save selected IDs to Django session
- `toggle_selection_in_session(request, obj_id)` - Toggle individual selection
- `clear_selection_from_session(request)` - Clear all selections

**HTMX Endpoints**:
- `toggle_selection_view()` - Handle individual checkbox toggles
- `clear_selection_view()` - Handle clear selection button
- Both return `partial/bulk_selection_status.html` for UI updates

**URL Patterns (url_mixin.py lines 209-233)**:
```python
# Individual selection toggle
path(f"{cls.url_base}/toggle-selection/<int:{cls.lookup_url_kwarg}>/", ...)

# Clear all selections
path(f"{cls.url_base}/clear-selection/", ...)
```

### New HTMX Architecture Design

#### 1. Selection Status Partial Template

**File**: `powercrud/templates/powercrud/daisyUI/partial/bulk_selection_status.html`

**Purpose**: Update bulk actions container and selection counter

**Context Variables**:
- `selected_count` - Number of currently selected items
- `model_name_plural` - For display text
- `storage_key` - For JavaScript compatibility (if needed)

**Template Content**:
```html
<!-- Bulk actions container - show/hide based on selection count -->
<div id="bulk-actions-container" class="join {% if selected_count == 0 %}hidden{% endif %}">
    <a href="{{ list_view_url }}bulk-edit/" class="join-item btn btn-primary {{ view.get_extra_button_classes }}"
        hx-get="{{ list_view_url }}bulk-edit/" hx-target="#powercrudModalContent"
        onclick="powercrudBaseModal.showModal();">
        Bulk Edit <span id="selected-items-counter">{{ selected_count }}</span>
    </a>
    <button class="join-item btn btn-outline btn-error {{ view.get_extra_button_classes }}"
            hx-post="{{ list_view_url }}clear-selection/"
            hx-target="#bulk-actions-container"
            hx-swap="outerHTML">
        Clear Selection
    </button>
</div>
```

#### 2. Checkbox State Management

**Individual Checkbox Updates**:
- Replace `onchange="toggleRowSelection(this)"` with HTMX attributes
- Use `hx-post` to toggle selection endpoint
- Target specific elements for partial updates

**Select-All Checkbox Logic**:
- Replace JavaScript `toggleAllSelection()` with server-side logic
- Handle via new endpoint that processes all visible page IDs
- Return updated checkbox states and bulk actions

#### 3. HTMX Request/Response Flow

**Individual Checkbox Toggle**:
```
User clicks checkbox →
hx-post="/books/toggle-selection/123/" →
BulkMixin.toggle_selection_view() →
Updates Django session →
Returns bulk_selection_status.html partial →
Updates bulk actions container
```

**Select-All Toggle**:
```
User clicks select-all →
hx-post="/books/toggle-all-selection/" →
New endpoint processes all page IDs →
Updates Django session for all visible items →
Returns full checkbox state update
```

**Clear Selection**:
```
User clicks clear →
hx-post="/books/clear-selection/" →
BulkMixin.clear_selection_view() →
Clears Django session →
Returns empty bulk actions container
```

### Implementation Tasks (5-9)

#### Task 5: Create Selection Status Partial Template

**File**: `powercrud/templates/powercrud/daisyUI/partial/bulk_selection_status.html`

**Requirements**:
- Show/hide bulk actions based on `selected_count`
- Update counter display
- Include clear selection button with HTMX
- Maintain existing daisyUI styling

#### Task 6: Update Checkbox Rendering

**File**: `powercrud/templates/powercrud/daisyUI/partial/list.html`

**Changes Required**:
- Remove `onchange="toggleRowSelection(this)"` from individual checkboxes (line 101)
- Add HTMX attributes: `hx-post`, `hx-target`, `hx-swap`
- Update checkbox `checked` state from server session data
- Remove `onchange="toggleAllSelection(this.checked)"` from select-all (line 52)
- Add server-side select-all logic

**New Checkbox Structure**:
```html
<!-- Individual row checkbox -->
<input type="checkbox"
       class="checkbox checkbox-sm row-select-checkbox"
       data-id="{{ object.id }}"
       {% if object.id|stringformat:"s" in selected_ids %}checked{% endif %}
       hx-post="{{ list_view_url }}toggle-selection/{{ object.id }}/"
       hx-target="#bulk-actions-container"
       hx-swap="outerHTML">

<!-- Select-all checkbox -->
<input type="checkbox" id="select-all-checkbox"
       class="checkbox checkbox-sm checkbox-neutral border-1 border-white"
       {% if all_selected %}checked{% endif %}
       {% if some_selected and not all_selected %}indeterminate{% endif %}
       hx-post="{{ list_view_url }}toggle-all-selection/"
       hx-target="#filtered_results"
       hx-swap="innerHTML">
```

#### Task 7: Replace sessionStorage JavaScript

**Files**: `powercrud/templates/powercrud/daisyUI/object_list.html`

**Functions to Remove**:
- `getStorageKey()` (lines 461-463)
- `getSelectedIds()` (lines 464-468)
- `saveSelectedIds(ids)` (lines 469-473)
- `toggleRowSelection(checkbox)` (lines 474-484)
- `toggleAllSelection(checked)` (lines 485-508)
- `clearSelection()` (lines 509-513)
- `updateSelectionUI()` (lines 413-450)

**Event Listeners to Remove**:
- `document.addEventListener('DOMContentLoaded', updateSelectionUI)` (line 452)
- `document.body.addEventListener('htmx:afterSwap', ...)` (lines 454-458)
- `document.body.addEventListener('htmx:beforeOnLoad', ...)` (lines 392-410)

**Bulk Edit Button Update**:
```html
<!-- Remove JavaScript onclick handler -->
<a href="{{ list_view_url }}bulk-edit/" class="join-item btn btn-primary {{ view.get_extra_button_classes }}"
    hx-get="{{ list_view_url }}bulk-edit/" hx-target="#powercrudModalContent"
    onclick="powercrudBaseModal.showModal();">
    Bulk Edit <span id="selected-items-counter">{{ selected_count }}</span>
</a>
```

#### Task 8: Update Bulk Actions Container

**File**: `powercrud/templates/powercrud/daisyUI/object_list.html`

**Current Container (lines 98-108)**:
```html
<div id="bulk-actions-container" class="join hidden">
    <a href="{{ list_view_url }}bulk-edit/" class="join-item btn btn-primary {{ view.get_extra_button_classes }}"
        hx-get="{{ list_view_url }}bulk-edit/" hx-target="#powercrudModalContent"
        onclick="this.setAttribute('hx-vals', JSON.stringify({'selected_ids': getSelectedIds()})); powercrudBaseModal.showModal();">
        Bulk Edit <span id="selected-items-counter">0</span>
    </a>
    <button class="join-item btn btn-outline btn-error {{ view.get_extra_button_classes }}" onclick="clearSelection()">
        Clear Selection
    </button>
</div>
```

**New Container**:
```html
{% partial bulk_selection_status %}
```
**Note**: The `bulk_selection_status` content was moved into a `partialdef` block within `object_list.html` itself, rather than using a separate include file, to better align with `django-template-partials` usage and keep related logic contained.

#### Task 9: Complete sessionStorage Removal

**Verification Checklist**:
- [ ] No `sessionStorage` references in any daisyUI template
- [ ] No `getSelectedIds()`, `saveSelectedIds()`, etc. function calls
- [ ] No JavaScript selection state management
- [ ] All checkbox interactions use HTMX endpoints
- [ ] Bulk edit form gets selected IDs from Django session
- [ ] Selection state persists across pagination/filtering via server session

### Additional Backend Requirements

#### New Endpoint: Toggle All Selection

**Method**: `toggle_all_selection_view()`
**URL**: `/{url_base}/toggle-all-selection/`
**Logic**:
1. Get all object IDs from current page
2. Check if all are selected or not
3. If all selected → deselect all page items
4. If none/some selected → select all page items
5. Return updated checkbox states for entire page

#### Context Updates

**BulkMixin.get_context_data() additions**:
```python
# Add selection state to context
selected_ids = self.get_selected_ids_from_session(request)
context['selected_ids'] = selected_ids
context['selected_count'] = len(selected_ids)

# For list view, add per-object selection state
if self.role == Role.LIST and hasattr(self, 'object_list'):
    for obj in context['object_list']:
        obj.is_selected = str(obj.id) in selected_ids
    
    # Calculate select-all checkbox state
    page_ids = [str(obj.id) for obj in context['object_list']]
    selected_page_ids = [id for id in selected_ids if id in page_ids]
    context['all_selected'] = len(page_ids) > 0 and len(selected_page_ids) == len(page_ids)
    context['some_selected'] = len(selected_page_ids) > 0
```

### Filter/Sort/Pagination Preservation

**Critical Requirement**: Must not break existing parameter preservation detailed in `filter_preservation.md`

**Current Preservation Methods**:
- **Filtering**: `hx-include="[name]"` gathers all form state
- **Sorting**: Template URL construction with explicit parameters
- **Pagination**: `hx-vals="js:getCurrentFilters()"` (already implemented)
- **Bulk Edit**: JavaScript refresh of `window.location.pathname + window.location.search`

**Migration Impact**:
- Selection state moves from client to server
- Parameter preservation mechanisms remain unchanged
- HTMX requests for selection changes must preserve current URL parameters

**Implementation Note**:
All new HTMX selection endpoints should include current filter/sort/pagination parameters in responses to maintain state consistency.

### Testing Strategy

**Manual Testing Checklist**:
1. **Basic Selection**: Individual checkbox toggle updates bulk actions
2. **Select-All**: Toggle all checkboxes on current page
3. **Cross-Page Selection**: Select items, navigate pages, selections persist
4. **Filter Preservation**: Apply filters, select items, selections maintained
5. **Sort Preservation**: Change sort order, selections persist
6. **Pagination**: Change page size, selections persist
7. **Bulk Edit**: Selected items correctly passed to bulk edit form
8. **Clear Selection**: All selections removed, bulk actions hidden
9. **Modal Integration**: Bulk edit opens in modal, success clears selections
10. **Error Handling**: Network errors don't break selection state

**Browser Compatibility**:
- Modern browsers with HTMX support
- JavaScript required (no graceful degradation needed per requirements)
- Session storage backend (database-based Django sessions)

### Performance Considerations

**Session Storage Impact**:
- Minimal server memory usage (IDs only)
- Database session backend handles persistence
- Session cleanup on bulk operation success

**HTMX Request Frequency**:
- One request per checkbox toggle (acceptable for user-initiated actions)
- Partial template updates minimize DOM changes
- No polling or background requests

**Scalability**:
- Selection state limited to current user session
- No cross-user selection conflicts
- Session data automatically cleaned up on session expiry

This architectural plan provides a complete roadmap for migrating from sessionStorage to Django sessions while preserving all existing functionality and maintaining the extensive filter/sort/pagination parameter preservation work.
