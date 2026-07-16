# Template Packs Master Plan

## Status

Active. Phases 0–2 are complete. Phase 3 is next. Every phase must keep the default DaisyUI experience working on `main`.

## Next

Await direction before creating the Phase 3 child plan or beginning reusable JavaScript adapter extraction.

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

1. [ ] Keep durable PowerCRUD semantics in core JavaScript.
2. [ ] Extract reusable framework behaviour into a DaisyUI adapter.
3. [ ] Support optional variant behaviour without copying core or framework JavaScript.
4. [ ] Preserve repeatable initialization, teardown, and stable runtime loading contracts.
5. [ ] Keep the compatible DaisyUI adapter automatically wired after every merged extraction slice.

## Phase 4: Package And Select The Default DaisyUI Pack

1. [ ] Package the characterized current implementation as the compatible default DaisyUI pack.
2. [ ] Add pack selection, composition, discovery, and configuration errors.
3. [ ] Preserve approved legacy settings and template paths.
4. [ ] Verify manual-static and bundled/Vite integrations.
5. [ ] Merge repackaging only when the default pack, compatibility paths, distribution artifacts, and both loading modes work together.

## Phase 5: Prove Reuse With A DaisyUI Variant

1. [ ] Build a visibly different internal DaisyUI reference variant.
2. [ ] Reuse the standard DaisyUI framework adapter without copying it.
3. [ ] Use optional variant JavaScript only where stable hooks cannot support the interaction.
4. [ ] Refine the contracts from the reference-variant findings.
5. [ ] Keep the reference variant opt-in so merging it cannot change the default experience.

## Phase 6: Complete Validation

1. [ ] Add template-pack contract and capability validation.
2. [ ] Validate wheel and sdist contents from clean installations.
3. [ ] Validate manual-static and bundled/Vite asset modes.
4. [ ] Run shared unit and browser behaviour across the default pack and reference variant.
5. [ ] Merge validation improvements progressively as reusable gates for later slices.

## Phase 7: Dogfood The Framework Boundary With Bootstrap 5

1. [ ] Build an optional co-distributed contrib-style Bootstrap 5 framework adapter and template pack.
2. [ ] Deliver full CRUD feature parity through the shared contracts, including a maintained crispy-Bootstrap integration.
3. [ ] Refine the contracts from cross-framework findings.
4. [ ] Decide separately whether Bootstrap becomes a supported production pack after the full-parity dogfood.
5. [ ] Keep Bootstrap optional so merging it cannot affect unconfigured projects.

## Phase 8: Promote Stable Documentation

1. [ ] Document downstream focused template overrides.
2. [ ] Document pack selection, composition, adapters, assets, forms, and validation.
3. [ ] Publish author guidance for framework packs and variants.
4. [ ] Archive temporary planning material when the stable documentation is complete.
5. [ ] Document only capabilities that have already merged and remain compatible on `main`.
