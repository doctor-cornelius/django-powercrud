# Phase 5 DaisyUI Reference Variant Plan

## Status

Phase 5.0 is complete locally and awaits its numbered integration commit. The proof contract, delivery sequence, Terra start gate, and Goal Mode workflow are locked; no Phase 5 application or template code has been implemented.

## Next

After the numbered 5.0 commit is integrated, begin Phase 5.1 from synchronized `staging/main` by establishing the shared sample-presentation settings harness without changing the default sample experience.

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

1. [ ] Establish the derived-settings overlay pattern and add the focused-override settings without changing the default settings module.
2. [ ] Add one sample-only presentation identity to the existing runtime metadata display.
3. [ ] Keep all presentations on the same database, fixtures, authentication roles, URL names, view classes, and navigation.
4. [ ] Reserve the reference settings contract for activation only after Phase 5.3 supplies its complete selectable namespace.
5. [ ] Document the explicit settings commands used to launch each available presentation without adding an in-application pack switcher.
6. [ ] Add focused settings-isolation and runtime-metadata tests before independent integration.

## Phase 5.2: Add The Focused-Override Sample

1. [ ] Add a settings-prepended override directory for the standard DaisyUI pack.
2. [ ] Add model-first Book overrides for list actions, filter trigger, table header, and pagination only.
3. [ ] Make the four components visibly different through structure and non-status semantic colours.
4. [ ] Preserve every documented context value, HTMX attribute, semantic hook, nested delegation point, and accessibility meaning.
5. [ ] Keep all functional JavaScript package-owned and include no scripts in the focused overrides.
6. [ ] Verify normal and HTMX list rendering, component resolution, and unchanged default rendering before independent integration.

## Phase 5.3: Add A Complete Selectable Reference-Pack Baseline

1. [ ] Add the internal `powercrud.packs.daisyui_reference:template_pack` declaration without adding a built-in alias.
2. [ ] Declare the `powercrud/packs/daisyui_reference` namespace, standard DaisyUI adapter, default capability set, native forms, and crispy-tailwind support.
3. [ ] Declare no legacy whole-tree destination, variant adapter, manual assets, or Vite assets.
4. [ ] Supply all 45 template paths before the reference settings select the pack.
5. [ ] Delegate unchanged templates to the compatible default pack rather than copying their implementation.
6. [ ] Preserve all 25 server-addressable partial names across the eight partial-bearing template paths.
7. [ ] Add the derived reference settings and select the declaration globally while leaving the default selector unchanged.
8. [ ] Verify declaration resolution, complete inventories, direct fragments, native/crispy rendering, and default isolation before independent integration.

## Phase 5.4: Redesign The Reference List Experience

1. [ ] Reorganize the reference heading, instructions, actions, filters, table container, header, and pagination into visibly different framed surfaces.
2. [ ] Use a distinct neutral colour hierarchy, spacing, density, borders, and action emphasis without misusing status colours.
3. [ ] Retain the table body and complex leaf components by delegation where rewriting them adds no proof value.
4. [ ] Preserve list roots, named fragments, filtering, sorting, pagination, selection, favourites, column controls, row actions, bulk operations, inline editing, modal targets, and HTMX lifecycle.
5. [ ] Continue nested reference-pack delegation so later focused replacements remain composable.
6. [ ] Add no variant JavaScript, additional asset entry, or public hook.
7. [ ] Run focused list rendering and browser behaviour before independent integration.

## Phase 5.5: Redesign The Main CRUD Shells

1. [ ] Provide structurally different create/update form, detail, delete, and modal shells.
2. [ ] Use alternative headings, content cards, context layouts, and action footers while retaining truthful action semantics.
3. [ ] Preserve native and crispy forms, CSRF, multipart encoding, retained query state, normal/modal rendering, conflict fragments, and direct HTMX targets.
4. [ ] Delegate unchanged fields, bulk outcomes, async surfaces, inline components, and other leaf renderers to the default pack.
5. [ ] Keep permissions, requests, persistence, state, and lifecycle decisions outside the reference templates.
6. [ ] Add no reference-pack JavaScript or assets.
7. [ ] Run focused form, detail, delete, modal, and fragment behaviour before independent integration.

## Phase 5.6: Prove The Shared Sample Catalogue

1. [ ] Confirm the default, focused-override, and reference presentations expose the same sample catalogue rather than copied applications or view families.
2. [ ] Confirm the focused presentation changes only the four agreed Book components.
3. [ ] Confirm the reference presentation selects its complete namespace globally.
4. [ ] Exercise list loading, filters, sorting, pagination, column controls, favourites, row actions, modal create/update, detail, delete, bulk operations, inline editing, dependencies, and authentication roles.
5. [ ] Cover Vite and manual-static loading without new asset entries or browser errors.
6. [ ] Confirm no duplicated models, routes, views, sample data, permissions, navigation, or functional JavaScript.
7. [ ] Run the shared-catalogue server and browser gate before independent integration.

## Phase 5.7: Pass The Phase Gate And Ratify

1. [ ] Run focused declaration, namespace, fragment, settings-isolation, rendering, script-ownership, and source-package inventory checks.
2. [ ] Run representative Playwright coverage under both non-default settings configurations.
3. [ ] Run the complete canonical default server and Playwright suite as the compatibility regression gate.
4. [ ] Rebuild generated assets when changed template class sources require it.
5. [ ] Defer reusable validation and clean wheel/sdist installation to Phase 6.
6. [ ] Reconcile the child plan, child notes, master plan, and master notes only after the integrated result is real.
7. [ ] Mark Master Phase 5 complete without promoting the reference pack as a supported production pack.
8. [ ] Retire every completed Phase 5 feature branch after its accepted integration into `staging/main`.
