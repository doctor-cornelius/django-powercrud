# Phase 9 Template-Pack Documentation Plan

## Status

Complete — 2026-07-16. The permanent five-page documentation, downstream override tooling, and current authoring boundary are published. The newly identified requirement for independently supplied framework adapters is transferred to Phase 10 rather than being hidden inside documentation work.

## Next

Proceed to Phase 10 planning. Retain these Phase 9 records until Michael explicitly approves archival.

## Phase 9.1: Establish The Documentation Contract

1. [x] Read the relevant stable documentation and Phase 7.10 evidence without editing implementation or documentation.
2. [x] Record the gaps and proposed documentation shape in [`phase9-documentation-inventory-audit.md`](phase9-documentation-inventory-audit.md).
3. [x] Settle the supported-pack, API-classification, unsupported-setting, Crispy, validation, navigation, and whole-tree-copy decisions.

## Phase 9.2: Publish The Pre-Cleanup Contract

1. [x] Deprecate plain-app DaisyUI whole-tree copying, emit and test its v1.0 removal warning, and leave model-scoped and focused copying supported.
2. [x] Add a top-level Template Packs documentation section covering the supported default DaisyUI pack, supported non-default Bootstrap pack, selection, architecture, and customization routes.
3. [x] Publish the portable, framework-translated, framework-specific, unsupported-setting, Crispy-ownership, and supported-pack validation rules without exposing internal verification gaps as product statuses.
4. [x] Reconcile the configuration, setup, styling, forms, customization, management-command, deprecation, testing, sample, and reference links with the authoritative contract.
5. [x] Validate the changed behaviour and documentation, then hand the accepted contract to Phase 8 planning.

## Phase 9.3.1: Verify The Post-Cleanup Documentation Facts

1. [x] Check the permanent DaisyUI and Bootstrap configuration, customization, authoring, packaging, and validation facts needed by the public guides.
2. [x] Identify stale or duplicated stable guidance, including any remaining active reference-pack wording.

## Phase 9.3.2: Write And Reconcile The Final Documentation

1. [x] Retain `template_packs/index.md` as the cleaned-up overview and supported-pack contract.
2. [x] Add `selecting-and-configuring.md` for supported DaisyUI and Bootstrap application setup.
3. [x] Add `customising.md` for focused, model-scoped, project-root, and asset ownership.
4. [x] Add `authoring-and-publishing.md` as a truthful statement of the current narrow authoring boundary, pending Phase 10's real external framework API.
5. [x] Add `testing-and-acceptance.md` for current pack validation and release evidence.
6. [x] Reconcile existing configuration, reference, and sample guidance with the five-page section.

## Phase 9.3.3: Validate And Finish

1. [x] Check terminology, examples, navigation, links, and retired-reference cleanup across the stable documentation.
2. [x] Pass focused implementation tests and the normal full regression gate; leave local MkDocs rendering to Michael as instructed.
3. [x] Reconcile the Phase 9 and master planning material after acceptance; retain it until explicit archive approval.

## Phase 9.4: Add Application-Owned Pack Assets

1. [x] Add app-level `pcrud_mktemplate --assets` copying for the supported DaisyUI and Bootstrap manual-static runtime trees.
2. [x] Preserve runtime contracts and existing package manual/Vite loading while rejecting model-scoped asset copies.
3. [x] Document snapshot ownership, activation, no-fallback behaviour, and the Vite boundary.
4. [x] Pass focused command/asset tests and the standard regression gate.

## Phase 9.5: Clarify Override Layers And Project Root Selection

1. [x] Allow a plain app target to copy one selected root template from the supported source pack.
2. [x] Preserve app-level template fallback and independent asset-copy behaviour.
3. [x] Document the override layers and concise project-command choices where developers make customization decisions.
4. [x] Pass focused command tests and the standard regression gate.
