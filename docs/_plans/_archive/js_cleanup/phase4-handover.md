# Phase 4 Handover: JavaScript Runtime Lifecycle

## Current State

Branch: `js_cleanup/phase_3`

Phase 4 is complete:

1. Phase 4.0 added a persistent manual-static sample/test path that loads local vendor globals and `powercrud/js/powercrud.js` through normal static tags.
2. Phase 4.2 introduced `window.initPowercrud(fragment)` as the shared per-fragment initializer and added a matching fragment teardown helper.
3. Phase 4.3 centralised once-only listener registration in `runtime/startup.js` while keeping feature handler bodies in `powercrud.js`.
4. Phase 4.4 hardened repeated same-DOM initialisation so live bulk-selection state survives repeated `window.initPowercrud(document)` calls.
5. The tracked Vite asset and manifest were rebuilt for the runtime changes.

Recent Phase 4 commits:

1. `8bc1fadd test(js-cleanup): add manual static asset smoke`
2. `c6f638fa refactor(js-cleanup): add shared fragment initializer`
3. `058d581c refactor(js-cleanup): centralize global listener registration`
4. `b5b1782b fix(js-cleanup): preserve selection across repeated init`

The agreed packaging decision remains active. Bundled/Vite users continue to use the manifest. Manual users keep the stable entry path and must use `type="module"`.

## Required Reading

Read these files before planning the next slice:

1. `AGENTS/AGENTS.md`
2. `AGENTS/AGENTS_planning.md`
3. `docs/_plans/js_cleanup/js_cleanup-plan.md`
4. `docs/_plans/js_cleanup/js_cleanup-notes.md`
5. `docs/_plans/js_cleanup/phase5-plan.md`
6. `docs/_plans/js_cleanup/powercrud-js-behaviour-inventory.md`
7. `docs/_plans/js_cleanup/powercrud-js-contract-map.md`
8. `docs/_plans/js_cleanup/powercrud-js-listeners-and-dependencies.md`
9. `docs/_plans/js_cleanup/powercrud-js-test-coverage-map.md`
10. `docs/_plans/template_packs/template_packs-plan.md` and `template_packs-notes.md` for future context only.

## Next Phase

Start Phase 5: reduce cross-control coupling.

The next slice should be planned read-only first and should stay narrow. Phase 5 should add small helpers for the state currently shared across controls; it should not introduce a large state-management abstraction unless the smaller helpers prove insufficient.

Phase 5 checklist from the plan:

1. Add narrow helpers for reading and writing current list view state.
2. Add narrow helpers for favourite selected and dirty state.
3. Add narrow helpers for visible-column state and reset-view coordination.
4. Add narrow helpers for selection and inline-row state where direct DOM updates currently leak across features.
5. Avoid a large state-management abstraction unless the smaller helpers prove insufficient.

## Orchestration Protocol

Run one Phase 5 slice at a time. Do not start multiple implementation agents in parallel for the same runtime boundary.

For each slice:

1. Brief one read-only sub-agent to plan that slice only.
2. The sub-agent must read all required JS cleanup plan and audit files, not just the main plan and notes.
3. The sub-agent must not edit files.
4. Review the slice plan before editing.
5. Implement only the accepted slice.
6. Run focused tests named for that slice.
7. Run the broader Phase 4 browser slice when the slice touches shared startup, lifecycle, module imports, or cross-feature state.
8. Update `js_cleanup-plan.md`, `js_cleanup-notes.md`, and this handover if the phase state changes.
9. Commit and push that slice before moving on.

If a test failure exposes ambiguous intended behaviour, stop and report before broadening scope.

## Compatibility And Non-Goals

Keep these contracts stable:

1. Public entry path: `powercrud/js/powercrud.js`
2. Manual loading form: `<script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>`
3. Bundled/Vite manifest entry: `config/static/js/main.js`
4. Existing public globals, including `window.initPowercrud`, searchable-select helpers, tooltip helpers, and `getCurrentFilters`
5. Existing `data-powercrud-*` and `data-inline-*` contracts
6. Existing HTMX event names and body custom events

Do not create `powercrud_daisyui`, separate pack JS, or `initPowercrudPack(fragment)` in Phase 5. Those remain future template-pack boundary work.

## Standard Verification Commands

Packaging check:

```bash
./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"
```

Broad lifecycle/browser slice:

```bash
./runproj exec --command "./runtests --playwright src/tests/playwright/test_manual_static_assets.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_inline_dependencies.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py"
```

Add narrower focused commands per slice based on the plan.
