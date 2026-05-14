# Abstract Surface Notes

## Source Material

This folder currently has one definitive brief and one audit:

1. `20260513_codex_surface_brief.md`
2. `abstract_surface-config-audit.md`

The Codex brief is the definitive direction. It frames the strategic risk: PowerCRUD has enough capability that the public API can feel like a broad set of unrelated settings unless the underlying concepts are named, and it tightens that direction against the live codebase and current option names.

The config audit groups the live option names by concept and records the downstream DDMS evidence that makes explicit-config precedence important.

## Current Working View

PowerCRUD should keep explicit view configuration as the primary public API.

The immediate problem is not lack of abstraction. The immediate problem is that the mental model is implicit.

The right first move is:

1. Concepts documentation.
2. Recipes using the current API.
3. Config audit by concept.
4. Helper design notes only after the audit.

## Concepts Page Landed

The public concepts page now lives at `docs/mkdocs/guides/concepts.md`.

It is useful as a standalone orientation page because it gives users a mental map before they read the full configuration reference. It explains that the concepts are not a second API and that explicit class attributes and hooks remain the source of truth.

The accepted direction is to finish current-API recipes before evaluating a future `PowerField` or similarly named helper.

## Recipes Draft Landed

The public recipes page now lives at `docs/mkdocs/guides/advanced/recipes.md`.

It intentionally uses only current PowerCRUD class attributes and hooks. The purpose is to make the concepts practical and expose repeated patterns before designing any helper API.

## Important Constraint

Do not implement `PowerField` as the first step.

`PowerField` may be a useful future helper, but it introduces a serious precedence problem. If helper declarations generate defaults and explicit config wins, the implementation must distinguish explicit downstream config from inherited defaults.

Example:

```python
power_fields = [
    PowerField("status", inline=True),
]

inline_edit_fields = []
```

If the empty list is explicit, it should probably disable inline editing. If the empty list is merely the inherited default, the helper might reasonably derive inline editing for `status`.

That distinction needs a deliberate resolver design before any helper is implemented.

## Real Config Names Matter

Any design note must use current PowerCRUD names rather than conceptual placeholders.

Relevant current names include:

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

Names such as `list_display`, `readonly_fields`, or `field_tooltips` should not appear as proposed PowerCRUD API unless a later design explicitly introduces them and explains why.

## Relationship To List Options

The list-options feature should remain separate from `PowerField`.

The confirmed list-options API is already narrow:

1. `fields` and `properties` define the list data-column allow-list.
2. `default_list_fields` defines the default visible subset.
3. Optional columns are derived from the difference.
4. System cells are not user-toggleable data columns.

That feature still needs decisions on stale state, empty active state, persistence, anonymous behaviour, and URL-visible state. Those questions should not be deferred into a broad abstract-surface rewrite.

## Likely Concept Buckets For Audit

Use these as draft buckets when auditing the current config surface:

1. Surface: queryset, list state, filters, sorting, pagination, count display.
2. Field intent: list/detail/form inclusion, properties, display-only fields, disabled fields, inline edit, links, tooltips, labels.
3. Action: header buttons, row actions, standard action policies, disabled reasons.
4. Presentation: modal settings, HTMX targets, link opening modes, template paths.
5. Selection: selected IDs, selection-aware buttons, selection metadata.
6. Bulk: bulk edit/delete, validation, sync persistence, async threshold.
7. Async: manager, backend, locks, progress, lifecycle, dashboard.
8. Styling: table classes, buttons, column alignment, widths, template packs.
9. Compatibility: legacy names, defaults that preserve existing behaviour.

## Open Questions

1. Where should the concepts page live in the published docs structure?
2. Should recipes be one page first, or a small folder from the start?
3. Should the config audit be an internal planning artifact first, then promoted into docs?
4. What exact rule should define "explicit config wins" if a helper API is later implemented?
5. Should `PowerField` cover filters in v1, or avoid filter behaviour until surface state is clearer?

## Read-Only DDMS Reference

DDMS should not be edited as part of this planning work.

Use it only as a downstream evidence source for current PowerCRUD usage patterns:

1. Shared base view defaults and pre-validation config mutation.
2. Explicit empty lists that intentionally disable forms, inline edit, and bulk edit.
3. Repeated field names across list, detail, form, inline, bulk, tooltip, and action config.
4. Real workflow action specs using disabled-state hooks.
5. Focused queue surfaces that override a broad base view.
