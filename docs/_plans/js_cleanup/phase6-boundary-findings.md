# Phase 6 Boundary Findings

## Purpose

Phase 6 did not change runtime code. Its output is a boundary decision record for future template-pack work.

The detailed slice tables are in [`js_cleanup-notes.md`](js_cleanup-notes.md), especially:

1. `Phase 6.0 Runtime Boundary Map Result`
2. `Phase 6.1 Core-Owned Contract Result`
3. `Phase 6.2 Adapter Behaviour Result`
4. `Phase 6.3 Boundary Hook And Characterization Result`
5. `Phase 6.4 Characterization Test Result`

This document is the durable summary of those findings.

## Main Finding

The future template-pack split is not simply "core versus DaisyUI".

The current JavaScript has three separate kinds of responsibility:

1. Shared PowerCRUD semantics that must stay in core.
2. Current-template DOM assumptions that depend on today's HTML shape and layout.
3. Presentation-library behaviour that depends on DaisyUI, Tippy, Tom Select, spinner classes, button classes, icons, colours, or modal APIs.

The important result is that later extraction should not move whole files by name. It should move behaviours by ownership.

## Core Runtime Ownership

Core owns contracts and behaviour that should remain stable regardless of template pack:

1. Stable public entry: `powercrud/js/powercrud.js`.
2. Public fragment initializer: `window.initPowercrud(fragment)`.
3. Manual loading:

    ```html
    <script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>
    ```

4. Bundled/Vite loading through `config/static/js/main.js`.
5. Object-list root discovery and scoped list refresh.
6. HTMX lifecycle handling and list-refresh rules.
7. URL/query-state rules for filters, page size, sorting, visible filters, and visible columns.
8. Favourites selected/dirty state and comparable view state.
9. Visible-column persistence and last-visible-column guard.
10. Bulk-selection state, selected IDs, select-all state, and minimum-selection semantics.
11. Inline-row lifecycle, save/cancel/error events, dependencies, and validation payloads.
12. Stable `data-powercrud-*` and `data-inline-*` contracts.
13. Public compatibility globals, custom events, storage keys, and server/list-refresh headers.

These are the API-like boundaries familiar from Python package work: pack extraction should not redefine them without an explicit public-contract decision.

## Adapter Ownership

Future adapter or pack code may own behaviour that is not PowerCRUD semantics.

Current-template DOM adapter behaviour:

1. Toolbar and filter-panel width measurement.
2. Floating row-action menu cloning and geometry.
3. Floating favourites panel cloning and geometry.
4. List-column chooser shell, focus, and placement.
5. Filter-panel shell display and current IDs such as `#filterCollapse`.
6. Bulk-selection counter and action-container visibility.

Presentation-library adapter behaviour:

1. DaisyUI dialog/modal handling and `modal-box` classes.
2. Tippy setup, hide, destroy, theme, placement, and overflow checks.
3. Tom Select construction, plugins, dropdown parent, clear button, and native-select restore.
4. Spinner markup and classes.
5. Disabled visual classes and tooltip reason rendering.
6. Favourite icon and colour treatment.
7. List-column disabled visual state.
8. Inline error popover DOM, classes, and placement.

These are not stable public APIs. They are implementation boundaries for a future adapter or template pack.

## What Hooks Mean Here

In Phase 6, "hook" does not necessarily mean a new public JavaScript API.

It means a formal boundary where core can say:

1. "A semantic state changed."
2. "A fragment has finished core initialization."
3. "A current-template or presentation adapter may now update visuals."
4. "The adapter may render or clean up a library-specific behaviour without owning the semantic state."

The hook could take one of three forms:

1. An injected adapter object used internally by core runtime modules.
2. A neutral DOM custom event that adapter code can listen to.
3. A future public initializer such as `window.initPowercrudPack(fragment)`.

Phase 6 deliberately did not choose which form to implement. That decision belongs to the first extraction-prep implementation slice because it should be made with the actual code movement in view.

## Mixed Boundaries That Need Hooks

| Area | Core should keep | Adapter may own | Likely boundary mechanism | Implement when |
| --- | --- | --- | --- | --- |
| Runtime initialization ordering | `initPowercrud(fragment)`, once-only listener registration, HTMX lifecycle order | Current-template and presentation initialization after core state is stable | Internal adapter lifecycle hook or future `initPowercrudPack(fragment)` | First extraction-prep slice, before moving adapter code |
| Row-action floating menus | Row action meaning, HTMX action execution, inline action semantics | Cloned menu shell, fixed positioning, close behaviour, tooltip init | Neutral row-action/menu hook or event | Before moving row-action menu code |
| Favourites panel | Favourite state, selected/dirty storage, apply/update/delete events | Floating panel clone, placement, icon/label/tooltip visuals | Favourite presentation hook after state sync | Before extracting favourites panel UI |
| Filter panel | Open/closed state and optional-filter semantics | `#filterCollapse`, hidden/display state, labels, tooltip refresh | Filter-panel display adapter hook | Before changing filter-panel DOM ownership |
| List-column chooser | Visible-column state, last-column guard, save/reset requests | `<details>` shell, focus, placement, disabled visual treatment | List-column presentation hook | Before moving chooser shell behaviour |
| Selection-aware actions | Minimum-count rules and disabled reason payload | Disabled classes, pointer-event classes, tooltip reason rendering | Selection presentation hook | Before extracting bulk/action visuals |
| Bulk modal success | `bulkEditSuccess` / `bulkEditQueued`, selection clearing, list refresh | DaisyUI modal close and duplicate modal cleanup | Modal adapter listener for neutral bulk result event | Before moving modal handling |
| Inline errors and focus | Inline lifecycle, dependency refresh, validation payloads | Body popovers, `sr-only`, Tom Select focus routing, spinner visuals | Inline presentation hook or neutral inline error event | Before extracting inline error presentation |
| Searchable selects | `data-powercrud-searchable-*` opt-in and value synchronization | Tom Select setup, plugins, native hiding/restoration, dropdown placement | Searchable-select adapter hook | Before moving Tom Select code |
| Tooltips | Tooltip intent/content attributes | Tippy instance lifecycle and visual treatment | Tooltip adapter hook | Before moving tooltip code |

## When Hooks Should Be Implemented

Hooks should not be added just because the boundary map exists.

They should be implemented in the first code slice that actually needs one of these transitions:

1. Moving current-template behaviour out of core runtime modules.
2. Moving presentation-library behaviour out of the current stable bundle.
3. Introducing a future pack initializer.
4. Creating a real `powercrud_daisyui` app.
5. Replacing direct visual calls with adapter-owned rendering.

The expected order is:

1. Choose one mixed area.
2. Add or confirm focused characterization tests for the behaviour being moved.
3. Introduce the smallest hook needed for that area.
4. Move only the adapter-owned behaviour.
5. Preserve core contracts and the stable public entry.

## Characterization Safeguards To Keep

No Phase 6 tests were needed because classification was possible from existing code and coverage. These tests should be added before moving the related code:

1. Native-select restore before moving Tom Select implementation.
2. Duplicate modal cleanup before moving modal adapter code.
3. Optional-filter removal/reset without a selected favourite before changing filter/list state ownership.
4. Selection-aware disabled visuals before extracting visual hooks.
5. Inline error popover rendering before moving popover presentation.
6. Row-action cloned-menu HTMX execution before extracting floating-menu behaviour.

## Non-Goals Preserved

Phase 6 did not create:

1. `powercrud_daisyui`
2. Separate pack JavaScript
3. `initPowercrudPack(fragment)`
4. Template-pack loader code
5. New public static asset paths

Those remain future implementation decisions.
