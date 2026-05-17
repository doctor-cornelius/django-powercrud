# Phase 6 Plan: Prove The Future Template-Pack Boundary

## Status

Phase 5 is complete. The shared runtime now has clearer state ownership boundaries, but template-pack extraction has not started.

Phase 6 is the next active JavaScript cleanup phase. Its goal is to prove the boundary between shared PowerCRUD runtime semantics, current-template DOM assumptions, and presentation-library behaviour before any `powercrud_daisyui` app or separate pack JavaScript exists.

## Objective

Phase 6 should make the future template-pack split concrete enough that implementation can proceed later without guessing which behaviours belong in core and which belong near a pack.

The output should be a defensible boundary map, not a template-pack implementation.

## Classification Model

Use these working classifications. A behaviour may be marked as mixed if a single function currently spans more than one category.

1. Core runtime: template/framework independent PowerCRUD semantics, durable state, storage, HTMX/list refresh rules, custom events, and stable `data-powercrud-*` or `data-inline-*` contracts.
2. Current-template DOM adapter: code that depends on the current HTML shape, selectors, IDs, DOM placement, table/list layout, toolbar layout, or floating-panel geometry, but not necessarily on DaisyUI itself.
3. Presentation-library adapter: code that depends directly on DaisyUI, Tippy, Tom Select visual APIs, spinner markup/classes, icon classes, button classes, colour classes, or framework-specific modal APIs.
4. Mixed adapter boundary: code that combines core semantics with current-template or presentation-library behaviour and likely needs a neutral event, hook, or injected adapter before later extraction.
5. Characterization needed: code that is too risky to classify without a focused browser proof.

## Non-Goals And Caveats

1. Do not create `powercrud_daisyui` in Phase 6.
2. Do not create separate pack JavaScript in Phase 6.
3. Do not add `initPowercrudPack(fragment)` in Phase 6.
4. Do not add template-pack loader code or new public static asset paths in Phase 6.
5. Do not change the public manual-loading contract:

    ```html
    <script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>
    ```

6. Do not change the bundled/Vite manifest entry path.
7. Do not change stable `data-powercrud-*`, `data-inline-*`, public globals, storage keys, HTMX events, or custom event semantics unless Michael explicitly approves a later implementation slice.
8. Do not touch `CHANGELOG.md`; Michael owns changelog updates.
9. Treat the template-pack plan as future implementation guidance. Phase 6 may update it, but should not start extraction.

## Orchestration Approach

Proceed one slice at a time.

For each slice:

1. Brief one read-only sub-agent to plan that slice only.
2. The read-only sub-agent must read all JS cleanup plan and audit files, not just the active plan and notes.
3. The read-only sub-agent must not edit files.
4. The coordinator reviews the proposed slice plan before implementation starts.
5. Implement only the accepted slice.
6. Prefer docs and classification output over code changes.
7. Add characterization tests only when a boundary cannot be classified safely from existing code and coverage.
8. Run focused tests only for touched behaviour areas.
9. Update the relevant plan, notes, handover, and template-pack docs.
10. Commit and push the completed slice before starting the next slice.
11. Stop and report back if a slice would require pack extraction, public contract changes, or a broad rewrite.

Do not run multiple implementation agents against the same runtime boundary in parallel. Read-only planning agents are useful for boundary review; implementation should stay coordinated because these modules share public contracts and browser coverage.

## Required Reading For Every Phase 6 Planning Agent

Every read-only Phase 6 planning agent must read:

1. `AGENTS/AGENTS.md`
2. `AGENTS/AGENTS_planning.md`
3. `docs/_plans/js_cleanup/js_cleanup-plan.md`
4. `docs/_plans/js_cleanup/js_cleanup-notes.md`
5. `docs/_plans/js_cleanup/phase5-plan.md`
6. `docs/_plans/js_cleanup/phase5-handover.md`
7. `docs/_plans/js_cleanup/phase6-plan.md`
8. `docs/_plans/js_cleanup/powercrud-js-behaviour-inventory.md`
9. `docs/_plans/js_cleanup/powercrud-js-contract-map.md`
10. `docs/_plans/js_cleanup/powercrud-js-listeners-and-dependencies.md`
11. `docs/_plans/js_cleanup/powercrud-js-test-coverage-map.md`
12. `docs/_plans/template_packs/template_packs-plan.md`
13. `docs/_plans/template_packs/template_packs-notes.md`

The agent should then inspect the current runtime files relevant to that slice, not rely only on the older audit snapshot.

## Slice 6.0: Refresh The Runtime Boundary Map

Status: complete.

Objective:

Reclassify the post-Phase-5 runtime against the older audit and current code.

Scope:

1. Review `powercrud.js` and every file under `src/powercrud/static/powercrud/js/runtime/`.
2. Classify each module and major function group using the Phase 6 classification model.
3. Identify places where one function currently spans multiple categories.
4. Produce a boundary table in `js_cleanup-notes.md`.

Likely verification:

1. `git diff --check`.
2. No runtime tests if the slice is docs-only.

Exit criteria:

1. The current runtime map is documented.
2. The next slice can focus on contracts without rereading the full runtime from scratch.

Result:

Slice 6.0 refreshed the runtime boundary map in `js_cleanup-notes.md` against the post-Phase-5 module split.

The updated map confirms:

1. Low-level DOM, URL, storage, state, and HTMX helpers are core runtime helpers.
2. `runtime/current-template.js` is adapter-heavy, but it contains both current-template DOM assumptions and direct presentation-library dependencies, so later work should not treat it as purely DaisyUI-specific.
3. Favourites, list columns, bulk actions, inline edit, searchable selects, and the entry listener shell each contain mixed boundaries that later slices need to classify more precisely before extraction.
4. No production code, tests, public static paths, pack initializers, or template-pack assets were introduced.

## Slice 6.1: Core-Owned Contract Pass

Status: complete.

Objective:

Identify the neutral shared contracts that core runtime must own.

Scope:

1. Identify core-owned `data-powercrud-*` contracts.
2. Identify core-owned `data-inline-*` contracts.
3. Identify public globals that must remain stable.
4. Identify custom events, HTMX events, body events, storage keys, and URL/query-state contracts.
5. Produce a core-owned contract table in `js_cleanup-notes.md`.

Likely verification:

1. `git diff --check` for docs-only work.
2. Packaging and focused browser tests only if a contract proof requires test edits.

Exit criteria:

1. Core-owned contracts are explicit enough to protect from accidental pack migration.
2. Any uncertain contracts are marked for characterization rather than silently classified.

Result:

Slice 6.1 added a core-owned contract table to `js_cleanup-notes.md`.

The table records:

1. Shared `data-powercrud-*` contracts for list roots, filters, favourites, visible columns, selection, and searchable-select opt-in semantics.
2. Shared `data-inline-*` contracts for inline row discovery, lifecycle, dependencies, and validation payloads.
3. Public globals that remain stable while implementation boundaries change.
4. HTMX lifecycle events, body custom events, storage keys, URL/query-state rules, and list-refresh headers that core owns.
5. Uncertain contracts to carry into Slice 6.3 or Slice 6.4 instead of forcing them into core.

No production code, tests, public contract changes, pack initializers, or template-pack assets were introduced.

## Slice 6.2: Current-Template And Presentation Adapter Pass

Status: complete.

Objective:

Identify behaviours that can later move toward adapter or pack-owned code without moving shared semantics.

Scope:

1. Classify `runtime/current-template.js` by function group.
2. Separate current-template DOM adapter concerns from presentation-library adapter concerns.
3. Include modals, modal-box classes, tooltips, toolbar geometry, row-action menus, favourites floating panels, list-column dropdown placement, spinners, disabled visuals, icon classes, and colour classes.
4. Produce a future adapter-owned behaviour table in `js_cleanup-notes.md`.

Likely verification:

1. `git diff --check` for docs-only work.
2. If tests are added later, focus on the relevant files such as `test_modal_crud.py`, `test_tooltips.py`, `test_row_actions_menu.py`, `test_list_options.py`, `test_filter_favourites.py`, or `test_bulk_selection.py`.

Exit criteria:

1. Future adapter-owned behaviours are explicit.
2. Behaviours that are only current-template-specific are not collapsed into "DaisyUI-specific" without evidence.

Result:

Slice 6.2 added future adapter-owned behaviour tables to `js_cleanup-notes.md`.

The pass separates:

1. Current-template DOM adapter behaviours such as toolbar/filter-panel geometry, floating row-action/favourites panels, list-column chooser shell behaviour, filter-panel display shell, and bulk-selection display containers.
2. Presentation-library adapter behaviours such as DaisyUI/modal classes, Tippy runtime setup, Tom Select enhancement, spinner markup, disabled visual classes, favourite icon/colour treatment, list-column disabled visuals, and inline error popover presentation.
3. Mixed behaviours that need Slice 6.3 hook or characterization decisions before any later extraction.

No production code, tests, public contract changes, pack initializers, or template-pack assets were introduced.

## Slice 6.3: Boundary Hook And Characterization Decisions

Status: complete.

Objective:

Identify mixed behaviours that need a hook, neutral event, injected adapter, or characterization test before future extraction.

Scope:

1. Review mixed areas such as searchable selects, filter panel presentation, favourite trigger presentation, selection-aware disabled visuals, inline error popovers, inline spinners, and bulk modal close after success.
2. For each mixed behaviour, decide one of:
    1. stay core
    2. move later as current-template adapter
    3. move later as presentation-library adapter
    4. needs neutral event
    5. needs injected hook
    6. needs characterization test
3. Record the decision table in `js_cleanup-notes.md`.

Likely verification:

1. `git diff --check` for docs-only work.
2. Focused browser tests only where characterization tests are added.

Exit criteria:

1. The next implementation phase can see which boundaries are ready and which require hooks or tests first.
2. No mixed behaviour is forced into a category just to simplify the table.

Result:

Slice 6.3 added a boundary decision table to `js_cleanup-notes.md`.

The decision pass records:

1. Which mixed behaviours can later move through injected adapter hooks.
2. Which behaviours likely need neutral core events before extraction.
3. Which behaviours can stay core while delegating presentation details.
4. Which under-covered behaviours are future extraction safeguards rather than Phase 6 blockers.

The current decision is that no characterization test is required merely to complete the Phase 6 classification. Slice 6.4 can close as a no-production-code slice unless Michael chooses to add the optional future-safeguard tests now.

## Slice 6.4: Characterization Tests If Needed

Status: complete.

Objective:

Add focused browser coverage only for boundaries that cannot be classified safely from existing tests and code review.

Scope:

1. Add tests only for real boundary risk identified in Slice 6.3.
2. Keep tests behaviour-focused and tied to existing user-visible contracts.
3. Avoid broad test sprawl.

Candidate behaviours:

1. Duplicate modal cleanup.
2. Spinner restoration.
3. Selection-aware disabled visual state.
4. Optional-filter removal/reset without favourites.
5. Tom Select native restore or repeated initialisation edge cases.

Likely verification:

1. Focused Playwright files for touched behaviours.
2. Packaging check if static assets are rebuilt.

Exit criteria:

1. Each added characterization test protects a boundary decision.
2. No production extraction happens in this slice.

Result:

Slice 6.4 closed as docs-only. A read-only test-planning pass confirmed that no characterization test is required to complete the Phase 6 boundary classification.

The optional tests identified in Slice 6.3 should stay attached to the later extraction slices where they protect moving code:

1. Native-select restore when Tom Select is destroyed before HTMX swaps.
2. Duplicate modal cleanup.
3. Optional-filter removal/reset without a selected favourite.
4. Selection-aware disabled visual state.
5. Inline error popover rendering after extraction.
6. Row-action cloned-menu HTMX execution after extraction.

No browser tests were added or run because this slice made no code or test changes.

## Slice 6.5: Template-Pack Plan Sync

Status: complete.

Objective:

Update the template-pack plan and notes so future implementation starts from current runtime truth.

Scope:

1. Record that `window.initPowercrud(fragment)` already exists.
2. Record that the stable public entry remains `powercrud/js/powercrud.js`.
3. Record that manual loading requires `type="module"`.
4. Record that `initPowercrudPack(fragment)` remains future, not current.
5. Make template-pack Phase 2 depend on the Phase 6 boundary map rather than immediate extraction.
6. Add a prerequisite checklist for starting actual pack JavaScript extraction.

Likely verification:

1. `git diff --check`.
2. No runtime tests if the slice is docs-only.

Exit criteria:

1. `docs/_plans/template_packs/` no longer contradicts the post-Phase-6 runtime state.
2. The next agent can tell what must be proven before any pack JavaScript extraction starts.

Result:

Slice 6.5 synced the template-pack plan and notes to the post-Phase-6 runtime truth.

The template-pack docs now record:

1. `powercrud/js/powercrud.js` remains the stable public runtime entry.
2. Manual users load that entry with `type="module"`.
3. Bundled/Vite users continue through `config/static/js/main.js`.
4. `window.initPowercrud(fragment)` already exists.
5. `initPowercrudPack(fragment)` remains future.
6. No `powercrud_daisyui`, separate pack JavaScript, loader helper, or new public static asset path exists yet.

Phase 6 also added [`phase6-boundary-findings.md`](phase6-boundary-findings.md) as the durable boundary decision record and [`phase6-handover.md`](phase6-handover.md) as the new-agent briefing point.

## Standard Verification Commands

Packaging check:

```bash
./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"
```

Broad boundary/browser slice:

```bash
./runproj exec --command "./runtests --playwright src/tests/playwright/test_manual_static_assets.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_inline_dependencies.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py"
```

Use narrower focused commands first. Only run the broad slice when implementation or characterization tests warrant it.

## Handover

Use [`phase6-handover.md`](phase6-handover.md) as the durable new-agent briefing point after Phase 6. Use [`phase6-boundary-findings.md`](phase6-boundary-findings.md) for the detailed boundary decisions and hook timing.

Phase 6 is complete on branch `js_cleanup/phase_6`. Future agents should start read-only, verify the branch and clean worktree, preserve the public JavaScript contract, and keep actual template-pack extraction deferred until Michael approves a later extraction phase.
