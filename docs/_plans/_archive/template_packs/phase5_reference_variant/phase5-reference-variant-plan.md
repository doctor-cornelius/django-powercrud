# Phase 5 DaisyUI Reference Variant Plan

## Status

Phases 5.0–5.7 are complete and integrated into `staging/main`. The reference pack remains an internal, opt-in Phase 5 proof rather than a supported production pack.

## Next

Begin Phase 6's reusable validation work from synchronized `staging/main`. Retain the lightweight same-adapter proof before any later reference-pack retirement is considered.

## Phase 5.0: Lock The Proof Contract

1. [x] Define the reference pack as an internal, opt-in, provisional proof that may be retired after the first serious alternative pack ships.
2. [x] Reuse the existing `module.path:attribute` selector and standard `daisyui` framework adapter.
3. [x] Add no built-in alias, public selector, style-provider API, variant JavaScript, or additional pack assets.
4. [x] Stop for guidance if implementation proves that a new public contract, variant adapter, or asset declaration is genuinely required.
5. [x] Use separate settings configurations rather than per-view pack selection.
6. [x] Share the existing sample models, data, permissions, URLs, views, navigation, and PowerCRUD JavaScript.
7. [x] Keep status colours truthful while varying neutral colour hierarchy, spacing, density, and structure.
8. [x] Divide implementation into bounded numbered slices that leave the compatible default DaisyUI experience unchanged.
9. [x] Require one semantic commit per completed sub-phase, with its `5.x` number in the subject, matching the Phase 3 delivery style.
10. [x] Require a Terra confirmation and a single Phase 5 Goal Mode goal before implementation begins.
11. [x] Permit bounded implementation sub-agents for contract mapping or validation while the primary agent owns all edits, tests, commits, and integrations.

## Phase 5.1: Establish The Shared Presentation Harness

1. [x] Establish the derived-settings overlay pattern and add the focused-override settings without changing the default settings module.
2. [x] Add one sample-only presentation identity to the existing runtime metadata display.
3. [x] Keep all presentations on the same database, fixtures, authentication roles, URL names, view classes, and navigation.
4. [x] Reserve the reference settings contract for activation only after Phase 5.3 supplies its complete selectable namespace.
5. [x] Document the explicit settings commands used to launch each available presentation without adding an in-application pack switcher.
6. [x] Add focused settings-isolation and runtime-metadata tests before independent integration.

## Phase 5.2: Add The Focused-Override Sample

1. [x] Add a settings-prepended override directory for the standard DaisyUI pack.
2. [x] Add model-first Book overrides for list actions, filter trigger, table header, and pagination only.
3. [x] Make the four components visibly different through structure and non-status semantic colours.
4. [x] Preserve every documented context value, HTMX attribute, semantic hook, nested delegation point, and accessibility meaning.
5. [x] Keep all functional JavaScript package-owned and include no scripts in the focused overrides.
6. [x] Verify normal and HTMX list rendering, component resolution, and unchanged default rendering before independent integration.

## Phase 5.3: Add A Complete Selectable Reference-Pack Baseline

1. [x] Add the internal `powercrud.packs.daisyui_reference:template_pack` declaration without adding a built-in alias.
2. [x] Declare the `powercrud/packs/daisyui_reference` namespace, standard DaisyUI adapter, default capability set, native forms, and crispy-tailwind support.
3. [x] Declare no legacy whole-tree destination, variant adapter, manual assets, or Vite assets.
4. [x] Supply all 45 template paths before the reference settings select the pack.
5. [x] Delegate unchanged templates to the compatible default pack rather than copying their implementation.
6. [x] Preserve all 25 server-addressable partial names across the eight partial-bearing template paths.
7. [x] Add the derived reference settings and select the declaration globally while leaving the default selector unchanged.
8. [x] Verify declaration resolution, complete inventories, direct fragments, native/crispy rendering, and default isolation before independent integration.

## Phase 5.4: Redesign The Reference List Experience

1. [x] Reorganize the reference heading, instructions, actions, filters, table container, header, and pagination into visibly different framed surfaces.
2. [x] Use a distinct neutral colour hierarchy, spacing, density, borders, and action emphasis without misusing status colours.
3. [x] Retain the table body and complex leaf components by delegation where rewriting them adds no proof value.
4. [x] Preserve list roots, named fragments, filtering, sorting, pagination, selection, favourites, column controls, row actions, bulk operations, inline editing, modal targets, and HTMX lifecycle.
5. [x] Continue nested reference-pack delegation so later focused replacements remain composable.
6. [x] Add no variant JavaScript, additional asset entry, or public hook.
7. [x] Run focused list rendering and browser behaviour before independent integration.

## Phase 5.5: Redesign The Main CRUD Shells

1. [x] Provide structurally different create/update form, detail, delete, and modal shells.
2. [x] Use alternative headings, content cards, context layouts, and action footers while retaining truthful action semantics.
3. [x] Preserve native and crispy forms, CSRF, multipart encoding, retained query state, normal/modal rendering, conflict fragments, and direct HTMX targets.
4. [x] Delegate unchanged fields, bulk outcomes, async surfaces, inline components, and other leaf renderers to the default pack.
5. [x] Keep permissions, requests, persistence, state, and lifecycle decisions outside the reference templates.
6. [x] Add no reference-pack JavaScript or assets.
7. [x] Run focused form, detail, delete, modal, and fragment behaviour before independent integration.

## Phase 5.6: Prove The Shared Sample Catalogue

1. [x] Confirm the default, focused-override, and reference presentations expose the same sample catalogue rather than copied applications or view families.
2. [x] Confirm the focused presentation changes only the four agreed Book components.
3. [x] Confirm the reference presentation selects its complete namespace globally.
4. [x] Exercise list loading, filters, sorting, pagination, column controls, favourites, row actions, modal create/update, detail, delete, bulk operations, inline editing, dependencies, and authentication roles.
5. [x] Cover Vite and manual-static loading without new asset entries or browser errors.
6. [x] Confirm no duplicated models, routes, views, sample data, permissions, navigation, or functional JavaScript.
7. [x] Run the shared-catalogue server and browser gate before independent integration.

## Phase 5.7: Pass The Phase Gate And Ratify

1. [x] Run focused declaration, namespace, fragment, settings-isolation, rendering, script-ownership, and source-package inventory checks.
2. [x] Run representative Playwright coverage under both non-default settings configurations.
3. [x] Run the complete canonical default server and Playwright suite as the compatibility regression gate.
4. [x] Rebuild generated assets when changed template class sources require it.
5. [x] Defer reusable validation and clean wheel/sdist installation to Phase 6.
6. [x] Reconcile the child plan, child notes, master plan, and master notes after the integrated result exists.
7. [x] Mark Master Phase 5 complete without promoting the reference pack as a supported production pack.
8. [x] Retire every completed Phase 5 feature branch after its accepted integration into `staging/main`.
