# Phase 6 Reusable Pack Validation Plan

## Status

Phase 6 is complete on `template_pack/6.6` and ready to integrate into `staging/main`. The compatible default DaisyUI experience remains the selected default.

## Next

Begin Phase 7 only as a separately authorized Bootstrap 5 implementation programme using the reusable Phase 6 gates.

## Phase 6.0: Lock The Consolidation Contract

1. [x] Keep Phase 6 limited to reusable validation, shared behaviour gates, installed-resource proof, and the durable same-adapter fixture.
2. [x] Keep runtime pack selection lightweight and leave Bootstrap implementation, Bootstrap assets, and Bootstrap adapter loading to Phase 7.
3. [x] Reuse the accepted Phase 4 and Phase 5 compatibility evidence instead of repeating their complete application and asset-mode programmes.
4. [x] Divide the work into bounded numbered slices that leave the compatible default DaisyUI experience unchanged.
5. [x] Preserve the existing Phase 6 roadmap commits, add one child-plan commit for Phase 6.0, and require one semantic commit for each later `6.x` subphase.
6. [x] Keep the validator extensible for Bootstrap without adding a speculative public registry or selecting an unavailable adapter.

## Phase 6.1: Add The Reusable Pack Validator

1. [x] Add one development and CI validator that accepts a resolved `TemplatePack` declaration without changing request-time selection.
2. [x] Validate contract version, capability vocabulary and dependencies, adapter declarations, form declarations, and asset declarations.
3. [x] Validate required baseline and capability-dependent templates through declared package resources and Django template loading.
4. [x] Validate server-addressable named fragments required by each declared capability.
5. [x] Validate native and crispy form requirements and declared manual-static and Vite resources where applicable.
6. [x] Report actionable failures that identify the pack, declaration field, capability, or missing resource.
7. [x] Prove the default and reference packs pass while focused malformed fixtures fail for the intended reasons.
8. [x] Keep capability and resource contracts data-driven so Phase 7 can extend them without rewriting the validator around Bootstrap.

## Phase 6.2: Establish The Shared Server Behaviour Matrix

1. [x] Create one presentation-independent server matrix that runs the same sample scenarios under default and reference settings.
2. [x] Select applicable scenarios from declared capabilities rather than pack identity.
3. [x] Cover list and HTMX rendering, filters, sorting, pagination, columns, favourites, row actions, bulk, async, inline, form, detail, delete, and modal outcomes where declared.
4. [x] Cover native forms and each declared crispy integration through the same reusable form assertions.
5. [x] Assert shared routes, models, data, permissions, requests, and outcomes without requiring identical presentation markup.
6. [x] Retain only genuinely presentation-specific structural tests outside the shared matrix.

## Phase 6.3: Establish The Shared Browser Behaviour Matrix

1. [x] Create one reusable browser matrix that runs the same high-value sample flows in separate default and reference settings processes.
2. [x] Cover representative list and HTMX navigation, filters, pagination, columns, favourites, row actions, modal CRUD, bulk, inline, detail, and delete behaviour where declared.
3. [x] Verify repeated initialization, teardown-sensitive interactions, the stable public runtime entry, and the absence of browser errors.
4. [x] Reuse the existing manual-static and Vite evidence except where a changed validation path requires a focused loading check.
5. [x] Keep the matrix presentation-independent so Bootstrap can join it after reaching Phase 7 parity.
6. [x] Avoid running the complete existing browser suite once per pack merely to restate Phase 4 and Phase 5 evidence.

## Phase 6.4: Preserve A Durable Same-Adapter Fixture

1. [x] Add a small test-only pack declaration and minimum valid template resources outside the visible sample catalogue.
2. [x] Reuse the standard DaisyUI framework adapter while declaring no variant adapter or additional assets.
3. [x] Prove two distinct pack identities can share one framework adapter without copied functional JavaScript.
4. [x] Run the fixture through the reusable validator and focused resolution checks.
5. [x] Keep the fixture independent of the reference declaration, reference namespace, reference settings, and reference-specific tests.
6. [x] Confirm Phase 8 can remove the visible reference implementation without deleting the same-adapter proof.

## Phase 6.5: Add The Installed-Resource Gate

1. [x] Add one repeatable clean-install harness for built wheel and sdist artifacts.
2. [x] Install each artifact into an isolated environment that cannot import package resources from the source checkout.
3. [x] Resolve and validate the co-distributed default and reference declarations from each installed artifact.
4. [x] Prove declared templates, named fragments, form resources, adapters, and assets remain discoverable after installation.
5. [x] Keep this gate limited to installed declaration and resource usability rather than repeating full sample application or browser suites.
6. [x] Record commands and results in the Phase 6 notes so Phase 7 can add Bootstrap to the same gate.

## Phase 6.6: Pass The Phase Gate And Ratify

1. [x] Run the focused validator tests for passing packs and malformed fixtures.
2. [x] Run the shared server and browser matrices under default and reference settings.
3. [x] Run the durable same-adapter fixture checks.
4. [x] Run the clean wheel and sdist installed-resource gate with explicit approval for build and installation commands.
5. [x] Assess broader regression and generated-asset rebuilds; neither is justified because Phase 6 changed neither the shipped runtime nor generated asset inputs.
6. [x] Reconcile the child plan, child notes, master plan, and master notes with the accepted evidence.
7. [x] Mark Master Phase 6 complete after every reusable gate passes while retaining the compatible default DaisyUI experience.
8. [x] Retire each completed Phase 6 implementation branch after its accepted integration into `staging/main`.
