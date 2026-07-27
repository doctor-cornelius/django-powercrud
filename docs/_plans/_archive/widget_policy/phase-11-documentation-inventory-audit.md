# Phase 11 Documentation Inventory Audit

## Status

This is the completed read-only documentation inventory for the widget-policy
branch. It identifies the stable pages that need correction or extension, the
pages that should remain authorities and receive links only, and the durable
release-note story. It does not change stable documentation, code, tests,
assets, or the existing widget-policy handover and notes.

The audit was performed on `widgets/plan` against the current worktree. The
worktree already contains unrelated changes; those changes are deliberately
outside this document's scope.

## Purpose and evidence boundary

The authoritative implementation evidence is the Phase 11 handover,
`widget_policy-plan.md`, `widget_policy-notes.md` (especially **Branch Change
Record**), `phase1.4-widget-policy-contract.md`, and
`phase1.2-semantic-ownership-matrix.md`. The stable documentation corpus and
the current `CHANGELOG.md` were screened against that evidence.

The active pack contract is version 2. There is no version 3 and no old-adapter
compatibility shim. The audit does not infer new APIs from source code or
commit history.

The stable corpus contains 52 Markdown pages and the MkDocs navigation files.
Every page was screened for widget, form, multiselect, datetime, template-pack,
bulk-edit, frontend-loading, sample-presentation, and semantic-column-width
claims. Pages with relevant claims were read as documentation sources; pages
without relevant claims are recorded below as screened with no required action.

## Executive findings

1. The current pack-author pages explain that adapters provide widget
   presentation, but do not yet explain the complete policy: semantic kinds,
   four surfaces, base defaults, surface variants, neutral Django fallback,
   enhancement intent, and the application-owned override boundary.
2. `guides/forms.md` correctly explains custom-form field ownership but does
   not state the settled narrower rule: a silent model-backed Django default
   widget may receive the selected pack's presentation, while explicit
   application widgets remain authoritative.
3. `guides/inline_editing.md` still describes a tall, row-growing ManyToMany
   control and suggests replacing it with an application widget. That wording
   predates the supported compact inline multiselect.
4. The generated filter and bulk guides mention dropdowns but do not describe
   true datetime controls, standard searchable multiselects, or the distinction
   between pack-owned visible widgets and generic bulk M2M operations.
5. `reference/config_options.md` describes searchable multiselect behaviour as
   filter-specific even though the policy now covers normal, inline, filter,
   and bulk surfaces. `guides/getting_started.md` and
   `guides/styling_tailwind.md` also retain manual Tom Select wording that only
   mentions `remove_button`.
6. The semantic column-width API is present in the option and PowerField
   references, but the main setup guide does not teach the opt-in policy and
   still says table headers retain their normal alignment even though headers
   are now centred by both first-party packs.
7. The five-page Template Packs section remains the right permanent information
   architecture. No sixth stable widget-policy page is required: user-facing
   behaviour belongs in the form/filter/inline/bulk guides, pack-author details
   belong in authoring and testing, and list geometry belongs in setup and
   references.
8. The next release needs one concise narrative entry covering the pack-owned
   widget architecture and its user-visible datetime, custom-form, multiselect,
   list-width, and cross-pack presentation outcomes. The clean version-2 pack
   author break must be called out as an upgrade boundary.

## Stable documentation inventory

### Required updates

| Destination | Audience | Required content |
| --- | --- | --- |
| `docs/mkdocs/guides/forms.md` | Application developers | Add a widget-presentation section covering generated form defaults, true `datetime-local` controls, standard versus compact multiselects, and the silent custom-`ModelForm` fallback. State exactly what remains application-owned: declared fields, `Meta.widgets`, runtime widget replacement, non-model fields, and hidden fields. Link to the pack selection and authoring pages. |
| `docs/mkdocs/guides/inline_editing.md` | Application developers | Replace the stale tall-row ManyToMany note with the compact inline `N selected` presentation, checked open-menu options, click-to-toggle, clear-all, upward/downward placement, typography/palette inheritance, and flash-free HTMX save behaviour. Clarify that explicit application widgets remain authoritative and that the pack owns the default enhancement. |
| `docs/mkdocs/guides/filtering.md` | Application developers | Explain that generated `DateTimeField` filters use datetime controls, while list-value formatting is a separate concern. Document standard searchable multiselect filters, preserved Django values, and the selected-pack presentation boundary. |
| `docs/mkdocs/guides/bulk_edit_sync.md` | Application developers | Add visible bulk value-widget guidance: standard searchable multiselects, clear-all and checked options, operation radios above the selector, and direct menu placement. Keep field selection and M2M add/remove/replace semantics explicitly generic PowerCRUD behaviour. Link to the policy detail in the pack-author page only where useful. |
| `docs/mkdocs/reference/config_options.md` | API readers | Correct the `searchable_selects` section so it covers all four surfaces and distinguishes the generic enable/disable intent from pack presentation. Link the form, inline, filtering, and bulk guides. Keep the option reference concise rather than duplicating the full interaction specification. Repoint semantic column-width links to the page that actually explains the policy. |
| `docs/mkdocs/guides/setup_core_crud.md` | Getting-started application developers | Add the user-facing semantic column-width API: legacy `bounded` default, opt-in `semantic`, inferred compact/auto/bounded modes, per-column overrides, and the `PowerField(column={"width": ...})` form. Correct the stale statement that headers retain their previous alignment; body-cell alignment remains independently configurable while pack headers are centred. Link to the option and PowerField references. |
| `docs/mkdocs/template_packs/authoring-and-publishing.md` | Independent pack authors | Expand the adapter section into the definitive widget-policy contract: `get_widget_presentation(context)`, semantic kind and surface (`form`, `inline`, `filter`, `bulk`), base defaults, surface overrides, neutral Django fallback, `WidgetPresentation` fields, `default`/`enabled`/`disabled` enhancement intent, pack-owned templates/CSS/browser adapter, and the application override boundary. State the clean API-version-2 break and clarify the misleading “Limits of version 1” wording. |
| `docs/mkdocs/template_packs/testing-and-acceptance.md` | Pack authors and maintainers | Add acceptance obligations for widget policy across native and supported Crispy rendering, all four surfaces, neutral fallback, silent custom-model fields, bulk integration, datetime parsing/presentation, multiselect checked-state/toggle/clear-all, HTMX reinitialisation, dropdown placement, and no native-control save flash. Keep equivalent behaviour—not identical DOM/classes/pixels—as the parity target. |
| `docs/mkdocs/guides/getting_started.md` | Application developers managing assets | Reconcile manual frontend guidance with pack-owned Tom Select registration. Do not instruct consumers to reproduce the pack's `checkbox_options`, `remove_button`, and `clear_button` registration when the selected pack adapter owns it; retain only the vendor load-order requirements that application-owned manual/Vite routes genuinely need. |
| `docs/mkdocs/guides/styling_tailwind.md` | DaisyUI/Tailwind users | Update the manual Tom Select note that currently names only `remove_button`; link to the shared multiselect guidance and state that selected-pack adapters own the enhancement plugins and styling. Keep DaisyUI-specific theme CSS advice here. |
| `docs/mkdocs/reference/sample_app.md` | Developers using the sample | Update the Book/PowerField Book descriptions to mention semantic column-width usage, the silent `genres` versus explicit `published_date` widget proof, and the current pack-owned multiselect experience. Record the Bootstrap light/dark selector and compact shell only as sample demonstrations, not new configuration APIs. |
| `CHANGELOG.md` | Release readers and upgraders | Add a narrative entry under the next release heading (version/date assigned by release work). Cover the public pack-owned widget policy, version-2 external-pack upgrade boundary, datetime correction, silent custom-form fallback, shared standard/compact multiselect UX, semantic list widths, and the material cross-pack UI polish. Avoid a commit-log list of every CSS correction. |

### Link, clarify, or verify without duplicating policy

| Destination | Disposition |
| --- | --- |
| `docs/mkdocs/template_packs/index.md` | Keep the overview and add only a short link or sentence making pack-owned widget presentation explicit. Do not duplicate the adapter contract. |
| `docs/mkdocs/template_packs/selecting-and-configuring.md` | Keep startup selection, native/Crispy ownership, and asset-route guidance as the authority. Add a link to the widget-policy explanation if needed; no new widget table belongs here. |
| `docs/mkdocs/template_packs/customising.md` | Keep focused/model-scoped override boundaries. Add a cross-link if the new forms or authoring sections refer to template ownership; do not describe widget defaults here. |
| `docs/mkdocs/guides/concepts.md` | Existing pack/core ownership language is broadly correct. Add a concise link or sentence for pack-owned widget presentation and retain this page as conceptual vocabulary, not API detail. |
| `docs/mkdocs/reference/complete_example.md` | Keep the example's custom-form field ownership. Add a short link or clarification that explicit form widgets remain authoritative even though silent model defaults may receive pack presentation. Do not turn the complete example into a widget catalogue. |
| `docs/mkdocs/reference/powerfields.md` | The semantic width mapping is already useful. Clarify or link the custom-form wording so “source of truth” is understood as field declarations/explicit widgets, not a contradiction of silent default-widget fallback. |
| `docs/mkdocs/guides/structured_api/powerfields.md` | Apply the same narrow clarification/link as the reference page; no duplicate widget-policy section is required. |
| `docs/mkdocs/reference/testing.md` | Keep the general test commands and link to `template_packs/testing-and-acceptance.md` for the pack-specific widget evidence. No new test matrix should be duplicated here. |
| `docs/mkdocs/reference/mgmt_commands.md` | Existing focused inline-field and bulk-field override guidance already preserves supplied widget attributes. Add a cross-link only if the stable authoring update needs it. |
| `docs/mkdocs/guides/advanced/customisation_tips.md` | Keep the focused override contract and supplied-bound-field guidance; link to the widget boundary if needed. |
| `docs/mkdocs/guides/dependent_form_fields.md` | Keep dependency semantics and refresh lifecycle as-is. The widget policy changes presentation, not dependency ownership. |
| `docs/mkdocs/reference/hooks.md` | Keep generic hook contracts. Link only where a hook description points users toward widget presentation without defining it. |
| `docs/mkdocs/reference/deprecations.md` | Keep as the authority for legacy framework-specific class warnings. Add no widget-policy duplication. |

### Screened with no Phase 11 action

The following pages were screened for the audit vocabulary and contain no
widget-policy claim that needs changing for this branch:

- `docs/mkdocs/index.md`
- `docs/mkdocs/guides/advanced/filter_favourites.md`
- `docs/mkdocs/guides/advanced/index.md`
- `docs/mkdocs/guides/advanced/lazy_evaluation.md`
- `docs/mkdocs/guides/advanced/list_options.md`
- `docs/mkdocs/guides/advanced/permission_aware_affordances.md`
- `docs/mkdocs/guides/advanced/persistence_hooks_async_bulk.md`
- `docs/mkdocs/guides/advanced/persistence_hooks_sync.md`
- `docs/mkdocs/guides/advanced/queryset_annotation_fields.md`
- `docs/mkdocs/guides/advanced/recipes.md`
- `docs/mkdocs/guides/async_dashboard.md`
- `docs/mkdocs/guides/async_manager.md`
- `docs/mkdocs/guides/bulk_edit_async.md`
- `docs/mkdocs/guides/structured_api/index.md`
- `docs/mkdocs/guides/structured_api/poweractions.md`
- `docs/mkdocs/guides/structured_api/recipes.md`
- `docs/mkdocs/reference/async.md`
- `docs/mkdocs/reference/dockerised_dev.md`
- `docs/mkdocs/reference/poweractions.md`
- `docs/mkdocs/reference/renovate.md`

These pages may retain ordinary references to forms, bulk operations, or
template packs. They should not acquire duplicated widget-policy prose.

## Branch-change to documentation coverage

| Branch outcome | Stable destination or disposition |
| --- | --- |
| Contract version 2 and clean adapter replacement | Authoring/testing pages plus one concise CHANGELOG upgrade note. No compatibility shim or version 3 wording. |
| Pack-owned defaults for all semantic widget categories and four surfaces | Forms, filtering, bulk, config reference, and authoring pages. |
| Silent custom-`ModelForm` fallback with explicit application ownership | Forms and sample-app pages; short clarifications in complete-example and PowerField references. |
| True datetime-local form, inline, and filter controls | Forms, inline, filtering, and CHANGELOG. Keep temporal list-value formatting separate. |
| Standard and compact multiselects, checked options, click-to-toggle, clear-all | Forms/inline/filter/bulk guides, config reference, pack acceptance, and CHANGELOG. |
| Generic field selection and M2M add/remove/replace semantics | Bulk guide and authoring/testing boundary; do not describe these as pack-owned. |
| HTMX dependency lifecycle and no native-select save flash | Inline guide and pack-browser acceptance; release note only for the flash correction. |
| Modal height/initialisation, dropdown placement, palette, typography, z-index | Brief user-facing notes only where they affect placement or operation visibility; otherwise pack acceptance and release-note context. |
| Semantic list-column width API | Setup guide, config reference, PowerField references, sample app, and CHANGELOG. |
| Centred headers, full-width sizing, table typography | Setup/sample guidance where users observe the result; concise release-note context. |
| Bootstrap theme selector and compact sample shell | Sample-app page and release-note context only; no new public setting. |
| Packaged asset rebuilds and installed-artifact validation | Pack testing/acceptance page; no user-facing asset-manifest detail. |

## Recommended writing order after this audit

1. Update the pack-author contract and acceptance pages so the version-2
   boundary and policy vocabulary have one authoritative home.
2. Update the forms, inline, filtering, and bulk guides with lifecycle-led
   application guidance and links to the pack contract.
3. Reconcile the configuration reference, setup guide, sample app, frontend
   loading notes, and PowerField clarifications.
4. Draft the next-release narrative from the final stable wording, then review
   the release story for upgrade impact and user-visible payoff.
5. After those stable edits are accepted, mark Phase 11 complete and reconcile
   the temporary plan/notes with the final documentation and validation
   evidence. That later reconciliation is not part of this audit-file commit.

## Acceptance checklist

- Every Branch Change Record outcome has exactly one documentation disposition.
- Every stable Markdown page and navigation file was screened; affected pages
  have an explicit destination and no-action pages are listed or grouped.
- The audit identifies the stale inline, custom-form, searchable-select,
  frontend-plugin, semantic-width, and header-alignment wording.
- The audit states what each destination should explain and what it must not
  duplicate.
- The audit separates generic PowerCRUD semantics, selected-pack presentation,
  application overrides, sample-only polish, and release-note-only detail.
- No new stable widget-policy page is proposed without evidence of an unowned
  audience or contract.
- The later implementation can update stable docs without reopening the
  contract, surface, fallback, or release-scope decisions.

## Sources reviewed

Internal evidence:

- `docs/_plans/widget_policy/phase-11-documentation-handover.md`
- `docs/_plans/widget_policy/widget_policy-plan.md`
- `docs/_plans/widget_policy/widget_policy-notes.md`
- `docs/_plans/widget_policy/phase1.4-widget-policy-contract.md`
- `docs/_plans/widget_policy/phase1.2-semantic-ownership-matrix.md`

Stable evidence:

- All 52 Markdown pages under `docs/mkdocs/`.
- All MkDocs `.nav.yml` files under `docs/mkdocs/`.
- `CHANGELOG.md` through the current `0.9.1` entry.

No implementation code, tests, assets, builds, or exploratory runtime checks
were used to create this documentation inventory.
