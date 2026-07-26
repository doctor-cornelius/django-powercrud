# Phase 3 Reusable JavaScript Adapters Plan

## Status

Complete. Phases 3.0–3.9 are verified; Phases 3.0–3.8 are independently integrated and Phase 3.9 is ready for integration.

## Next

Integrate and retire `template_pack/3.9`; any Phase 4 work requires its own reviewed plan and branch.

## Phase 3.0: Characterize And Plan Adapter Extraction

1. [x] Confirm the stable runtime entry, public globals, semantic attributes, events, storage, and both loading modes that Phase 3 must preserve.
2. [x] Map current runtime behaviour by ownership: PowerCRUD core, current-template DOM adapter, DaisyUI presentation-library adapter, and potential variant-only behaviour.
3. [x] Characterize initialization order, HTMX swap lifecycle, listener guards, state preservation, and teardown responsibilities.
4. [x] Map existing server, Playwright, manual-static, bundled/Vite, asset, and packaging coverage; identify only genuine pre-extraction gaps.
5. [x] Reconcile the audit evidence into the boundary record without selecting an unproven public adapter API.
6. [x] Define the smallest independently mergeable Phase 3 implementation slices, their compatibility gates, and the first slice's exact acceptance criteria.
7. [x] Update the master planning documents and publish the reviewed planning branch without implementing Phase 3 runtime changes.

## Phase 3.1: Extract DaisyUI Tooltip Lifecycle

1. [x] Add an internal `daisyui-tooltip-adapter` factory that owns only Tippy setup, lazy-tooltip behavior, hide/destroy, and scheduled refreshes.
2. [x] Keep `powercrud.js` as the automatic composition shell, retain its lifecycle order and all existing public tooltip globals as forwards, and preserve every tooltip call path for list roots and detached presentation panels.
3. [x] Add focused Vite and tooltip lifecycle characterization for public globals, repeated initialization, HTMX teardown/reinitialization, lazy detached-trigger cleanup, and absence of stale Tippy roots.
4. [x] Preserve manual-static loading, the stable entry, semantic tooltip attributes, themes, placement, and all non-tooltip runtime behavior.
5. [x] Run focused server/browser/asset checks before independently integrating and retiring `template_pack/3.1`; the canonical regression remains reserved for the Phase 3.3 checkpoint.

## Phase 3.2: Extract DaisyUI Searchable-Select Lifecycle

1. [x] Add native-select restoration and single-fresh-wrapper characterization across HTMX replacement before moving Tom Select behavior.
2. [x] Move only Tom Select construction, library configuration, dropdown presentation, and restore/destroy behavior behind the internally composed DaisyUI adapter.
3. [x] Retain searchable-select semantic attributes, value synchronization, existing public globals, and core list/inline semantics.
4. [x] Run focused asset/browser checks before independently integrating and retiring `template_pack/3.2`; the canonical regression remains reserved for the Phase 3.3 checkpoint.

## Phase 3.3: Extract DaisyUI Modal Lifecycle

1. [x] Characterize duplicate-dialog cleanup and refresh-on-close before moving dialog presentation.
2. [x] Move DaisyUI dialog classes, close presentation, and duplicate cleanup only; retain core bulk/form/list refresh decisions and events.
3. [x] Keep current modal IDs, semantic hooks, manual/Vite loading, and public runtime entry unchanged.
4. [x] Run focused modal/browser checks and the canonical regression before independently integrating and retiring `template_pack/3.3`.

## Phase 3.4: Extract Action And Selection Presentation

1. [x] Characterize disabled reasons, hoverability, visual classes, and spinner presentation before moving them.
2. [x] Move only presentation treatment for dynamic row and selection-aware actions; retain selection state, minimum-count rules, requests, permissions, and event semantics in core.
3. [x] Run focused bulk/action/browser checks before independently integrating and retiring `template_pack/3.4`; the canonical regression remains reserved for the Phase 3.6 checkpoint.

## Phase 3.5: Extract Inline Presentation

1. [x] Characterize inline popover rendering/cleanup, focus routing, and spinner treatment against the completed searchable-select adapter.
2. [x] Move only inline error/popover, focus, and visual presentation; retain inline save, cancel, dependency, validation, and guard semantics in core.
3. [x] Run focused inline/browser checks before independently integrating and retiring `template_pack/3.5`; the canonical regression remains reserved for the Phase 3.6 checkpoint.

## Phase 3.6: Extract List-Column Presentation

1. [x] Move chooser shell, placement, focus, and disabled visual behavior only after retaining visible-column state, persistence, last-column protection, and requests in core.
2. [x] Preserve detached-panel lifecycle and focused template hooks through the adapter boundary.
3. [x] Run focused list-option/browser checks and the canonical regression before independently integrating and retiring `template_pack/3.6`.

## Phase 3.7: Extract Favourites And Filter-Panel Presentation

1. [x] Separate panel display, clone/geometry, and presentation initialization from favourites/filter state, URL rules, and server events.
2. [x] Preserve raw-favourites handling before generic fragment initialization, panel state across swaps, and existing semantic hooks.
3. [x] Run focused favourites/filter/browser checks before independently integrating and retiring `template_pack/3.7`; the canonical regression remains reserved for Phase 3.9.

## Phase 3.8: Extract Row-Action Floating-Menu Presentation

1. [x] Retain lazy action availability, permission/state responses, and HTMX action semantics in core while moving only cloned-menu presentation and geometry.
2. [x] Preserve detached-menu cleanup, tooltip composition, modal behavior, and cloned-menu HTMX execution.
3. [x] Run focused row-action/browser checks before independently integrating and retiring `template_pack/3.8`; the canonical regression remains reserved for Phase 3.9.

## Phase 3.9: Ratify The Reusable DaisyUI Adapter

1. [x] Confirm the automatically composed DaisyUI adapter owns only extracted presentation behavior and no durable core state.
2. [x] Confirm all established public contracts, loading modes, teardown behavior, and Phase 3 slice gates remain intact.
3. [x] Mark Master Phase 3 complete only after every preceding adapter extraction is independently integrated; defer pack selection and variants to their governing phases.
