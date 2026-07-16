# Phase 9 Template-Pack Documentation Plan

## Status

The pre-cleanup contract is published and validated, and Phase 8 has retired the temporary DaisyUI reference pack. DaisyUI remains the supported default; Bootstrap is a supported non-default pack. The plain-app DaisyUI whole-tree copy is deprecated for v1.0 removal; model-scoped and focused copying remain supported.

## Next

Resume Phase 9.3 against the accepted permanent DaisyUI and Bootstrap implementation.

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

## Phase 9.3: Complete Post-Cleanup Template-Pack Documentation

1. [ ] Remove or revise stable guidance that referred to the retired temporary reference pack, and retain the current Template Packs page as the cleaned-up contract overview.
2. [ ] Add a page for selecting and configuring the supported DaisyUI and Bootstrap packs, including assets, forms, Crispy ownership, and startup-only selection.
3. [ ] Add a page for customizing an existing pack through focused overrides, model-scoped roots, and explicitly owned custom packs.
4. [ ] Publish a definitive third-party authoring and publishing guide covering package structure, declarations, namespaces, templates and fragments, adapters, assets, capabilities, form integrations, selection, and distribution metadata.
5. [ ] Add a dedicated testing and acceptance guide covering declaration validation, shared server behaviour, pack-specific tests, targeted Playwright coverage, and installed wheel/sdist resource validation.
6. [ ] Reconcile the final default, focused-override, Bootstrap, configuration, reference, and sample guidance with the new multi-page section.
7. [ ] Validate the complete stable documentation and update or archive planning material only after acceptance.
