# Phase 11 Documentation Handover

## Purpose and Working Boundary

You are taking over the `widgets/plan` branch after the widget-policy and
multiselect implementation work. Your immediate job is **not** to inspect the
repository, audit the branch, review the implementation, run exploratory
tests, or make documentation or code changes. Read this briefing and the
specified documents only, then stand by to discuss the Phase 11 documentation
work with Michael.

Phase 11 is a discussion-first documentation phase. Wait for Michael to decide
what stable documentation and release-note scope he wants before proposing a
plan or making edits.

## Required Reading Order

Read only these items before the discussion:

1. `AGENTS/AGENTS.md` for the repository working rules.
2. This briefing.
3. `docs/_plans/widget_policy/widget_policy-plan.md` for the completed phases
   and the three remaining Phase 11 documentation outcomes.
4. `docs/_plans/widget_policy/widget_policy-notes.md`, especially **Branch
   Change Record**, for the authoritative branch-change and release-note
   checklist.
5. `docs/_plans/widget_policy/phase1.4-widget-policy-contract.md` for the
   clean template-pack contract boundary. The active, unreleased contract is
   version 2; there is no version 3.
6. `docs/_plans/widget_policy/phase1.2-semantic-ownership-matrix.md` for the
   intended division between generic PowerCRUD and template packs.
7. `docs/mkdocs/template_packs/authoring-and-publishing.md`, which already
   contains the initial public pack-author contract text.
8. `docs/mkdocs/guides/forms.md` and
   `docs/mkdocs/guides/inline_editing.md`, the most likely stable user-facing
   destinations for the remaining form, custom-form, and multiselect guidance.
9. `CHANGELOG.md` only when Michael is ready to discuss release wording.

Do not broaden this reading list into a code review or repository audit. The
documents above are the handover evidence and decision record.

## What This Branch Has Delivered

The architecture is deliberately simple:

- PowerCRUD continues to own field meaning, values, choices/querysets,
  validation, submission, dependencies, bulk operation semantics, and HTMX
  lifecycle.
- The selected template pack decides the visible widget presentation through
  `get_widget_presentation(context)`. It receives a semantic kind and surface
  (`form`, `inline`, `filter`, or `bulk`), rather than frontend-framework
  details.
- A pack has semantic base defaults and may add a small surface-specific
  adjustment, such as a compact inline multiselect. A neutral decision leaves
  Django's compatible widget in place.
- The first-party DaisyUI and Bootstrap packs implement those policies. The
  former adapter contract was cleanly replaced, so external packs must adopt
  contract version 2 rather than relying on a compatibility shim.

The user-visible results include:

- pack-owned defaults for text, textarea, number, date, datetime, time,
  boolean, select, multiselect, and file widgets across generated forms,
  inline editing, filters, and bulk value controls;
- true `datetime-local` generated DateTimeField controls and datetime filters;
- policy application to silent Django-default fields of a custom ModelForm,
  while explicit application widgets remain authoritative;
- a Tom Select multiselect with checkboxes, click-to-toggle, clear-all, and a
  compact inline `N selected` presentation;
- improved inline menu placement, no native-select flash on inline save, and
  pack-specific modal initialisation;
- semantic list-column sizing as an opt-in view API, with `bounded` retaining
  legacy behaviour;
- centred table headers, better typography inheritance, and improved table
  sizing in both packs;
- Bootstrap sample light/dark selection and a more compact sample shell; and
- the Book and PowerField Book sample views using semantic column sizing.

The branch-change record in `widget_policy-notes.md` is the definitive detailed
list. Do not reconstruct it from commits.

## Important Supported Boundary

For a custom ModelForm, PowerCRUD applies the selected pack only when a
model-backed visible field still carries Django's silent default widget. An
application-declared field, `Meta.widgets` choice, runtime replacement,
non-model field, or hidden field stays application-owned. This distinction is
proved by the sample `BookForm`: its silent M2M field inherits the pack policy,
while its explicit date widget does not change.

Bulk selection checkboxes and M2M add/remove/replace remain generic PowerCRUD
behaviour. The selected pack controls the visible bulk value widget.

## Known Follow-up to Preserve

The radio choices for a bulk M2M operation now appear above the selector in
both packs, so the dropdown cannot hide them. DaisyUI still has one known bulk
dropdown-position defect that Michael observed after that change:

- The DaisyUI bulk multiselect policy applies `min-h-[150px]` to the original
  select.
- Tom Select copies that class to its wrapper.
- Inside its modal, DaisyUI intentionally retains the dropdown within the
  dialog; normal `top: 100%` placement therefore starts below the 150-pixel
  wrapper instead of immediately below the approximately 44-pixel visible
  control.

This is recorded in the notes but is not the next autonomous task. Do not
investigate or fix it unless Michael explicitly reopens it. The next agreed
step is to discuss Phase 11 stable documentation.

## Phase 11 Discussion Starting Point

When Michael is ready, help him decide how to promote the settled behaviour
into stable documentation. The existing plan names three outcomes:

1. Document the datetime correction and silent-custom-ModelForm fallback.
2. Document pack widget defaults, surface variants, neutral Django fallback,
   application overrides, and bulk-policy integration.
3. Document shared multiselect behaviour, then reconcile temporary plan notes
   with the final supported boundary and validation evidence.

Likely supporting material includes the semantic column-width API and concise
release-note wording, but do not assume their exact placement or write a plan
until Michael has discussed the documentation shape with you.
