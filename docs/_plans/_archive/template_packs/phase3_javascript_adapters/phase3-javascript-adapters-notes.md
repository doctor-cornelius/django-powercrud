# Phase 3 Reusable JavaScript Adapters Notes

## Purpose

These notes support [`phase3-javascript-adapters-plan.md`](phase3-javascript-adapters-plan.md), the active child plan for Master Phase 3. They record the audit evidence, accepted ownership boundaries, deferred decisions, and implementation-slice rationale needed to extract reusable JavaScript adapters without changing current DaisyUI behaviour.

## Starting Contract

1. `powercrud/js/powercrud.js` and `window.initPowercrud(fragment)` remain stable public runtime contracts.
2. Manual-static and bundled/Vite loading both remain supported and automatically compose compatible DaisyUI behaviour during extraction.
3. PowerCRUD core keeps durable request, state, URL, HTMX, selection, filtering, favourites, inline-editing, semantic-attribute, event, and storage behaviour.
4. DaisyUI/current-template presentation and library behaviour may move only after focused characterization proves the boundary.
5. No public adapter initializer, pack selector, metadata API, new static entry, or template-pack packaging change is assumed by this planning effort.

## Inputs

1. Master Phase 3 contract: [`../template_packs-master-plan.md`](../template_packs-master-plan.md) and [`../template_packs-master-notes.md`](../template_packs-master-notes.md).
2. Previous boundary decision record: [`../../_archive/js_cleanup/phase6-boundary-findings.md`](../../_archive/js_cleanup/phase6-boundary-findings.md).
3. Current runtime guide: [`../../../../src/powercrud/static/powercrud/js/README.md`](../../../../src/powercrud/static/powercrud/js/README.md).
4. Phase 3 evidence record: [`phase3-javascript-boundary-audit.md`](phase3-javascript-boundary-audit.md).

## Plan

### Phase 3.0: Characterize And Plan Adapter Extraction

The audit will record verified current behaviour, existing coverage, genuine gaps, candidate ownership boundaries, and an evidence-backed extraction order. The primary agent will reconcile parallel read-only findings; sub-agents do not edit planning documents.

The first audit wave confirms that current runtime files are mixed ownership units, so later extraction is behavior-level. The independent challenge review ratifies Tippy lifecycle as the best-evidenced first DaisyUI presentation boundary: tooltip behavior is concentrated, existing manual and browser coverage is strong, and core can preserve stable tooltip globals while automatically composing the default adapter. The complete evidence is in [`phase3-javascript-boundary-audit.md`](phase3-javascript-boundary-audit.md).

Any unresolved choice affecting public compatibility, core/framework ownership, or the first extraction's presentation semantics becomes a blocker record rather than an implementation assumption. Reversible internal detail remains deferred until the first extraction proves the smallest viable seam.

### Phase 3.1: Extract DaisyUI Tooltip Lifecycle

`template_pack/3.1` adds `runtime/daisyui-tooltip-adapter.js` with one internal factory:

```js
createDaisyuiTooltipLifecycleAdapter({
    global,
    documentObject,
    warnMissingDependency,
})
```

It returns `init`, `hide`, `destroy`, `scheduleInit`, and `scheduleResizeInit`. It owns Tippy dependency handling, semantic/overflow/lazy tooltip behavior, theme/placement, lazy request cleanup, and tooltip timers. `powercrud.js` remains the composition and lifecycle owner, directly constructs the factory, and forwards its `init`, `hide`, and `destroy` methods through the existing public tooltip globals. No adapter registry or public initializer is created.

The slice preserves every existing tooltip call path: fragment initialization, HTMX request/swap/settle lifecycle, resize refresh, list-column and favourites detached panels, cloned row-action menus, and changed favourite triggers. It must not reorder searchable selects, object-list bootstrap, tooltip initialization, bulk's early before-swap return, raw-favourites processing, or inline post-settle behavior.

Before movement, add a Vite smoke covering stable runtime/global loading, tooltip initialization, and clean browser/page errors. Add a focused lifecycle test proving one instance per trigger after repeated initialization, destruction before HTMX replacement, one fresh replacement instance, no stale Tippy root, and no lazy-tooltip replay after its detached source resolves. Retain existing manual-static and tooltip coverage. The slice regenerates normal package assets only if the source change changes the built hash, then runs focused asset/browser checks and the canonical full regression.

The just-in-time Phase 3.1 maps found no blocker and refined two details. `current-template.js` must receive adapter `init`, `destroy`, and scheduled-init callbacks for cloned row-action menus and changing favourites triggers; leaving its direct `_tippy.destroy()` would make adapter ownership incomplete. Existing close functions remove detached panels without explicitly destroying their Tippy instances, but changing that behavior is outside this pure extraction and is not required by the HTMX/lazy-detachment contract.

The unique test gaps are one Vite-backed runtime/global/error smoke, direct observation that the last pre-swap Tippy instance is destroyed before a real `#filtered_results` replacement and replaced exactly once, and a delayed lazy response whose source trigger is detached before resolution. Existing tooltip nodes will be strengthened for the first two where practical; the detached lazy response needs one new focused node because the current pointer-leave test protects a different connectivity condition.

The completed extraction keeps the existing globals and lifecycle call sites in `powercrud.js`, injects only the three tooltip callbacks still needed by `current-template.js`, and moves the Tippy-specific implementation into the private adapter. The legitimate source change regenerated the bundled JavaScript and manifest hash. No compatibility path was removed.

The focused gate passed 19 packaging tests and 9 Playwright tests covering manual-static and bundled/Vite loading. Ruff passed for the affected Python tests and `git diff --check` was clean. Test discipline: one new browser test uniquely protects delayed lazy completion after HTMX detaches its trigger; two existing tooltip tests were strengthened for the Vite public-runtime smoke and pre-swap destruction/single replacement lifecycle. No parallel test was added for behavior already covered.

### Phase 3.2: Extract DaisyUI Searchable-Select Lifecycle

Before movement, characterize native-select restoration during HTMX replacement and exactly one new Tom Select wrapper after reinitialization. The adapter then owns Tom Select construction, plugins, dropdown presentation, and destroy/restore behavior. Core retains semantic opt-in attributes, values, list/inline state, and the existing public searchable-select forwards.

The just-in-time Phase 3.2 maps found no blocker. The smallest seam keeps semantic candidate discovery, root scanning, visibility decisions, and value synchronization in `searchable-selects.js`. A private adapter can own dependency resolution, construction and plugin fallback, single/multi settings, disabled bridging, native hide/restore, DaisyUI/Tom Select classes, inline/favourites presentation, clear-button behavior, and instance destruction. Its private interface is `ensureAvailable`, `enhanceSingle`, `enhanceMultiple`, and `destroy`; `powercrud.js` composes it without adding a public adapter API.

The one genuine coverage gap is teardown truth during a real HTMX replacement. The existing idempotence browser test is strengthened to observe the original instance and wrapper at `htmx:beforeSwap`, native-select restoration before removal, a distinct replacement select/instance/wrapper, and repeated initialization retaining exactly that fresh instance. The existing manual-static and Vite smoke tests also gain the already-public destroy-global assertion. No new test is justified; existing filter, bulk, modal, inline-save, inline-focus, and dependency tests already own the remaining behavior.

The completed extraction keeps `searchable-selects.js` responsible for semantic candidate checks, visibility decisions, root/self scanning, and value synchronization. `powercrud.js` privately composes `daisyui-searchable-select-adapter.js`, whose four callbacks own Tom Select availability, enhancement, presentation, native restoration, and destruction while the established public globals continue to forward through the core runtime. The moved `table-cell` source token was retained so Tailwind's generated utility set and CSS asset remain unchanged; only the legitimate bundled JavaScript hash changed.

The focused gate passed 19 packaging tests and 10 Playwright tests covering manual-static and Vite loading, HTMX restoration/replacement, inline save/focus/dependencies, filter single/multi behavior, modal creation, and bulk editing. Ruff passed for affected Python tests and `git diff --check` was clean. Test discipline: zero new tests, three existing tests strengthened, and one brittle private-source assertion removed rather than relocated. No coverage was duplicated.

### Phase 3.3: Extract DaisyUI Modal Lifecycle

Characterize duplicate-dialog cleanup and refresh-on-close first. Move dialog classes, close presentation, and duplicate cleanup only; core retains bulk/form response decisions, list refresh semantics, and events.

The just-in-time Phase 3.3 maps found no blocker. The private adapter can own duplicate cleanup, per-trigger modal-box classes, and native dialog closing. `current-template.js` remains the coordinator: it resolves the semantic trigger and object-list-scoped modal, arms the existing refresh-on-close WeakMap/WeakSet bridge, and passes a before-close callback so programmatic bulk-success close disarms any pending refresh before the native `close` event fires. Click-capture order, the second `htmx:beforeRequest` application, modal IDs/targets, server triggers, and template-owned close/backdrop controls remain unchanged.

No new test is justified. The existing per-trigger class test is strengthened by introducing a closed duplicate before a real modal action and proving the open dialog survives as the only instance. The existing flagged row-action close test is strengthened to open and close twice across real HTMX list refreshes, proving one refresh per close and one listener per dialog. Existing server, modal CRUD, cloned-row-action, bulk-success, manual-static, and packaging coverage owns the remaining contract.

The completed extraction privately composes `daisyui-modal-adapter.js` from the stable entry. The adapter owns per-trigger box classes, the exact open-over-closed/newest duplicate rule, document-wide dialog closing, and native `close()` calls. `current-template.js` retains trigger/root resolution, refresh-on-close listener state, connected-root checks, and the before-close disarm callback used by programmatic bulk success. No public global, modal hook, ID, target, event, server outcome, or template close/backdrop control changed.

The focused gate passed 22 server/packaging tests and 6 Playwright tests across manual-static loading, modal CRUD, duplicate cleanup, per-trigger sizing, cloned row actions, repeated refresh-on-close, and bulk refresh behavior. Ruff passed for affected Python tests and `git diff --check` was clean. Test discipline: zero new tests and two existing behavioral tests strengthened; packaging/manual-loading assertions were extended without testing private helper methods.

The fresh Phase 3.3 compatibility reviewer found no blocking issue and confirmed that duplicate selection, core refresh state, callback-before-close ordering, click/HTMX listener order, IDs/hooks/events, loading modes, and generated assets remain compatible. Its two low-severity test observations were resolved by extending the existing duplicate scenario to cover both newest-closed and open-over-closed behavior, and by waiting for network idle between repeated close-refresh cycles.

The isolated canonical checkpoint then passed in full: 934 server tests passed with 78 Playwright tests deselected in the first stage, followed by all 78 Playwright tests passing with 934 server tests deselected. The earlier overlapping diagnostic run was discarded because a concurrently started targeted process dropped the shared test database; it did not represent a product failure and the clean isolated rerun supersedes it.

### Phase 3.4: Extract Action And Selection Presentation

Characterize disabled reasons, hoverability, visual classes, and spinners before movement. The adapter owns visual treatment only; core retains selection state, count rules, requests, and event timing.

The just-in-time Phase 3.4 maps found no blocker. The smallest private adapter owns dynamic row-action disabled presentation, selection-aware disabled presentation, and generic form/button spinner markup plus restoration state. Core retains lazy row-action requests and hidden decisions, selection count/minimum/reason calculation, bulk confirmation enablement, click prevention, HTMX listeners, and event ordering. The adapter keeps separate row-action and selection cleanup rules so re-enabling a selection-aware button removes only its own minimum-reason tooltip, not an unrelated semantic tooltip.

No new test is justified. The existing bulk-selection smoke is strengthened for disabled classes, hover-preserving computed styles, visible reason tooltip, blocked click, live enablement, and disabled restoration. The existing lazy row-action test records button-spinner appearance without a sleep and proves exact trigger restoration plus disabled-link hoverability. The existing filtered bulk-edit test records form-spinner state at real `htmx:beforeRequest`, restoration after an intercepted response error, and then the unchanged success path. Server coverage already owns arithmetic, permission/reason precedence, outcomes, and initial rendering.

The completed extraction privately composes `daisyui-action-selection-adapter.js`. It owns the two intentionally different disabled-tooltip cleanup paths and idempotent generic form/button spinner state. `current-template.js` still owns lazy row-action request/outcome and menu lifecycle, `bulk-actions.js` still owns selection arithmetic and bulk control state, and `powercrud.js` still owns listener order and request timing. Inline save presentation remains in `current-template.js` for Phase 3.5.

The focused gate passed 151 server/packaging tests and 4 Playwright tests across live selection presentation, blocked disabled actions, visible disabled reasons, lazy row-action state/spinner restoration, bulk form spinner error restoration followed by success, and manual-static loading. Ruff passed for affected Python tests and `git diff --check` was clean. Test discipline: zero new tests, three existing behavioral tests strengthened, one loading-mode test extended, and three brittle private-source assertions removed rather than relocated.

### Phase 3.5: Extract Inline Presentation

After searchable-select extraction, characterize and move inline popover, focus-routing, and spinner presentation only. Inline save/cancel/dependency/validation/guard behavior remains core-owned.

The just-in-time Phase 3.5 maps found no blocker. The smallest private adapter owns focus-target resolution and focus/open/highlight presentation against the existing searchable-select instance, all body-level field-error popover DOM and cleanup, and the inline save-button spinner. `inline-edit.js` retains pending focus/highlight state, one-row guards, activation ordering, searchable initialization, dependencies, save/cancel decisions, validation payloads, events, and refresh policy. Table width locking and row-attention orchestration remain in core because moving them is not required by this bounded slice.

No new test is justified. The existing validation-recovery test records spinner appearance without a sleep and proves the replacement save control is restored before continuing through popover dismissal and successful save. The existing searchable-focus test is strengthened to prove exactly one wrapper, actual focus on the Tom Select control input, and an open visible dropdown. Existing validation input/cancel/success cleanup, one-active-row focus, dependencies, guards, hidden columns, and server contracts own the remaining behavior.

The completed extraction privately composes `daisyui-inline-presentation-adapter.js`. It owns focus-target resolution and presentation, body-level error-popover creation/positioning/dismissal/orphan cleanup, legacy inline-Tippy cleanup, and inline save-spinner markup. `inline-edit.js` retains pending semantic state and every request, dependency, validation, guard, event, and refresh decision. Searchable-select construction stays in its existing adapter; the inline adapter only routes focus to and opens an established instance.

The focused gate passed 65 server/packaging tests and 11 Playwright tests covering manual-static loading, the complete inline behavior file, and real dependency swaps. Ruff passed for affected Python tests and `git diff --check` was clean. Test discipline: zero new tests, two existing behavioral tests strengthened, one loading-mode test extended, and two brittle private-source tests removed rather than relocated; the existing CSS contract assertion remains.

### Phase 3.6: Extract List-Column Presentation

Move chooser shell, focus, placement, and disabled visuals while preserving visible-column state, persistence, last-column protection, requests, detached-panel lifecycle, and focused template hooks in core.

The just-in-time Phase 3.6 maps found no blocker. The smallest private adapter owns cloning and preparing the hidden chooser shell, native and detached placement, reveal styling, first-checkbox focus scheduling, and the last-option visual classes. `list-columns.js` retains generated source IDs and detached association hooks, body append/removal, active references, HTMX/tooltips, aria/open state, draft restoration, last-column arithmetic/revert and semantic markers, persistence requests, outside/Escape/resize/before-swap teardown, and focused template hooks. The generic reveal helper remains temporarily in `current-template.js` for its Phase 3.7 favourites consumer.

No new test is justified. Existing chooser tests are strengthened for dynamic disabled visuals, first-checkbox focus and Escape focus return, save-time detached cleanup and immediate post-swap reopening, and vertical as well as horizontal viewport bounds. The manual-static smoke opens exactly one chooser after repeated initialization. Existing save/reset/persistence, overflow escape, wrapped placement, mutual-exclusion cleanup, inline compatibility, server state, focused overrides, and copy-command tests own the remaining behavior.

The completed extraction privately composes `daisyui-list-column-presentation-adapter.js`. It owns chooser-shell cloning, hidden preparation and reveal, native/detached placement, first-option focus, and DaisyUI disabled-option classes. `list-columns.js` retains every stable detached association hook, body-level lifecycle, HTMX and tooltip ordering, active/open/aria state, column arithmetic, persistence, request, and teardown decision. The generic reveal helper remains in `current-template.js` solely for the Phase 3.7 favourites consumer.

The focused gate passed 29 server/packaging tests and 12 Playwright tests. Ruff passed for affected Python tests and `git diff --check` was clean. Test discipline: zero new tests, four existing list-option tests strengthened, one manual-loading test extended, and one brittle private-source test removed rather than relocated. The independent checkpoint reviewer found no compatibility blocker and confirmed the ownership split, lifecycle ordering, stable hooks/globals, loading modes, and generated asset. Its one low-severity test observation led to replacing a direct-parent XPath with the stable option hook.

The first canonical browser stage then exposed an incorrect scope in that newly changed semantic-hook locator, not a product regression. The single test reproduced the issue, the locator was corrected, and the isolated canonical rerun passed in full: 931 server tests passed with 78 Playwright tests deselected, followed by all 78 Playwright tests passing with 931 server tests deselected.

### Phase 3.7: Extract Favourites And Filter-Panel Presentation

Separate panel display, clone/geometry, and presentation initialization from favourites/filter state, URL rules, and server events. Preserve raw-favourites handling before generic initialization and panel state across swaps.

The just-in-time Phase 3.7 maps found no blocker. The smallest private adapter owns the favourites shell clone, hidden preparation/reveal, viewport geometry, DaisyUI dropdown and heart/icon classes, searchable-select/tooltip presentation initialization, filter-panel visibility classes, filter icon classes, add-filter display, always-visible favourites toolbar, and the two existing deferred searchable-select initialization paths. Core retains all selection/dirty/storage/URL/request semantics, active detached-panel references, body append/removal, HTMX processing and events, semantic data/ARIA/tooltip content, filter open/preservation decisions, and swap ordering. Stable detached association hooks remain core-owned. `syncListToolbarWidth` stays in `current-template.js` because it jointly sizes the toolbar, filter panel, pagination, and view help.

No new test is justified. Five existing tests are strengthened for body-level fixed/clamped panel geometry and teardown state, raw server markup copied into the hidden template before one Tom Select wrapper is initialized, filter-panel presentation surviving a real swap and repeated initialization, dirty-to-clean heart colours, and manual-static composition. Existing server contracts, URL/result behavior, shell navigation, active-filter toggle presentation, Vite smoke, and focused templates own the remaining behavior.

The completed extraction privately composes `daisyui-filter-favourites-presentation-adapter.js`. It owns favourites shell cloning/preparation/reveal/geometry, dropdown and icon classes, presentation initialization, filter-panel and optional-filter visibility, and the preserved deferred searchable-select calls. `filter-favourites.js` retains semantic trigger content and every state/request/HTMX/detached lifecycle decision; `list-view-state.js` retains active-filter calculation and filter-panel preservation/open decisions. Raw response markup is still copied into the hidden template by the after-swap feature handler before generic initialization.

The focused gate passed 49 server/packaging tests and 9 Playwright tests across manual-static and Vite loading, server contribution contracts, focused templates, filter toggle and tooltip presentation, favourites apply/save/update/shell-return flows, raw-template enhancement order, detached geometry, and transient-control cleanup. Ruff passed for affected Python tests and `git diff --check` was clean. Test discipline: zero new tests, five existing behavioral tests strengthened, one manual-loading test extended, no duplicate coverage, and two pre-existing unused local bindings removed from the affected test file so its lint gate is clean. The one pre-extraction HTMX timing failure occurred before a new assertion and passed on the required targeted rerun without a code change.

### Phase 3.8: Extract Row-Action Floating-Menu Presentation

This remains last because it combines cloned body UI, lazy availability, HTMX processing, tooltips, and modal behavior. Core retains the response semantics; the adapter owns only the presentation shell and geometry after cloned-menu HTMX execution and cleanup are re-proven.

The just-in-time Phase 3.8 maps found no blocker. The smallest private, stateless, listener-free adapter owns only cloning the focused-template menu shell, hidden fixed preparation, viewport-clamped placement, and reveal. The current-template coordinator retains trigger/template lookup, active menu and trigger references, body append/removal, semantic floating-panel and ARIA hooks, all lazy fetch/state/permission/empty-menu decisions, spinner/busy state, HTMX processing, tooltip ordering, modal behavior, and every outside/Escape/pagehide/scroll/resize/before-swap teardown path. The menu's DaisyUI classes remain template-owned.

No new test is justified. Existing tests are strengthened for one direct-body fixed clone, both-axis viewport bounds, active-trigger ARIA and Escape cleanup, definitive removal before modal execution, fresh connected triggers across two real list-refresh cycles, and manual-static composition after repeated initialization. Existing lazy success/failure/hidden/disabled/tooltip coverage, server permission and endpoint contracts, focused override/copy coverage, Vite behavior, modal sizing, and favourite auto-apply guards own the remaining behavior. One brittle private-call source assertion is removed rather than relocated.

The completed extraction privately composes `daisyui-row-action-menu-presentation-adapter.js`. It owns only focused-template shell cloning, hidden fixed preparation, viewport placement, and reveal. `current-template.js` remains the row-action coordinator and retains all lazy fetch/state/permission decisions, spinners, active refs, association hooks, body lifecycle, HTMX and tooltip ordering, modal integration, and delayed enabled-action cleanup. The adapter has no state and installs no listeners.

The focused gate passed 28 server/packaging tests and 8 Playwright tests across manual-static and Vite loading, focused templates and copy guidance, lazy endpoint/state contracts, permissions, disabled and hidden actions, cloned modal execution, tooltip behavior, repeat-swap cleanup, and the favourite auto-apply guard. Ruff passed for affected Python tests and `git diff --check` was clean. Test discipline: zero new tests, three existing row-action tests strengthened, one manual-loading test extended, one brittle private-source assertion removed, and no duplicate coverage. The manual-static characterization was authenticated with the existing manager fixture because anonymous permission semantics correctly omit the manager-only More trigger.

### Phase 3.9: Ratify The Reusable DaisyUI Adapter

Confirm that the automatically composed adapter owns only extracted presentation behavior, all stable contracts and loading modes remain intact, and every numbered extraction has been independently integrated. Pack selection, metadata, default-pack repackaging, and variants remain outside Phase 3.

Three fresh read-only ratification audits found no runtime or compatibility blocker. All eight private factories are directly composed by `powercrud.js`; public globals, startup listener events/counts, semantic hooks, custom events, selectors, storage contracts, stable manual-static entry, and Vite manifest key remain unchanged from the Phase 3.0 base. No compatibility path is unused, and no pack loader, public adapter API, metadata contract, or variant module was introduced.

The audits required documentation reconciliation before completion: stale master/child status text, the master variant outcome, the intentional lazy-tooltip request exception, and the runtime guide's already-completed “future” list are corrected in this phase. Existing manual-static and Vite smoke tests are strengthened to assert the complete public favourite/tooltip global set; no new test is justified. The final canonical gate remains pending.

The focused ratification gate passed 16 packaging tests and 2 loading-mode Playwright tests. Ruff passed for the affected Python tests and `git diff --check` was clean. The first canonical browser run produced one timing failure in an existing synthetic duplicate-modal assertion while a preceding HTMX settle could still perform legitimate cleanup; the test passed on targeted reproduction, was stabilized with a network-idle lifecycle boundary, and passed again in isolation.

The final isolated canonical rerun passed in full: 931 server tests passed with 78 Playwright tests deselected, followed by all 78 Playwright tests passing with 931 server tests deselected. Across Phase 3, only one genuinely new browser test was added; the remaining safeguards strengthened existing behavioral/loading tests, and brittle private-source assertions were removed rather than relocated. No blocker register was needed.
