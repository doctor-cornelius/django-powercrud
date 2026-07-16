# Phase 5 DaisyUI Reference Variant Notes

## Purpose

These notes support [`phase5-reference-variant-plan.md`](phase5-reference-variant-plan.md), which implements Phase 5 of the [`template_packs-master-plan.md`](../template_packs-master-plan.md).

Phase 5 proves two different customisation paths without copying PowerCRUD's functional JavaScript. One sample presentation uses four model-first overrides against the compatible default pack. The other selects a complete but provisional DaisyUI reference pack that changes the main CRUD structure while reusing the standard DaisyUI framework adapter.

## Binding Inputs

1. Phase 2 shipped 31 model-first focused components and retained all legacy paths, fragments, and copy modes.
2. Phase 3 split DaisyUI presentation behaviour into eight private adapters behind the stable `powercrud/js/powercrud.js` entry.
3. Phase 4 established dynamic pack declarations and selection, the permanent `powercrud/packs/daisyui` namespace, and the 0.x compatibility facades.
4. The master plan defines the reference pack as an opt-in internal proof, not a production-support commitment.
5. Phase 6 owns reusable contract validation, clean wheel/sdist installation, and the lightweight same-adapter proof that survives any later retirement of this reference implementation.

## Locked Decisions

### Public Contract

Phase 5 uses the public machinery already delivered by Phase 4. The reference settings select `powercrud.packs.daisyui_reference:template_pack` through the existing `module.path:attribute` grammar. The declaration uses identity `daisyui-reference`, namespace `powercrud/packs/daisyui_reference`, template package `powercrud`, framework adapter `daisyui`, the compatible default capability set, native forms, and crispy template pack `tailwind`.

The reference pack declares `legacy_copy_destination=None`, `variant_adapter=None`, and no manual or Vite assets. It is not added to the built-in alias table. Phase 5 adds no per-view selector, public initializer, style-provider extension, pack-specific loader, or new public semantic hook. If the proof cannot proceed without one of those contracts, implementation stops for guidance.

### Sample Presentation Configurations

The sample uses three explicit settings configurations over the same application:

1. `config.settings` remains the compatible default presentation.
2. `config.settings_focused_overrides` prepends a focused override directory while retaining the default DaisyUI pack.
3. `config.settings_daisyui_reference` selects the reference declaration globally.

The settings overlays do not copy application configuration. They import the default sample settings, make only their presentation-specific changes, and set a sample-only `SAMPLE_PRESENTATION` label. The existing `sample.context_processors.app_meta` exposes that label to `sample/_runtime_meta.html` so a running sample identifies its presentation clearly.

The supported local launch shape is an explicit settings selection, for example:

```text
./src/manage.py runserver --settings=config.settings_focused_overrides 0:8001
./src/manage.py runserver --settings=config.settings_daisyui_reference 0:8001
```

These commands are implementation guidance, not authorization to run non-test container actions. There is no runtime switcher, query parameter, duplicated URL namespace, or copied view hierarchy.

### Focused-Override Presentation

The focused presentation changes only these Book component destinations under its prepended template directory:

1. `sample/book_list_actions.html`
2. `sample/book_filter_trigger.html`
3. `sample/book_table_header.html`
4. `sample/book_pagination.html`

The components should look intentionally related: a different neutral colour hierarchy, stronger bordered surfaces, and altered action/header/pagination composition. They preserve the published context and semantic contracts recorded by `pcrud_mktemplate --component`. They contain no functional scripts and continue to rely on the standard pack templates, core runtime, and DaisyUI adapter.

### Reference-Pack Composition

The selectable baseline must exist as a complete contract before the reference settings activate it. It contains the same 45 relative template paths as the compatible default source. Ordinary unchanged files may be one-line delegation includes. The eight paths that expose 25 server-addressable partials must load `powercrud_partials`, preserve ordinary rendering, and re-declare each historic partial name against a valid reference or default target.

This delegation is intentional. Phase 5 is a disposable proof of pack selection, structure, and same-adapter reuse; duplicating 45 maintained implementations would create no useful evidence. The reference namespace owns the structural templates changed by Phases 5.4 and 5.5 and delegates leaves where the compatible implementation already satisfies the contract.

The reference pack does not receive a pack-specific Python style provider. Template-owned neutral actions may exchange `primary`, `secondary`, and `accent` treatment. Python-resolved row-action and widget styles continue to come from the shared DaisyUI framework contract. `warning`, `error`, and `success` remain tied to their actual meanings.

### Structural Proof Boundary

The reference list changes the composition around the existing semantic behavior. Its owned surface includes the list orchestrator, list actions, filter trigger/panel/form presentation, table shell/header presentation, and pagination. It may retain the default table-row, row-action, selection, inline, and complex leaf renderers through delegation.

The other structurally distinct surfaces are the form shell, detail shell/content, delete shell/content/actions/conflict, and modal shell. Native/crispy field rendering, bulk outcomes, async surfaces, inline fields/rows, and other leaves remain delegated unless a structural shell cannot be coherent without a bounded replacement.

This is more than a list-only demonstration but deliberately less than a broad pack rewrite. Visual difference comes from layout, hierarchy, spacing, density, borders, surfaces, and truthful neutral action emphasis rather than a DaisyUI theme change.

## Delivery Rule

Phase 5.0 is the planning contract on `template_pack/5.0`. Before any implementation, Michael confirms that the working model is Terra and the primary agent creates one Goal Mode goal covering Phase 5.0–5.7. Each implementation phase begins from synchronized `staging/main` on its own `template_pack/5.x` branch, receives proportionate focused tests, is committed and pushed as a bounded slice, and is integrated before the next independent phase begins. The compatible default pack remains unchanged and automatically selected throughout.

Each completed sub-phase has exactly one semantic commit whose subject contains the sub-phase number. The required subjects are:

1. `docs(template-packs): 5.0 plan DaisyUI reference variant`
2. `feat(sample): 5.1 add presentation settings harness`
3. `feat(sample): 5.2 add focused Book overrides`
4. `feat(template-packs): 5.3 add DaisyUI reference baseline`
5. `feat(template-packs): 5.4 redesign reference list experience`
6. `feat(template-packs): 5.5 redesign reference CRUD shells`
7. `test(template-packs): 5.6 prove shared sample catalogue`
8. `docs(template-packs): 5.7 ratify DaisyUI reference variant`

Do not add unnumbered follow-up commits to a completed slice. Resolve pre-integration corrections by amending its single commit. Bounded sub-agents may map an existing contract or independently validate a specific slice during implementation, but the primary agent owns all edits, tests, commits, integrations, and final decisions. No sub-agent or audit work was used to create this planning contract.

The complete reference namespace is one selectable-baseline gate. Do not activate `config.settings_daisyui_reference` against a partial namespace that cannot satisfy direct fragments or declared capabilities. Later visual slices may merge independently because the reference pack is opt-in and must remain functional after every integration.

Do not create a blocker register pre-emptively. Create `phase5-blockers.md` only when the first genuine stop condition occurs, then record the evidence, affected phase, safe independent work, and exact guidance required.

## Stop Conditions

Stop for guidance before proceeding when implementation finds:

1. A required new public selector, alias, declaration field, style-provider contract, JavaScript initializer, semantic hook, or asset-loading API.
2. A reference interaction that genuinely requires variant JavaScript or additional pack assets.
3. A server-addressable partial that cannot be preserved by the complete reference namespace.
4. A need to change unconfigured/default rendering or the stable manual/Vite entries.
5. A need to duplicate models, routes, view classes, permissions, data, navigation, or functional PowerCRUD JavaScript.
6. An unexplained deterministic regression, non-trivial conflict, unrelated worktree mutation, or unexpected movement of remote `staging/main`.

## Validation Boundary

Phase 5 proves the implemented presentations proportionately. It adds focused declaration, inventory, fragment, settings, rendering, script-ownership, and browser behavior checks, then runs the canonical default regression before ratification. Generated assets are rebuilt when new template class sources affect the bundle.

Phase 6 remains responsible for the reusable general validator, capability-driven pack matrix, clean wheel/sdist installation, and the minimal same-adapter fixture retained after any future reference-pack retirement. Phase 5 may verify that its source paths fall within existing package inclusion, but it does not pull those Phase 6 outcomes forward.

## Plan

### Phase 5.0: Lock The Proof Contract

The planning contract is complete. The reference pack is provisional, settings-selected, same-adapter, asset-free, and JavaScript-free. The focused sample uses exactly four Book-list components. The reference sample changes the main CRUD shells while delegating unchanged leaves. No planning audit or sub-agent work was used.

### Phase 5.1: Establish The Shared Presentation Harness

Add the two derived settings modules and presentation label without changing `config.settings`. The focused overlay prepends its template directory. The reference overlay will select the module-path declaration once Phase 5.3 supplies the complete namespace; until then it must not create a runnable broken configuration.

Settings-isolation tests should prove the default selector and template directories remain unchanged, each overlay reports the correct presentation label, and all configurations retain the same root URL configuration, installed sample application, and view routes. The runtime badge must remain absent from HTMX fragments just as the existing metadata footer does.

### Phase 5.2: Add The Focused-Override Sample

Implement only the four agreed model-first Book templates. Existing component characterization and `pcrud_mktemplate` guidance define their required context and hooks. Add source/rendering tests that prove the focused settings choose them while default settings still choose the compatible components, and that none contains functional JavaScript.

The browser proof covers a full Book list load followed by HTMX filtering or sorting and pagination. It must demonstrate that the visible overrides survive the swap and continue using the standard runtime.

### Phase 5.3: Add A Complete Selectable Reference-Pack Baseline

Add the declaration, Python package, template resource root, complete 45-path namespace, and reference settings selection as one bounded baseline. Ordinary delegation stays context-preserving. Partial-bearing files expose all 25 required names under the reference namespace before selection is considered valid.

Focused tests cover module-path resolution, exact declaration shape, matching default/reference relative inventories, compilation and direct rendering of all applicable fragments, native/crispy paths, and the absence of new assets or variant JavaScript. The unconfigured and explicit `daisyui` selections must remain unchanged.

### Phase 5.4: Redesign The Reference List Experience

Replace only the list templates needed for a coherent different structure. Preserve all runtime-consumed hooks and accessibility relationships while changing the visible composition. Nested candidates must continue to resolve reference components first and delegated compatible leaves second.

Focused browser coverage exercises normal and HTMX loading, filters, sorting, pagination, list columns, favourites, selection, row actions, bulk entry, and inline entry. Any browser failure caused by an unstated DOM-shape assumption is evidence to refine the template or existing internal adapter seam, not permission to add variant JavaScript silently.

### Phase 5.5: Redesign The Main CRUD Shells

Replace the form, detail, delete, and modal shells as a cohesive slice or bounded sub-slices that always leave the opt-in pack functional. Preserve every direct root and conflict fragment. The reference form supports both native and crispy-tailwind rendering and both full-page and modal transport.

Focused server and browser coverage includes create/update, detail, delete, conflict presentation where practical, modal replacement, repeated initialization, and return-to-list behavior. Bulk, async, and inline leaves remain default-delegated but must continue to work through the reference outer structure.

### Phase 5.6: Prove The Shared Sample Catalogue

Run the same sample URLs, fixtures, roles, and CRUD scenarios under all three settings configurations. Tests should compare configuration and route identity directly rather than relying only on visual similarity. No variant may introduce an alternative model, view family, URL namespace, navigation tree, or seed-data path.

The reference behavior gate covers its declared capabilities across representative server and Playwright flows. Manual-static and Vite pages continue to load the stable PowerCRUD entries and shared DaisyUI dependencies, with no reference asset request and no console or page errors.

### Phase 5.7: Pass The Phase Gate And Ratify

Run the complete focused evidence for both non-default presentations, followed by the canonical default regression. Record exact commands, results, asset hashes when rebuilt, and any intentionally deferred Phase 6 validation.

Only after accepted integrations exist should the child and master documents state that Phase 5 is complete. Ratification must say explicitly that the reference pack is internal and provisional, that no new public pack API or JavaScript was added, and that production support remains undecided.
