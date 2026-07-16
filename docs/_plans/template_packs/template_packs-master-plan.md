# Template Packs Master Plan

## Status

Active. Phases 0–8 and the Phase 7.10 API-contract hardening follow-up are integrated into `staging/main`. The temporary DaisyUI reference pack is retired, leaving DaisyUI as the supported default and Bootstrap as the supported non-default production pack. Every later phase must keep the compatible default DaisyUI experience working on `staging/main` and protected `main`.

## Next

Resume the remaining Phase 9.3 documentation and acceptance work, using the completed Phase 9.5 project-root selection and override-layer guidance.

## Phase 0: Establish The JavaScript Foundation

1. [x] Modularise the existing runtime behind the stable public entry.
2. [x] Establish repeatable full-page and HTMX fragment initialization.
3. [x] Classify core, template-structure, and presentation-library responsibilities.
4. [x] Record candidate extraction boundaries and missing characterization safeguards.
5. [x] Preserve the stable public entry and current default behaviour throughout the cleanup.

## Phase 1: Lock The Template-Pack Contracts

1. [x] Lock legacy compatibility and resolution precedence.
2. [x] Lock the template and focused-override contract.
3. [x] Lock the core, framework-adapter, and optional variant-adapter contract.
4. [x] Lock pack composition, asset, and form-rendering contracts.
5. [x] Lock packaging, capability, and validation contracts.
6. [x] Lock the incremental merge invariant and identify the few changes that require atomic compatibility checkpoints.

## Phase 2: Create Focused DaisyUI Override Points

1. [x] Refactor current DaisyUI templates into focused override points.
2. [x] Preserve current template paths, rendering, HTMX responses, and runtime behaviour.
3. [x] Update downstream template-copy workflows for focused overrides.
4. [x] Merge each characterized override-point slice independently before starting the next slice.

## Phase 3: Extract Reusable JavaScript Adapters

1. [x] Keep durable PowerCRUD semantics in core JavaScript.
2. [x] Extract reusable framework behaviour into a DaisyUI adapter.
3. [x] Preserve internal extension seams for later optional variants without adding a speculative variant implementation or public API before Phase 5.
4. [x] Preserve repeatable initialization, teardown, and stable runtime loading contracts.
5. [x] Keep the compatible DaisyUI adapter automatically wired after every merged extraction slice.

## Phase 4: Package And Select The Default DaisyUI Pack

1. [x] Package the characterized current implementation as the compatible default DaisyUI pack.
2. [x] Add pack selection, composition, discovery, and configuration errors.
3. [x] Preserve approved legacy settings and template paths.
4. [x] Verify manual-static and bundled/Vite integrations.
5. [x] Merge repackaging only when the default pack, compatibility paths, distribution artifacts, and both loading modes work together.

## Phase 5: Prove Reuse With A DaisyUI Variant

1. [x] Build a deliberately small, visibly different internal DaisyUI reference variant with meaningful structural changes rather than a theme-only treatment.
2. [x] Reuse the standard DaisyUI framework adapter without copying it.
3. [x] Use optional variant JavaScript only where stable hooks cannot support the interaction.
4. [x] Expose default, focused-override, and reference-pack variants of one shared sample-app feature catalogue.
5. [x] Keep sample navigation, data, and CRUD scenarios shared rather than duplicating each sample implementation.
6. [x] Refine the contracts from the reference-variant and sample-app findings.
7. [x] Keep the reference variant opt-in so merging it cannot change the default experience.
8. [x] Treat the reference variant as a provisional proof whose visible sample and implementation may be retired after the first serious alternative pack ships.

## Phase 6: Consolidate Reusable Pack Validation

1. [x] Add one reusable validator for pack declarations, required templates and fragments, capabilities, adapters, forms, and assets.
2. [x] Establish a shared behaviour-test matrix for the default and reference packs using the same sample scenarios.
3. [x] Verify that selectable pack resources remain present and usable in clean wheel and sdist installations.
4. [x] Preserve a small same-adapter fixture that survives any later retirement of the visible reference pack.
5. [x] Reuse Phase 4 and Phase 5 evidence instead of repeating already-proven asset-mode and application behaviour checks.
6. [x] Merge the bounded validation improvements as reusable gates for Bootstrap implementation.

## Phase 7: Deliver The Bootstrap 5 Pack

1. [x] Build an optional co-distributed Bootstrap 5 framework adapter and template pack.
2. [x] Add a derived Bootstrap sample settings configuration and documented launch command while leaving the default DaisyUI settings unchanged.
3. [x] Allow the shared sample to run as DaisyUI or Bootstrap on demand, including simultaneous processes on different ports, without runtime or per-view pack selection.
4. [x] Keep Bootstrap components, assets, and JavaScript lifecycle independent of Tailwind CSS and DaisyUI.
5. [x] Deliver full applicable CRUD parity through the existing shared contracts and sample scenarios.
6. [x] Support native form rendering and the maintained `crispy-bootstrap5` integration.
7. [x] Validate Bootstrap modals, dropdowns, forms, and repeated HTMX initialization and teardown.
8. [x] Refine the pack contracts from genuine cross-framework findings without changing unconfigured projects.
9. [x] Add Bootstrap to the shared sample catalogue after it reaches the required parity.
10. [x] Decide separately whether Bootstrap becomes a supported production pack, then retain the temporary reference pack only until the Phase 8 cleanup gate.

## Pre-Phase-8 Documentation Gate

1. [x] Inventory the stable documentation and settle the supported-pack, API, Crispy, validation, navigation, and whole-tree-copy decisions.
2. [x] Publish and validate the pre-cleanup contract, DaisyUI whole-tree deprecation, support matrix, and linked references.

## Phase 8: Retire The Temporary DaisyUI Reference Pack

1. [x] Create the Phase 8 child plan from the published contract, mapping every proposed removal to the compatibility and validation surfaces that must remain.
2. [x] Confirm Bootstrap has reached the required parity, accepted support status, and joined the shared sample catalogue.
3. [x] Confirm the Phase 6 test-only fixture preserves same-adapter reuse without the visible reference implementation.
4. [x] Remove the reference declaration, templates, sample settings, presentation metadata, and launch guidance.
5. [x] Remove reference-specific server and browser tests while retaining reusable validators and shared behaviour tests.
6. [x] Move the shared cross-pack behaviour matrix from default/reference coverage to default/Bootstrap coverage.
7. [x] Pass the complete regression and installed-package gates after the reference implementation is removed.

## Phase 9: Complete Template-Pack Documentation

1. [ ] Publish a dedicated authoring-and-testing page for defining, packaging, and validating a new template pack against the permanent post-Phase-8 implementation.
2. [ ] Complete focused-override and custom-pack guidance against the permanent post-Phase-8 implementation.
3. [ ] Publish final default, focused-override, and Bootstrap sample guidance.
4. [ ] Validate the complete stable documentation and close or archive planning material after acceptance.
5. [x] Add and document opt-in application-owned manual-static snapshots for supported pack assets without changing package runtime loading.
6. [x] Add and document single-root project-pack copying, with a clear overview of the supported override layers.
