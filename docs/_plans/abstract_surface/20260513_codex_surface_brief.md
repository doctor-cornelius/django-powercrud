# Codex Brief: Abstract Surface Direction

## Summary

PowerCRUD does not need a new abstraction layer yet.

The useful next step is to make the existing API easier to understand:

1. Name the main concepts already present in PowerCRUD.
2. Show recipes using the current explicit configuration.
3. Audit the current config options by concept.
4. Only then decide whether helper APIs such as `PowerField` are worth designing.

This keeps the current API as the source of truth and avoids creating a second, half-overlapping API surface.

## Position

The other AI brief is directionally useful, especially its warning that PowerCRUD risks becoming an accidental language of unrelated settings.

The correction is that any design work must use the real current PowerCRUD names. Some names in that brief are conceptual or Django-admin-like, not current PowerCRUD API names. For example, PowerCRUD currently uses names such as:

1. `fields`
2. `properties`
3. `detail_fields`
4. `detail_properties`
5. `form_fields`
6. `form_display_fields`
7. `form_disabled_fields`
8. `filterset_fields`
9. `default_filterset_fields`
10. `inline_edit_fields`
11. `link_fields`
12. `column_help_text`
13. `list_cell_tooltip_fields`

Before inventing helpers, the project should audit those real options and identify the concepts they already express.

## Concepts

The likely conceptual primitives are:

1. Surface: the configured working screen for listing, filtering, sorting, paging, selecting, and acting on records.
2. Field intent: how a model field or property participates in list, detail, form, inline-edit, link, tooltip, and filter behaviour.
3. Action: a user-visible operation at row, header, selection, bulk, or workflow level.
4. Presentation target: whether a link or action opens in the current page, a new context, a modal, or another HTMX target.
5. Selection: persisted selected-row state and rules for selection-aware controls.
6. Bulk operation: multi-record validation, persistence, conflict handling, and reporting.
7. Async operation: long-running task execution, progress, lifecycle, and cleanup.
8. Recipe: a documented composition of primitives for a common screen pattern.

These are documentation concepts first, not implementation classes.

## Near-Term Boundary

Do not implement `PowerField` yet.

Do not block the list-options feature on `PowerField`.

The list-options public API is already narrow and compatible with the current model:

1. Keep `fields` and `properties` as the list data-column allow-list.
2. Add `default_list_fields` as the default visible subset.
3. Derive optional columns from the allow-list minus defaults.
4. Keep system cells such as selection, row actions, and bulk controls outside the user-toggleable data-column API.

That feature can proceed as a focused column-visibility feature if its unresolved state and persistence questions are settled.

## Helper API Risk

The hardest part of any helper API is precedence.

The rule should be:

```text
Helper declarations generate defaults. Explicit PowerCRUD config wins.
```

That rule is simple to state but not simple to implement with class attributes.

For example:

```python
power_fields = [
    PowerField("status", inline=True),
]

inline_edit_fields = []
```

This should probably mean that explicit `inline_edit_fields = []` disables inline editing, even though the helper requested it. But the implementation must distinguish an explicitly declared empty list from the inherited default empty list.

That implies a helper implementation would need a reliable way to detect which config attributes were explicitly declared on the downstream view class.

Until that problem is designed clearly, helper APIs should stay as design notes.

## Recommended First Deliverables

1. Add a concepts page under `docs/mkdocs/` that explains PowerCRUD's conceptual vocabulary without inventing unimplemented API.
2. Add a small recipe section using only current explicit config.
3. Add an internal config audit mapping current options to concepts.
4. Add a design note for `PowerField` only after the audit, using real PowerCRUD option names.

## Design Tests For Any Future Helper

A helper API should proceed only if it passes these tests:

1. It compiles to current explicit configuration.
2. It does not replace or rename current public API.
3. Explicit config can override helper-derived defaults.
4. Existing views behave exactly as before when the helper is absent.
5. The docs can explain the precedence rule in a few sentences.
6. Tests can prove the helper does not create ambiguous overlap.

## Practical Recommendation

Treat abstract-surface work as documentation and design consolidation first.

Treat list options as a separate focused feature.

Treat `PowerField` as a possible later helper, not as the foundation for the next implementation slice.
