# List Options Notes

## Problem Summary

Some operational list screens need more columns than should be shown by default. A different system shown by the user lets users choose which list columns are visible through a compact "Cols" control.

The proposed PowerCRUD version is a default-vs-optional column model, similar to the existing default-vs-optional filter model.

An example from a completely different system is Uptick, as shown below:
![](images/list_options-notes/uptick_add_cols.png){width=50%}

## Initial Feasibility Assessment

This looks feasible in PowerCRUD's current architecture.

PowerCRUD already resolves list display from configured `fields` and `properties`, builds generic header and cell payloads, and renders those payloads through the shared list template. That means column visibility can probably be handled by filtering the resolved headers and row cells before rendering, instead of creating a second table system.

Since the queryset annotation fields work landed, `fields` is no longer model-field-only. Explicit `fields` entries may resolve to model fields or supported queryset annotation names. `properties` remains the separate display-only property list appended after `fields`.

That means list options should treat the allow-list as:

1. Resolved `fields`, including model field names and queryset annotation names.
2. Resolved `properties`.

The resolver must preserve the existing ordering: all resolved `fields` in their declared order first, then resolved `properties` in their declared order.

The closest existing pattern is optional filter visibility:

1. Treat the declared filter set as the full allow-list.
2. Treat `default_filterset_fields` as the initially visible subset.
3. Preserve explicitly visible optional filters through request state.
4. Validate submitted visibility choices against the effective allow-list.

List-column visibility can follow the same conceptual model.

## Public API Decision

Use the existing `fields` and `properties` configuration as the public allow-list for user-selectable list data columns. This keeps backwards compatibility and matches PowerCRUD's current public docs, where `fields` already means ordered list-view columns and may include queryset annotation fields.

Use `list_options_enabled = True` to enable the **Cols** control without narrowing the default visible set:

```python
fields = ["ref", "category", "status", "task", "created", "client", "property", "sla"]
properties = ["sla_state"]
list_options_enabled = True
```

Use `default_list_fields` when the default/reset state should be a visible subset:

```python
fields = ["ref", "category", "status", "task", "created", "client", "property", "sla"]
properties = ["sla_state"]
list_options_enabled = True
default_list_fields = ["ref", "status", "task", "created", "client"]
```

In that shape:

1. `fields` and `properties` define the full allowed rendered-column universe.
2. `fields` entries may be model fields or queryset annotation fields.
3. `list_options_enabled` enables user choice without requiring defaults to be restated.
4. `default_list_fields` defines what appears when the user has no saved preference. If omitted, every allowed column is default-visible.
5. Everything allowed but not default-visible is available through a column chooser.

This mirrors the existing filter pattern:

```python
filterset_fields = ["owner", "status", "created_date", "category"]
default_filterset_fields = ["owner", "status"]

fields = ["ref", "status", "created_date", "category", "owner", "notes"]
properties = ["sla_state"]
list_options_enabled = True
default_list_fields = ["ref", "status", "created_date", "sla_state"]
```

Do not introduce `optional_list_fields` in the first version. The optional set is derived from the resolved allow-list minus `default_list_fields`, which avoids a second allow-list and the precedence questions that would come with it.

Do not introduce `list_fields` in the first version. It would duplicate or compete with the existing public meaning of `fields`, which already means list columns. Keeping `fields` and `properties` as the allow-list is clearer and less disruptive.

The public contract should be:

1. `list_options_enabled = None` and `default_list_fields = None` preserves current behaviour and renders all resolved `fields` and `properties` without a chooser.
2. `list_options_enabled = True` opts the view into the chooser while using all allowed columns as the default/reset state.
3. `default_list_fields = [...]` narrows the default/reset visible subset and remains a backward-compatible shorthand for enabling list options.
4. Every `default_list_fields` entry must exist in the resolved `fields` and `properties` allow-list.
5. Duplicate names are deduped while preserving first occurrence, consistent with existing list-style config handling.
6. Empty `default_list_fields` should be invalid unless a later deliberate decision supports tables with no data columns.
7. Selection checkboxes, row actions, bulk controls, and other system cells are outside the user-toggleable data-column API.
8. Queryset annotation fields are eligible list columns but remain read-only list/filter/sort columns.

Internally, resolver and template context code can use column-oriented names such as `allowed_columns`, `default_columns`, and `active_columns`. Public configuration should keep the `fields` naming to align with the existing PowerCRUD API.

## Queryset Annotation Fields

Queryset annotation fields should be eligible configurable columns.

The queryset-fields work deliberately kept annotations behind the existing `fields` API rather than adding a `queryset_fields` setting. The list-options feature should follow that settled contract.

The visibility resolver must therefore handle both validation timings:

1. Static querysets can expose annotation names during view initialization.
2. Request-time `get_queryset()` annotations may require deferred validation until the effective queryset exists.

Annotation fields should remain field cells, not property cells. They appear in `fields` order, may be sortable and filterable when the effective queryset exposes the same public annotation name, and are not valid for editable surfaces such as `form_fields`, `inline_edit_fields`, or `bulk_fields`.

## Properties

Properties should be eligible configurable columns.

Validation should check visibility config against the effective rendered-column universe:

1. Resolved model fields and queryset annotation fields from `fields`.
2. Resolved properties from `properties`.

Properties remain display-only. Inline editing should stay model-field-only unless a separate future feature deliberately changes that contract.

## Persistence Direction

The initial v1 implementation used a core `PowerCRUDListPreference` table for authenticated users. That gave good UX, but it was removed before release because it made a core PowerCRUD migration mandatory for unnamed column preferences.

The closest existing pattern is filters:

1. Filter values live in URL/query state.
2. Optional filter visibility lives in the `visible_filters` query parameter.
3. Durable named filter state exists only when the optional favourites app is installed and activated.

List columns do not currently have a URL-state equivalent, and URL-shareable columns are not compelling enough for the RC. Unnamed column choices persist through session-backed state, including for anonymous users. Browser `localStorage` remains unattractive because server validation is better handled by server-side state.

The current release direction is:

1. Avoid requiring a core PowerCRUD DB migration just because a view opts into `default_list_fields`.
2. Use session-backed current column state for unnamed preferences that survive navigation within a browser session.
3. Put durable DB-backed saved column state behind the optional favourites app.
4. Extend favourites toward saved views containing filters, visible optional filters, sort, page size, and visible columns.
5. Do not add cache in front of DB persistence unless profiling later shows a real issue.

The favourites contrib app is currently DB-backed, not cache-backed. It stores a normal model with `JSONField` state per user, view key, and favourite name. That is an acceptable long-term source of truth for saved views. A DB-backed cache layer is not needed for the current scale; direct DB reads are simpler and more reliable.

The core `PowerCRUDListPreference` model/migration was removed before release. If automatic cross-session unnamed preferences are re-approved later, a core DB table remains technically straightforward, but it should be an explicit product/API decision rather than an accidental release requirement.

## URL State And Sharing

There are three possible layers:

1. Session-backed current state for unnamed column choices.
2. Favourites-backed saved-view state for durable named layouts.
3. Optional `visible_columns` query parameters for shareable or one-off list layouts.

URL-visible column state is low priority and deferred from the RC. If URL state is supported later, submitted column names must be validated against the same resolved allow-list before rendering, and precedence against session state and saved-view state must be defined first.

## JavaScript Direction

Avoid localStorage for this feature. Current column choices should be server-led: session-backed if unnamed state persists, and DB-backed through favourites/saved views when the user deliberately saves a named layout.

Some JavaScript is still useful for the column chooser UI, but it should stay small and server-led:

1. Open and close the column chooser.
2. Collect checked column names.
3. Submit a small form or HTMX request.
4. Support a reset-to-default action.
5. Prevent the user from unchecking the final visible data column while keeping server validation as the authoritative guard.
6. Improve keyboard/focus handling.

Do not copy the full optional-filter localStorage machinery in v1. Do not add chooser search for the RC.

The current `powercrud.js` is already becoming large. This feature should either be implemented as a small isolated module/section or be paired with a light JS organization pass before adding more state machinery.

## Frontend Polish Direction

The RC polish pass should make list-state controls feel like a coherent group without redesigning the whole list toolbar.

Agreed polish:

1. Show an active count on the column chooser trigger, for example `Cols 8/12`.
2. Disable or otherwise guard the last checked column so the user cannot create a zero-data-column table from the frontend.
3. Improve the dropdown on narrow screens so it does not clip or feel detached from the trigger.
4. Improve focus and keyboard handling.
5. Group view controls together: filters, columns, and page size should read as a related cluster.
6. Keep chooser search out of the RC.

The filter controls moved toward the same visual pattern as columns: an icon-only filter trigger sits near `Cols`, filter reset lives inside the expanded filter panel, and `Add filter` lives inside the filter panel rather than widening the top toolbar. The key product rule remains that hiding a filter control must not silently clear an active filter value. Active filters should remain visible; reset is the deliberate way to clear filter values, sort, and page size.

Dirty-state behaviour, where Save stays disabled until the chooser changes, is a possible later polish. It is not required for the RC unless user testing shows the current form interaction is confusing.

The RC polish pass is complete for the column chooser and toolbar cluster: the trigger shows an active/allowed count, the final visible column is guarded in the frontend, the chooser handles Escape/focus, the view-control cluster is constrained to the narrower of the table edge or viewport edge, wrapped view controls align left instead of hanging from the right edge, and the expanded filter panel follows the table/viewport width constraint.

Top action overflow is implemented as `extra_buttons_mode = "buttons" | "dropdown"`. This is deliberately separate from row-level `extra_actions_mode`. The default remains `"buttons"` for compatibility. `"dropdown"` moves configured top-level `extra_buttons` into a toolbar `More` menu while leaving built-in actions such as Create outside the overflow.

## Inline Editing Considerations

Inline editing needs explicit handling.

If a column is hidden, any inline-edit form for that row should not unexpectedly expose the hidden field. Current inline code derives visible form fields from row cells, which may help, but required hidden fields still need to be preserved safely.

Potential rule:

1. Hidden columns are not displayed or inline-editable in the row.
2. Required or preserved form fields needed for save correctness remain hidden inputs where the existing inline-preservation machinery requires them.
3. `inline_edit_fields` remains validated against editable model fields, not against currently visible columns.

## Sorting Considerations

Sorting by a hidden column needs a rule.

Candidate default:

1. If a user hides the currently sorted column through the column chooser, clear the sort.
2. If a hidden sort appears in the URL, ignore it.

Clearing it on hide is probably less surprising for the user.

## Filter Considerations

Filters do not need to be visible as columns. Filtering by a hidden column can be useful.

Important distinction:

1. `filterset_fields` controls which fields can filter the queryset.
2. List-column choices control only display.

The implementation should avoid coupling filter availability to visible columns. The main validation relationship is that both systems should validate submitted names against their own allow-lists.

## Product Value

This feature is most valuable for wide operational lists, not every CRUD screen.

Expected value:

1. Reduces default list clutter while preserving access to useful data.
2. Lets different users shape the same list for different jobs.
3. Avoids downstream template forks or duplicate CRUD views just to change columns.
4. Makes queryset annotations and computed `properties` more useful without crowding the default table.
5. Pairs naturally with saved favourites.
6. Makes PowerCRUD feel closer to mature operational admin tools.

The main risk is complexity. The first implementation should be disciplined: allow-listed columns, simple chooser UI, no drag-and-drop ordering, no URL-visible column state, and no localStorage. Persistence should either be session-backed for unnamed current state or DB-backed through explicit favourites/saved-view election.

## Phase Notes

### Phase 1: Lock the public column model

This phase should settle the public API before implementation starts.

The public API decision is to keep existing `fields` and `properties` as the full column allow-list, add `list_options_enabled` as the explicit chooser opt-in, and keep `default_list_fields` as the optional default visible subset. `fields` includes model fields and queryset annotation fields. There should be no first-version `optional_list_fields` or `list_fields` setting.

The visible-column state contract is settled for v1: when both `list_options_enabled` and `default_list_fields` are unset, existing behaviour is preserved and all resolved list fields/properties render without a chooser. When `list_options_enabled = True`, all resolved list fields/properties render by default and the chooser is available. When `default_list_fields` is set, that subset is used before any user preference exists. System columns such as selection, row actions, and bulk controls sit outside user-toggleable data columns.

Settled v1 state rules: stale saved or submitted column names are dropped; if the remaining active set is empty or invalid, PowerCRUD falls back to `default_list_fields`, or every allowed column when no default subset is declared; explicit empty defaults and user-selected zero-data-column tables are invalid in v1.

### Phase 2: Make list rendering column-aware

This phase should introduce one resolver for allowed, default, and active visible list columns, then route existing header and row-cell generation through that resolved set.

The key requirement is that existing views keep current behaviour unless they opt in. Hidden columns should disappear from headers and cells, but row selection, row actions, bulk action containers, and counters should remain independent of column visibility.

Rendering still needs to preserve the current field and property order, sortable header metadata, field/annotation/property formatting, cell alignment, column help text, semantic tooltips, overflow tooltips, `link_fields`, and `get_list_cell_link(...)` for visible cells.

The resolver must handle request-time queryset annotations the same way the existing list rendering path does: allow unresolved configured field names when validation can be deferred, then validate against the effective queryset before rendering.

### Phase 3: Add the column chooser and preference flow

This phase should add the visible "Cols" control and the server-led apply/reset flow.

The chooser should show one checkbox per allow-listed data column, avoid presenting selection/actions as normal data columns, validate submitted column names against the resolved allow-list, and re-render the list without dropping current filters, page size, or selection state.

If the user hides the currently sorted column, the v1 behaviour should clear sort and reset to page 1. JavaScript should stay small: open and close the chooser, collect checked column names, submit the state, and support reset. It should not introduce localStorage.

### Phase 4: Add persistence and stale-state handling

This phase should settle and implement the first persistence source of truth.

The earlier core per-user, per-view DB-backed preference was removed as the release direction. The release direction avoids a mandatory core PowerCRUD migration for unnamed column choices. Unnamed state now persists through session-backed per-view state. Durable saved column state should live in the optional favourites/saved-views path.

Stale state must degrade cleanly: drop column names that are no longer allowed, fall back to defaults if session state becomes empty or invalid, and avoid raising errors after a view config changes.

Saved favourites now carry visible columns as part of the saved list state. Existing favourites that contain filters but no visible-column state remain valid; applying them clears the current column session override so the list falls back to `default_list_fields`, or to every allowed column when no default subset is declared.

### Phase 5: Protect filters, sorting, pagination, and URL state

This phase should prove that changing columns does not corrupt the surrounding list state.

Filters must remain independent from visible columns. Active filters should not be removed because the filtered field is hidden, optional filter controls should not disappear because the matching column is hidden, and filter state should survive column changes.

Sorting uses this v1 rule: hiding the currently sorted column clears sort and resets to page 1; hidden sort parameters received from the URL are ignored. Sort indicators should only render for visible sortable columns.

Pagination, page size, query parameters, and HTMX targets also need explicit behaviour so column changes refresh the intended list area without disturbing unrelated controls.

### Phase 6: Protect inline editing, links, tooltips, row actions, and bulk selection

This phase should cover the list behaviours most likely to break if columns are filtered too bluntly.

Hidden columns should not display inline edit triggers, but `inline_edit_fields` should remain an editability config rather than a visibility config. Queryset annotation fields remain read-only and ineligible for inline edit. Any required hidden-field preservation needed by inline saves must continue to work.

Row-level update/delete policies should remain independent of visible columns. `link_fields`, `get_list_cell_link(...)`, and `get_list_cell_tooltip(...)` should apply only to visible eligible cells, while preserving the existing rule that inline-editable cells are not converted to links.

Bulk selection should remain stable through column changes: selected IDs, select-all state, persisted selection, and bulk action visibility should not be lost merely because visible columns changed.

### Phase 7: Add sample app coverage, tests, and documentation

This phase should make the feature visible, tested, and understandable.

The sample app should demonstrate default and optional columns, include model fields, queryset annotation fields, and properties, and exercise at least one realistic interaction with filters, sorting, inline editing, links, or bulk selection.

Tests should cover config validation, visible-column resolution for model fields, queryset annotations, and properties, header/cell rendering, filters on hidden columns, sorting behaviour, stale state, inline editing around hidden/visible columns, linked cells, and HTMX apply/reset flows if the chooser uses HTMX.

Docs should include copyable configuration snippets, final config reference entries, hook reference updates if hooks are added, and limitations such as no arbitrary fields, no user drag ordering unless implemented, and filter availability remaining independent of column visibility.

Deferred follow-up decisions should prioritise saved views through favourites and download/export behaviour. URL-shareable visible-column state and user-controlled column ordering are low priority. Zero-data-column tables should remain invalid.

## Resolved V1 Decisions

1. V1 supports show/hide only, not user-controlled column ordering.
2. `visible_columns` query parameters are deferred from v1.
3. Durable saved column state should live with optional favourites/saved views unless core DB preferences are explicitly re-approved.
4. Session-backed current column state is the v1 non-DB source for unnamed choices within a browser session.
5. Saved favourites should include visible columns.
6. Saved or submitted stale columns are dropped.
7. Empty or invalid active visible-column state falls back to `default_list_fields`, or to every allowed column when no default subset is declared.
8. Explicit empty defaults and user-selected zero-data-column tables are invalid in v1.

## Deferred Future Work

1. Export/download behaviour needs a separate decision about whether exports follow visible columns or a dedicated export schema.
2. URL-shareable visible-column state may later support one-off or shared table layouts, but it is low priority.
3. User-controlled column ordering may later become a richer saved-view feature, but it is low priority.
4. Zero-data-column tables should remain invalid.
5. Top action overflow for `extra_buttons` is implemented through `extra_buttons_mode`; `extra_actions_mode` remains row-action only and should not be reused implicitly for toolbar buttons.

## Likely Code Areas

1. `src/powercrud/mixins/config_mixin.py`
2. `src/powercrud/validators.py`
3. `src/powercrud/templatetags/powercrud.py`
4. `src/powercrud/templates/powercrud/daisyUI/object_list.html`
5. `src/powercrud/templates/powercrud/daisyUI/partial/list.html`
6. `src/powercrud/static/powercrud/js/powercrud.js`
7. Session state handling in the list-options mixin if core DB persistence is removed
8. `src/powercrud/contrib/favourites/` for saved-view column state
9. `docs/mkdocs/guides/` and `docs/mkdocs/reference/config_options.md` later

## Decisions Confirmed

1. Keep `fields` and `properties` as the public allow-list for rendered list data columns.
2. Add `list_options_enabled` as the explicit chooser opt-in.
3. Add `default_list_fields` as the optional default visible-column subset and backward-compatible shorthand.
4. Do not add first-version `optional_list_fields`; derive optional columns from the allow-list minus defaults.
5. Do not add first-version `list_fields`; it would duplicate the existing public meaning of `fields`.
6. Preserve existing behaviour when both `list_options_enabled` and `default_list_fields` are unset.
7. Keep selection, row actions, bulk controls, and other system cells outside the user-toggleable data-column API.
8. Include queryset annotation fields as eligible configurable columns through the existing `fields` API.
9. Keep annotation fields read-only and ineligible for editable field configs.
10. Avoid localStorage for list-column persistence.
11. Prefer no mandatory core DB migration for unnamed column preferences unless explicitly re-approved.
12. Make favourites/saved views the durable DB-backed persistence path for columns.
13. Defer URL-sharing and user-controlled ordering.
14. Keep zero-data-column tables invalid.
