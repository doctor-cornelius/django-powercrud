# Template Packs Plan

## Status

The archived template-pack proposal has been promoted into an active planning folder. Phase 1 is treated as conceptually complete from the source proposal, but it should be refreshed against current code before implementation starts.

## Next

1. Refresh the Phase 1 contract against the current templates, runtime JS, CSS assets, and packaging layout.
2. Decide the first implementation slice for the core-vs-pack JavaScript split.
3. Confirm whether DaisyUI moves into a separate Django app immediately or whether a compatibility bridge is needed first.

## Source

This plan is based on [`docs/archive/blog/posts/20251120_template_packs.md`](../../archive/blog/posts/20251120_template_packs.md). The archived post remains the source evidence for the original reasoning; this folder is the active engineering plan.

## Phase 1: Define Template And JavaScript Contract

1. [x] Inventory existing templates, partials, context variables, HTMX snippets, and `partialdef` usage.
2. [x] Review the current template architecture.
    1. [x] Compare inline `partialdef` blocks against separate partial files.
    2. [x] Identify how filters and sub-components are structured.
    3. [x] Assess how understandable the structure is for future template-pack authors.
3. [x] Evaluate `HtmxMixin.get_framework_styles`.
    1. [x] Identify current DaisyUI-specific style data.
    2. [x] Identify call sites in filtering and template tags.
    3. [x] Decide how template-pack modularisation should consume style data.
4. [x] Decide the standard structure for template packs.
    1. [x] Define required templates.
    2. [x] Define required blocks and partials.
    3. [x] Decide which pieces stay inline and which become dedicated partial files.
    4. [x] Define naming conventions.
5. [x] Specify the JavaScript API.
    1. [x] Define `initPowercrud(fragment)` as the core initializer.
    2. [x] Define `initPowercrudPack(fragment)` as the optional pack initializer.
    3. [x] Define expected custom events and hooks.
6. [x] Decide template-pack packaging and discovery strategy.
    1. [x] Define pack app naming conventions.
    2. [x] Define template and static asset layout.
    3. [x] Define styles module expectations.

## Phase 2: Implement Core Versus Template-Pack JavaScript Split

1. [ ] Move core runtime behavior into `powercrud/static/powercrud/powercrud.js`.
    1. [ ] Expose `window.initPowercrud(fragment)`.
    2. [ ] Ensure the initializer is idempotent for full-page loads and HTMX swaps.
    3. [ ] Keep global event registration guarded so listeners are not duplicated.
2. [ ] Update the real base-template contract for loading core JS once.
    1. [ ] Document the expected `{% static 'powercrud/powercrud.js' %}` include.
    2. [ ] Preserve downstream ownership of the actual site base template.
3. [ ] Remove inline scripts from swapped fragments.
    1. [ ] Replace fragment-local script execution with HTMX lifecycle initialization.
    2. [ ] Prefer a single global `htmx:load` listener in core runtime if practical.
    3. [ ] Keep template-level `hx-on` wiring only if the global listener proves too broad.
4. [ ] Extract DaisyUI-specific runtime behavior into pack JS.
    1. [ ] Create `powercrud_daisyui/static/powercrud_daisyui/daisyui.js`.
    2. [ ] Expose `window.initPowercrudPack(fragment)`.
    3. [ ] Keep pack JS responsible for framework-specific modal, tooltip, toast, and visual embellishment behavior.
5. [ ] Decide initializer orchestration.
    1. [ ] Confirm whether core calls `initPowercrudPack` when present.
    2. [ ] Confirm whether fragments explicitly call both initializers.
    3. [ ] Preserve the contract that core initialization runs before pack initialization.

## Phase 3: Turn DaisyUI Into The First Template Pack

1. [ ] Move DaisyUI templates into a `powercrud_daisyui` template namespace.
2. [ ] Update `{% extends %}`, `{% include %}`, and partial references to use the template-pack contract.
3. [ ] Remove DaisyUI-specific markup from core templates.
    1. [ ] Keep core templates framework-neutral.
    2. [ ] Keep visual classes and visual behavior in the pack.
4. [ ] Verify the DaisyUI pack conforms to the contract.
    1. [ ] Required orchestrator templates exist.
    2. [ ] Required partial templates exist.
    3. [ ] Required partial definitions exist where core depends on them.
    4. [ ] Required context variables are still consumed correctly.
5. [ ] Refactor `get_framework_styles` according to the pack-style strategy.
    1. [ ] Move DaisyUI style data into `powercrud_daisyui.styles`.
    2. [ ] Delegate core style lookup through pack helper functions.
    3. [ ] Preserve a compatibility path for current configuration where feasible.

## Phase 4: Add Template-Pack Selection And Discovery

1. [ ] Introduce `POWERCRUD_TEMPLATE_PACK`, defaulting to DaisyUI.
2. [ ] Implement loader helpers.
    1. [ ] Resolve the active pack name.
    2. [ ] Resolve the pack app label.
    3. [ ] Resolve the template prefix.
    4. [ ] Resolve pack styles.
    5. [ ] Resolve pack JS and CSS asset paths.
3. [ ] Add clear configuration errors.
    1. [ ] Raise when a configured pack cannot be imported.
    2. [ ] Raise when a configured pack app is not in `INSTALLED_APPS`.
    3. [ ] Explain the required app and setting in the error.
4. [ ] Load active pack assets explicitly.
    1. [ ] Load core JS.
    2. [ ] Load active pack JS.
    3. [ ] Load active pack CSS helpers if the pack ships any.

## Phase 5: Build And Extend Tests

1. [ ] Add unit tests for required templates and blocks.
2. [ ] Add pack-contract tests.
    1. [ ] Check required orchestrator templates.
    2. [ ] Check required partial templates.
    3. [ ] Check required `partialdef` names where applicable.
    4. [ ] Check required `PACK_STYLES` sections.
3. [ ] Add focused browser coverage.
    1. [ ] Cover at least CRUD list and form for the default pack.
    2. [ ] Verify HTMX lifecycle initialization.
    3. [ ] Verify visual wiring that depends on pack JS.
4. [ ] Implement `validate_template_pack()`.
    1. [ ] Verify pack importability and `INSTALLED_APPS` presence.
    2. [ ] Verify template availability.
    3. [ ] Verify required style module content.
    4. [ ] Provide an optional management-command wrapper if useful.
5. [ ] Document testing expectations for template-pack authors.
    1. [ ] State which central PowerCRUD tests pack authors should run.
    2. [ ] State when to use `validate_template_pack()`.
    3. [ ] State when pack authors should add pack-specific tests.

## Phase 6: Documentation And Cookbook

1. [ ] Update public docs to explain template packs.
    1. [ ] Explain the pack contract.
    2. [ ] Explain how to switch packs.
    3. [ ] Explain required `INSTALLED_APPS` and settings.
2. [ ] Write a template-pack author cookbook.
    1. [ ] Show the expected Django app structure.
    2. [ ] Show the JS structure with core and pack initializers.
    3. [ ] Show style module structure.
    4. [ ] Show Playwright and contract-test patterns.
3. [ ] Promote only stable content into `docs/mkdocs/`.
    1. [ ] Keep experimental rationale in this plan folder until settled.
    2. [ ] Archive this folder only after the stable docs are promoted.

## Phase 7: Dogfood With Bootstrap 5

1. [ ] Implement a minimal Bootstrap 5 pack using the same contract as DaisyUI.
2. [ ] Use the Bootstrap 5 pack to expose contract gaps.
    1. [ ] Fix missing hooks.
    2. [ ] Fix leaky DaisyUI assumptions.
    3. [ ] Update the contract based on real findings.
3. [ ] Decide whether Bootstrap 5 becomes production-ready in this phase.
    1. [ ] If yes, cover lists, forms, filters, modals, bulk actions, and inline editing.
    2. [ ] If no, defer production hardening to a follow-up phase.
4. [ ] Add Bootstrap 5 tests and docs if it becomes an official pack.
5. [ ] Update the cookbook based on Bootstrap dogfooding.

