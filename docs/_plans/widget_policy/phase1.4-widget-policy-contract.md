# Phase 1.4: Widget-Policy Contract

## Status

Complete. The first-party packs, validator, fixtures, stable documentation, and
acceptance coverage use the clean replacement contract.

## Contract

PowerCRUD supplies a semantic widget context for each generated control. The
context identifies its surface (`form`, `inline`, `filter`, or `bulk`), semantic
category, native or Crispy rendering path, field name, required and disabled
state, relationship and dependency facts, and whether searchable presentation
was requested.

The selected pack's server adapter must return a widget presentation for that
context. A presentation may specify a compatible Django widget class, HTML
attributes, and a semantic enhancement request. The generic layer translates an
enhancement request into PowerCRUD's shared marker; the selected pack's browser
adapter decides how to implement that marker.

The core continues to own values, choices, querysets, validation, single- and
multi-value submission, dependency resolution, and HTMX lifecycle. It does not
name a CSS framework or presentation library.

## Clean Contract Change

The current adapter contract is replaced, not extended. The old
`filter_widget_attrs` presentation field is removed and the required adapter
method supplies the unified widget policy. Old external adapters are rejected
clearly; no compatibility shim is retained.

The existing contract/API compatibility markers will be incremented from `1` to
`2` solely to make this incompatibility explicit. This does not describe a new
PowerCRUD product version or a second maintained contract.

## Compatibility Boundary

The change is a pack-author API break. It does not intentionally change
applications using the shipped DaisyUI or Bootstrap packs. Custom application
forms and custom filtersets remain outside the policy and are neither restyled
nor normalised.

## Deferred Datetime Correction

Generated `DateTimeField` forms and auto filters currently pass the `DateField`
branch before a dedicated datetime branch can be reached. The behaviour is
preserved as part of the Phase 1–4 baseline, then handled as a separate focused
defect rather than combined with this ownership refactor or the 0.8.6 list-value
format feature.
