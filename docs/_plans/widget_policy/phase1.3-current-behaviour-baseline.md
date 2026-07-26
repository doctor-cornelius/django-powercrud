# Phase 1.3: Current Behaviour Baseline

## Status

Complete. The focused generated form, filter, inline, and template-pack tests
now characterize the behaviour that Phases 2–4 must preserve under DaisyUI and
Bootstrap.

## Confirmed Baseline

1. Generated create/update forms retain Django's ordinary text, textarea,
   number, boolean, select, multiselect, and file semantics. The selected pack
   owns any compatible presentation supplied for those semantic categories.
2. Generated date and time controls retain their existing HTML input treatment.
   The former generic `form-control` temporal class is now selected by the
   first-party pack policy, preserving the current output during the ownership
   move.
3. Generated `DateTimeField` forms take the existing `DateField`-first branch:
   they render a date widget rather than `datetime-local`. Automatically
   generated datetime filters also use the date branch. This is preserved by
   explicit tests and deferred as a separate focused defect.
4. Generated filters retain their current first-party classes, `size=5`
   multiselect treatment, HTMX triggers, and Tom Select marker behaviour.
5. Inline forms retain their ordinary rendering and dependency lifecycle. The
   only intentional visible change is the later inline M2M enhancement.
6. Bulk field markup remains owned by the selected pack template. Its existing
   generic metadata contract is unchanged.

## Deferred Behaviour

The generated datetime date-only behaviour is not related to 0.8.6 temporal
list-column formatting. Correct it in a dedicated follow-up after this
ownership refactor is ratified. Auto-filter file fallback and bulk time/file
fallback remain existing behaviour, not a new widget-policy feature.

## Evidence

Focused regression coverage covers generated form/filter paths, both first-party
pack contract paths, inline M2M semantic enhancement selection, and the explicit
datetime characterization. Browser and installed-artifact evidence remain Phase
4 acceptance work.
