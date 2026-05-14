# Queryset Fields Plan

## Status

Implemented behind the existing `fields` and `filterset_fields` APIs.

## Next

1. Keep this folder as temporary implementation context until the stable docs are reviewed and the plan is archived.

## Phase 1: Lock The Public Contract

1. [x] Keep `fields` as the ordered list-column API.
    1. [x] Allow entries to resolve against model fields first.
    2. [x] Allow entries to resolve against queryset annotation names.
    3. [x] Keep `properties` as the existing secondary display-only property list.
2. [x] Keep the first version free of a new `queryset_fields` config setting.
    1. [x] Treat `fields` as the public intent declaration.
    2. [x] Require annotation names to match the public column names used in `fields`.
    3. [x] Do not support differently named queryset sources in this feature.
3. [x] Define the first filtering contract.
    1. [x] Allow `filterset_fields` to include model fields and queryset annotation names.
    2. [x] Generate filters for annotation fields from their Django `output_field`.
    3. [x] Keep custom `filterset_class` behaviour unchanged.

## Phase 2: Resolve Fields From Model Metadata And Queryset Annotations

1. [x] Add a shared resolver for configured read-only list/filter names.
    1. [x] Resolve model fields from `model._meta`.
    2. [x] Resolve annotation fields from the effective queryset.
    3. [x] Return enough metadata for labels, display formatting, sorting, and filtering.
2. [x] Preserve current validation for editable surfaces.
    1. [x] Keep `form_fields`, `inline_edit_fields`, and `bulk_fields` model-field-only.
    2. [x] Keep non-editable queryset fields out of generated forms and bulk forms.
    3. [x] Raise clear errors if a queryset field is configured on an editable surface.
3. [x] Preserve existing behaviour for views without annotations.
    1. [x] Keep existing model-field validation outcomes.
    2. [x] Keep existing property resolution and ordering.
    3. [x] Keep duplicate list normalization unchanged.

## Phase 3: Render, Sort, And Filter Annotation Fields

1. [x] Render annotation fields as first-class list cells in `fields` order.
    1. [x] Avoid calling `model._meta.get_field(...)` on annotation fields.
    2. [x] Use `getattr(obj, field_name)` for annotation values.
    3. [x] Apply existing boolean, date, text, alignment, help, tooltip, and link behaviour where appropriate.
2. [x] Sort annotation fields by their public annotation name.
    1. [x] Treat annotation fields as sortable when their expression is available on the effective queryset.
    2. [x] Keep `column_sort_fields_override` available for custom sort expressions.
    3. [x] Preserve stable secondary `pk` ordering.
3. [x] Generate filters for annotation fields when `filterset_fields` requests them.
    1. [x] Build boolean, text, number, date, time, and fallback filters from `output_field`.
    2. [x] Apply filters to the public annotation name.
    3. [x] Raise a clear error when an annotation lacks usable type metadata.

## Phase 4: Handle Queryset Timing And Error Reporting

1. [x] Support class-level querysets during view initialization.
    1. [x] Inspect `self.queryset.query.annotations` when a static queryset is configured.
    2. [x] Validate static annotation-backed `fields` and `filterset_fields` early.
    3. [x] Avoid evaluating the queryset.
2. [x] Support request-time querysets from `get_queryset()`.
    1. [x] Defer unresolved non-model names until the effective queryset is available.
    2. [x] Validate deferred names before rendering, sorting, or building generated filters.
    3. [x] Resolve metadata from the effective queryset when needed rather than adding a cache layer.
3. [x] Make failure modes explicit.
    1. [x] Unknown names should say they are not model fields or queryset annotations.
    2. [x] Name mismatches should point users to matching `annotate(public_name=...)`.
    3. [x] Unsupported annotation types should ask for an explicit Django `output_field`.

## Phase 5: Add Sample App, Tests, And Docs

1. [x] Add a sample view that demonstrates annotation-backed columns.
    1. [x] Include one boolean annotation in `fields`.
    2. [x] Include that annotation in `filterset_fields`.
    3. [x] Show sorting and filtering on the annotation column.
2. [x] Add focused tests for resolver, rendering, sorting, filtering, and timing.
    1. [x] Test class-level queryset annotation validation.
    2. [x] Test `get_queryset()` annotation validation at request time.
    3. [x] Test invalid names, annotation name mismatches, and missing `output_field`.
3. [x] Update public docs and references.
    1. [x] Explain queryset annotations in beginner-friendly terms.
    2. [x] Document `annotate()`, public annotation names, and `output_field`.
    3. [x] State that annotation fields are read-only and not valid for edit/bulk/inline config.
