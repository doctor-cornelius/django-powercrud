# Phase 6 Handover: Future Template-Pack Boundary

## Current State

Branch: `js_cleanup/phase_6`

Phase 6 is complete through Slice 6.5. It proved the future template-pack boundary but did not implement a template pack. The durable boundary summary is [`phase6-boundary-findings.md`](phase6-boundary-findings.md).

Current runtime truth:

1. `powercrud/js/powercrud.js` remains the stable public entry.
2. Manual users load it with:

    ```html
    <script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>
    ```

3. Bundled/Vite users continue through `config/static/js/main.js`.
4. `window.initPowercrud(fragment)` exists and is the public fragment initializer.
5. `initPowercrudPack(fragment)` remains future.
6. No `powercrud_daisyui`, separate pack JS, loader code, or new public static paths were created.
7. Michael owns `CHANGELOG.md`.

## Boundary Result

Shared core owns durable PowerCRUD semantics: object-list roots, HTMX/list refresh, query/view state, favourites state, visible columns, bulk selection, inline lifecycle, public globals, storage keys, and stable `data-powercrud-*` / `data-inline-*` contracts.

Future adapter or pack code may own current-template and presentation behaviour: toolbar geometry, floating panels, DaisyUI modal handling, Tippy setup, Tom Select implementation, spinner markup, disabled visual classes, icon/colour treatment, and inline error popover presentation.

Mixed areas need hooks or neutral events before extraction: `initPowercrud()` adapter ordering, favourites panel opening, selection-aware visual state, inline focus/errors, bulk modal success, row-action cloned-menu HTMX execution, and list-column chooser shell.

## Before Starting Pack Extraction

1. Read `phase6-boundary-findings.md`, `phase6-plan.md`, `js_cleanup-notes.md`, and the refreshed `docs/_plans/template_packs/` docs.
2. Do not create `powercrud_daisyui` or separate pack JS as a first step.
3. First design the adapter hook/orchestration contract.
4. Add characterization safeguards only where code is actually being moved.
5. Preserve the stable public entry and manual module-script contract.

## Useful Future Safeguards

1. Native-select restore before moving Tom Select implementation.
2. Duplicate modal cleanup before moving modal adapter code.
3. Optional-filter removal/reset without a selected favourite before changing filter/list state ownership.
4. Selection-aware disabled visuals before extracting visual hooks.
5. Inline error popover rendering before moving popover presentation.
6. Row-action cloned-menu HTMX execution before extracting floating-menu behaviour.
