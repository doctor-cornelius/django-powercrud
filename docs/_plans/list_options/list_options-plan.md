# List Options Plan

## Status

Public column-model decisions confirmed.

## Next

1. Decide stale-state, empty-state, and persistence behaviour before implementation.

## Phase 1: Lock the Public Column Model

1. [x] Confirm the public config names and whether `fields`/`properties` define the allow-list.
    1. [x] Choose the default visible-column config name.
    2. [x] Decide whether a separate optional-column config is needed.
    3. [x] Confirm which system columns are outside user-toggleable data columns.
2. [ ] Define default, active, invalid, and stale visible-column behaviour.
    1. [x] Define behaviour when no user preference exists.
    2. [ ] Define behaviour when saved or submitted columns are no longer allowed.
    3. [ ] Confirm the fallback when the active visible set is empty or invalid.
3. [ ] Decide the minimal hook surface needed beyond declarative config.
    1. [x] Keep the declarative API narrow.
    2. [ ] Add hooks only where downstream apps need broader resolution control.
    3. [x] Keep current views unchanged unless they opt in.

## Phase 2: Make List Rendering Column-Aware

1. [ ] Resolve allowed, default, and active visible columns in one place.
    1. [ ] Preserve current field and property ordering.
    2. [ ] Include configured model fields and configured properties.
    3. [ ] Validate active columns against the resolved allow-list.
2. [ ] Filter headers and row cells through the visible-column set.
    1. [ ] Preserve sortable header metadata for visible sortable fields.
    2. [ ] Preserve field and property display formatting.
    3. [ ] Preserve alignment, help text, links, and tooltips for visible cells.
3. [ ] Preserve existing table behaviour for views that do not opt in.
    1. [ ] Keep row selection independent of visible data columns.
    2. [ ] Keep row actions independent of visible data columns.
    3. [ ] Keep bulk action containers and counters independent of visible data columns.

## Phase 3: Add the Column Chooser and Preference Flow

1. [ ] Add the "Change columns" UI with allow-listed checkbox options.
    1. [ ] Show one option per allow-listed data column.
    2. [ ] Avoid presenting selection and row actions as normal data columns.
    3. [ ] Include a clear reset-to-default affordance.
2. [ ] Apply and reset column choices through a server-validated flow.
    1. [ ] Validate submitted column names against the resolved allow-list.
    2. [ ] Re-render the list through the existing list refresh path.
    3. [ ] Clear persisted state when resetting to defaults.
3. [ ] Keep current filter, sort, page size, and selection state during refreshes.
    1. [ ] Preserve existing query parameters where appropriate.
    2. [ ] Preserve selected IDs and bulk state.
    3. [ ] Keep JavaScript limited to chooser interaction and submission.

## Phase 4: Add Persistence and Stale-State Handling

1. [ ] Decide the first persistence source for authenticated and anonymous users.
    1. [ ] Decide whether preferences live in core or a contrib app.
    2. [ ] Decide whether anonymous users use session state or default-only behaviour.
    3. [ ] Decide whether URL-visible column state is supported in the first release.
2. [ ] Store per-user, per-view visible-column preferences if DB persistence is selected.
    1. [ ] Key preferences by user and stable view key.
    2. [ ] Store visible columns in structured JSON.
    3. [ ] Track update timestamps for inspectability.
3. [ ] Drop stale columns safely and fall back to defaults when needed.
    1. [ ] Drop column names no longer allowed by the view.
    2. [ ] Fall back to defaults when a preference becomes empty or invalid.
    3. [ ] Keep saved filter favourites separate unless deliberately expanded.

## Phase 5: Protect Filters, Sorting, Pagination, and URL State

1. [ ] Keep filters and optional filters independent from visible columns.
    1. [ ] Preserve active filters when matching columns are hidden.
    2. [ ] Preserve optional filter controls when matching columns are hidden.
    3. [ ] Validate filter state and column state against separate allow-lists.
2. [ ] Define sorting behaviour when the sorted column is hidden.
    1. [ ] Decide whether hiding the sorted column clears or preserves sort.
    2. [ ] Define behaviour for hidden sort parameters received through the URL.
    3. [ ] Render sort indicators only for visible sortable columns.
3. [ ] Preserve pagination, page size, query parameters, and HTMX targets.
    1. [ ] Decide whether applying column changes keeps the current page or resets to page 1.
    2. [ ] Preserve page size across column changes.
    3. [ ] Refresh the intended list area without disturbing unrelated controls.

## Phase 6: Protect Inline Editing, Links, Tooltips, Row Actions, and Bulk Selection

1. [ ] Ensure hidden columns do not expose inline edit triggers.
    1. [ ] Keep `inline_edit_fields` as an editability config, not a visibility config.
    2. [ ] Preserve hidden-field handling needed by inline saves.
    3. [ ] Keep hidden columns out of row display and inline trigger rendering.
2. [ ] Preserve linked-cell, tooltip, row action, update, and delete behaviour for visible cells and rows.
    1. [ ] Apply `link_fields` and `get_list_cell_link(...)` only to visible eligible cells.
    2. [ ] Apply `get_list_cell_tooltip(...)` only to visible eligible cells.
    3. [ ] Keep row-level update and delete policy independent of visible columns.
3. [ ] Keep selected IDs, select-all state, and bulk action visibility stable through column changes.
    1. [ ] Preserve persisted selected IDs through column refreshes.
    2. [ ] Preserve select-all state calculations.
    3. [ ] Preserve bulk action visibility and counters.

## Phase 7: Add Sample App Coverage, Tests, and Documentation

1. [ ] Demonstrate configurable columns in the sample app with fields and properties.
    1. [ ] Include default-visible and optional columns.
    2. [ ] Include at least one selectable property column.
    3. [ ] Exercise a realistic interaction with filters, sorting, inline editing, links, or bulk selection.
2. [ ] Add focused tests for resolution, rendering, state preservation, stale preferences, and HTMX flows.
    1. [ ] Test config validation and visible-column resolution.
    2. [ ] Test headers, cells, filters, sorting, and stale preferences.
    3. [ ] Test inline editing, linked cells, bulk state, and chooser apply/reset flows.
3. [ ] Update public docs, reference docs, and deferred follow-up notes.
    1. [ ] Add copyable guide snippets for the final API.
    2. [ ] Update config and hooks references where needed.
    3. [ ] Record deferred decisions for favourites, export/download, and user-controlled ordering.
