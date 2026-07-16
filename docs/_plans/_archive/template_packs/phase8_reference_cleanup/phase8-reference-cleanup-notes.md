# Phase 8 DaisyUI Reference Cleanup Notes

## Purpose

These notes support [`phase8-reference-cleanup-plan.md`](phase8-reference-cleanup-plan.md), which implements Phase 8 of the [`template_packs-master-plan.md`](../template_packs-master-plan.md).

Phase 8 retires the temporary visible DaisyUI reference implementation now that Bootstrap supplies the accepted production-grade cross-framework proof. It is a bounded cleanup, not a redesign. The default DaisyUI pack remains the compatibility baseline, Bootstrap remains supported and opt-in, and the Phase 6 test-only fixture remains the durable proof that distinct packs can reuse one framework adapter.

## Binding Inputs

1. The stable [Template Packs contract](../../../mkdocs/template_packs/index.md) is the public pre-cleanup authority.
2. Phase 7 and its Phase 7.10 follow-up accepted Bootstrap 5 as a supported non-default production pack with shared sample, server, browser, native-form, Crispy, asset, and installed-package evidence.
3. Phase 6 established the reusable validator, shared server and browser matrices, installed-artifact harness, and reference-independent same-adapter fixture.
4. Phase 5 remains the historical explanation for the temporary reference proof, but its provisional implementation is not a supported downstream pack or permanent compatibility surface.
5. Phase 9.3 owns the complete post-cleanup authoring, packaging, publishing, customization, and testing guides. Phase 8 changes only stable wording made stale by removing the reference implementation.

## Cleanup Invariants

Phase 8 must retain:

1. Implicit default selection of the supported DaisyUI pack for unconfigured projects.
2. The permanent DaisyUI templates and `powercrud/daisyUI` 0.x compatibility façade.
3. The supported Bootstrap declaration, templates, adapters, assets, native forms, and `crispy-bootstrap5` integration.
4. Focused component overrides, model-scoped template roots, and the current whole-tree deprecation contract.
5. The stable settings-based pack-selection API and startup-only selection boundary.
6. The published portable, framework-translated, framework-specific, no-silent-ignore, and Crispy-ownership rules.
7. The reusable validator and presentation-independent shared server and browser behaviour matrices.
8. The installed wheel and sdist resource-validation harness.
9. `src/tests/test_same_adapter_template_pack.py`, `src/tests/template_pack_fixtures.py`, and `src/tests/templates/tests/template_packs/same_adapter/` as the independent same-adapter proof.

Phase 8 must not remove deprecated compatibility APIs early, add runtime or per-view switching, change Crispy ownership, redesign either supported pack, create another pack, or begin the full Phase 9.3 documentation set.

## Current Removal Map

The live `staging/main` checkout contains 46 files under the reference template namespace, including `crispy_partials.html`. Earlier handover wording described 45 templates; execution must use the current 46-file inventory and verify the namespace is absent from built artifacts.

| Proposed removal | Current surface | Retained obligation |
| --- | --- | --- |
| Reference declaration | Delete the complete `src/powercrud/packs/daisyui_reference/` tree. | Keep default DaisyUI and `powercrud.contrib.bootstrap5` declarations and stable selector resolution. |
| Reference templates | Delete the complete `src/powercrud/templates/powercrud/packs/daisyui_reference/` tree and every file beneath it. | Keep permanent DaisyUI, legacy DaisyUI façade, Bootstrap templates, focused overrides, and test-only same-adapter resources outside that tree. |
| Sample presentation settings | `src/config/settings_daisyui_reference.py` | Keep default, focused-override, and Bootstrap sample configurations over the shared application. |
| Test presentation settings | `src/tests/settings_daisyui_reference.py` | Keep default and Bootstrap settings coverage for shared matrices plus focused-override coverage where applicable. |
| Reference declaration and structure tests | `src/tests/test_daisyui_reference_template_pack.py`, `src/tests/test_daisyui_reference_list.py`, `src/tests/test_daisyui_reference_crud_shells.py` | Keep reusable validator coverage, supported-pack tests, and presentation-independent outcomes. |
| Reference browser tests | `src/tests/playwright/test_daisyui_reference_list.py`, `src/tests/playwright/test_daisyui_reference_crud_shells.py` | Keep the shared browser matrix and Bootstrap-specific lifecycle and geometry sentinels. |
| Reference sample metadata and catalogue assertions | Reference branches in `src/tests/test_sample_presentation_catalogue.py` and the two reference settings files | Preserve one shared model, route, data, permission, and view catalogue for default, focused overrides, and Bootstrap. |
| Installed-artifact selector | Reference entry in `scripts/verify_installed_template_pack_artifacts.py` | Keep isolated wheel and sdist validation for DaisyUI and Bootstrap, including their declared forms, adapters, assets, and templates. |
| Temporary stable guidance | Reference launch and status wording in `docs/mkdocs/reference/sample_app.md` and `docs/mkdocs/template_packs/index.md` | Leave a truthful post-cleanup overview and sample launch guide; defer the full multi-page guides to Phase 9.3. |

Historical Phase 3–7 planning documents are evidence of how the programme evolved. They are not active product surfaces and should not be rewritten or deleted merely because they mention the retired proof.

## Shared Files Requiring Selective Edits

The following files contain permanent coverage and must not be deleted wholesale:

1. `src/tests/test_template_pack_behaviour_matrix.py` already recognizes default DaisyUI, the reference selector, and Bootstrap. Remove the reference branch while preserving presentation-independent scenarios and explicit DaisyUI/Bootstrap selection assertions.
2. `src/tests/playwright/test_template_pack_behaviour_matrix.py` is already presentation-independent and contains a Bootstrap-specific translation assertion. Retain the scenarios and run them under default and Bootstrap settings.
3. `src/tests/test_template_pack_validation.py` must replace reference positive coverage with Bootstrap positive coverage while retaining all focused malformed-declaration checks.
4. `src/tests/test_sample_presentation_catalogue.py` mixes permanent shared-catalogue proof with reference-only imports and assertions. Retain or reshape the shared proof around default, focused overrides, and Bootstrap rather than deleting the whole module mechanically.
5. `scripts/verify_installed_template_pack_artifacts.py` must lose only the reference selector. Its isolated-environment checks, DaisyUI selector, Bootstrap selector, dependencies, resource checks, form rendering, and source-checkout rejection remain.

## Delivery And Atomicity

The planning work belongs on `template_pack/8.0`. No removal begins until Michael approves the plan.

Phase 8.1 may be delivered as an independently safe validation retarget because the reference implementation can remain present while the permanent matrix moves to DaisyUI and Bootstrap. The actual removal in Phase 8.2 is an atomic cleanup transition across package resources, sample settings, tests, the installed-artifact selector, and stable wording. Do not integrate a state that removes the declaration but leaves broken selectors, imports, settings, or documentation behind.

The Phase 8.2 cleanup must remain isolated from the accepted Phase 7 delivery evidence until focused checks pass. The complete Phase 8.3 server, browser, documentation, wheel, and sdist gates then decide whether the cleanup is acceptable for integration. Build, installation, and non-test container commands require Michael's explicit approval under repository policy when that gate is ready.

## Stop Conditions

Stop for guidance if implementation finds:

1. Any evidence that the reference pack has become a documented supported downstream selector or compatibility promise.
2. Any reference dependency inside the default DaisyUI pack, Bootstrap pack, stable selector, or reusable validator that cannot be removed without changing a public contract.
3. Any Bootstrap failure in the shared sample or behaviour matrices that requires a feature or styling redesign rather than a cleanup repair.
4. Any need to weaken or delete the independent same-adapter fixture.
5. Any need to remove deprecated compatibility APIs before their published removal version.
6. Any need to broaden Phase 8 into runtime switching, new pack APIs, Crispy ownership changes, or the Phase 9.3 documentation programme.

## Plan

### Phase 8.0: Lock The Cleanup Contract

This planning slice records the removal map, retained compatibility surfaces, selective-edit boundaries, validation gate, and stop conditions. It does not authorize deletion. Michael's approval is the final Phase 8.0 gate.

The current inventory corrects one stale count from the handover: the visible reference namespace now contains 46 templates because `crispy_partials.html` was added during later contract hardening.

### Phase 8.1: Move Permanent Cross-Pack Coverage To DaisyUI And Bootstrap

Retarget the reusable server, browser, and positive validator matrices to the two supported production packs. This is a behaviour-equivalence comparison, not an identical markup or styling comparison.

Re-run the same-adapter fixture separately. Its continued success is the required architectural proof that removing the visible reference implementation does not erase same-framework adapter reuse.

Completed on `template_pack/8.1` before reference removal. The shared server matrix, validator positives, sample catalogue, and selection assertions now target implicit DaisyUI and explicit Bootstrap. Focused evidence passed:

1. Default settings server gate: 45 passed.
2. Bootstrap settings server gate: 33 passed.
3. Default shared browser matrix: 4 passed.
4. The same-adapter fixture passed within the default server gate, and its declaration/resources remain independent of the visible reference pack.
5. The browser asset rebuild produced no tracked asset changes.

### Phase 8.2: Remove The Temporary Reference Surface

Delete the complete `src/powercrud/packs/daisyui_reference/` declaration tree and the complete `src/powercrud/templates/powercrud/packs/daisyui_reference/` template tree. Nothing inside either reference-only namespace is retained. Remove their settings, presentation metadata, direct tests, installed-artifact selector, and launch guidance at the same time. Selectively edit shared tests and stable pages so they describe only permanent supported and customization surfaces.

Keep the complete removal atomic until focused checks prove there are no stale imports, selectors, settings modules, template paths, or stable documentation claims.

Completed on `template_pack/8.1`. The full declaration and 46-file template namespace, both settings modules, five reference-only test modules, reference artifact selector, and temporary stable guidance were removed. Active source, scripts, and stable-doc scans contain no reference identifiers. Tailwind/Vite output was regenerated because removing reference templates changes the discovered DaisyUI class set; the resulting manifest and hashed DaisyUI assets are part of this cleanup.

The Bootstrap focused browser gate exposed one existing lifecycle defect while exercising the retained Bootstrap surface: repeated initialization disposed an active Tooltip and allowed Bootstrap to process a later trigger with null active state. `bootstrap5-tooltip-adapter.js` now reuses an existing Tooltip instance during initialization, preserving repeated HTMX initialization without disposing active trigger state. The complete focused Bootstrap browser set then passed 8 tests.

### Phase 8.3: Pass The Cleanup Acceptance Gate

Use focused tests first, then run the complete canonical server and Playwright gates. Because Phase 8 changes stable guidance and distributed resources, it also requires a strict MkDocs build and fresh wheel and sdist installed-resource validation.

Completed on `template_pack/8.1`.

1. Focused default server gate: 45 passed. Focused Bootstrap server gate: 33 passed. Bootstrap validator acceptance: 7 passed. The full default server gate then passed 1,008 tests with 14 skips and 89 deselections.
2. The full default Playwright gate passed 84 tests with 5 skips and 1,022 deselections. The focused Bootstrap browser lifecycle and shared-pack gate passed 8 tests. These are separate successful gates, not one combined run.
3. `uv run --extra docs mkdocs build --strict` completed successfully. MkDocs reported three pre-existing pages outside the configured nav (`guides/dependent_form_fields.md`, `guides/poweractions.md`, and `guides/powerfields.md`) but no build error.
4. `uv build` produced the wheel and sdist. `scripts/verify_installed_template_pack_artifacts.py` passed for both isolated artifacts, validating DaisyUI and Bootstrap declarations, templates, adapters, assets, native forms, and Crispy integrations.
5. Wheel, sdist, tracked-file, and active source/docs scans contain no `daisyui_reference` or `daisyui-reference` namespace. The empty filesystem directories were also removed after file deletion.

The only cleanup-exposed production repair was the Bootstrap tooltip-instance lifecycle fix recorded under Phase 8.2. No pack redesign or new API work was introduced.

### Phase 8.4: Ratify The Permanent Pack Set

Every acceptance gate passed, and Michael accepted the result for integration into `staging/main`.

Phase 8 is complete. Phase 9.3 can resume the deferred third-party authoring, publishing, customization, and testing guidance against the permanent DaisyUI and Bootstrap implementation.
