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

After every implementation merge into `staging/main`, that branch must retain a working compatible default DaisyUI experience. Protected `main` remains untouched until changes reach it through the repository's pull-request workflow. Existing settings, template paths, runtime entry points, and supported loading modes remain usable on both branches unless a complete, tested compatibility transition lands atomically.

The default delivery pattern is:

```text
characterize one behaviour -> implement one bounded slice -> verify compatibility -> merge to staging/main -> begin the next slice from updated staging/main
```

Feature flags or dormant internal infrastructure may be used where helpful, but they must not create an untested second system. New packs and variants remain opt-in until separately promoted.

The few changes that cannot be safely divided must have an explicit atomic merge gate. In particular, default-pack repackaging cannot merge until legacy resolution, distribution contents, default adapter loading, and both supported asset modes work together.

## Current Position

The primary driver is to let downstream projects override focused templates or use substantially different templates without copying PowerCRUD's functional JavaScript. Supporting another serious alternative presentation stack is a later proof of the boundary, not the sole reason for the work.

The target runtime composition is:

```text
PowerCRUD core behaviour and JavaScript
    ├── DaisyUI framework adapter
    │       ├── standard DaisyUI templates
    │       └── provisional alternative DaisyUI templates + optional variant adapter
    └── selected alternative framework adapter
            └── full-parity alternative templates + optional variant adapter
```

A selected pack is a composition of a template namespace, reusable framework adapter, optional variant adapter, optional assets, capabilities, and form-rendering requirements. Most variants should not need variant JavaScript.

Downstream DaisyUI theme and brand configuration are already supported and are outside this project. The intended customisation mechanism here is focused Django template overrides and alternative template structures that continue to reuse PowerCRUD JavaScript.

Compatibility is an explicit programme requirement. The current DaisyUI implementation becomes the source of the compatible default pack; behaviour is preserved with characterization and regression tests rather than a permanent duplicate implementation.

## Sample Application Proof Strategy

The sample application is the maintained, executable comparison surface for template customisation and pack reuse. It should expose one shared catalogue of models, data, permissions, CRUD scenarios, and navigation through progressively added presentation variants:

1. The compatible default DaisyUI pack.
2. The default pack with a curated set of downstream-style focused component overrides.
3. The structurally different DaisyUI reference pack from Phase 5.
4. The Bootstrap or Tailwind-only pack selected in Phase 7 after it reaches the required feature parity.

These are thin presentation configurations over shared scenarios, not duplicated sample applications or copied CRUD view families. The focused-override variant demonstrates representative customisation boundaries rather than copying all focused components into a second maintained pack.

The sample must not dictate a broader public selection API than package users need. Phase 4 should settle the real selection and composition contract first. Phase 5 may use separate settings configurations for simultaneously demonstrable packs unless independently useful per-view selection has been accepted as part of that contract.

The reference DaisyUI variant is a provisional internal proof rather than a promised production pack. After the serious Phase 7 alternative reaches parity, remove the reference variant from the visible sample catalogue if it no longer adds enough value. Its implementation may also be retired, but Phase 6 must leave a lightweight automated fixture or equivalent coverage proving that multiple packs can reuse one framework adapter.

## Alternative-Pack Sequence

Phase 5 and Phase 7 answer different questions. Phase 5 proves that structurally different template packs can reuse the same DaisyUI framework adapter. Phase 7 proves that PowerCRUD can support a serious alternative presentation stack with its own framework boundary.

Phase 5 should therefore stay deliberately small and disposable. Its fastest visual distinction may come from a different non-status semantic colour hierarchy, spacing, density, and surface treatment, but it must also alter meaningful template structure. `warning`, `error`, and `success` remain attached to their real meanings; swapping those classes onto ordinary actions would make the proof visually different at the cost of misleading semantics. The reference variant should add no JavaScript unless stable hooks genuinely cannot express an intended interaction.

Phase 7 begins with an explicit choice between Bootstrap 5 and a Tailwind-only, shadcn-inspired design. Bootstrap is the stronger architectural stress test because it changes the component framework, asset assumptions, and form integration. A Tailwind-only pack is likely the stronger product and showcase option for projects that want a modern bespoke identity without leaving their existing Tailwind pipeline. A shadcn-inspired pack borrows a visual language for Django templates; it does not claim to use shadcn's React component implementation.

The choice remains open until Phase 7 because Phase 5 and Phase 6 evidence should inform it. Whichever option is selected must reach full applicable CRUD parity before joining the maintained sample catalogue or being considered for production support. The other option becomes a later decision, not an automatic implementation commitment: demand, architectural value, and ongoing maintenance cost must justify a second serious alternative pack.

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

This phase did not create the template-pack adapters. It established the runtime foundation that Phase 3 later used to extract the reusable DaisyUI presentation adapters.

Merge position: this work was deliberately delivered behind the existing public runtime entry, demonstrating the compatibility-first pattern the remaining programme should follow.

### Phase 1: Lock The Template-Pack Contracts

The completed child plan is [`phase1_contract/phase1-contract-plan.md`](phase1_contract/phase1-contract-plan.md), supported by [`phase1_contract/phase1-contract-notes.md`](phase1_contract/phase1-contract-notes.md).

This phase converts the agreed direction into testable contracts without prematurely publishing an unproven Python or JavaScript API. It covers compatibility, template overrides, runtime layers, composition, assets, forms, packaging, capabilities, and validation.

Phase 3 subsequently proved the private adapter-injection and initializer seams. Phase 4 still owns any public pack-composition and selection mechanism.

Phase 1 is complete. Its ratified compatibility decisions are recorded in [`phase1_contract/phase1.1-compatibility-resolution-audit.md`](phase1_contract/phase1.1-compatibility-resolution-audit.md); its remaining contract decisions are in [`phase1_contract/phase1.2-1.5-template-pack-contract-analysis.md`](phase1_contract/phase1.2-1.5-template-pack-contract-analysis.md) and the corresponding child notes. The completed Phase 2 child plan is [`phase2_override_points/phase2-override-points-plan.md`](phase2_override_points/phase2-override-points-plan.md), supported by its [notes](phase2_override_points/phase2-override-points-notes.md). The completed Phase 3 child plan is [`phase3_javascript_adapters/phase3-javascript-adapters-plan.md`](phase3_javascript_adapters/phase3-javascript-adapters-plan.md), supported by its [notes](phase3_javascript_adapters/phase3-javascript-adapters-notes.md).

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

Phase 2 shipped 31 model-first focused components while retaining 0.x template/fragment paths and root/whole-tree copy modes. Runtime JavaScript remains package-owned; no blocker register was needed, and no Phase 4 pack-selection/metadata API was introduced. Phases 3.1–3.8 then extracted the characterized private adapters as independently integrated slices, and Phase 3.9 completed the ratification gate.

### Phase 3: Extract Reusable JavaScript Adapters

The JavaScript boundary findings distinguish three responsibilities:

1. Core owns durable PowerCRUD state and request semantics.
2. Framework adapters own reusable presentation-framework and library behaviour.
3. Optional variant adapters own only behaviour unique to a template variant.

The extraction must proceed by behaviour rather than moving whole files by name. Each slice requires focused safeguards before movement, followed by unchanged core behaviour and DaisyUI parity verification.

Initialization order is core, framework adapter, then optional variant adapter. Every layer must be repeatable across HTMX swaps, guard global listeners, preserve user state, and support teardown where a library attaches instances to swapped fragments.

Phase 3 proves and automatically composes the private DaisyUI framework seams only. It deliberately does not add a variant implementation, public initializer, registry, selector, or metadata API. The master outcome is therefore to preserve extension seams for later optional variants; Phase 4 owns public pack composition/selection and Phase 5 owns the first reference variant.

Master Phase 3 is complete. Phases 3.1–3.8 were independently characterized, extracted, verified, squash-integrated into `staging/main`, and retired. Phase 3.9's three fresh audits found no runtime blocker or public-contract drift; the final isolated canonical gate passed 931 server tests followed by all 78 Playwright tests. The stable public entry and both loading modes remain unchanged, all eight private adapters are composed automatically, and protected `main` was not touched.

Merge position: extract one behaviour boundary at a time. The compatible DaisyUI adapter must be automatically composed after each slice so users do not need new settings or script tags while the split is incomplete.

### Phase 4: Package And Select The Default DaisyUI Pack

The completed child plan is [`phase4_default_pack/phase4-default-pack-plan.md`](phase4_default_pack/phase4-default-pack-plan.md), supported by its [notes](phase4_default_pack/phase4-default-pack-notes.md) and [audit record](phase4_default_pack/phase4-implementation-audits.md). Its initial read-only audits established the ratified contract before implementation.

The current DaisyUI implementation is the behavioural baseline for the default pack. Existing projects that do not opt into a new pack must continue to render and behave as they do now.

Compatibility includes existing `POWERCRUD_CSS_FRAMEWORK` configuration, explicit per-view `templates_path` overrides, existing `powercrud/daisyUI/...` paths during the approved migration period, and both current runtime-loading modes.

Phase 1 decided that official packs are co-distributed. The compatible DaisyUI pack remains inside the installed `powercrud` application so existing users gain no new `INSTALLED_APPS` requirement; optional official packs may use a contrib-style package in the same distribution. The build must include every declared Python module, template, and static asset in wheel and sdist artifacts.

The selection contract must be driven by package-user requirements rather than sample-app convenience. A per-view pack selector should be added only if Phase 4 finds it independently useful and compatible; otherwise later sample variants may use separate settings configurations.

The Phase 4 delivery sequence was deliberately staged. It introduced and verified pack architecture while the compatible default continued to resolve from `powercrud/daisyUI`, then atomically relocated the source of truth to `powercrud/packs/daisyui`; the former namespace now remains a 0.x compatibility façade.

Master Phase 4 is complete. The final atomic transition was squash-integrated into `staging/main` as `c792c7f5` and its feature branch retired. The built-in pack is selected for unconfigured canonical DaisyUI projects; its 45 permanent templates, 45 legacy facades, pack-owned style provider, stable runtime entries, and copy workflows are covered by focused tests. The final gates passed 966 server tests, 78 Playwright tests across manual-static and Vite loading, and clean wheel/sdist installations. A fresh independent review found no remaining blocker. Protected `main` was not changed.

Phase 4 deliberately does not implement the Phase 5 reference variant, per-view pack selection, or Phase 6's reusable validator. Stable public documentation remains Phase 9 work after the reference-variant and serious-alternative proofs.

### Phase 5: Prove Reuse With A DaisyUI Variant

The active child plan is [`phase5_reference_variant/phase5-reference-variant-plan.md`](phase5_reference_variant/phase5-reference-variant-plan.md), supported by its [notes](phase5_reference_variant/phase5-reference-variant-notes.md).

The first proof pack is a small, visibly different internal DaisyUI variant rather than a theme change. It should use an alternative visual hierarchy and alter meaningful template structure while reusing the standard DaisyUI adapter. Colour, spacing, density, and surface changes may make the distinction immediate, but status colours must keep truthful meanings and structural reuse remains the actual proof.

This proof directly tests the primary requirement: alternative templates must not need to copy core or framework JavaScript. Variant JavaScript is added only for genuinely different interaction behaviour that stable hooks cannot express.

The sample application makes that proof inspectable. One shared feature catalogue supplies the same navigation, models, data, permissions, and CRUD scenarios to the compatible default pack, a curated focused-override presentation, and the DaisyUI reference pack. The variants should differ only in the presentation configuration needed to prove their boundary.

The reference variant remains internal and provisional unless a separate decision promotes it to a supported production pack. Its purpose is to establish the same-adapter reuse contract for Phase 6, not to become the programme's long-term showcase pack.

Once the Phase 7 alternative reaches full parity, review the visible reference sample and implementation for retirement. Removing them is acceptable when Phase 6 has retained a lightweight fixture or equivalent automated proof that two packs can share the DaisyUI adapter without copied JavaScript.

Merge position: the reference variant is opt-in and may merge progressively because it cannot alter the default selection or runtime composition.

### Phase 6: Complete Validation

Validation covers required and capability-dependent templates, semantic hooks, adapter declarations, form-rendering requirements, assets, packaging, configuration errors, and shared behaviour.

Rendering and browser behaviour are preferred over brittle template-source inspection where practical. Artifact validation must install built wheel and sdist outputs into clean environments rather than relying only on the source tree.

The default DaisyUI pack and reference variant should run through the same applicable central behaviour suite using their shared sample scenarios. The focused-override sample should retain targeted coverage proving that downstream overrides work without copied PowerCRUD JavaScript.

The validation architecture must outlive the provisional Phase 5 implementation. Before the reference variant is retired, retain a small same-adapter fixture or equivalent automated contract that continues proving framework-adapter reuse independently of the visible sample catalogue.

Merge position: validators, artifact tests, and shared browser contracts should merge as soon as they are reliable so subsequent implementation slices can use them as gates.

### Phase 7: Deliver The First Serious Alternative Pack

Phase 7 starts with an explicit Bootstrap 5 versus Tailwind-only decision. It does not inherit Bootstrap merely because the earlier roadmap named it before the same-adapter proof and validation work were complete.

Bootstrap provides the stronger cross-framework stress test. A Tailwind-only, shadcn-inspired pack may provide greater user and showcase value while still requiring an honest presentation-adapter boundary rather than being described as another DaisyUI variant. The child plan must record the evidence and value judgment used to choose between them.

The selected pack is an optional co-distributed, full-feature-parity dogfood implementation rather than a minimal demo. Form rendering is part of the proof: it must include native rendering and any applicable maintained crispy integration. Production support remains a separate decision after full parity has tested the contract.

Once the selected alternative reaches the required parity, it joins the same shared sample catalogue rather than introducing another copied demo application. This makes presentation differences visible while keeping scenario behaviour comparable.

At that point, review the provisional Phase 5 reference variant. Its visible sample and full implementation may be retired if they have become maintenance noise, but retain the lightweight same-adapter proof established in Phase 6.

Merge position: the chosen alternative remains an optional installed and selected component. Its incremental merges must have no effect on projects that do not configure it.

### Phase 8: Consider A Second Serious Alternative Pack

After Phase 7, consider the Bootstrap-or-Tailwind option that was not selected. This is a decision checkpoint, not a promise to maintain two serious alternatives.

Proceed only when demonstrated demand, additional architectural evidence, or clear product value justifies the cost of full CRUD parity, forms, assets, validation, browser coverage, packaging, documentation, and ongoing maintenance. If authorized, the second alternative uses the established contracts and shared sample scenarios rather than reopening the architecture or creating another demo application.

Merge position: no implementation branch begins until the second pack receives separate approval and a child plan. Deferral is a valid completed decision for this phase.

### Phase 9: Promote Stable Documentation

Stable guidance moves into `docs/mkdocs/` only after the contracts have survived the DaisyUI reference variant and serious-alternative proof.

Public guidance should distinguish template packs, framework adapters, and optional variant adapters; explain focused downstream overrides; and document selection, assets, forms, packaging, validation, and compatibility. A concise implementation gallery should connect those concepts to the shared sample variants and the small configuration or template changes that distinguish them.

The planning folder remains available for implementation history until the user chooses to archive it.

Merge position: documentation follows shipped behaviour. It may merge progressively, but it must not present future or partially landed capabilities as currently available.
