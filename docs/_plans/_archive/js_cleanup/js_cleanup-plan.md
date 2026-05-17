# JavaScript Cleanup Plan

## Status

Phase 1 inventory and classification write-up is complete. Phase 2 browser safety rails are in place for the main shared-runtime, DaisyUI-specific, and boundary behaviours identified by the audit. Phase 3 split the current public bundle into internal ES modules while keeping the stable public entry path. Phase 4 centralised shared runtime initialisation, once-only listener registration, and repeated-init idempotency. Phase 5 reduced cross-control coupling with narrow helper boundaries and did not introduce a broad state-management abstraction. Phase 6 proved the future template-pack boundary and synced the template-pack planning docs to the current runtime truth. Phase 7 documented the internal runtime architecture, added targeted maintainer comments, validated the current browser/runtime gate, and closed the JavaScript cleanup plan.

## Next

1. Treat JavaScript cleanup Phases 1 through 7 as complete.
    1. Use [Phase 7 handover](phase7-handover.md) as the current new-agent briefing point.
    2. Use the internal runtime README at `src/powercrud/static/powercrud/js/README.md` as the source-adjacent architecture guide.
    3. Use [Phase 6 boundary findings](phase6-boundary-findings.md) as the template-pack boundary decision record.
2. Keep actual template-pack extraction deferred until an explicit extraction phase is approved.
3. Continue to preserve the stable public entry path and manual `type="module"` loading contract.

## Phase 3 Packaging Decision

1. [x] Proceed with real ES-module source splitting for the remaining Phase 3 slices.
2. [x] Keep bundled/Vite mode as the primary packaged path.
    1. [x] `src/config/static/js/main.js` continues to import the stable package entry.
    2. [x] Downstream bundled users should continue to load the generated Vite asset through `django-vite` and the manifest.
    3. [x] Downstream bundled users should not hard-code hashed `powercrud-*.js` filenames.
3. [x] Keep manual mode on a stable entry path, but update the contract from classic script to module script.
    1. [x] Manual users should load only `{% static 'powercrud/js/powercrud.js' %}`.
    2. [x] Manual users should use `<script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>`.
    3. [x] Manual users do not need to know or load the internal imported module files directly.
4. [x] Treat old manual classic-script loading as a compatibility break to document before release.
    1. [x] Old usage `<script defer src="{% static 'powercrud/js/powercrud.js' %}"></script>` will no longer be valid once `powercrud.js` contains imports.
    2. [x] Stable docs must call out the manual-mode `type="module"` change.

## Phase 1: Inventory And Risk Map

1. [x] Map the current `powercrud.js` behaviours into named areas.
    1. [x] Identify filter and optional-filter behaviour.
    2. [x] Identify saved-favourites and current-view-state behaviour.
    3. [x] Identify list-column chooser behaviour.
    4. [x] Identify toolbar layout, dropdown placement, and row-action menu behaviour.
    5. [x] Identify inline-edit and dependency-refresh behaviour.
    6. [x] Identify bulk-selection and bulk-edit behaviour.
    7. [x] Identify modal, tooltip, and third-party widget initialisation.
2. [x] Map current selectors and `data-*` attributes used by each behaviour area.
3. [x] Identify global listeners and classify them as once-only page listeners or per-fragment initialisation.
4. [x] Classify each behaviour area as core, DaisyUI-specific, or boundary/unclear.
    1. [x] Core means behaviour that depends only on PowerCRUD semantics and stable `data-*` contracts.
    2. [x] DaisyUI-specific means behaviour that depends on DaisyUI markup, classes, modal APIs, visual conventions, or pack-owned styling.
    3. [x] Boundary/unclear means behaviour that currently mixes core state semantics with DaisyUI-specific presentation.
5. [x] Produce a short dependency map showing which features update or depend on each other.
6. [x] Identify browser-test coverage for each behaviour area.
7. [x] Record the classification table in the notes before implementation starts.

## Phase 2: Add Boundary Safety Rails

1. [x] Add focused browser tests for high-risk shared-runtime behaviours before refactoring internals.
    1. [x] Favourite state after filter changes remains selected or dirty as appropriate.
    2. [x] Favourite state after page-size changes is preserved or marked dirty as appropriate.
    3. [x] Reset view clears stored filters, page size, visible columns, and selected favourite state.
    4. [x] Favourite delete clears browser-side selected and dirty state.
    5. [x] Inline edit works when visible columns are hidden.
    6. [x] Column chooser draft state resets when closed without saving.
    7. [x] Tooltip and searchable-select initialisation remains idempotent across HTMX swaps.
2. [x] Add focused browser tests for high-risk DaisyUI-specific behaviours that later pack JS would own.
    1. [x] Per-trigger modal-box classes are applied before the DaisyUI dialog opens.
    2. [x] Row action floating menus remain usable after being cloned and HTMX-processed.
    3. [x] Bulk edit success closes the current DaisyUI modal and clears selection.
3. [x] Keep tests behaviour-focused so the refactor can change internals without rewriting every assertion.

## Phase 3: Split Source Inside The Current Public Bundle

1. [x] Extract runtime shell, bundle guard, public globals, and top-level startup wiring.
    1. [x] Keep existing exported globals available.
    2. [x] Keep the current public static bundle path and template includes stable.
    3. [x] Run the focused lifecycle, tooltip, modal, and favourites smoke tests before continuing.
1A. [x] Introduce the first ES-module entry split and document the manual-mode loading contract.
    1. [x] Extract only a very small, behaviour-neutral runtime boundary that proves `powercrud/js/powercrud.js` can import internal module files.
    2. [x] Keep the public entry path as `powercrud/js/powercrud.js` for both bundled and manual users.
    3. [x] Update stable docs, especially `docs/mkdocs/guides/getting_started.md` and `docs/mkdocs/guides/styling_tailwind.md`, so manual users load the stable entry with `type="module"` instead of classic/deferred script loading.
    4. [x] Do not move feature behaviour in this slice; leave low-level utility extraction for Phase 3.2.
    5. [x] Run the packaging check and full Phase 2 browser file slice before continuing.
2. [x] Extract low-level DOM, storage, URL, HTMX, selector, and state utility helpers.
    1. [x] Keep this slice behaviour-neutral; do not redesign state ownership here.
    2. [x] Run the Phase 2 browser file slice before continuing.
3. [x] Extract filters, optional filters, page size, current view state, and reset view.
    1. [x] Preserve filter refresh, page-size refresh, optional-filter visibility, current-view persistence, and reset-view semantics.
    2. [x] Run the favourites, tooltip, bulk-selection filter, and list-options focused tests before continuing.
4. [x] Extract saved favourites.
    1. [x] Preserve favourite apply, selected state, dirty state, update, delete, inline save, and current-state comparison.
    2. [x] Run `test_filter_favourites.py` before continuing.
5. [x] Extract list-column chooser.
    1. [x] Preserve visible-column save/reset, last-column guard, draft reset on close, and current toolbar/dropdown placement behaviour.
    2. [x] Run `test_list_options.py` plus the favourite visible-column tests before continuing.
6. [x] Extract bulk selection and bulk edit.
    1. [x] Preserve row selection, shift selection, server selection persistence, selection-aware actions, bulk modal success handling, and bulk edit refresh behaviour.
    2. [x] Run `test_bulk_selection.py` before continuing.
7. [x] Extract inline edit and inline dependencies.
    1. [x] Preserve active-row lifecycle, save/cancel, validation recovery, hidden-column compatibility, searchable selects, focus rules, and dependent-field refresh.
    2. [x] Run `test_inline_editing.py` and `test_inline_dependencies.py` before continuing.
8. [x] Extract DaisyUI/current-template behaviours.
    1. [x] Include modal API handling, modal-box classes, Tippy setup, floating favourites panels, row-action floating menus, toolbar geometry, dropdown placement, spinners, icon toggles, disabled visual classes, and colour classes.
    2. [x] Keep shared PowerCRUD semantics in the already-extracted core modules; move only presentation/runtime glue that is tied to the current DaisyUI templates.
    3. [x] Run the Phase 2 browser file slice and any touched surrounding Playwright files before continuing.
9. [x] Commit each extraction slice separately after its focused tests pass.

## Phase 4: Centralise Shared Runtime Initialisation

0. [x] Add a persistent manual-static sample/test path that loads vendor globals and `powercrud/js/powercrud.js` through normal static tags.
    1. [x] Keep the existing Vite sample base unchanged.
    2. [x] Prove the browser follows the stable module entry's internal `runtime/*.js` imports.
    3. [x] Avoid hard-coded hashed Vite asset filenames in the manual-static path.
1. [x] Create a clear internal `initPowercrud(fragment)` path for shared per-fragment initialisation.
    1. [x] Keep existing public helper globals while adding `window.initPowercrud`.
    2. [x] Keep listener registration unchanged for the first lifecycle slice.
    3. [x] Add a matching fragment teardown helper for HTMX before-swap cleanup.
2. [x] Centralise once-only document and window listener registration.
    1. [x] Move listener registration and startup idempotency guards into `runtime/startup.js`.
    2. [x] Keep feature handler bodies in `powercrud.js` for this slice.
    3. [x] Preserve existing listener order, targets, and capture/bubble options.
3. [x] Make repeated initialisation idempotent for full-page loads, shell HTMX navigation, and HTMX swaps.
    1. [x] Keep same-DOM row selection intact across repeated `initPowercrud(document)` calls.
    2. [x] Preserve server-rendered selection hydration for new HTMX-swapped markup.
    3. [x] Guard manual-static repeated init against duplicate Tom Select wrappers, tooltip loss, and duplicate startup styles.
4. [x] Keep pack-specific initialisation behaviour separate enough that a later `initPowercrudPack(fragment)` can be introduced without rewriting core lifecycle rules.
    1. [x] Keep template/current-DaisyUI presentation hooks separate from the shared `initPowercrud(fragment)` lifecycle.
    2. [x] Do not introduce `initPowercrudPack(fragment)` yet; leave that for the future template-pack boundary proof.
5. [x] Preserve current compatibility while the public runtime still has one stable public entry path.
    1. [x] Keep bundled/Vite users on the existing manifest entry.
    2. [x] Keep manual users on `powercrud/js/powercrud.js` loaded with `type="module"`.

## Phase 5: Reduce Cross-Control Coupling

Detailed Phase 5 sequencing, caveats, handover, and sub-agent orchestration are tracked in [`phase5-plan.md`](phase5-plan.md).

1. [x] Add narrow helpers for reading and writing current list view state.
2. [x] Add narrow helpers for favourite selected and dirty state.
3. [x] Add narrow helpers for visible-column state and reset-view coordination.
4. [x] Add narrow helpers for selection and inline-row state where direct DOM updates currently leak across features.
5. [x] Avoid a large state-management abstraction unless the smaller helpers prove insufficient.

## Phase 6: Prove The Future Template-Pack Boundary

Detailed Phase 6 sequencing, classification categories, caveats, and orchestration are tracked in [`phase6-plan.md`](phase6-plan.md).

1. [x] Revisit the Phase 1 classification after the source split and lifecycle cleanup.
2. [x] Identify neutral `data-*` contracts that shared core owns.
3. [x] Identify behaviours that can later move to current-template or presentation-library adapter code without moving shared semantics.
    1. [x] Modal API calls and modal-box class application.
    2. [x] Tooltip library setup and visual treatment.
    3. [x] Floating favourites panel and row action menu presentation.
    4. [x] Toolbar geometry and DaisyUI dropdown placement.
    5. [x] Spinner, button, icon, disabled, and colour class treatment.
4. [x] Identify boundary/unclear behaviours that need either a neutral core event or a pack hook.
5. [x] Add characterization tests only where a boundary cannot be classified safely from existing coverage and code review.
6. [x] Update the template-pack plan before creating a `powercrud_daisyui` app or separate pack JS.

## Phase 7: Validate And Close Out

1. [x] Run focused or broad browser validation for every touched behaviour area.
    1. [x] `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.
    2. [x] `./runproj exec --command "./runtests --playwright"` passed, 48 selected tests.
2. [x] Run the full Playwright suite when the source split is complete.
3. [x] Decide that the backend regression suite is not required because Phase 7 did not change Python, templates, rendered `data-*` attributes, or server-side template contracts.
4. [x] Document the new internal runtime structure for future maintainers in `src/powercrud/static/powercrud/js/README.md`.
5. [x] Add human- and AI-readable JavaScript architecture documentation before closing the plan.
    1. [x] Explain the runtime design, ownership boundaries, public entry path, and manual/bundled loading contracts.
    2. [x] Map how the JavaScript files hang together, including startup/lifecycle, shared state helpers, current-template hooks, and feature runtimes.
    3. [x] Record enough context that future agents can navigate the architecture without reconstructing it from commits.
6. [x] Decide that template-pack Phase 2 can start only as extraction-prep: read the runtime README and Phase 6 boundary findings, then design the smallest hook needed for the first concrete movement before creating `powercrud_daisyui`, separate pack JavaScript, loader code, or new public static paths.
