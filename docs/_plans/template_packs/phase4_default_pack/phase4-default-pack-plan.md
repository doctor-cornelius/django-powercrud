# Phase 4 Default DaisyUI Pack Plan

## Status

Complete. `template_pack/4.4` was squash-integrated into `staging/main` as `c792c7f5` and retired. The staged namespace approach now selects the permanent `powercrud/packs/daisyui` source while retaining `powercrud/daisyUI` 0.x compatibility facades.

## Next

Begin Phase 5 only when its reference-variant and shared sample-catalogue work is authorized.

## Phase 4.0: Confirm Evidence And The Implementation Contract

1. [x] Run one fresh read-only sub-agent audit of settings, template resolution, styles, copy workflows, package layout, and distribution compatibility.
2. [x] Run one fresh read-only sub-agent audit of runtime composition, manual-static and Vite assets, existing tests, and genuine coverage gaps.
3. [x] Require both audits to confirm or disprove the recorded Phase 4 hypotheses without editing files or proposing competing plans.
4. [x] Reconcile both audits against the Phase 1 contracts and completed Phase 2–3 implementation evidence.
5. [x] Lock `POWERCRUD_SETTINGS["POWERCRUD_TEMPLATE_PACK"]`, the `daisyui` built-in identity, `module.path:attribute` third-party declarations, and the minimum declaration contract.
6. [x] Keep per-view pack selection out of Phase 4; retain explicit `templates_path` as the supported per-view custom-template mechanism.
7. [x] Name the `powercrud/daisyUI` to `powercrud/packs/daisyui` relocation as the exact atomic default-pack transition.
8. [x] Record the numbered branch sequence and stop conditions before implementation begins.

## Phase 4.1: Introduce Dormant Pack Identity And Discovery

1. [x] Add the smallest internal pack representation proved by Phase 4.0.
2. [x] Represent the compatible built-in DaisyUI pack inside the existing `powercrud` application with its contract version, current `powercrud/daisyUI` namespace, adapters, capabilities, form support, and assets.
3. [x] Add identity and discovery helpers without changing current default template or runtime resolution, caching, or class-import behaviour.
4. [x] Add lightweight identity, import, contract-version, and unavailable-pack configuration errors.
5. [x] Characterize and verify the dormant infrastructure before independent integration.

## Phase 4.2: Add Compatible Selection And Template Resolution

1. [x] Add the ratified pack-selection configuration separately from legacy `POWERCRUD_CSS_FRAMEWORK`.
2. [x] Automatically select the compatible DaisyUI pack when no new selector is configured.
3. [x] Preserve explicit `template_name`, app/model convention, per-view `templates_path`, and legacy global-setting precedence.
4. [x] Resolve generic roots, focused components, direct fragments, template-tag styles, and copy-command sources through the selected pack where the ratified contract requires it.
5. [x] Keep existing `powercrud/daisyUI/...` names and every server-addressable legacy fragment usable through the approved 0.x compatibility period.
6. [x] Add focused configuration and resolution tests without activating the physical default-pack move.
7. [x] Run the full non-Playwright regression as the compatible pack-resolution checkpoint.
8. [x] Integrate only if default rendering and all legacy resolution paths remain unchanged while `powercrud/daisyUI` remains the active implementation namespace.

## Phase 4.3: Add Compatible Runtime And Asset Composition

1. [x] Compose the supported `daisyui` framework adapter with no variant through the stable `powercrud/js/powercrud.js` entry.
2. [x] Keep the compatible DaisyUI adapters automatically selected with no new script tag, installed app, or setting for existing users.
3. [x] Preserve public globals, semantic hooks, lifecycle ordering, teardown, and repeated HTMX initialization.
4. [x] Preserve manual-static and bundled/Vite loading; record that the built-in pack declares no additional assets and reject unsupported adapter or asset declarations clearly.
5. [x] Avoid duplicate vendor loading and keep downstream base-template ownership unchanged.
6. [x] Add or strengthen only the behavioural and loading tests needed for the selected-pack composition boundary.
7. [x] Integrate only infrastructure that leaves the current default runtime path fully compatible.

## Phase 4.4: Build The Atomic Default-Pack Transition

1. [x] Begin one dedicated atomic-transition branch from synchronized `staging/main` after Phases 4.1–4.3 are integrated.
2. [x] Relocate the characterized DaisyUI template tree, focused components, pack metadata, and Python style provider from `powercrud/daisyUI` to `powercrud/packs/daisyui`.
3. [x] Switch default selection and composition to `powercrud/packs/daisyui` as the sole permanent source of truth.
4. [x] Preserve all 45 legacy template names through thin facades, including explicit named-fragment wrappers for every server-addressable partial.
5. [x] Retain the private adapter modules and stable `powercrud/css/powercrud.css` path unless a separately proved static façade is required; do not conflate template relocation with a static-path migration.
6. [x] Preserve legacy settings, explicit `templates_path`, tag/style resolution, native and crispy rendering, and all `pcrud_mktemplate` modes.
7. [x] Preserve default behaviour for unconfigured projects and clear errors for invalid explicit configuration.
8. [x] Keep the branch complete and unsplit until every compatibility path is available and packaged.

## Phase 4.5: Pass The Atomic Compatibility And Distribution Gate

1. [x] Verify default, legacy-setting, explicit-path, model-first override, focused-copy, root-copy, whole-tree-copy, tag/style, fragment, native-form, and crispy-form paths.
2. [x] Verify the complete applicable server and Playwright behaviour with unchanged default DaisyUI outcomes.
3. [x] Verify manual-static and bundled/Vite loading from their stable entries with selected-pack composition.
4. [x] Build wheel and sdist artifacts and verify templates, Python modules, metadata, and static assets from clean installed artifacts.
5. [x] Run focused configuration-error and unavailable-pack checks.
6. [x] Obtain a fresh independent compatibility review of the atomic diff and its recorded evidence.
7. [x] Resolve every deterministic regression or record a genuine blocker rather than weakening the gate.
8. [x] Squash-integrate the complete transition into `staging/main` only after every atomic acceptance condition passes together.

## Phase 4.6: Ratify Phase 4

1. [x] Confirm the compatible default DaisyUI pack is selected automatically for existing projects.
2. [x] Confirm the selected-pack contract is sufficient for the Phase 5 reference variant without implementing that variant early.
3. [x] Confirm no sample-app convenience introduced an otherwise unjustified public selection API.
4. [x] Record exact focused, full-regression, loading-mode, artifact, and independent-review results.
5. [x] Reconcile the master plan, master notes, runtime guidance, and shipped public documentation with completed behaviour only.
6. [x] Mark Master Phase 4 complete only after the integrated result is accepted and the numbered branches are retired.
