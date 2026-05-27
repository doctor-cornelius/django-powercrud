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

That was the accepted direction before PowerField implementation began: finish current-API recipes first, then evaluate whether a helper was justified. PowerField has since been implemented as the accepted helper for repeated Field Intent.

## Recipes Draft Landed

The public recipes page now lives at `docs/mkdocs/guides/advanced/recipes.md`.

It intentionally uses only current PowerCRUD class attributes and hooks. The purpose is to make the concepts practical and expose repeated patterns before designing any helper API.

## Important Constraint

Do not implement the public `PowerField` API as the first step.

`PowerField` is now the accepted helper direction, but it introduces a serious precedence problem. If helper declarations generate defaults and explicit config wins, the implementation must distinguish explicit downstream config from inherited defaults.

Example:

```python
power_fields = [
    PowerField("status", inline=True),
]

inline_edit_fields = []
```

If the empty list is explicit, it should probably disable inline editing. If the empty list is merely the inherited default, the helper might reasonably derive inline editing for `status`.

That distinction needs a deliberate resolver design before the public helper API is implemented.

## PowerField Implementation Plan

The updated plan should start with config resolver standardisation.

Build the internal normalized config path first, without changing public behaviour. Goal: primitive class attrs still behave exactly as today, but class-time URL registration, instance validation, and runtime `config()` stop being separate mental models.

Then add the `PowerField` compiler.

Add `PowerField` / `PowerOverride` as plain declarations that compile into normalized primitive Field Intent config. Enforce strict inheritance: one Field Intent style per inheritance chain, no implicit bridging.

Then wire startup integration.

Wire compiled config into the places that currently read raw class attrs: bulk URLs, inline URLs, list-options URLs, then instance validation. This is where most subtle regressions will be.

Then lock down validation and edge cases.

Lock down error messages, duplicate fields, unsupported links, invalid excludes, `PowerOverride` sentinels, properties vs model fields, default-list behaviour, and explicit "absence means absence" semantics.

The sample app should start once there is a meaningful PowerField implementation to exercise. Use `Book` as the first proof path, but add a new PowerField-based Book view variant rather than replacing the existing primitive Book views. Add it to the sample app navigation in a discoverable but non-disruptive way.

Public docs should follow the working implementation. Add side-by-side primitive vs PowerField examples, and keep the primitive API as the main stable API with PowerField presented as a helper for repeated field intent.

Finally, run a DDMS reality check.

Try converting one DDMS-style surface in a branch or spike, especially one with tooltips, bulk, inline, `default_list_fields`, and queryset dependencies. Use that to decide whether the current ergonomics are enough or whether a later explicit inheritance bridge is worth designing.

The implementation should not start by adding the public `PowerField` class alone. Start by cleaning the config consumption path, because that gives the safety net needed for both legacy preservation and PowerField.

## Current Implementation State

The first five implementation and documentation slices have been implemented and pushed on the `powerfield` branch.

The completed work is still deliberately narrow:

1. `resolve_class_config()` now gives class-time code a normalized primitive snapshot instead of each classmethod reading raw attributes independently.
2. URL registration and list-options registration now use that class-time snapshot.
3. `PowerField` and `PowerOverride` now exist as an internal Field Intent compiler that can extract primitive config fragments.
4. `ConfigMixin.__init__` now consumes the same class snapshot, so compiled `power_fields` flow through existing validation and `_configure_*` startup.
5. PowerField mode tracks which primitive dimensions were actually declared, so absent list/detail/form dimensions do not silently fall through to legacy defaults.
6. Strict style checks now reject class hierarchies that mix primitive Field Intent declarations and `power_fields`.
7. The sample app now includes `PowerFieldBookCRUDView`, a sibling Book view configured through `power_fields`.
8. The sample navigation exposes `PowerField Books` beside the existing Book samples, with both HTMX and full-page load links.
9. The current primitive API remains protected: the focused compatibility tests and the broader non-Playwright pytest suite passed after the fourth slice.
10. Public docs now include a PowerField guide at `docs/mkdocs/guides/powerfields.md`.
11. Public docs now include a PowerField API reference at `docs/mkdocs/reference/powerfields.md`.
12. Concepts, configuration reference, sample app docs, navigation, and the docs home page now link PowerField as a core Field Intent helper.

The important remaining limit is that no DDMS-style downstream surface has been converted as a private proof. `power_fields` is now implemented, tested, exercised through the sample app, and documented publicly, but it still needs a reality check against one downstream-style surface before treating the ergonomics as settled.

## Book Sample Primitive Equivalence

The Book sample now has a stronger backend proof path than a standalone PowerField spot check.

`BookCRUDView` is treated as the golden primitive Field Intent baseline. `PowerFieldBookCRUDView` remains a sibling view with its own `powerfield-book` URL base, but its resolved primitive config is compared directly against `BookCRUDView`.

This deliberately does not duplicate Playwright interaction tests yet. The confidence comes from two layers:

1. Existing route, render, menu, list-options, inline URL, and bulk URL tests prove the PowerField sample travels through normal PowerCRUD routes.
2. The equivalence test proves the generated primitive lists and mappings match the established primitive Book view.

The one intentional normalization is the `pages` link target. `BookCRUDView` links to `sample:bigbook-detail`; `PowerFieldBookCRUDView` links to `sample:powerfield-book-detail` so the sample variant stays self-contained.

`PowerFieldBookCRUDView` uses repeated `PowerField` declarations where different primitive dimensions need different order. This is a useful implementation lesson: one declaration per field is a nice compact convention, but exact primitive equivalence can require declaring the same field in separate dimension-specific positions. That avoids introducing a new ordering API before there is enough evidence for it.

The view now uses the same `forms.BookForm` as `BookCRUDView` for clone-equivalence testing. At class-time, the compiled PowerField config still exposes generated `form_fields`; at runtime, the existing custom-form rule clears `form_fields` because `form_class` is the source of truth.

## Public PowerField Docs

PowerField is now documented as a core PowerCRUD helper, not a contrib app and not a replacement API.

The guide uses collapsible Material examples with tabs to show primitive Field Intent and PowerField side by side. The reference page carries the constructor kwargs, primitive compile targets, `PowerOverride`, validation rules, inheritance/coexistence rules, `form_class` behaviour, and primitive extraction helpers.

The docs intentionally keep the primitive API as the underlying contract. PowerField is framed as an abstraction that reduces repeated field declarations while still compiling to the primitive config PowerCRUD already understands.

## Testing Expectations

Most current tests should continue to run as-is if the resolver standardisation preserves the primitive API contract. The main purpose of Phase 1 is to make the internals cleaner while proving existing primitive views still behave exactly as they do today.

PowerField-specific work will need additional tests for compilation, strict inheritance/coexistence checks, `PowerOverride`, absence semantics, primitive extraction helpers, and the Book sample variant. Existing tests should not need a broad rewrite; any adjustment should be limited to places that intentionally inspect raw class attributes instead of the normalized primitive config.

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
5. Should `PowerField` cover filters, or avoid filter behaviour until surface state is clearer?

## Read-Only DDMS Reference

DDMS should not be edited as part of this planning work.

Use it only as a downstream evidence source for current PowerCRUD usage patterns:

1. Shared base view defaults and pre-validation config mutation.
2. Explicit empty lists that intentionally disable forms, inline edit, and bulk edit.
3. Repeated field names across list, detail, form, inline, bulk, tooltip, and action config.
4. Real workflow action specs using disabled-state hooks.
5. Focused queue surfaces that override a broad base view.
