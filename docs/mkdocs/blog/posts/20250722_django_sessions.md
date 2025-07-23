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
  selections = request.session.get('nominopolitan_selections', {})
  return selections.get(key, [])

def save_selected_ids_to_session(self, request, ids):
  """Save selected IDs for current model to Django session"""
  if 'nominopolitan_selections' not in request.session:
      request.session['nominopolitan_selections'] = {}
    
  key = self.get_storage_key()
  request.session['nominopolitan_selections'][key] = ids
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

3. ✅ **Add selection management views**

     - Add `toggle_selection_view` method to handle HTMX checkbox toggles
     - Add `clear_selection_view` method for clear button
     - Return partial template updates for selection status
     - **Critical**: Ensure these views preserve existing filter, sort, and pagination parameters in their responses.

4. **Update templates**

     - Replace JavaScript sessionStorage calls with HTMX attributes on checkboxes
     - Update checkbox rendering to show server session state
     - Keep existing JavaScript as fallback for non-HTMX scenarios
     - Selection status partial for bulk actions container
     - Checkbox state partial for individual row updates

## Parameter Preservation Integration

The migration to Django sessions for bulk selection must critically ensure the preservation of existing filter, sort, and pagination parameters. The current system relies on URL-based parameters for these functionalities, and any change to the selection mechanism must not disrupt this.

This requires a hybrid approach:
- **URL-based parameters**: Continue to manage filtering, sorting, and pagination state via URL query parameters.
- **Django session selections**: Manage bulk selections via Django sessions.

It is paramount that the new HTMX-driven selection updates do not interfere with the existing URL parameters. For more details on filter preservation, refer to the [Filter Preservation Blog Post](20250711_filter_preservation.md).

### Technical Implementation Notes:

- **Separate HTMX Targets**: Ensure HTMX requests for selection updates target specific, isolated elements (e.g., the bulk action container, individual checkboxes) and do not inadvertently trigger full page reloads or reset URL parameters.
- **Parameter Preservation in HTMX Requests**: When making HTMX requests for selection changes, explicitly include all relevant filter, sort, and pagination parameters from the current URL or form state. This can be achieved using `hx-vals` or by including hidden inputs within the form that triggers the HTMX request.
- **Maintain Existing JavaScript**: During the transition, existing JavaScript functions responsible for parameter preservation (e.g., those that read URL parameters and populate hidden form fields) must be maintained and potentially adapted to work alongside the new HTMX interactions. This ensures a smooth transition and prevents regressions in existing functionality.
     - **Critical**: Verify that existing parameter preservation mechanisms (e.g., hidden inputs, URL parameters) continue to function correctly after template updates.

### Phase 3: Testing and Cleanup

5. **Test migration**

     - Test selection persistence across page loads
     - Test bulk operations with session-stored selections
     - Verify fallback behavior works
     - Test with multiple models/suffixes

6. **Documentation**

     - Update docs with session backend requirements
     - Add configuration notes about Django sessions
     - Document new server-side selection capabilities

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
- **Backward Compatibility**: Maintains existing filter, sort, and pagination parameter preservation functionality.

That's it. Simple migration, real benefits, no rocket science.
