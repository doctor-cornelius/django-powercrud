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

### Phase 9.3.1: Verify The Post-Cleanup Documentation Facts

Complete. The read-only audit is recorded in [`phase9-post-cleanup-documentation-facts-audit.md`](phase9-post-cleanup-documentation-facts-audit.md). It confirms the permanent DaisyUI and Bootstrap declarations, startup-only selection boundary, manual/Vite assets, native/Crispy ownership, focused/model-scoped customization, legacy façade, whole-tree deprecation, reusable validator, shared server/browser matrices, and installed wheel/sdist harness.

The audit identifies the accepted five-page section as the next documentation source of truth and records stale or duplicated active wording in getting started, styling, configuration, management-command, customization, inline-editing, and testing pages. No active `daisyui-reference` residue remains. It also records the current third-party authoring boundary: module-path declarations may reuse shipped adapter/Crispy identities, but arbitrary new framework/variant adapters and a generic third-party artifact harness are not current public APIs.

The sample application retains three presentation examples over one shared application: default DaisyUI, standard DaisyUI with four focused Book overrides, and Bootstrap. The focused presentation is an application-level customization example, not another template pack. Phase 8 removed only the temporary selectable DaisyUI reference pack.

### Phase 9.3.2: Write And Reconcile The Final Documentation

The accepted top-level documentation structure is:

```text
docs/mkdocs/template_packs/
├── index.md
├── selecting-and-configuring.md
├── customising.md
├── authoring-and-publishing.md
└── testing-and-acceptance.md
```

Page ownership is:

1. `index.md` owns the overview, terminology, supported-pack contract, startup-only selection boundary, API classifications, Crispy ownership, and customization routes.
2. `selecting-and-configuring.md` owns application setup for DaisyUI and Bootstrap, including assets, native forms, Crispy, and settings-based selection.
3. `customising.md` owns focused overrides, model-scoped roots, explicit template ownership, and the whole-tree-copy deprecation boundary.
4. `authoring-and-publishing.md` takes a third-party maintainer from an empty distributable package to a selectable published pack, including declarations, namespaces, templates, fragments, adapters, capabilities, assets, forms, and package metadata.
5. `testing-and-acceptance.md` owns declaration validation, shared server behaviour, pack-specific sentinels, targeted Playwright coverage, and isolated wheel/sdist resource validation.

Existing configuration and reference pages remain detailed authorities for their own APIs and link to this section instead of duplicating its contract. The existing sample-app page remains the implementation gallery for default DaisyUI, focused overrides, and Bootstrap; it is not a sixth Template Packs contract page.

### Phase 9.3.3: Validate And Finish

Complete. The section was reconciled as one user journey, and the later Phase 9.4 and 9.5 slices added project-owned asset snapshots, one-root project copies, and an override-layer overview. The final focused command and asset-packaging gate passed 79 tests. One uninterrupted full regression passed 1,024 non-Playwright tests with 14 skips, followed by 84 Playwright tests with 5 skips. Michael retained local MkDocs rendering and visual review for his own handoff workflow, so no local MkDocs build is claimed.

The authoring discussion then established that independently supplied new-framework adapters are a fundamental product requirement rather than optional future polish. That architectural work is transferred to the dedicated Phase 10 plan. Phase 9 is complete as documentation of the current shipped boundary; its authoring page must be replaced with a practical external-author guide when Phase 10 makes that workflow real.

### Phase 9.4: Add Application-Owned Pack Assets

The command gains one opt-in plain-app `--assets` flag. It remains independent of template scope: no scope copies four root templates, `--all` copies the complete template tree, and `--assets` adds the selected pack's PowerCRUD-owned manual-static CSS and JavaScript snapshot. `--all --assets` is the explicit complete template-and-asset ownership choice; no `--both` flag is needed.

The snapshot lives under `<app>/static/<app>/powercrud/`. DaisyUI receives the shared runtime and stylesheet. Bootstrap receives that same shared tree plus its contrib stylesheet, entry, and private adapters, preserving the existing relative imports. Third-party vendor dependencies stay application-owned. The base template must replace, not add alongside, the package-owned PowerCRUD asset entry because the duplicate-load guard makes the first entry decisive.

Snapshots have no file-by-file fallback. They are application and selected-pack scoped because the base template loads them; `app.Model`, role, and focused-component operations reject `--assets`. Existing model-specific templates remain valid with either a package-owned or application-owned runtime. The first release intentionally supports manual-static only: it does not infer or modify downstream Vite configuration, and users must not combine the snapshot with the packaged Vite entry.

Focused tests should prove copied directories and files, Bootstrap's preserved shared-runtime import, output activation guidance, destination overwrite/retention, and model-operation rejection. Existing runtime packaging tests continue to establish that the copied source files are package-owned resources. No browser test is needed unless static-path inspection finds a real ambiguity.

### Phase 9.5: Clarify Override Layers And Project Root Selection

Plain-app copying should offer the same root-template precision already available for a model: list, detail, form, or delete. The selected file belongs below the existing pack-identified project root, so views with `template_override_path` use it while every missing root, component, and nested template continues to fall back to the selected pack. The option remains independent of `--assets`.

The customisation page needs to start with a plain-English map of the allowed layers: one focused component for a model, one or all roots for a model, an explicit candidate for one view, one or all roots for a configured project root, a complete project pack, and application/pack-level runtime assets. The project-pack section should provide an initially collapsed choices table and defer detailed command reference material to Management Commands.
