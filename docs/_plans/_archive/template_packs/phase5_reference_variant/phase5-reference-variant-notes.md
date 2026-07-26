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

Completed in `bc132f56` and integrated into `staging/main`. The focused overlays deep-copy and prepend only `sample/template_overrides/focused`; the unchanged default uses the `Standard DaisyUI` fallback label. The sample footer exposes the active presentation only in full-page shells. The focused test gates passed under both `tests.settings` and `tests.settings_focused_overrides` (10 tests each).

### Phase 5.2: Add The Focused-Override Sample

Implement only the four agreed model-first Book templates. Existing component characterization and `pcrud_mktemplate` guidance define their required context and hooks. Add source/rendering tests that prove the focused settings choose them while default settings still choose the compatible components, and that none contains functional JavaScript.

The browser proof covers a full Book list load followed by HTMX filtering or sorting and pagination. It must demonstrate that the visible overrides survive the swap and continue using the standard runtime.

Completed in `7ea87d29` and integrated into `staging/main`. `sample/book_list_actions.html`, `sample/book_filter_trigger.html`, `sample/book_table_header.html`, and `sample/book_pagination.html` use a visibly different secondary/accent hierarchy without changing truthful status colours. They preserve Create/modal, filter-toggle, sorting, selection, tooltip, pagination, query-state, and HTMX hooks. Default and focused server gates passed (3 tests each); focused Playwright coverage passed after rebuilding the Vite assets, including sorting, pagination, and browser-error checks.

### Phase 5.3: Add A Complete Selectable Reference-Pack Baseline

Add the declaration, Python package, template resource root, complete 45-path namespace, and reference settings selection as one bounded baseline. Ordinary delegation stays context-preserving. Partial-bearing files expose all 25 required names under the reference namespace before selection is considered valid.

Focused tests cover module-path resolution, exact declaration shape, matching default/reference relative inventories, compilation and direct rendering of all applicable fragments, native/crispy paths, and the absence of new assets or variant JavaScript. The unconfigured and explicit `daisyui` selections must remain unchanged.

Completed in `213d8392` and integrated into `staging/main`. The internal `powercrud.packs.daisyui_reference:template_pack` declaration reuses the standard `daisyui` framework adapter and declares neither a built-in alias nor variant/manual/Vite assets. Its complete 45-path namespace delegates unchanged source to `powercrud/packs/daisyui`; the eight partial-bearing facades re-declare all 25 server-addressable names. `config.settings_daisyui_reference` and `tests.settings_daisyui_reference` select the existing module-path declaration and expose the sample label without changing default settings. The source-package command `./runproj exec "./runtests src/tests/test_daisyui_reference_template_pack.py src/tests/test_template_packs.py src/tests/test_template_partials_compat.py"` passed 43 tests. The opt-in command `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_daisyui_reference ./runtests src/tests/test_daisyui_reference_template_pack.py src/tests/test_list_options.py::test_book_list_renders_column_chooser_for_anonymous_user"` passed 7 tests, including a real Book list render.

### Phase 5.4: Redesign The Reference List Experience

Replace only the list templates needed for a coherent different structure. Preserve all runtime-consumed hooks and accessibility relationships while changing the visible composition. Nested candidates must continue to resolve reference components first and delegated compatible leaves second.

Focused browser coverage exercises normal and HTMX loading, filters, sorting, pagination, list columns, favourites, selection, row actions, bulk entry, and inline entry. Any browser failure caused by an unstated DOM-shape assumption is evidence to refine the template or existing internal adapter seam, not permission to add variant JavaScript silently.

Completed in `15d7fdd7` and integrated into `staging/main`. The reference list owns eight structural templates: its root, list actions, filter trigger/panel/form, table shell/header, and pagination. The new composition creates distinct heading, controls, filter, summary, table, and pagination surfaces while retaining the default table body, row actions, selection, favourites, column controls, bulk flows, inline rows, and modal runtime through the existing focused-candidate delegation. `secondary` and `accent` distinguish non-status actions; `error` remains limited to removing an optional filter. No reference JavaScript, new asset entry, or public hook was added. The default-focused command `./runproj exec "./runtests src/tests/test_daisyui_reference_template_pack.py src/tests/test_daisyui_reference_list.py src/tests/test_template_packs.py src/tests/test_template_partials_compat.py"` passed 44 tests. The reference-settings server command `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_daisyui_reference ./runtests src/tests/test_daisyui_reference_template_pack.py src/tests/test_daisyui_reference_list.py src/tests/test_list_options.py::test_book_list_renders_column_chooser_for_anonymous_user"` passed 8 tests. The reference Playwright command `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_daisyui_reference ./runtests --rebuild-assets src/tests/playwright/test_daisyui_reference_list.py"` passed and rebuilt only the shared Vite manifest entries (`powercrud-CSc9MBX6.js`, `powercrud-3vApjQAB.css`); Vite repeated its existing htmx direct-`eval` vendor warning.

### Phase 5.5: Redesign The Main CRUD Shells

Replace the form, detail, delete, and modal shells as a cohesive slice or bounded sub-slices that always leave the opt-in pack functional. Preserve every direct root and conflict fragment. The reference form supports both native and crispy-tailwind rendering and both full-page and modal transport.

Focused server and browser coverage includes create/update, detail, delete, conflict presentation where practical, modal replacement, repeated initialization, and return-to-list behavior. Bulk, async, and inline leaves remain default-delegated but must continue to work through the reference outer structure.

Completed in `d8ed362e` and integrated into `staging/main`. The reference pack now owns only the outer form, detail, delete, conflict, action-footer, and modal presentation templates. Forms use a header/context/body/footer composition, details use labelled field cards, destructive delete retains truthful `error` emphasis, and conflict retains truthful `warning` emphasis. Native and crispy fields still delegate to the compatible source; bulk, async, inline, persistence, permissions, and modal lifecycle remain shared. The default-focused command `./runproj exec "./runtests src/tests/test_daisyui_reference_template_pack.py src/tests/test_daisyui_reference_list.py src/tests/test_daisyui_reference_crud_shells.py src/tests/test_template_packs.py src/tests/test_template_partials_compat.py"` passed 46 tests. The reference-settings server command `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_daisyui_reference ./runtests src/tests/test_daisyui_reference_template_pack.py src/tests/test_daisyui_reference_crud_shells.py"` passed 8 tests. The reference Playwright command `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_daisyui_reference ./runtests --rebuild-assets src/tests/playwright/test_daisyui_reference_crud_shells.py"` passed after correcting the test's live-server URL construction, and rebuilt only the shared Vite manifest entries (`powercrud-RBGl-XFz.js`, `powercrud-q3a2mMez.css`); Vite repeated its existing htmx direct-`eval` vendor warning.

### Phase 5.6: Prove The Shared Sample Catalogue

Run the same sample URLs, fixtures, roles, and CRUD scenarios under all three settings configurations. Tests should compare configuration and route identity directly rather than relying only on visual similarity. No variant may introduce an alternative model, view family, URL namespace, navigation tree, or seed-data path.

The reference behavior gate covers its declared capabilities across representative server and Playwright flows. Manual-static and Vite pages continue to load the stable PowerCRUD entries and shared DaisyUI dependencies, with no reference asset request and no console or page errors.

Completed in `3eb99207` and integrated into `staging/main`. `test_sample_presentation_catalogue.py` proves all three settings overlays retain the default URL configuration, installed applications, database configuration, and one `sample.views.BookCRUDView`; it also proves that only the reference settings use the module-path selector. Its two tests passed independently under default, focused-override, and reference settings. The focused presentation retains exactly its four agreed Book overrides, while the reference presentation selects the complete 45-path namespace globally. Reference Playwright coverage passed for bulk selection, saved-favourite application, inline dependencies, row-action menus, in-page and modal delete, and manual-static assets, in addition to the 5.4/5.5 list and CRUD flows. A stale Docker test runner initially held the PostgreSQL test database and caused duplicate fixture data; after replacing it with a fresh test database, the representative and canonical gates passed. The reference delete flow also retained the historic `h2.card-title` identity and contiguous empty-state text expected by existing browser coverage, without changing its new structural composition.

### Phase 5.7: Pass The Phase Gate And Ratify

Completed and integrated as the numbered ratification slice. Source-package declaration, namespace, fragments, settings isolation, rendering, script ownership, and package-inventory coverage remained green through the prior 5.3–5.6 gates. The complete non-Playwright canonical server suite passed with `982 passed, 81 deselected` and 88% PowerCRUD coverage. A fresh-database canonical Playwright gate passed with `78 passed, 3 skipped, 982 deselected`; the three skips are intentional settings-specific presentation proofs. The explicit reference-settings Playwright command passed `2 passed`, and the focused-settings command passed `1 passed`. The shared manifest rebuilt to `powercrud-RBGl-XFz.js` and `powercrud-q3a2mMez.css`; the only build warning remained Vite's existing htmx direct-`eval` vendor warning.

The canonical suite exposed that the three presentation-specific browser tests were being collected under default settings. They now use module-level settings guards, so each proof runs only where its selected presentation exists and cannot manufacture a default-pack failure. The focused proof uses `tests.settings_focused_overrides`, not the sample's development settings, so its browser environment loads the manifest-backed shared PowerCRUD runtime.

Phase 5 is now complete. The reference pack is still internal, opt-in, and provisional; no public pack API, variant JavaScript, or pack-specific asset was added, and production support remains undecided. Phase 6 retains responsibility for reusable validation, clean wheel/sdist installation, and a lightweight same-adapter proof that survives any later reference-pack retirement.
