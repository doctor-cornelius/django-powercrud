# List Options Plan

## Status

Column model, rendering, chooser flow, session-backed current state, surrounding-list behavior, sample coverage, docs, Playwright coverage, the first RC UI polish pass, and top action overflow are implemented. The unreleased core `PowerCRUDListPreference` DB table/migration path was removed so opting into `default_list_fields` does not require a new core PowerCRUD migration.

## Next

1. Validate the session-backed persistence slice in the browser and focused automated tests.
    1. [x] Prefer no mandatory core PowerCRUD DB migration for unnamed column preferences.
    2. [x] Use session-backed current state outside saved favourites.
    3. [x] Remove the unreleased core `PowerCRUDListPreference` model/migration path.
2. Later slices: export/download and deeper saved-view refinements.

## Phase 1: Lock the Public Column Model

1. [x] Confirm the public config names and whether `fields`/`properties` define the allow-list.
    1. [x] Choose the default visible-column config name.
    2. [x] Decide whether a separate optional-column config is needed.
    3. [x] Confirm which system columns are outside user-toggleable data columns.
2. [x] Define default, active, invalid, and stale visible-column behaviour.
    1. [x] Define behaviour when no session state exists.
    2. [x] Drop session or submitted columns that are no longer allowed.
    3. [x] Fall back to `default_list_fields` when the active visible set is empty or invalid.
    4. [x] Treat explicitly empty `default_list_fields` and user-selected zero-column state as invalid for v1.
3. [x] Decide the minimal hook surface needed beyond declarative config.
    1. [x] Keep the declarative API narrow.
    2. [x] Add no new hook surface for v1 unless implementation evidence shows a concrete downstream need.
    3. [x] Keep current views unchanged unless they opt in.

## Phase 2: Make List Rendering Column-Aware

1. [x] Resolve allowed, default, and active visible columns in one place.
    1. [x] Preserve current field and property ordering.
    2. [x] Include configured list fields, including model fields and queryset annotation fields.
    3. [x] Include configured properties after resolved `fields`, preserving current ordering.
    4. [x] Defer validation for request-time queryset annotation fields until the effective queryset is available.
    5. [x] Validate active columns against the resolved allow-list.
2. [x] Filter headers and row cells through the visible-column set.
    1. [x] Preserve sortable header metadata for visible sortable model and annotation fields.
    2. [x] Preserve field, annotation, and property display formatting.
    3. [x] Preserve alignment, help text, links, and tooltips for visible cells.
3. [x] Preserve existing table behaviour for views that do not opt in.
    1. [x] Keep row selection independent of visible data columns.
    2. [x] Keep row actions independent of visible data columns.
    3. [x] Keep bulk action containers and counters independent of visible data columns.

## Phase 3: Add the Column Chooser and Preference Flow

1. [x] Add the column chooser UI with allow-listed checkbox options.
    1. [x] Show one option per allow-listed data column.
    2. [x] Include model field, queryset annotation, and property columns.
    3. [x] Avoid presenting selection and row actions as normal data columns.
    4. [x] Include a clear reset-to-default affordance.
2. [x] Apply and reset column choices through a server-validated flow.
    1. [x] Validate submitted column names against the resolved allow-list.
    2. [x] Re-render the list through the existing list refresh path.
    3. [x] Clear persisted state when resetting to defaults.
    4. [x] Reject attempts to apply an empty visible data-column set.
3. [x] Keep current filter, page size, and selection state during refreshes.
    1. [x] Preserve existing query parameters where appropriate.
    2. [x] Clear sort and reset to page 1 if the user hides the currently sorted column.
    3. [x] Preserve selected IDs and bulk state.
    4. [x] Keep JavaScript limited to chooser interaction and submission.

## Phase 4: Add Persistence and Stale-State Handling

1. [x] Finalise the RC persistence source for unnamed current column choices.
    1. [x] Avoid a mandatory core PowerCRUD DB migration solely for unnamed column preferences unless explicitly re-approved.
    2. [x] Persist current column choices in the session outside saved favourites.
    3. [x] Keep localStorage out of the v1 persistence model.
2. [x] Store per-session, per-view visible-column state.
    1. [x] Key session state by stable view key.
    2. [x] Store visible columns in structured session data.
    3. [x] Clear session state when resetting to defaults.
3. [x] Drop stale columns safely and fall back to defaults when needed in the current implementation.
    1. [x] Drop column names no longer allowed by the view.
    2. [x] Fall back to defaults when session state becomes empty or invalid.
    3. [x] Keep empty user-selected zero-data-column state invalid.
4. [x] Move durable saved column persistence into saved favourites.
    1. [x] Extend the optional favourites state contract to include visible columns.
    2. [x] Preserve compatibility for existing saved favourites without column state by resetting columns to defaults on apply.
    3. [x] Keep durable DB-backed saved state behind explicit favourites app election.
5. [x] Remove the unreleased core `PowerCRUDListPreference` model/migration because the release direction excludes core DB persistence.

## Phase 5: Protect Filters, Sorting, Pagination, and URL State

1. [x] Keep filters and optional filters independent from visible columns.
    1. [x] Preserve active filters when matching columns are hidden.
    2. [x] Preserve optional filter controls when matching columns are hidden.
    3. [x] Validate filter state and column state against separate allow-lists.
2. [ ] Define sorting behaviour when the sorted column is hidden.
    1. [x] Clear sort when the user hides the currently sorted column.
    2. [ ] Ignore hidden sort parameters received through the URL.
    3. [x] Render sort indicators only for visible sortable columns.
3. [x] Preserve pagination, page size, query parameters, and HTMX targets.
    1. [x] Reset to page 1 when applying column changes.
    2. [x] Preserve page size across column changes.
    3. [x] Refresh the intended list area without disturbing unrelated controls.

## Phase 6: Protect Inline Editing, Links, Tooltips, Row Actions, and Bulk Selection

1. [x] Ensure hidden columns do not expose inline edit triggers.
    1. [x] Keep `inline_edit_fields` as an editability config, not a visibility config.
    2. [x] Keep queryset annotation fields read-only and ineligible for inline edit.
    3. [x] Preserve hidden-field handling needed by inline saves.
    4. [x] Keep hidden columns out of row display and inline trigger rendering.
2. [x] Preserve linked-cell, tooltip, row action, update, and delete behaviour for visible cells and rows.
    1. [x] Apply `link_fields` and `get_list_cell_link(...)` only to visible eligible cells.
    2. [x] Apply `get_list_cell_tooltip(...)` only to visible eligible cells.
    3. [x] Keep row-level update and delete policy independent of visible columns.
3. [x] Keep selected IDs, select-all state, and bulk action visibility stable through column changes.
    1. [x] Preserve persisted selected IDs through column refreshes.
    2. [x] Preserve select-all state calculations.
    3. [x] Preserve bulk action visibility and counters.

## Phase 7: Add Sample App Coverage, Tests, and Documentation

1. [ ] Demonstrate configurable columns in the sample app with fields, queryset annotations, and properties.
    1. [x] Include default-visible and optional columns.
    2. [x] Include at least one selectable queryset annotation column in a live chooser sample.
    3. [x] Include at least one selectable property column.
    4. [x] Exercise a realistic interaction with filters, sorting, inline editing, links, or bulk selection.
2. [x] Add focused tests for resolution, rendering, state preservation, stale state, and HTMX flows.
    1. [x] Test config validation and visible-column resolution for model fields, queryset annotations, and properties.
    2. [x] Test headers, cells, filters, sorting, and stale state.
    3. [x] Test inline editing, linked cells, bulk state, and chooser apply/reset flows.
3. [x] Update public docs, reference docs, and deferred follow-up notes.
    1. [x] Add copyable guide snippets for the final API.
    2. [x] Update config and hooks references where needed.
    3. [x] Record deferred decisions for favourites, URL sharing, export/download, user-controlled ordering, and zero-data-column tables.
4. [x] Polish the RC list controls UI.
    1. [x] Show an active count on the column trigger, for example `Cols 8/12`.
    2. [x] Prevent unchecking the final visible data column in the frontend while retaining server validation.
    3. [x] Improve narrow-screen dropdown positioning and sizing.
    4. [x] Improve keyboard and focus handling for the column chooser.
    5. [x] Cluster view controls together, including filters, columns, and page size.
    6. [x] Do not add chooser search for the RC.
    7. [x] Defer dirty-state Save-button behaviour unless testing shows the current form interaction is confusing.
5. [x] Polish filter and saved-favourites control placement.
    1. [x] Move the filter entry point into the same top-level view-controls cluster as `Cols` and page size.
    2. [x] Move filter reset into the expanded filter panel so it clearly affects filters only.
    3. [x] Keep the `Cols` reset inside the `Cols` dropdown.
    4. [x] Move saved favourites to the same top-level view-controls row as the filter trigger, `Cols`, and page size.
    5. [x] Keep active filters visible and never clear filter values merely because a filter control is hidden.
    6. [x] Preserve favourites/optional-filter behavior while changing the control shell.
6. [x] Tighten narrow-table toolbar and filter-panel behaviour.
    1. [x] Move `Add filter` into the expanded filter panel so it does not widen the top view-controls row.
    2. [x] Constrain the expanded filter panel to the narrower of the table edge or viewport edge.
    3. [x] Align wrapped view controls left instead of leaving them right-aligned on a second row.
    4. [x] Keep saved favourites icon-only, with outline heart when unselected and filled primary heart plus tooltip when selected.
    5. [x] Preserve selected saved-favourite icon state across full page refresh when the current list state still matches the saved favourite.
    6. [x] Add top-level `extra_buttons` overflow through separate `extra_buttons_mode = "buttons" | "dropdown"` config, keeping `extra_actions_mode` row-only.

## Phase 8: Future Extensions After V1

1. [x] Extend saved favourites into saved list states.
    1. [x] Store visible columns in saved-favourite state.
    2. [x] Include filters, visible optional filters, sort, page size, and visible columns in the saved-state contract.
    3. [x] Preserve compatibility for existing saved favourites.
    4. [x] Applying a saved favourite replaces current columns; legacy favourites without column state reset columns to defaults.
2. [ ] Add download/export behaviour as a subsequent feature.
    1. [ ] Decide whether exports follow visible columns or use a separate export schema.
    2. [ ] Decide whether saved views can include export presets later.
    3. [ ] Keep export decisions independent from the v1 show/hide table feature until deliberately implemented.
3. [ ] Deprioritise URL-shareable visible-column state.
    1. [ ] Keep `visible_columns` query parameters out of the RC unless a concrete sharing use case appears.
    2. [ ] If added later, validate URL column state against the same resolved allow-list.
    3. [ ] Define precedence against session state and saved-view state before implementation.
4. [ ] Deprioritise user-controlled column ordering.
    1. [ ] Keep default declared order as the v1 baseline.
    2. [ ] Revisit ordering only as part of richer saved views if downstream use proves it valuable.
5. [ ] Keep zero-data-column tables invalid.
    1. [ ] Maintain the minimum-one-visible-data-column rule.
    2. [ ] Do not pursue zero-column CRUD tables without a concrete product requirement.
