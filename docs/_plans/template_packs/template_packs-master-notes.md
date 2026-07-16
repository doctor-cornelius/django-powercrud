# Template Packs Master Notes

## Purpose

These notes support the authoritative [`template_packs-master-plan.md`](template_packs-master-plan.md). They hold cross-cutting rationale, evidence, decisions, dependencies, and phase-level handover information. Detailed implementation work belongs in the child plan and notes for the relevant master phase.

## Governance

1. The master plan controls programme scope, sequence, and phase completion.
2. Each master phase receives a child plan only when that phase approaches active work.
3. A child plan may break its master phase into its own phases and nested tasks, but it may not silently expand or redefine the master plan.
4. Each plan has a corresponding notes file whose `## Plan` section mirrors the plan's phase headings at `###` level and in the same order.
5. Completion rolls upward only after the child plan's outcomes have been accepted.
6. Plan files contain status, next action, phases, and nested tasks. Rationale, evidence, alternatives, and implementation discussion belong in notes.

## Delivery Invariant

This programme is expected to run alongside other work over an extended elapsed period. It must not depend on a long-lived implementation branch.

After every implementation merge, `main` must retain a working compatible default DaisyUI experience. Existing settings, template paths, runtime entry points, and supported loading modes remain usable unless a complete, tested compatibility transition lands atomically in the same merge.

The default delivery pattern is:

```text
characterize one behaviour -> implement one bounded slice -> verify compatibility -> merge to main -> begin the next slice from updated main
```

Feature flags or dormant internal infrastructure may be used where helpful, but they must not create an untested second system. New packs and variants remain opt-in until separately promoted.

The few changes that cannot be safely divided must have an explicit atomic merge gate. In particular, default-pack repackaging cannot merge until legacy resolution, distribution contents, default adapter loading, and both supported asset modes work together.

## Current Position

The primary driver is to let downstream projects override focused templates or use substantially different templates without copying PowerCRUD's functional JavaScript. Supporting another framework such as Bootstrap is a later proof of the boundary, not the sole reason for the work.

The target runtime composition is:

```text
PowerCRUD core behaviour and JavaScript
    ├── DaisyUI framework adapter
    │       ├── standard DaisyUI templates
    │       └── alternative DaisyUI templates + optional variant adapter
    └── Bootstrap framework adapter
            └── Bootstrap templates + optional variant adapter
```

A selected pack is a composition of a template namespace, reusable framework adapter, optional variant adapter, optional assets, capabilities, and form-rendering requirements. Most variants should not need variant JavaScript.

Downstream DaisyUI theme and brand configuration are already supported and are outside this project. The intended customisation mechanism here is focused Django template overrides and alternative template structures that continue to reuse PowerCRUD JavaScript.

Compatibility is an explicit programme requirement. The current DaisyUI implementation becomes the source of the compatible default pack; behaviour is preserved with characterization and regression tests rather than a permanent duplicate implementation.

## Sources

1. Original proposal: [`docs/archive/blog/posts/20251120_template_packs.md`](../../archive/blog/posts/20251120_template_packs.md).
2. Completed JavaScript cleanup plan: [`docs/_plans/_archive/js_cleanup/js_cleanup-plan.md`](../_archive/js_cleanup/js_cleanup-plan.md).
3. JavaScript boundary findings: [`docs/_plans/_archive/js_cleanup/phase6-boundary-findings.md`](../_archive/js_cleanup/phase6-boundary-findings.md).
4. Current JavaScript architecture: [`src/powercrud/static/powercrud/js/README.md`](../../../src/powercrud/static/powercrud/js/README.md).

## Plan

### Phase 0: Establish The JavaScript Foundation

This enabling work was completed through the separate JavaScript cleanup project.

Completed outcomes include:

1. `powercrud/js/powercrud.js` is the stable public runtime entry.
2. `window.initPowercrud(fragment)` supports repeatable full-page and HTMX fragment initialization.
3. Once-only global listener registration and per-fragment initialization are separate lifecycle concerns.
4. Runtime code was split into internal modules without changing the public entry.
5. Core semantics, current-template DOM assumptions, and presentation-library behaviour were classified.
6. Candidate adapter boundaries and missing characterization safeguards were recorded.

This phase did not create the template-pack adapters. DaisyUI behaviour, current-template DOM behaviour, and optional variant behaviour still need to be separated through characterized implementation slices in Phase 3.

Merge position: this work was deliberately delivered behind the existing public runtime entry, demonstrating the compatibility-first pattern the remaining programme should follow.

### Phase 1: Lock The Template-Pack Contracts

The completed child plan is [`phase1_contract/phase1-contract-plan.md`](phase1_contract/phase1-contract-plan.md), supported by [`phase1_contract/phase1-contract-notes.md`](phase1_contract/phase1-contract-notes.md).

This phase converts the agreed direction into testable contracts without prematurely publishing an unproven Python or JavaScript API. It covers compatibility, template overrides, runtime layers, composition, assets, forms, packaging, capabilities, and validation.

The exact adapter-injection and initializer mechanisms remain implementation decisions until a real extraction slice proves the smallest useful boundary.

Phase 1 is complete. Its ratified compatibility decisions are recorded in [`phase1_contract/phase1.1-compatibility-resolution-audit.md`](phase1_contract/phase1.1-compatibility-resolution-audit.md); its remaining contract decisions are in [`phase1_contract/phase1.2-1.5-template-pack-contract-analysis.md`](phase1_contract/phase1.2-1.5-template-pack-contract-analysis.md) and the corresponding child notes. The completed Phase 2 child plan is [`phase2_override_points/phase2-override-points-plan.md`](phase2_override_points/phase2-override-points-plan.md), supported by its [notes](phase2_override_points/phase2-override-points-notes.md). Phase 3 is next but has not started.

Merge position: Phase 1 is documentation and contract work and can merge progressively. Its contract must define the permanent delivery invariant, per-slice gates, and the atomic repackaging checkpoint before implementation begins.

### Phase 2: Create Focused DaisyUI Override Points

The completed child plan is [`phase2_override_points/phase2-override-points-plan.md`](phase2_override_points/phase2-override-points-plan.md), supported by its [notes](phase2_override_points/phase2-override-points-notes.md). This phase refactored the current DaisyUI implementation in place without changing its public namespace.

The child plan delivered pagination, toolbar/actions, filters, table structure and row actions, bulk, modal, forms, detail/delete, inline editing, and final focused-copy consolidation as independently integrated slices.

Phases 2.1–2.9 are integrated into `staging/main`. The final Phase 2.9 gate passed 934 non-browser and 77 Playwright tests at 88% combined coverage before squash integration and feature-branch retirement.

Every slice should follow:

```text
characterize -> extract override point -> verify unchanged behaviour
```

Each override point must state the context variables, partial names, semantic `data-powercrud-*` hooks, and events that alternative templates must preserve.

Merge position: each override-point extraction should be independently mergeable with unchanged default rendering and behaviour. Do not accumulate all template restructuring on one branch.

Phase 2 shipped 31 model-first focused components while retaining 0.x template/fragment paths and root/whole-tree copy modes. Runtime JavaScript remains package-owned; no blocker register was needed, and no Phase 3 adapter or Phase 4 pack-selection/metadata API was introduced. Phase 3 is next and awaits direction.

### Phase 3: Extract Reusable JavaScript Adapters

The JavaScript boundary findings distinguish three responsibilities:

1. Core owns durable PowerCRUD state and request semantics.
2. Framework adapters own reusable presentation-framework and library behaviour.
3. Optional variant adapters own only behaviour unique to a template variant.

The extraction must proceed by behaviour rather than moving whole files by name. Each slice requires focused safeguards before movement, followed by unchanged core behaviour and DaisyUI parity verification.

Initialization order is core, framework adapter, then optional variant adapter. Every layer must be repeatable across HTMX swaps, guard global listeners, preserve user state, and support teardown where a library attaches instances to swapped fragments.

Merge position: extract one behaviour boundary at a time. The compatible DaisyUI adapter must be automatically composed after each slice so users do not need new settings or script tags while the split is incomplete.

### Phase 4: Package And Select The Default DaisyUI Pack

The current DaisyUI implementation is the behavioural baseline for the default pack. Existing projects that do not opt into a new pack must continue to render and behave as they do now.

Compatibility includes existing `POWERCRUD_CSS_FRAMEWORK` configuration, explicit per-view `templates_path` overrides, existing `powercrud/daisyUI/...` paths during the approved migration period, and both current runtime-loading modes.

Whether the official DaisyUI pack is a co-distributed Django app or a separate distribution is decided by the Phase 1 contract. The build must include every declared Python module, template, and static asset in wheel and sdist artifacts.

Merge position: resolver helpers and dormant compatibility infrastructure may land earlier, but moving the default implementation is an atomic gate. Do not merge a state that removes legacy paths, requires an unavailable app, changes the stable runtime entry, or breaks either supported asset mode.

### Phase 5: Prove Reuse With A DaisyUI Variant

The first proof pack is a small, visibly different internal DaisyUI variant rather than a theme change. It should alter meaningful template structure while reusing the standard DaisyUI adapter.

This proof directly tests the primary requirement: alternative templates must not need to copy core or framework JavaScript. Variant JavaScript is added only for genuinely different interaction behaviour that stable hooks cannot express.

The reference variant remains internal unless a separate decision promotes it to a supported production pack.

Merge position: the reference variant is opt-in and may merge progressively because it cannot alter the default selection or runtime composition.

### Phase 6: Complete Validation

Validation covers required and capability-dependent templates, semantic hooks, adapter declarations, form-rendering requirements, assets, packaging, configuration errors, and shared behaviour.

Rendering and browser behaviour are preferred over brittle template-source inspection where practical. Artifact validation must install built wheel and sdist outputs into clean environments rather than relying only on the source tree.

The default DaisyUI pack and reference variant should run through the same applicable central behaviour suite.

Merge position: validators, artifact tests, and shared browser contracts should merge as soon as they are reliable so subsequent implementation slices can use them as gates.

### Phase 7: Dogfood The Framework Boundary With Bootstrap 5

Bootstrap is the later optional co-distributed contrib-style cross-framework proof. It is a full-feature-parity dogfood pack, rather than a minimal example, so it can expose assumptions that two DaisyUI template structures cannot.

Form rendering is part of this proof: the Bootstrap pack includes native forms and a maintained, declared, and tested crispy-Bootstrap integration.

Production support for Bootstrap remains a separate decision after the full-parity contract has been tested.

Merge position: Bootstrap remains an optional installed and selected component. Its incremental merges must have no effect on projects that do not configure it.

### Phase 8: Promote Stable Documentation

Stable guidance moves into `docs/mkdocs/` only after the contracts have survived the DaisyUI reference variant and cross-framework proof.

Public guidance should distinguish template packs, framework adapters, and optional variant adapters; explain focused downstream overrides; and document selection, assets, forms, packaging, validation, and compatibility.

The planning folder remains available for implementation history until the user chooses to archive it.

Merge position: documentation follows shipped behaviour. It may merge progressively, but it must not present future or partially landed capabilities as currently available.
