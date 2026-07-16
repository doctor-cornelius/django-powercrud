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

The primary driver is to let downstream projects override focused templates or use substantially different templates without copying PowerCRUD's functional JavaScript. The default DaisyUI pack, the provisional same-framework reference proof, and the serious Bootstrap alternative have now tested that boundary from complementary directions.

The target runtime composition is:

```text
PowerCRUD core behaviour and JavaScript
    ├── DaisyUI framework adapter
    │       ├── standard DaisyUI templates
    │       └── provisional alternative DaisyUI templates + optional variant adapter
    └── Bootstrap framework adapter
            └── Bootstrap templates
```

A selected pack is a composition of a template namespace, reusable framework adapter, optional variant adapter, optional assets, capabilities, and form-rendering requirements. Most variants should not need variant JavaScript.

Downstream DaisyUI theme and brand configuration are already supported and are outside this project. The intended customisation mechanism here is focused Django template overrides and alternative template structures that continue to reuse PowerCRUD JavaScript.

Compatibility is an explicit programme requirement. The current DaisyUI implementation becomes the source of the compatible default pack; behaviour is preserved with characterization and regression tests rather than a permanent duplicate implementation.

The immediate sequence is a pre-Phase-8 documentation gate, Phase 8 cleanup, then Phase 9 completion. The gate publishes the durable supported-pack contract before the provisional reference implementation is removed. Final pack-authoring mechanics follow cleanup after the permanent paths have settled.

## Sample Application Proof Strategy

The sample application is the maintained, executable comparison surface for template customisation and pack reuse. It should expose one shared catalogue of models, data, permissions, CRUD scenarios, and navigation through progressively added presentation variants:

1. The compatible default DaisyUI pack.
2. The default pack with a curated set of downstream-style focused component overrides.
3. The structurally different DaisyUI reference pack from Phase 5.
4. The Bootstrap 5 pack from Phase 7 after it reaches the required feature parity.

These are thin presentation configurations over shared scenarios, not duplicated sample applications or copied CRUD view families. The focused-override variant demonstrates representative customisation boundaries rather than copying all focused components into a second maintained pack.

Bootstrap follows the Phase 5 presentation-settings pattern. `config.settings` continues to launch the unchanged DaisyUI default, while a derived `config.settings_bootstrap` selects the Bootstrap pack and its required assets. The same sample may therefore be launched as either presentation on demand, or as two processes on different ports for side-by-side comparison, while retaining the same models, views, URLs, data, permissions, and navigation.

The sample does not require a broader public selection API. Phase 4 established global settings-based pack selection, and Phases 5 and 7 use separate settings configurations for demonstrable presentations. Runtime, query-parameter, and per-view framework switching remain outside the contract.

The reference DaisyUI variant is a provisional internal proof rather than a promised production pack. After the serious Phase 7 alternative reaches parity, remove the reference variant from the visible sample catalogue if it no longer adds enough value. Its implementation may also be retired, but Phase 6 must leave a lightweight automated fixture or equivalent coverage proving that multiple packs can reuse one framework adapter.

## Alternative-Pack Sequence

Phase 5 and Phase 7 answer different questions. Phase 5 proves that structurally different template packs can reuse the same DaisyUI framework adapter. Phase 7 proves that PowerCRUD can support a serious alternative presentation stack with its own framework boundary.

Phase 5 should therefore stay deliberately small and disposable. Its fastest visual distinction may come from a different non-status semantic colour hierarchy, spacing, density, and surface treatment, but it must also alter meaningful template structure. `warning`, `error`, and `success` remain attached to their real meanings; swapping those classes onto ordinary actions would make the proof visually different at the cost of misleading semantics. The reference variant should add no JavaScript unless stable hooks genuinely cannot express an intended interaction.

Phase 7 is now locked to Bootstrap 5. Bootstrap is the stronger architectural stress test because it is independent of the existing Tailwind CSS and DaisyUI stack: it changes component markup, asset assumptions, JavaScript lifecycle, modal and dropdown behaviour, and maintained crispy form integration. It is also sufficiently popular and familiar to be a credible optional pack rather than an artificial test fixture.

The roadmap makes no commitment to another alternative pack after Bootstrap. Any future Tailwind-only or other framework proposal would require a new, separately approved programme rather than occupying a speculative phase here.

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

Master Phase 5 is complete. The numbered delivery slices established the shared presentation harness, four focused Book overrides, a complete `daisyui-reference` namespace, a structurally different list and CRUD shell composition, and shared-catalogue proof without duplicating models, views, routes, permissions, navigation, or functional JavaScript. The final gates passed the complete canonical server suite (`982 passed, 81 deselected`), canonical Playwright suite (`78 passed, 3 intentional presentation-setting skips, 982 deselected`), reference-settings browser proof (`2 passed`), and focused-settings browser proof (`1 passed`). The reference pack remains internal, opt-in, asset-free, JavaScript-free, and provisional; Phase 6 must add the reusable validation and clean-install gates before Phase 7 begins implementing Bootstrap.

### Phase 6: Consolidate Reusable Pack Validation

The planned child work is [`phase6_validation/phase6-validation-plan.md`](phase6_validation/phase6-validation-plan.md), supported by its [notes](phase6_validation/phase6-validation-notes.md).

Phase 6 is a short consolidation phase, not another broad regression programme. Its purpose is to turn the one-off proof and bespoke checks from Phases 4 and 5 into reusable machinery that the Bootstrap implementation can use.

The validator covers pack declarations, required and capability-dependent templates and fragments, adapter declarations, form-rendering requirements, assets, and useful configuration errors. Rendering and browser behaviour retain responsibility for semantic hooks and lifecycle outcomes rather than relying on brittle source inspection.

The default DaisyUI pack and reference pack should run through one shared applicable behaviour matrix using the same sample scenarios. Clean wheel and sdist installation should verify that selectable pack resources survive packaging, but Phase 6 should reuse rather than repeat the broader clean-install, manual-static, Vite, and application behaviour evidence already established in Phases 4 and 5.

The validation architecture must outlive the provisional Phase 5 implementation. Before the reference variant is retired, retain a small same-adapter fixture or equivalent automated contract that continues proving framework-adapter reuse independently of the visible sample catalogue.

Merge position: deliver the validator, shared matrix, installed-resource check, and durable same-adapter fixture as bounded reusable gates before Bootstrap implementation begins.

Master Phase 6 is complete. The preserved `6.0`–`6.6` commits establish a reusable validator; shared server and browser matrices run independently under the default and reference settings; a small test-only same-adapter fixture protects the architectural proof after the reference pack is removed; and `scripts/verify_installed_template_pack_artifacts.py` validates built wheel and sdist artifacts from isolated `site-packages` installations. Final ratification passed 13 focused default-settings server checks, 11 focused reference-settings server checks, three browser scenarios under each setting, and separate wheel/sdist installed-resource probes for both selectable declarations. Phase 6 adds no public runtime selector, in-application switcher, new asset, or changed default presentation; it is reusable validation infrastructure for Phase 7.

### Phase 7: Deliver The Bootstrap 5 Pack

Phase 7 is the first serious cross-framework proof and is locked to Bootstrap 5. The decision is based on architectural value and practical relevance: Bootstrap is independent of Tailwind CSS and DaisyUI, exercises different component and asset contracts, and remains widely used.

The active child plan is [`phase7_bootstrap_pack/phase7-bootstrap-pack-plan.md`](phase7_bootstrap_pack/phase7-bootstrap-pack-plan.md), supported by its [notes](phase7_bootstrap_pack/phase7-bootstrap-pack-notes.md). Phase 7.0 locks the optional contrib-style package, private Bootstrap adapter lifecycle, native and crispy-bootstrap5 forms, derived sample settings, shared parity gate, targeted screenshot inspection, and Michael's post-parity styling review before implementation begins.

The implementation is an optional co-distributed Bootstrap framework adapter and template pack, not a small visual demo. It must exercise Bootstrap-specific markup, assets, modal and dropdown lifecycle, native forms, maintained `crispy-bootstrap5` rendering, and repeatable HTMX initialization and teardown without changing unconfigured projects.

A derived `config.settings_bootstrap` sample configuration selects the Bootstrap declaration and assets while `config.settings` remains DaisyUI. Documented launch commands must support choosing either presentation at process startup and running both simultaneously on separate ports. This is a sample presentation configuration, not an in-application switcher, query-parameter selector, or new per-view/public pack-selection API.

Bootstrap must reach full applicable CRUD parity through the existing shared contracts and sample scenarios before joining the maintained sample catalogue. Genuine cross-framework findings may refine the contracts, but they do not authorize Bootstrap-specific assumptions in PowerCRUD core or regressions in the compatible DaisyUI default.

Once Bootstrap reaches the required parity, it joins the same shared sample catalogue rather than introducing another copied demo application. This makes presentation differences visible while keeping scenario behaviour comparable.

The temporary DaisyUI reference pack remains available through the Bootstrap parity gate so the implementation can still be compared against both same-adapter and cross-framework examples. Once Bootstrap has joined the shared sample catalogue, Phase 8 removes that temporary implementation while retaining the lightweight same-adapter proof established in Phase 6.

Merge position: Bootstrap remains an optional installed and selected component. Its incremental merges must have no effect on projects that do not configure it.

Master Phase 7 is complete on the accepted `template_pack/7.9` tip. The final focused server gates passed 22 Bootstrap-settings tests and 11 reference-settings tests; the reference browser matrix passed 3 tests and the Bootstrap shared/manual-static browser gate passed 4 tests. The complete canonical default regression then passed 1,001 server tests with 11 skips and 90 Playwright deselections, followed by 83 Playwright passes with 7 skips and 1,012 server deselections. The approved Vite rebuild left only the deterministic generated manifest/hash updates already committed.

The final wheel and sdist installed-resource probes each passed from isolated `site-packages` environments. Each artifact resolved and validated the default DaisyUI, DaisyUI reference, and Bootstrap declarations, including package templates, direct fragments, declared assets, private Bootstrap adapter modules, native forms, and crispy-tailwind/bootstrap5 rendering. The distribution harness now carries Bootstrap's selector and dependency requirements. One pre-existing focused test expectation for valid single-quoted action markup was reconciled during the canonical gate; no production runtime change was required.

Bootstrap is distribution- and parity-ratified and is now accepted as a supported non-default production pack. DaisyUI remains the supported default and compatibility baseline. The provisional DaisyUI reference implementation remains available only until the separate Phase 8 cleanup gate.

The Phase 7.10 API-contract hardening follow-up is recorded in [`phase7_bootstrap_pack/phase7-bootstrap-product-api-audit-plan.md`](phase7_bootstrap_pack/phase7-bootstrap-product-api-audit-plan.md). It formalizes portable versus framework-specific presentation contracts, prohibits silent unsupported settings, adds portable modal presentation and view-help controls, fixes the remaining clear Bootstrap parity defects, deprecates raw modal-class controls without removing compatibility, and strengthens shared server and targeted browser validation. Its final evidence is 1,018 passing canonical server tests with 13 skips, followed by a separate isolated 91-test default browser gate with zero failures and 7 intentional skips. The follow-up is integrated, and its evidence supports promoting Bootstrap as a supported non-default production pack.

### Pre-Phase-8 Documentation Gate

The gate is governed by the pre-cleanup part of the single [`Phase 9 plan`](phase9_contract_strategy/phase9-contract-strategy-plan.md), supported by its [notes](phase9_contract_strategy/phase9-contract-strategy-notes.md) and [inventory](phase9_contract_strategy/phase9-documentation-inventory-audit.md).

Complete. The inventory and decisions were published in the top-level Template Packs documentation section. DaisyUI remains the supported default and compatibility baseline; Bootstrap is a supported non-default production pack. Semantic APIs are portable and pack-translated, raw classes are framework-specific, Crispy remains application-controlled, and supported packs may not silently ignore accepted configuration.

Stable docs now publish those rules, the support matrix, and the supported-pack validation model. Plain-app DaisyUI whole-tree copying remains usable during 0.x with a v1.0 removal warning. Focused and model-scoped copying remain supported; Bootstrap and future packs need not offer whole-tree copying.

The gate passed with 83 focused command/pack tests, a strict MkDocs build, and a complete `./runtests` run of 1,018 passes, 13 skips, and 91 Playwright deselections. The published contract is now the basis for the Phase 8 child plan; removal mapping belongs to Phase 8.

### Phase 8: Retire The Temporary DaisyUI Reference Pack

The child work is [`phase8_reference_cleanup/phase8-reference-cleanup-plan.md`](phase8_reference_cleanup/phase8-reference-cleanup-plan.md), supported by its [notes](phase8_reference_cleanup/phase8-reference-cleanup-notes.md). Michael accepted the validated cleanup for integration into `staging/main`, completing Master Phase 8.

Phase 8 is a short cleanup phase after Bootstrap reaches parity and the pre-Phase-8 documentation gate publishes the contract that cleanup must preserve. It removes the provisional `daisyui-reference` implementation rather than carrying a disposable proof as a maintained production surface.

Removal covers the complete reference Python declaration tree, the complete current 46-file reference template namespace, reference sample and test settings, presentation metadata and launch guidance, and tests that exist only for that implementation. The generic pack validator, reusable shared behaviour tests, default DaisyUI pack, legacy `powercrud/daisyUI` compatibility façade, and Bootstrap implementation remain.

Before deletion, Phase 6 must have left a small test-only fixture proving that two packs can share one framework adapter independently of the visible reference pack. The documentation gate must also have published the supported-pack, compatibility, API-classification, warning, and acceptance rules. Phase 8 begins by creating its child plan from that contract and mapping each planned removal to the retained obligations. The shared cross-pack behaviour matrix then moves from default/reference to default/Bootstrap, followed by the complete canonical regression and installed-package gates.

The live Phase 8 planning inventory contains 46 files in the temporary reference namespace, including the later `crispy_partials.html` addition. Removal must cover the actual namespace while leaving the Phase 6 same-adapter fixture untouched. Shared validator, catalogue, behaviour-matrix, and installed-artifact files require selective edits rather than mechanical deletion.

Merge position: retire the reference implementation only after Bootstrap parity and support status are accepted and the pre-cleanup contract review passes. Keep the cleanup as a separate bounded change so reference removal cannot obscure the Phase 7 delivery evidence.

Implementation evidence: the complete reference declaration/template namespace, settings, direct tests, artifact selector, and temporary stable guidance were removed. Focused server and Bootstrap browser gates passed; the full default server gate passed 1,008 tests with 14 skips and the full default Playwright gate passed 84 tests with 5 skips. Strict MkDocs, wheel/sdist isolated-resource validation, and artifact namespace scans passed. The accepted cleanup is integrated into `staging/main` as one bounded Phase 8 change.

### Phase 9: Complete Template-Pack Documentation

Phase 9 resumes after Phase 8 leaves the permanent pack architecture in its final programme shape. The durable strategy and public contract published by the pre-cleanup gate remain authoritative.

Final public guidance includes a dedicated page for authoring and testing a template pack: declaration, namespace, adapters, capabilities, assets, forms, selection, packaging, declaration validation, shared server behaviour, pack-specific sentinels, targeted Playwright coverage, and installed wheel/sdist resources. Focused downstream overrides and a concise implementation gallery connect those concepts to the maintained default, focused-override, and Bootstrap sample presentations without documenting the retired reference implementation as a supported choice.

Phase 9.4 adds a bounded application-owned asset snapshot to the established plain-app copy command. It copies package-owned manual-static runtime and stylesheet files under the downstream app's static namespace without creating a selector, registry, per-view asset mode, Vite convention, or package-loading change. The generated snapshot is explicit complete ownership with no file-level fallback; model-specific template overrides remain independent of this application-level base-template choice.

Phase 9.5 removes the artificial difference between model and project-root main-template copies. A project can now copy one selected root and retain package fallback for everything else. The customisation page starts with the scope and precedence of every supported override layer, while its collapsed project-command choices table directs detailed option reference back to Management Commands.

The planning folder remains available for implementation history until the user chooses to archive it.

Merge position: documentation follows shipped behaviour. Phase 9 may merge progressively, but it must not present future, retired, or partially landed capabilities as currently available. Archive planning material only after explicit user acceptance.
