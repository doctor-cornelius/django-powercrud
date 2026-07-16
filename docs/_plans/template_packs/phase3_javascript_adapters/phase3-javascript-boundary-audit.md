# Phase 3 JavaScript Boundary Audit

## Status

Complete. The planning audit identified the first proven seam, Phases 3.1–3.8 implemented the private adapters incrementally, the final compatibility review found no runtime blocker, and the Phase 3.9 canonical gate passed.

## Scope And Method

The audit is read-only. It maps the current stable runtime, its behaviour ownership, lifecycle and loading contracts, existing tests, and genuine gaps needed before code movement. It does not implement an adapter, move JavaScript, alter templates, introduce a pack selector, or reclassify stable public contracts without evidence.

## Baseline Constraints

1. Preserve `powercrud/js/powercrud.js`, `window.initPowercrud(fragment)`, existing public globals, semantic attributes, events, storage keys, and server interaction contracts.
2. Preserve manual-static and bundled/Vite loading without new settings, script tags, installed apps, or static paths for existing users.
3. Keep durable PowerCRUD semantics in core; isolate current-template and DaisyUI/presentation-library behavior only where the runtime evidence supports it.
4. Keep adapter API shape internal until the first implementation slice requires and proves a minimal seam.

## Verified Runtime Shape

`powercrud/js/powercrud.js` is the stable public composition shell. It installs the duplicate-load guard and public globals, constructs feature runtimes, registers once-only listeners, and owns the ordered fragment lifecycle. Both manual-static and bundled/Vite loading expose their vendor globals before loading that same entry.

Current initialization order is deliberate: searchable selects, object-list bootstrap, then tooltips. Before an HTMX replacement, the runtime hides tooltips, gives semantic runtimes a chance to cancel or preserve state, destroys fragment-bound widgets, closes detached presentation UI, and clears inline state. After a swap, favourites must process raw server markup before generic initialization adds Tom Select wrappers; after settle, layout-sensitive tooltips and inline popovers are finalized.

The following public and compatibility contracts remain unchanged throughout Phase 3:

1. `powercrud/js/powercrud.js`, `window.__powercrudRuntimeLoaded`, and `window.initPowercrud(fragment)`.
2. Existing public filter, searchable-select, tooltip, and favourite globals.
3. Semantic `data-powercrud-*` and `data-inline-*` attributes, custom events, storage keys, server headers, and durable request/state behavior.
4. Manual-static and bundled/Vite loading, including the `config/static/js/main.js` manifest entry.
5. Once-only listener registration, HTMX event order, state preservation, and teardown before replacement.

## Ownership Map

| Boundary | Current ownership | Extraction implication |
| --- | --- | --- |
| PowerCRUD core | Object-list discovery/refresh, URL and storage rules, filters, favourites state, visible-column state, bulk selection, inline lifecycle, public globals, events, and listener registration. | Remains in shared runtime. No adapter owns durable/domain request semantics or durable state; lazy tooltip content retrieval remains intentionally coupled to the private Tippy lifecycle. |
| Current-template DOM behavior | Filter and toolbar geometry, floating panels, cloned row-action menus, list-column shell placement, and direct current-template IDs. | Move only after each area's state/display distinction and focused template hooks are characterized. |
| DaisyUI/presentation-library behavior | DaisyUI dialog classes, Tippy lifecycle, Tom Select construction/restoration, spinner and disabled visuals, icon/color treatment, and inline error-popover presentation. | Eligible for an internal DaisyUI adapter one bounded behavior at a time. |
| Variant-only behavior | None exists today. | Do not create a variant module, selector, or public variant API during Phase 3. |

Whole files are not clean ownership units. `powercrud.js` currently injects presentation callbacks into semantic feature runtimes, and several feature modules still mix durable state with current-template DOM mechanics. Extraction must therefore move behavior rather than files.

## Existing Coverage And Genuine Gaps

The server suite protects semantic attributes and rendering contracts. Frontend packaging tests protect the stable entry, internal imports, public globals, teardown shell, manual/Vite template separation, and manifest key. Manual-static Playwright verifies module loading, vendor/public globals, idempotent initialization, Tom Select and Tippy behavior, and the absence of Vite assets. The 77-test Playwright suite already covers tooltip lifecycle and HTMX reinitialization, selection persistence, floating row actions, chooser geometry, inline error cleanup, and filter/favourites state.

Gaps are behavior-specific rather than a reason for a new general suite:

1. Add a direct bundled/Vite runtime smoke before changing runtime composition: prove the Vite path loads the stable runtime, exposes expected globals, initializes a tooltip, and reports no browser/page errors.
2. Characterize exactly one Tippy instance per trigger through initial load, repeated initialization, HTMX replacement, and teardown/reinitialization, including no stale body popper.
3. Before a later Tom Select extraction, add native-select restoration across an HTMX replacement and prove one fresh wrapper after reinitialization.
4. Defer duplicate-modal cleanup, floating-menu HTMX execution, selection-aware visual state, and remaining filter/inline characterization until a later slice moves those behaviors.

## Candidate Boundaries And Recommended First Slice

Do not extract global initialization, filter-panel behavior, inline error/select interaction, floating favourites/list-columns panels, or row-action menus first. Each combines core semantics with current-template or body-level presentation and needs further characterization.

The recommended first implementation slice is a narrowly scoped **DaisyUI tooltip lifecycle adapter**. Tippy setup, hide, destroy, lazy-tooltip handling, theme, and placement are concentrated presentation behavior; existing tooltip coverage is broad; and the stable entry can continue to compose the default DaisyUI behavior automatically. The slice must preserve current initialization order and public tooltip globals as compatibility wrappers. It must not introduce a pack loader, setting, static entry, or public adapter initializer.

Phase 3.1 uses one internal factory in `runtime/daisyui-tooltip-adapter.js`:

```js
createDaisyuiTooltipLifecycleAdapter({
    global,
    documentObject,
    warnMissingDependency,
}) => ({
    init(root = documentObject),
    hide(root = documentObject),
    destroy(root = documentObject),
    scheduleInit(root = documentObject, delay = 0),
    scheduleResizeInit(root = documentObject, delay = 100),
})
```

`powercrud.js` constructs that factory directly, retains lifecycle ownership, and exposes its first three methods through the existing tooltip globals. This is not a registry, pack loader, or public initializer. The default adapter is automatically available in both supported loading modes.

Tooltip extraction preserves every call path, not only fragment initialization: current list roots, HTMX request/swap/settle, delayed and resize refreshes, list-column and favourites detached panels, cloned row-action menus, changed favourite triggers, and lazy tooltip fetch cleanup. It must preserve the current searchable-select → list-bootstrap → tooltip order, bulk's before-swap early return, raw-favourites processing before generic initialization, and inline post-settle work.

The Phase 3.1 characterization gate adds a bundled/Vite smoke for stable runtime/global loading, tooltip initialization, and clean browser/page errors. It also adds a focused lifecycle case for repeated initialization, old-instance destruction before HTMX replacement, a single replacement instance, no stale Tippy root, and a lazy trigger whose request resolves after its source detaches. Existing manual-static and tooltip behavior coverage remain required.

## Decisions And Blockers

No genuine blocker exists for planning the tooltip-lifecycle slice. The current evidence does not support a variant-only module or public adapter initializer, so both remain deferred.

A separate `phase3-blockers.md` will be created only if the second independent review finds an unresolved compatibility, ownership, or scope decision that prevents the first slice from being specified safely.

## Phase 3.9 Ratification Findings

All eight private factories are composed directly by the stable `powercrud.js` entry. Core retains public globals, semantic hooks, custom events, storage, listener registration, HTMX ordering, detached lifecycle decisions, and domain requests. The adapters own the characterized Tippy, Tom Select, modal, dynamic action/selection, inline, list-column, filter/favourites, and row-menu presentation behavior only.

The final independent reviews found no unused compatibility path, public-contract drift, missing packaging entry, pack loader, selector, metadata API, or variant module. Public composition and selection remain deferred to Phase 4, while a reference variant remains Phase 5 work.
