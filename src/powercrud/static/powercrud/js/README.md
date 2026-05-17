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

`powercrud.js` is the public entry and composition shell. It imports internal modules from `runtime/`, builds the feature runtimes, exposes compatibility globals, and registers the once-only page listeners.

The runtime modules have these broad responsibilities:

1. `runtime/startup.js`: once-only document/window/body listener registration.
2. `runtime/dom.js`, `runtime/htmx.js`, `runtime/storage.js`, `runtime/url.js`, `runtime/state.js`: shared helper boundaries.
3. `runtime/list-view-state.js`: filters, optional filters, page size, current view state, reset view, URL/query-state rules, and list refresh.
4. `runtime/filter-favourites.js`: saved favourite state, selected/dirty state, favourite apply/update/delete handling, and favourite panel coordination.
5. `runtime/list-columns.js`: visible-column chooser state, save/reset request payloads, and last-visible-column guard.
6. `runtime/bulk-actions.js`: row selection, select-all state, selection persistence, selection-aware action semantics, and bulk success/queued events.
7. `runtime/inline-edit.js`: inline row lifecycle, save/cancel/error handling, dependencies, focus recovery, and inline validation payloads.
8. `runtime/searchable-selects.js`: Tom Select enhancement for `data-powercrud-searchable-*` controls.
9. `runtime/current-template.js`: current-template DOM adapter and presentation-library behaviour such as DaisyUI dialogs, Tippy, floating panels, toolbar geometry, spinners, and visual classes.
10. `runtime/selectors.js`: shared selectors, attribute names, storage prefixes, and class constants.

## Public Contracts

The runtime keeps these public contracts stable unless a later public API change is explicitly approved:

1. `window.initPowercrud(fragment)`: idempotent fragment initializer for full pages and HTMX swaps.
2. `window.getCurrentFilters(options)`: current filter query helper.
3. `window.initPowercrudSearchableSelects(root)` and `window.destroyPowercrudSearchableSelects(root)`.
4. `window.initPowercrudTooltips(root)`, `window.hidePowercrudTooltips(root)`, and `window.destroyPowercrudTooltips(root)`.
5. `window.powercrudToggleFavouriteSaveForm`.
6. Stable `data-powercrud-*` and `data-inline-*` contracts.
7. Storage keys and custom events documented in `docs/_plans/js_cleanup/js_cleanup-notes.md`.

The duplicate-load guard `window.__powercrudRuntimeLoaded` prevents the same public entry from installing listeners twice.

## Lifecycle

The runtime has two lifecycle layers:

1. Once-only listener registration in `runtime/startup.js`.
2. Repeatable per-fragment initialization through `initPowercrud(fragment)`.

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

## Template-Pack Boundary

There is no `window.initPowercrudPack(fragment)` yet.

Template-pack hook creation is deferred until template-pack extraction or extraction-prep starts. The boundary decision record is `docs/_plans/js_cleanup/phase6-boundary-findings.md`.

Future extraction should not move whole files by name. It should move behaviours by ownership:

1. Keep core semantics in the shared runtime.
2. Move current-template DOM behaviour behind a current-template or pack adapter.
3. Move presentation-library behaviour behind a presentation adapter.
4. Add characterization tests before moving under-covered behaviour.

Likely future hook points include runtime initialization ordering, row-action floating menus, favourites panel presentation, filter panel display, list-column chooser presentation, selection-aware visuals, bulk modal success handling, inline error presentation, searchable selects, and tooltips.
