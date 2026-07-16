# Phase 9 Template-Pack Documentation Notes

## Purpose

These notes support [`phase9-contract-strategy-plan.md`](phase9-contract-strategy-plan.md). Phase 9 publishes the durable contract before Phase 8 and completes authoring guidance after Phase 8 leaves the permanent pack structure.

The completed inventory is [`phase9-documentation-inventory-audit.md`](phase9-documentation-inventory-audit.md).

## Decisions

1. DaisyUI is the supported default and compatibility baseline.
2. Bootstrap is a supported production pack but is not the default.
3. Template Packs receives its own top-level documentation section.
4. Semantic APIs are portable and translated by each supported pack.
5. Raw class values are selected-framework inputs and are not translated.
6. Supported packs must not silently ignore accepted configuration.
7. Crispy selection remains controlled by the downstream application.
8. Public docs classify product support, not internal test-coverage gaps.
9. Broad parity belongs in server tests; Playwright covers browser lifecycle and geometry; distributed packs require installed-resource validation.
10. Focused overrides are the supported application-customization route.
11. Plain-app DaisyUI whole-tree copying remains usable during 0.x but is deprecated for removal in v1.0. Bootstrap and future packs need not support it; complete ownership belongs in a custom pack.

## Pre-Phase-8 Completion Gate

Phase 8 may begin only after:

1. the DaisyUI whole-tree command warns about v1.0 removal and has focused test coverage;
2. the top-level Template Packs section states the supported-pack strategy and API matrix;
3. stable docs state the no-silent-ignore, Crispy, deprecation, and validation rules;
4. affected references link to one authoritative contract; and
5. the changed behaviour and documentation have been validated.

The deprecated command scope is only plain-app whole-tree copying such as `pcrud_mktemplate myapp --all`. Model-scoped copying and focused `--component` overrides remain supported.

## Plan

### Phase 9.1: Establish The Documentation Contract

Complete. The inventory records the stable pages and documentation gaps. Michael then settled the supported-pack, navigation, API, Crispy, validation, and whole-tree-copy decisions listed above.

### Phase 9.2: Publish The Pre-Cleanup Contract

Complete. The plain-app DaisyUI whole-tree command now emits `FutureWarning` for its v1.0 removal. The authoritative top-level Template Packs section publishes selection, support, API-classification, Crispy, customization, and validation rules, with relevant stable pages linking back to it. It does not remove the temporary pack or finalize paths that Phase 8 will change.

Validation passed: the focused management-command and pack tests passed 83 tests; the strict MkDocs build passed; and the complete `./runtests` gate passed 1,018 tests with 13 skips and 91 Playwright deselections. The published contract is the basis for Phase 8 removal mapping.

### Phase 9.3: Complete Post-Cleanup Template-Pack Documentation

The existing page is deliberately the pre-cleanup contract overview, not the finished documentation set. After Phase 8 leaves permanent paths and fixtures, Template Packs becomes a multi-page section with:

1. the cleaned-up overview and supported-pack contract;
2. a user guide for selecting and configuring DaisyUI or Bootstrap;
3. a customization guide for focused overrides, model roots, and custom-pack ownership;
4. a definitive third-party guide to creating, packaging, and publishing a template pack; and
5. a testing and acceptance guide for pack maintainers.

The publishing guide should serve the same practical purpose as established template-pack author guides in the Django ecosystem. It must take a maintainer from an empty distributable package to a selectable PowerCRUD pack, covering package layout, declaration and namespace, required roots and fragments, reusable or pack-specific adapters, assets, capabilities, native and Crispy form integration, settings-based selection, packaging metadata, and installed-package resources.

The testing guide must distinguish shared product parity from framework-specific presentation evidence. It covers declaration validation, shared server behaviour, pack-specific sentinels and translation tests, targeted Playwright coverage for browser lifecycle and geometry risks, and clean wheel/sdist validation. Final sample and reference pages link into this section rather than duplicating the governing contract.
