# PowerCRUD JavaScript Runtime

This folder contains the source for the public PowerCRUD browser runtime.

The stable public entry is:

```text
powercrud/js/powercrud.js
```

Manual users load that entry as an ES module:

```html
<script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>
```

Bundled/Vite users continue through `src/config/static/js/main.js`, which imports the same stable package entry.

## Runtime Shape

`powercrud.js` is the public entry and composition shell. It imports internal modules from `runtime/`, builds the feature runtimes, exposes compatibility globals, and registers the once-only page listeners. Its private `runtime/daisyui-composition.js` factory constructs the supported DaisyUI presentation adapters before the entry wires them into durable feature runtimes.

The runtime modules have these broad responsibilities:

1. `runtime/startup.js`: once-only document/window/body listener registration.
2. `runtime/dom.js`, `runtime/htmx.js`, `runtime/storage.js`, `runtime/url.js`, `runtime/state.js`: shared helper boundaries.
3. `runtime/list-view-state.js`: filters, optional filters, page size, current view state, reset view, URL/query-state rules, and list refresh.
4. `runtime/filter-favourites.js`: saved favourite state, selected/dirty state, favourite apply/update/delete handling, and favourite panel coordination.
5. `runtime/list-columns.js`: visible-column chooser state, save/reset request payloads, and last-visible-column guard.
6. `runtime/bulk-actions.js`: row selection, select-all state, selection persistence, selection-aware action semantics, and bulk success/queued events.
7. `runtime/inline-edit.js`: inline row lifecycle, save/cancel/error handling, dependencies, focus recovery, and inline validation payloads.
8. `runtime/searchable-selects.js`: semantic discovery and value synchronization for `data-powercrud-searchable-*` controls.
9. `runtime/daisyui-composition.js`: private ordered construction of the DaisyUI adapters and adapter-wired searchable-select runtime.
10. `runtime/daisyui-searchable-select-adapter.js`: private Tom Select construction, presentation, native restoration, and destruction.
11. `runtime/daisyui-tooltip-adapter.js`: private Tippy presentation lifecycle for semantic, overflow, and lazy tooltips.
12. `runtime/daisyui-modal-adapter.js`: private native-dialog classes, duplicate cleanup, and close presentation.
13. `runtime/daisyui-action-selection-adapter.js`: private dynamic disabled-action visuals and generic request spinners.
14. `runtime/daisyui-inline-presentation-adapter.js`: private inline focus routing, error popovers, and save-spinner presentation.
15. `runtime/daisyui-list-column-presentation-adapter.js`: private list-column chooser shell, placement, focus, and disabled visuals.
16. `runtime/daisyui-filter-favourites-presentation-adapter.js`: private filter-panel display plus favourites shell, geometry, initialization, and icon visuals.
17. `runtime/daisyui-row-action-menu-presentation-adapter.js`: private row-action menu shell cloning, fixed placement, and reveal.
18. `runtime/current-template.js`: current-template DOM coordinator for modal lifecycle, lazy row actions, and shared toolbar geometry.
19. `runtime/selectors.js`: shared selectors, attribute names, storage prefixes, and class constants.

## Public Contracts

The runtime keeps these public contracts stable unless a later public API change is explicitly approved:

1. `window.initPowercrud(fragment)`: idempotent fragment initializer for full pages and HTMX swaps.
2. `window.getCurrentFilters(options)`: current filter query helper.
3. `window.initPowercrudSearchableSelects(root)` and `window.destroyPowercrudSearchableSelects(root)`.
4. `window.initPowercrudTooltips(root)`, `window.hidePowercrudTooltips(root)`, and `window.destroyPowercrudTooltips(root)`.
5. `window.powercrudToggleFavouriteSaveForm`.
6. Stable `data-powercrud-*` and `data-inline-*` contracts.
7. Storage keys and custom events documented in `docs/_plans/js_cleanup/js_cleanup-notes.md`.

Custom modal `extra_buttons` and `extra_actions` may render
`data-powercrud-refresh-list-on-modal-close="true"`. When that flagged modal is
closed, the current-template adapter reports the close to `powercrud.js`, and
the composed list-refresh runtime refreshes the originating object-list root.

The duplicate-load guard `window.__powercrudRuntimeLoaded` prevents the same public entry from installing listeners twice.

## Lifecycle

The runtime has two lifecycle layers:

1. Once-only listener registration in `runtime/startup.js`.
2. Repeatable per-fragment initialization through `initPowercrud(fragment)`.

The startup installer also handles late private composition imports. If the
document has already left its loading state before listener installation, it
runs the DOM-ready bootstrap immediately through the same once-only guard. This
keeps initial full-page behaviour aligned with later HTMX fragment behaviour.

The core fragment initialization order is:

1. Initialize searchable selects.
2. Bootstrap affected object-list roots.
3. Initialize tooltips.

That order is intentional. Select enhancement runs first so list bootstrap can interact with enhanced controls when it opens or restores panels. List bootstrap may then reveal controls, restore list state, or sync current-template presentation before tooltip setup runs. HTMX swaps call teardown before replacing a fragment, then call `initPowercrud()` again after swap/settle.

Fragment teardown currently destroys Tom Select instances, destroys Tippy instances, and removes detached inline error popovers.

## Ownership Boundaries

Core runtime owns durable PowerCRUD semantics:

1. Object-list roots and scoped list refresh.
2. HTMX/list refresh rules.
3. URL/query-state rules.
4. Favourite selected/dirty state.
5. Visible-column state.
6. Bulk-selection state.
7. Inline-row lifecycle and validation payloads.
8. Public globals, storage keys, custom events, and stable `data-*` contracts.

Current-template DOM adapter code owns behaviour tied to today's HTML shape, selectors, IDs, DOM placement, table/list layout, toolbar geometry, or floating panel geometry.

Presentation-library adapter code owns behaviour tied to DaisyUI, Tippy, Tom Select, spinner markup/classes, icon classes, button classes, colour classes, or framework-specific modal APIs.

## Application-Owned Asset Snapshots

`pcrud_mktemplate app --assets` may copy the package-owned manual-static CSS and JavaScript tree into an application's static namespace. This is an opt-in snapshot for a project that needs to own pack presentation assets; it does not change the stable package entry, public globals, selector, or lifecycle contracts.

The application must replace the package-owned PowerCRUD asset tags in its base template with the generated static tags. It must not load both entries: the duplicate-load guard means the first entry determines the active runtime. A copied snapshot has no file-by-file fallback to package assets, remains application and pack scoped rather than model scoped, and supports manual-static integration only. Vite users maintain their own frontend entry instead of combining it with a generated manual-static snapshot.

## Template-Pack Boundary

The compatible DaisyUI presentation behavior is now split into private adapters and composed automatically by the stable `powercrud.js` entry. This extraction did not add a public adapter registry, pack selector, variant module, new setting, or `window.initPowercrudPack(fragment)` API.

Core runtime modules continue to own durable state, requests, HTMX decisions, public globals, events, storage, semantic hooks, and listener ordering. The private adapters own only the characterized library and presentation behavior listed above. `current-template.js` remains the coordinator for shared toolbar geometry, modal refresh behavior, and lazy row-action semantics that do not belong to a presentation adapter.

Phase 4 may package and select the default DaisyUI pack using these proven internal seams. Any public composition or selection contract must be designed there; Phase 3 deliberately leaves existing projects on the same automatic loading path. The earlier boundary rationale remains archived in `docs/_plans/_archive/js_cleanup/phase6-boundary-findings.md`.
