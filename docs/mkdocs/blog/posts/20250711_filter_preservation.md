---
date: 2025-07-11
categories:
  - frontend
  - filters
---
# Preserving Filtering, Sort and Pagination Parameters

This is a record of my thought procss (yeah and the AI coding assistant's) of solving the problem of how to ensure that filter, sort and pagination parameters as well as current page number are preserved on edit, bulk edit, change of filtering and change of page number.

<!-- more -->
## Overview

There are four operations where filter, sort and pagination parameters need to be preserved:

- single record edit
- bulk edit operations
- filter form
- page number selection

At present (unfortunately) the methods used to achieve this are different, and page number selection does **not** yet preserve parameters. But as a first step we will document how things currently work as a base for reconsideration.

And before we get into how params are preserved, let's start with what we have going on.

### Filtering

#### Front End

- Filtering is only present `{% if filterset %}`, which is True if `filterset_fields` is not empty
- Filter toggle button conditionally displayed in `object_list.html` to show/hide filter form
- Filter form (`#filter-form`) displays fields configured on backend as `{% for field in filterset.form %}`
- Each filter field gets HTMX attributes via `HTMXFilterSetMixin.setup_htmx_attrs()` for dynamic updates
- Hidden fields preserve non-filter parameters (sort, page_size) during filter changes
- Form targets `#filtered_results` for partial page updates
- **Key files**: `object_list.html` (lines 76-95, 150-194)

#### Back End

- View classes specify `filterset_fields = [...]` to enable filtering
- `HTMXFilterSetMixin` adds HTMX attributes to filter fields (`hx-get`, `hx-include="[name]"`, `hx-trigger`)
- `PowerCRUDMixin.get_filterset()` creates django-filter FilterSet with HTMX support
- Filter field widgets get appropriate triggers (keyup for text, change for selects)
- `list()` method processes filterset and applies filtering to queryset
- **Key files**: `mixins.py` (HTMXFilterSetMixin, get_filterset method)

### Sorting

#### Front End

- Column headers in table are clickable when `is_sortable=True`
- Sort indicators (up/down arrows) show current sort direction using SVG icons
- Each header constructs URL with new sort parameter while preserving other params
- Sort toggles between ascending (`field`), descending (`-field`), and unsorted
- Uses HTMX for dynamic updates or full page reload depending on `use_htmx` setting
- **Key files**: `partial/list.html` (table header section with sort logic)

#### Back End

- `current_sort` tracked from `request.GET.get('sort', '')` 
- Template tag `object_list` processes sort parameter and generates headers with sort state
- Sorting includes secondary sort by primary key for stable pagination
- Sort parameter cleaned and passed to pagination/filtering to maintain state
- **Key files**: `templatetags/powercrud.py` (object_list function), `mixins.py` (list method)

### Pagination

#### Front End

- Page size selector dropdown allows user to choose records per page (5, 10, 25, 50, 100, "All")
- User selection becomes `page_size` URL parameter (e.g., `?page_size=25`)
- When `page_size="all"`, pagination is disabled and all records shown
- Page size changes use HTMX with `hx-include="[name]"` to preserve filters/sort while updating results
- Pagination links show page numbers with proper elision (1 ... 5 6 7 ... 20)

- **Currently broken**: Page number links fail to preserve `page_size` and filter parameters when clicked
- Page size persists across filtering and sorting operations via hidden form fields
- **Key files**: `object_list.html` (page-size-form, pagination partial)

#### Back End

- Views specify `paginate_by` to set default page size
- `get_paginate_by()` checks `request.GET.get('page_size')` and overrides default if present
- Special handling: `page_size="all"` returns None to disable pagination completely
- `get_page_size_options()` generates available choices (includes default if not in standard list)
- `paginate_queryset()` applies user-selected page size from request parameters
- Page object and pagination context passed to templates with current page size preserved
- **Key files**: `mixins.py` (get_paginate_by, get_page_size_options), `object_list.html` (pagination partial)


## How Params are Preserved

### Single Record Edit

**Method**: Hidden form fields → POST extraction → request.GET patching → role switching → response headers

**Frontend (object_form.html)**:
- Edit form includes hidden fields for all current GET parameters (except csrf, page)
- Parameters are prefixed with `_PowerCRUD_filter_` to avoid conflicts:
```html
{% for key, values in request.GET.lists %}
    {% if key != 'csrfmiddlewaretoken' and key != 'page' %}
        {% for value in values %}
            <input type="hidden" name="_PowerCRUD_filter_{{ key }}" value="{{ value }}">
        {% endfor %}
    {% endif %}
{% endfor %}
```

**Backend (form_valid method)**:
1. **Extract parameters**: Parse POST data for `_PowerCRUD_filter_` prefixed fields
2. **Build canonical URL**: Create clean URL with filter/sort parameters
3. **Patch request**: Temporarily replace `request.GET` with extracted filter parameters
4. **Role switch**: Change role to `Role.LIST` and call `list()` method to reuse filtering logic
5. **Set headers**: 
   - `HX-Trigger: {"formSuccess": True}` (close modal)
   - `HX-Retarget` to original target (usually `#content`)
   - `HX-Push-Url` with canonical URL (updates browser address bar)
   - `X-Redisplay-Object-List` and `X-Filter-Sort-Request` (template selection)

**Key insight**: Reuses the existing `list()` method and template rendering logic by temporarily "faking" a list request with the preserved parameters.

### Bulk Edit Operations

**Method**: SessionStorage selection → Hidden fields for IDs only → POST success → JavaScript refresh of current URL

**Frontend Selection (object_list.html)**:
- Selected record IDs stored in `sessionStorage` using storage key
- Bulk edit button appears only when `>=1` records selected
- Selection state persists across pagination and page reloads

**Form Setup (bulk_edit_form.html)**:
- Selected IDs become hidden form fields (NOT filter parameters):
```html
<!-- Hidden field for selected IDs -->
{% for id in selected_ids %}
<input type="hidden" name="selected_ids[]" value="{{ id }}">
{% endfor %}
```

**Backend Processing (bulk_edit_process_post)**:
- Processes bulk updates atomically
- On successful POST, sets HTMX triggers:
```python
response["HX-Trigger"] = json.dumps({"bulkEditSuccess": True, "refreshTable": True})
```

**Frontend Response (object_list.html JavaScript)**:

1. **Trigger detection**: JavaScript listens for HTMX response headers:
```javascript
document.body.addEventListener('htmx:afterOnLoad', function (event) {
    const triggerHeader = xhr.getResponseHeader('HX-Trigger');
    const triggers = JSON.parse(triggerHeader);
    
    // Handle form success - close modal and refresh list
    if (triggers.formSuccess || triggers.bulkEditSuccess) {
        // Close the modal if it exists
        const modalElement = document.getElementById('powercrudBaseModal');
        if (modalElement) modalElement.close();

        // Check if we should refresh the table
        if (triggers.refreshTable) {
            // Use HTMX to swap in the new content with a smooth transition
            htmx.ajax('GET', window.location.pathname + window.location.search, {
                target: '#filtered_results',
                swap: 'innerHTML transition:opacity:350ms',
                headers: { 'X-Filter-Sort-Request': 'true' }
            });
        }
    }
});
```

2. **Parameter preservation**: Make fresh GET request to current URL:

```javascript
htmx.ajax('GET', window.location.pathname + window.location.search, {
    target: '#filtered_results',
    headers: { 'X-Filter-Sort-Request': 'true' }
});
```

Where:

- `window.location.pathname` = The path part of current URL (without domain)
- `window.location.search` = The query string part (the ? and everything after)
- Combined = The exact same URL the user is currently viewing

3. **Selection cleanup**: Clear sessionStorage after successful bulk edit:

```javascript
// Clear selection on bulkEditSuccess
if (triggers.bulkEditSuccess) {
    sessionStorage.removeItem(storageKey);
}
```

**Key insight**: Simpler than single edit - preserves parameters by refreshing the current URL (`window.location.pathname + window.location.search`) which already contains all filter/sort/pagination state.

### Filter Form Selection

**Method**: Individual field HTMX triggers → Include all form fields → GET request with updated parameters → Dynamic results update

**Form Setup (object_list.html)**:
- Filter form has HTMX attributes on the form level:

```html
<form id="filter-form" method="get" 
      hx-target="#filtered_results" 
      hx-push-url="true" hx-replace-url="true"
      hx-headers='{"X-Filter-Sort-Request": "true"}'>
```

- Each individual filter field gets HTMX attributes via `HTMXFilterSetMixin.setup_htmx_attrs()`:

```python
HTMX_ATTRS = {
    'hx-get': '',  # Send to form's action URL
    'hx-include': '[name]',  # Include all named form fields
}
```

- Hidden fields preserve non-filter parameters:

```html
{% for key, value in request.GET.items %}
    {% if key != 'page_size' and key != 'page' %}
        {% if filterset and key not in filterset.form.fields %}
            <input type="hidden" name="{{ key }}" value="{{ value }}">
        {% endif %}
    {% endif %}
{% endfor %}
```

**How `hx-include="[name]"` works**:
This HTMX attribute tells the browser to include ALL form elements that have a `name` attribute in the request. So when a user changes the "author" filter field, HTMX includes:

- The new "author" value they just selected
- All other current filter field values (title, date, etc.)
- All hidden fields (sort parameters, page_size, etc.)

**How the GET request works**:
When a filter field changes:

1. **HTMX trigger** fires (e.g., user selects new author)
2. **Field collection**: `hx-include="[name]"` gathers ALL current form values
3. **Request construction**: HTMX sends GET request to form's action URL with ALL collected values as query parameters
4. **URL example**: `/books/?author=smith&title=python&sort=name&page_size=25` (includes new filter + existing params)
5. **Response**: Server returns filtered results, `hx-push-url="true"` updates browser URL

**Key insight**: The "current URL" gets dynamically constructed from all current form field values, so it automatically includes the newly changed filter along with all preserved parameters. HTMX essentially rebuilds the query string from the live form state.

### Page Number Selection

At this point page number selection does not preserve parameters. This is a shortfall in the UX for the package.

### Sort Selection

**Method**: Template-constructed URLs → Explicit parameter inclusion → HTMX request with preserved state

**Backend Parameter Preparation (powercrud.py template tag)**:

```python
# Get all current filter parameters
filter_params = request.GET.copy() if request else {}
if 'sort' in filter_params:
    filter_params.pop('sort')
if 'page' in filter_params:
    filter_params.pop('page')

# Only keep the last value for each key to avoid duplicate params in URLs
clean_params = {}
for k in filter_params:
    clean_params[k] = filter_params.getlist(k)[-1]
filter_params = filter_params.__class__('', mutable=True)
for k, v in clean_params.items():
    filter_params[k] = v
```

**Frontend Template Logic (list.html)**:
- Each sortable column header includes explicit URL construction:

```html
{% if is_sortable %}
    {% if use_htmx %}
    hx-get="?sort={% if current_sort == field_name %}-{% elif current_sort == '-'|add:field_name %}{% else %}{% endif %}{{ field_name }}{% if request.GET.page_size %}&page_size={{ request.GET.page_size }}{% endif %}{% if filter_params %}&{{ filter_params }}{% endif %}"
    hx-headers='{"X-Filter-Sort-Request": "true"}'
    hx-target="#filtered_results"
    hx-push-url="true"
    hx-trigger="click"
    {% else %}
    onclick="window.location.href='?sort={% if current_sort == field_name %}-{% elif current_sort == '-'|add:field_name %}{% else %}{% endif %}{{ field_name }}{% if request.GET.page_size %}&page_size={{ request.GET.page_size }}{% endif %}{% if filter_params %}&{{ filter_params }}{% endif %}'"
    {% endif %}
{% endif %}
```

**When user clicks column header**:

1. **Sort logic**: Template toggles between ascending (`title`), descending (`-title`), and unsorted
2. **URL construction**: Template builds URL including:
   - New sort parameter
   - Current `page_size` (if set) 
   - All existing `filter_params` (cleaned current filters)
3. **HTMX request**: Sent to constructed URL like `?sort=title&page_size=25&author=smith&category=fiction`
4. **Headers**: `X-Filter-Sort-Request: true` for server template selection
5. **Target**: `#filtered_results` for partial update
6. **Browser URL**: Updated via `hx-push-url="true"`

**Key insight**: Unlike filter forms that use `hx-include` to gather live form state, sorting uses **pre-built URLs** that explicitly include all parameters to preserve. The template does the heavy lifting of parameter preservation by constructing comprehensive URLs.

## Current Approach Assessment

**Complexity Spectrum** (simple → complex):
1. **Bulk Edit**: Simple JavaScript URL refresh 
2. **Filter Form**: Clean HTMX `hx-include` mechanism
3. **Sort Selection**: Template URL construction
4. **Single Record Edit**: Complex POST extraction + request patching + role switching

**Problems with Current Approach**:

1. **Inconsistency**: Four completely different mechanisms for the same goal
2. **Maintainability**: Different bugs, edge cases, and failure modes for each approach  
3. **Complexity Mismatch**: Single record edit is massively over-engineered compared to bulk edit
4. **HTMX Dependency**: Some work with/without HTMX, others don't
5. **Code Duplication**: Single edit recreates list view logic instead of reusing it

## Recommended Approach: Targeted Improvements

Upon deeper analysis, **standardization for its own sake would actually make things worse**. Different interaction patterns legitimately require different preservation strategies, and some current approaches are actually using the right tools for their jobs.

### What's Actually Working Well

**Filter Form (`hx-include`)**: **Perfect as-is**. When dealing with forms containing multiple fields, `hx-include="[name]"` is exactly the right tool - it automatically gathers all current form state including the field that just changed. This is clean, appropriate, and leverages HTMX's strengths.

**Sort Selection (template URL construction)**: **Quite good as-is**. For single-parameter changes like sorting, explicit URL construction is clear and works with both HTMX and non-HTMX. While verbose, it's explicit and predictable.

**Bulk Edit (JavaScript refresh)**: **Elegant and simple**. This approach essentially says "I just made changes, go get the current URL again" which leverages the fact that the current URL already contains all state.

### The Real Problems

Only **two** things actually need fixing:

1. **Page Number Selection**: Currently broken (no parameter preservation)
2. **Single Record Edit**: Massively over-engineered compared to simpler alternatives

## Design Options Analysis and Recommendations

### Available Design Options

From analysis of potential approaches, there are four main strategies for parameter preservation:

#### 1. URL + hx-vals

**Mechanism**: JavaScript reads current URL parameters, sends via hx-vals

- ✅ Simple conceptual model (URL is source of truth)
- ✅ No storage management needed  
- ✅ Stateless
- ✅ One place to read state (URL)
- ❌ JavaScript must parse URL parameters for every request

#### 2. SessionStorage + hx-vals

**Mechanism**: JavaScript reads sessionStorage, sends via hx-vals

- ✅ Per-tab isolation built-in
- ✅ Can store complex objects
- ✅ No URL parameter parsing needed
- ❌ Client-side storage management required
- ❌ Must sync sessionStorage with URL state

#### 3. Django Sessions

**Mechanism**: Server stores state, pagination sends minimal data

- ✅ Simplest front-end (no JavaScript state management)
- ✅ Server has immediate access to state
- ❌ Server-side storage required
- ❌ Multiple tabs share same session
- ❌ Memory usage on server
- ❌ Too heavy for this specific problem

#### 4. Forms with Hidden Fields

**Mechanism**: Hidden form fields preserve state, HTMX includes automatically

- ✅ No JavaScript state management needed
- ✅ HTMX handles inclusion automatically
- ❌ More HTML per page
- ❌ Template must generate hidden fields for pagination
- ❌ Verbose with large page ranges

#### 5. Current Bulk Edit Pattern (JavaScript URL Refresh)

**Mechanism**: Server triggers JavaScript to refresh current URL

- ✅ Extremely simple (just refresh current URL)
- ✅ Perfect separation of concerns
- ✅ Works regardless of how user reached current state
- ❌ Requires two-step process (trigger → refresh)
- ❌ Not suitable for direct navigation (like pagination links)

### Design Option Evaluation for Targeted Fixes

#### For Pagination Links

**Rejected Options**:

- **Current Bulk Edit Pattern**: Would create weird two-step flow:
  - Click page 2 → GET request → Server response with trigger → JavaScript makes ANOTHER GET for page 2
  - This is wasteful (two round trips) and confusing
- **Forms with Hidden Fields**: Would make pagination template extremely verbose with hidden fields for every page link
- **SessionStorage + hx-vals**: Adds unnecessary storage management complexity for simple parameter passing
- **Django Sessions**: Complete overkill for client-side state that's already in the URL

**Selected: URL + hx-vals**

Clean, direct, single round-trip approach:

Current broken pagination:

```html
<a class="join-item btn btn-sm" 
   href="?page={{ i }}{% if request.GET.page_size %}&page_size={{ request.GET.page_size }}{% endif %}{% if filter_params %}&{{ filter_params }}{% endif %}" 
   {% if use_htmx and original_target %} 
   hx-get="?page={{ i }}{% if request.GET.page_size %}&page_size={{ request.GET.page_size }}{% endif %}{% if filter_params %}&{{ filter_params }}{% endif %}"
   hx-target="{{original_target}}" 
   {% endif %}>{{ i }}
</a>
```

Proposed fix using hx-vals:

```html
<a class="join-item btn btn-sm" 
   hx-get="?page={{ i }}" 
   hx-vals="js:getCurrentFilters()"
   hx-target="#filtered_results"
   hx-push-url="true">{{ i }}
</a>
```

Supporting JavaScript function:

```javascript
function getCurrentFilters() {
    const params = new URLSearchParams(window.location.search);
    const clean = {};
    for (const [key, value] of params) {
        if (value && key !== 'page') clean[key] = value;
    }
    return clean;
}
```

**Why this is superior**:

- **Single round trip**: Click → GET with all params → Response
- **Clean template**: No verbose URL construction in template
- **Maintainable**: JavaScript function can be enhanced/debugged independently
- **URL as source of truth**: Always reads current browser state

#### For Single Record Edit

**Rejected Options**:

- **URL + hx-vals**: Form submission already handles parameter passing; this doesn't solve the core complexity
- **SessionStorage + hx-vals**: Adds storage management without addressing the real issue
- **Django Sessions**: Overkill for parameter preservation
- **Forms with Hidden Fields**: Already used, but server-side processing is overcomplicated

**Selected: Keep Current Bulk Edit Pattern (JavaScript URL Refresh)**

The current approach for single record edit has the right client-side pattern (JavaScript refresh after success) but overcomplicated server-side processing. The fix is to simplify the server response while keeping the client-side trigger pattern.

Current complex server-side approach:

```python
def form_valid(self, form):
    self.object = form.save()
    
    if hasattr(self, 'request') and getattr(self.request, 'htmx', False):            
        # Complex parameter extraction from POST
        filter_params = QueryDict('', mutable=True)
        filter_prefix = '_PowerCRUD_filter_'
        for k, v in self.request.POST.lists():
            if k.startswith(filter_prefix):
                real_key = k[len(filter_prefix):]
                for value in v:
                    filter_params.appendlist(real_key, value)
        
        # Build canonical URL
        # Patch self.request.GET
        # Change role to LIST
        # Call list() method
        # Set complex headers
        
    return HttpResponseRedirect(self.get_success_url())
```

Proposed simplified server-side approach:

```python
def form_valid(self, form):
    self.object = form.save()
    
    if hasattr(self, 'request') and getattr(self.request, 'htmx', False):
        response = HttpResponse("")
        response["HX-Trigger"] = json.dumps({"formSuccess": True, "refreshTable": True})
        return response
        
    return HttpResponseRedirect(self.get_success_url())

The existing JavaScript handler already responds correctly to formSuccess triggers:

// Handle form success - close modal and refresh list
if (triggers.formSuccess || triggers.bulkEditSuccess) {
    // Close the modal if it exists
    const modalElement = document.getElementById('powercrudBaseModal');
    if (modalElement) modalElement.close();

    // Check if we should refresh the table
    if (triggers.refreshTable) {
        // Use HTMX to swap in the new content with a smooth transition
        htmx.ajax('GET', window.location.pathname + window.location.search, {
            target: '#filtered_results',
            swap: 'innerHTML transition:opacity:350ms',
            headers: { 'X-Filter-Sort-Request': 'true' }
        });
    }
}
```

**Why this is superior**:

- **Massive simplification**: Server doesn't need to understand current UI state
- **Consistent with bulk edit**: Same pattern for all post-operation refreshes  
- **Separation of concerns**: Server handles business logic, client handles UI state
- **Maintainable**: Much simpler to debug and enhance

### Final Implementation Strategy

**Mixed Approach Using Right Tool for Each Job**:

1. **Pagination**: Fix with `hx-vals="js:getCurrentFilters()"` approach
2. **Single Record Edit**: Simplify server-side to use bulk edit trigger pattern  
3. **Filter Form**: Keep current `hx-include` approach (works perfectly)
4. **Sort Selection**: Keep current template URL construction (appropriate for single-parameter changes)

This gives us the benefits of each approach where they're most appropriate, rather than forcing everything into one pattern. The result is:

- **Fixed pagination** (currently broken)
- **Simplified single record edit** (remove complex server-side processing)
- **Maintained strengths** of filter form and sort selection approaches
- **Consistent post-operation refresh pattern** between bulk edit and single edit

## How Pagination Was Actually Fixed

### The Original Problem

Pagination links were not preserving filter, sort, and page_size parameters. When users clicked on page numbers after applying filters, the filtering would reset, leading to a poor user experience where applied filters would be lost during navigation.

### The Real Issue Discovered

During debugging, we uncovered that the core problem was not pagination link parameter preservation, but **duplicate parameter submission** in HTMX filter requests. The backend was receiving duplicate parameters like `'genres': ['4', '5']` instead of single values like `'genres': ['5']` when users changed filter selections.

### Debugging Process

1. **Backend Logging**: Added debug logging to the list() method showing received filter parameters and result counts
2. **HTMX Request Inspection**: Used browser developer tools to examine HTMX request data
3. **FormData Analysis**: Added JavaScript event listener for `htmx:beforeRequest` to capture form data at request time
4. **Key Discovery**: FormData showed correct single values (e.g., `genres → "5"`), but backend received duplicate arrays

### Root Cause Analysis

The issue was traced to the interaction between:

- **HTMXFilterSetMixin**: Dynamically adds HTMX attributes to filter fields for generic package functionality
- **Field-level HTMX triggers**: Each filter field gets `hx-get=""` and `hx-include: '[name]'` attributes
- **Request timing**: HTMX was somehow including both old and new parameter values in requests

The duplicate parameters caused a "lag" effect where:

- Filter changes resulting in fewer records showed previous results (using first parameter value)
- Filter changes resulting in more records worked correctly (using last parameter value)

### Architectural Context

This is a **generic package** issue where the HTMXFilterSetMixin serves a critical purpose:

- Downstream developers specify arbitrary `filterset_fields` lists
- Package must dynamically configure HTMX attributes for unknown field combinations
- Different field types require different HTMX triggers (text inputs vs selects vs dates)
- The `hx-include: '[name]'` attribute ensures all current filter values are included when any field changes

### Resolution

After extensive debugging, the issue was resolved by implementing a **JavaScript-based solution** that:

- Uses explicit event handling instead of automatic HTMX attribute injection
- Provides reliable form data serialization without duplicate parameters
- Maintains the same user experience with better reliability
- Preserves the generic package architecture while solving the timing/duplication issues

The JavaScript solution uses `htmx.ajax()` with `source: form` to properly serialize the current form state without the timing issues that caused parameter duplication in the native HTMX attribute approach.

### Technical Note

The root cause of why HTMX was creating duplicate parameters was never definitively determined, despite the FormData showing correct single values at request time. This suggests the duplication occurred during HTMX's internal request processing, possibly related to timing of form state capture or conflicts between multiple HTMX attribute configurations on the same form elements.

### Future Considerations

While the JavaScript solution resolves the immediate issue, the underlying HTMX parameter duplication behavior may warrant further investigation for potential simplification of the HTMXFilterSetMixin approach in future versions.
