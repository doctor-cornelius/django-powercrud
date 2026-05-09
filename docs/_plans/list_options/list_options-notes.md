# List Options Notes

## Problem Summary

Some operational list screens need more columns than should be shown by default. A different system shown by the user lets users choose which list columns are visible through a "Change columns" control.

The proposed PowerCRUD version is a default-vs-optional column model, similar to the existing default-vs-optional filter model.

## Initial Feasibility Assessment

This looks feasible in PowerCRUD's current architecture.

PowerCRUD already resolves list display from configured `fields` and `properties`, builds generic header and cell payloads, and renders those payloads through the shared list template. That means column visibility can probably be handled by filtering the resolved headers and row cells before rendering, instead of creating a second table system.

The closest existing pattern is optional filter visibility:

1. Treat the declared filter set as the full allow-list.
2. Treat `default_filterset_fields` as the initially visible subset.
3. Preserve explicitly visible optional filters through request state.
4. Validate submitted visibility choices against the effective allow-list.

List-column visibility can follow the same conceptual model.

## Candidate API Shape

Possible configuration:

```python
fields = ["ref", "category", "status", "task", "created", "client", "property", "sla"]
default_list_fields = ["ref", "status", "task", "created", "client"]
```

In that shape:

1. `fields` and `properties` define the full allowed rendered-column universe.
2. `default_list_fields` defines what appears when the user has no saved preference.
3. Everything allowed but not default-visible is available through a column chooser.

An alternative naming option is to introduce `list_fields`, but that may duplicate the existing meaning of `fields`. The first-pass design should decide whether reusing `fields` is clearer and less disruptive.

## Properties

Properties should be eligible configurable columns.

Validation should check visibility config against the effective rendered-column universe:

1. Resolved model fields from `fields`.
2. Resolved properties from `properties`.

Properties remain display-only. Inline editing should stay model-field-only unless a separate future feature deliberately changes that contract.

## Persistence Direction

The preferred direction is user-profile-backed column choices, not browser-local-only state.

The existing favourites contrib app is DB-backed, not cache-backed. It uses a normal model with a `JSONField` state per user, view key, and favourite name.

For column choices, the cleaner first design is probably a separate per-user, per-view preference model rather than forcing current column choices into named favourites immediately.

Candidate concept:

```text
PowerCRUDListPreference
- user
- view_key
- state JSONField  # for example {"visible_columns": [...]}
- updated_at
```

Named saved filter favourites could later be extended to include `visible_columns`, because a full saved view is naturally filters plus visible optional filters plus sort plus page size plus visible columns.

## URL State And Sharing

There are two possible layers:

1. User preference as the normal source of truth.
2. Optional `visible_columns` query parameters for shareable or one-off list layouts.

If URL state is supported, submitted column names must be validated against the allowed columns before rendering.

## JavaScript Direction

Avoid localStorage for this feature if user-profile-backed preferences are the goal.

Some JavaScript is still useful for the column chooser UI, but it should stay small and server-led:

1. Open and close the column chooser.
2. Collect checked column names.
3. Submit a small form or HTMX request.
4. Support a reset-to-default action.

Do not copy the full optional-filter localStorage machinery unless there is a strong anonymous-user requirement.

The current `powercrud.js` is already becoming large. This feature should either be implemented as a small isolated module/section or be paired with a light JS organization pass before adding more state machinery.

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
2. If a hidden sort appears in the URL, either ignore it or allow it but do not show a header indicator.

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
4. Makes computed `properties` more useful without crowding the default table.
5. Pairs naturally with saved filter favourites and eventual saved views.
6. Makes PowerCRUD feel closer to mature operational admin tools.

The main risk is complexity. The first implementation should be disciplined: allow-listed columns, simple chooser UI, DB-backed user preference, no drag-and-drop ordering, and no localStorage unless explicitly justified.

## Open Questions

1. What public config names should be used: `default_list_fields`, `optional_list_fields`, `list_fields`, or another naming scheme?
2. Should column order be configurable by the user in phase 1, or should phase 1 only support show/hide?
3. Should user preferences live in core PowerCRUD or an optional contrib app?
4. Should saved filter favourites grow a `visible_columns` state key immediately, or only after current column preferences exist?
5. Should anonymous users get session-backed column choices, default-only behavior, or no persistence?
6. Should `visible_columns` be URL-shareable in phase 1?
7. What should happen when a saved preference references a column that the view no longer allows?

## Likely Code Areas

1. `src/powercrud/mixins/config_mixin.py`
2. `src/powercrud/validators.py`
3. `src/powercrud/templatetags/powercrud.py`
4. `src/powercrud/templates/powercrud/daisyUI/object_list.html`
5. `src/powercrud/templates/powercrud/daisyUI/partial/list.html`
6. `src/powercrud/static/powercrud/js/powercrud.js`
7. `src/powercrud/contrib/` or a new core preference model area
8. `docs/mkdocs/guides/` and `docs/mkdocs/reference/config_options.md` later

## Decisions Tentatively Favoured

1. Include model properties as eligible configurable columns.
2. Keep inline editing model-field-only.
3. Use DB-backed user preference as the primary persistence mechanism.
4. Avoid localStorage for column choices.
5. Keep the first UI simple: show/hide columns and reset to defaults.
6. Do not couple filter availability to visible columns.
