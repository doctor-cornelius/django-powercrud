# Phase 8 DaisyUI Reference Cleanup Plan

## Status

Complete and accepted for integration into `staging/main`. The temporary reference pack and its empty directories are removed, and the acceptance evidence is recorded below.

## Next

Resume Phase 9.3 authoring, publishing, customization, and testing guidance against the permanent DaisyUI and Bootstrap pack set.

## Phase 8.0: Lock The Cleanup Contract

1. [x] Confirm Bootstrap 5 is an accepted supported non-default production pack and the permanent cross-framework comparison target.
2. [x] Confirm the pre-cleanup documentation gate published the compatibility, API, Crispy, customization, and supported-pack validation rules that removal must preserve.
3. [x] Map the reference-only declaration, templates, settings, sample metadata, launch guidance, tests, and installed-artifact selector proposed for removal.
4. [x] Map shared files that require selective edits rather than deletion.
5. [x] Map the default DaisyUI, legacy façade, Bootstrap, focused-override, validator, same-adapter, shared-matrix, and installed-artifact surfaces that must remain.
6. [x] Obtain Michael's approval before implementation or deletion begins.

## Phase 8.1: Move Permanent Cross-Pack Coverage To DaisyUI And Bootstrap

1. [x] Run the shared server behaviour matrix under default DaisyUI and Bootstrap settings only.
2. [x] Run the shared browser behaviour matrix under default DaisyUI settings; retain the same matrix for the Bootstrap gate after cleanup.
3. [x] Make reusable validator acceptance coverage compare the two supported production packs without weakening malformed-pack coverage.
4. [x] Confirm Bootstrap's shared sample, native-form, Crispy, asset, and browser-lifecycle coverage remains intact.
5. [x] Re-run the independent test-only same-adapter fixture and confirm it has no reference-pack dependency.

## Phase 8.2: Remove The Temporary Reference Surface

1. [x] Delete `src/powercrud/packs/daisyui_reference/` and the entire `src/powercrud/templates/powercrud/packs/daisyui_reference/` tree with no retained files inside either reference-only namespace.
2. [x] Remove the sample and test settings, presentation label, catalogue entry, and launch command that expose the reference presentation.
3. [x] Remove server and browser tests whose only purpose is validating the visible reference implementation.
4. [x] Selectively revise shared catalogue, validator, and behaviour tests while retaining their permanent default, focused-override, and Bootstrap obligations.
5. [x] Remove the reference selector from the installed-artifact harness while retaining DaisyUI and Bootstrap resource validation.
6. [x] Remove temporary reference wording from stable Template Packs and sample-app guidance without starting the deferred Phase 9.3 authoring guides.
7. [x] Keep the cleanup atomic until the focused compatibility gate passes.

## Phase 8.3: Pass The Cleanup Acceptance Gate

1. [x] Run focused declaration, selection, shared-matrix, same-adapter, sample-presentation, forms, and Bootstrap tests.
2. [x] Run the complete canonical server regression gate.
3. [x] Run the complete Playwright regression gate, including default DaisyUI and Bootstrap shared behaviour coverage.
4. [x] Run a strict MkDocs build for the changed stable guidance.
5. [x] Build clean wheel and sdist artifacts and prove installed DaisyUI and Bootstrap declarations, templates, adapters, assets, native forms, and Crispy integrations from isolated `site-packages` environments.
6. [x] Confirm the built artifacts contain no reference declaration or template namespace.
7. [x] Fix only defects caused or exposed by the cleanup; do not broaden Phase 8 into pack redesign or new API work.

## Phase 8.4: Ratify The Permanent Pack Set

1. [x] Record the focused, server, browser, documentation, wheel, and sdist evidence in the Phase 8 notes.
2. [x] Confirm DaisyUI remains the supported default and Bootstrap remains the supported non-default production pack.
3. [x] Confirm focused overrides, model-scoped copying, the legacy DaisyUI façade, stable selection, native forms, and supported Crispy paths remain available.
4. [x] Confirm the validator, shared behaviour matrices, installed-artifact harness, and same-adapter fixture remain reusable for future third-party packs.
5. [x] Reconcile the Phase 8 child plan, child notes, master plan, master notes, and Phase 9 handoff.
6. [x] Mark Master Phase 8 complete only after Michael accepts the cleanup evidence.
7. [x] Hand the permanent post-cleanup implementation to Phase 9.3 for the full authoring, publishing, customization, and testing guides.
