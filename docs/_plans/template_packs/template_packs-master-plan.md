# Template Packs Master Plan

## Status

Active. Phases 0–4 are complete. Every later phase must keep the compatible default DaisyUI experience working on `staging/main` and protected `main`.

## Next

When authorized, begin Phase 5's shared sample-presentation harness from the accepted child plan.

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

1. [ ] Build a deliberately small, visibly different internal DaisyUI reference variant with meaningful structural changes rather than a theme-only treatment.
2. [ ] Reuse the standard DaisyUI framework adapter without copying it.
3. [ ] Use optional variant JavaScript only where stable hooks cannot support the interaction.
4. [ ] Expose default, focused-override, and reference-pack variants of one shared sample-app feature catalogue.
5. [ ] Keep sample navigation, data, and CRUD scenarios shared rather than duplicating each sample implementation.
6. [ ] Refine the contracts from the reference-variant and sample-app findings.
7. [ ] Keep the reference variant opt-in so merging it cannot change the default experience.
8. [ ] Treat the reference variant as a provisional proof whose visible sample and implementation may be retired after the first serious alternative pack ships.

## Phase 6: Complete Validation

1. [ ] Add template-pack contract and capability validation.
2. [ ] Validate wheel and sdist contents from clean installations.
3. [ ] Validate manual-static and bundled/Vite asset modes.
4. [ ] Run shared unit and browser behaviour across the default pack and reference variant through the applicable sample-app scenarios.
5. [ ] Preserve a lightweight automated same-adapter reuse proof that can survive retirement of the visible reference variant.
6. [ ] Merge validation improvements progressively as reusable gates for later slices.

## Phase 7: Deliver The First Serious Alternative Pack

1. [ ] Decide whether Bootstrap 5 or a Tailwind-only, shadcn-inspired design is the more valuable first serious alternative.
2. [ ] Build the chosen optional co-distributed framework adapter and template pack.
3. [ ] Deliver full CRUD feature parity through the shared contracts, including applicable native and maintained crispy form rendering.
4. [ ] Refine the contracts from the chosen alternative's findings.
5. [ ] Decide separately whether the completed alternative becomes a supported production pack.
6. [ ] Keep the alternative optional so merging it cannot affect unconfigured projects.
7. [ ] Add the alternative to the shared sample-app catalogue once it reaches the required feature parity.
8. [ ] Review the Phase 5 reference variant for retirement while retaining sufficient automated proof that multiple packs can reuse one framework adapter.

## Phase 8: Consider A Second Serious Alternative Pack

1. [ ] Evaluate demand, architectural evidence, and maintenance cost for the Bootstrap-or-Tailwind alternative not selected in Phase 7.
2. [ ] Record an explicit proceed-or-defer decision, proceeding only when another full-parity maintained pack is justified and separately approved.
3. [ ] Reuse the established contracts, validation, and shared sample catalogue if the second alternative is authorized.

## Phase 9: Promote Stable Documentation

1. [ ] Document downstream focused template overrides.
2. [ ] Document pack selection, composition, adapters, assets, forms, and validation.
3. [ ] Publish author guidance for framework packs and variants.
4. [ ] Publish a sample-app implementation gallery for the default, focused-override, and supported alternative-pack variants.
5. [ ] Archive temporary planning material when the stable documentation is complete.
6. [ ] Document only capabilities that have already merged and remain compatible on `staging/main` and protected `main`.
