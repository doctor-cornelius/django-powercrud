# Phase 7 Bootstrap 5 Pack Plan

## Status

Phase 7.0 is integrated into `staging/main` at `8b9f383c`, the selectable Phase 7.1 Bootstrap baseline at `776eed33`, the Bootstrap list/filter presentation at `3e98c039`, Bootstrap CRUD forms at `67215fff`, Bootstrap adapter lifecycle at `bc2a2d78`, Bootstrap capabilities at `984e66aa`, the Bootstrap sample presentation at `1d1abe90`, and the Phase 7.7 parity and visual-evidence slice at `38658a66`. Michael accepted the completed Phase 7.8 evidence comparison, styling-API decisions, repair programme, quality-control reset, and final visual refinements; that slice is integrated into `staging/main`. Phase 7.9 distribution and ratification passed on `template_pack/7.9` through commits `9f416f4c`, `15abb4d8`, `b7be206a`, and `00410ab6`; this tip is ready to integrate into `staging/main`. The compatible default DaisyUI experience remains unchanged.

## Next

Fast-forward the accepted Phase 7.9 tip into `staging/main`, then retain the provisional reference pack for the separate Phase 8 cleanup gate.

## Phase 7.0: Lock The Bootstrap Delivery Contract

1. [x] Define Bootstrap 5 as an optional co-distributed contrib-style pack selected only through process-startup settings.
2. [x] Preserve the unconfigured DaisyUI default, legacy paths, stable public runtime entry, and supported loading modes.
3. [x] Reuse the Phase 6 validator, shared matrices, same-adapter fixture, and installed-resource harness as entry gates.
4. [x] Lock the Bootstrap package identity, template namespace, adapter identity, settings overlays, form integrations, and sample-presentation boundary.
5. [x] Keep core CRUD semantics and functional JavaScript shared while assigning Bootstrap component behaviour to a private framework adapter.
6. [x] Require native forms and maintained `crispy-bootstrap5` rendering without adding crispy dependencies to unconfigured projects.
7. [x] Define functional, responsive, and accessible parity before subjective styling refinement.
8. [x] Define targeted Playwright screenshot inspection as committed review evidence rather than a broad pixel-snapshot contract.
9. [x] Divide delivery into independently integratable `7.x` slices, except for the named selectable-baseline atomic gate.
10. [x] Require one semantic commit per accepted slice and preserve every `7.x` commit separately on `staging/main`.

## Phase 7.1: Establish The Selectable Bootstrap Baseline

1. [x] Add the optional `powercrud.contrib.bootstrap5` Django app and its module-path `TemplatePack` declaration without adding a built-in alias.
2. [x] Use identity and framework-adapter key `bootstrap5`, namespace `powercrud/packs/bootstrap5`, no legacy copy destination, and no variant adapter.
3. [x] Add a complete baseline namespace for list, form, detail, and delete before any settings module selects the pack.
4. [x] Add Bootstrap framework styles for filters, actions, disabled states, spinners, and modal triggers without changing downstream `get_framework_styles()` overrides.
5. [x] Extend runtime resolution and the Phase 6 validator to recognize the implemented Bootstrap adapter and assets while retaining clear failures for unknown declarations; defer the crispy dependency until 7.3.
6. [x] Add package-owned Bootstrap integration CSS/runtime assets and a `config/static/js/bootstrap5.js` Vite entry; bundle Bootstrap in Vite while keeping manual-mode Bootstrap vendor assets consumer-supplied.
7. [x] Compose Bootstrap privately behind the stable PowerCRUD runtime lifecycle without adding a public browser registry, initializer, or selector.
8. [x] Preserve the default DaisyUI composition when Bootstrap is not explicitly selected.
9. [x] Treat declaration, app installation, baseline templates, styles, assets, and runtime composition as one atomic acceptance gate.
10. [x] Add a minimal `tests.settings_bootstrap` overlay for selected-pack verification, then verify declaration shape, baseline resources, direct fragments, adapter selection, asset isolation, and unchanged default selection before integration.

## Phase 7.2: Build The Bootstrap List And Navigation Presentation

1. [x] Add the Bootstrap list-level page shell and navigation over the existing sample routes and runtime metadata; retain the complete Bootstrap sample base for Phase 7.6.
2. [x] Implement Bootstrap list heading, instructions, actions, filters, table shell, table header, table rows, pagination, and page-size controls.
3. [x] Preserve focused component resolution, context values, semantic hooks, HTMX attributes, URL state, and named fragments.
4. [x] Use Bootstrap layout, buttons, tables, forms, alerts, badges, and responsive containers without Tailwind or DaisyUI classes.
5. [x] Retain full-page and HTMX list loading, filtering, sorting, pagination, row links, and ordinary actions.
6. [x] Add the `filters` capability only after its complete list presentation and behaviour pass; keep later optional capability controls unavailable until their own slices.
7. [x] Verify server rendering and representative list navigation under Bootstrap plus unchanged default DaisyUI rendering before integration.

## Phase 7.3: Build The Bootstrap CRUD And Form Presentation

1. [x] Implement Bootstrap create, update, detail, delete, conflict, and action-footer shells.
2. [x] Implement native Django field rendering with labels, help text, required state, bound values, errors, and accessible relationships.
3. [x] Add `crispy-bootstrap5` to the Bootstrap test configuration and declare the `bootstrap5` crispy template pack; retain the derived sample configuration for Phase 7.6.
4. [x] Preserve form ownership of CSRF, multipart encoding, HTMX transport, query state, and modal-compatible fragments.
5. [x] Preserve all form, detail, delete, conflict, and crispy server-addressable partials without nested form elements.
6. [x] Keep form persistence, validation, permissions, requests, and success/error semantics in shared PowerCRUD code.
7. [x] Verify native and crispy rendering, ordinary CRUD, validation, conflicts, full-page transport, and unchanged DaisyUI forms before integration.

## Phase 7.4: Implement The Bootstrap Framework Adapter Lifecycle

1. [x] Implement the private Bootstrap composition for the currently renderable modal, tooltip, searchable-select, and spinner seams; retain explicit no-op seams for 7.5-only inline, column, favourite, and row-action presentation.
2. [x] Use Bootstrap Modal and Tooltip APIs rather than DaisyUI dialog or Tippy presentation behaviour; defer Bootstrap dropdown-owned PowerCRUD controls until their 7.5 templates exist.
3. [x] Continue using the shared semantic searchable-select runtime with a Bootstrap-compatible Tom Select presentation adapter.
4. [x] Use `getOrCreateInstance()` for repeatable fragment initialization and `getInstance()` plus `dispose()` before HTMX removes owned elements.
5. [x] Preserve the stable `window.initPowercrud(fragment)` entry, once-only listeners, custom events, state, URLs, and request semantics.
6. [x] Preserve modal labels, backdrops, keyboard dismissal, close-triggered list refresh, form-error hosting, and success teardown through the selected adapter.
7. [x] Prevent duplicate Bootstrap modal instances and stale owned elements across repeated swaps; defer 7.5 floating-panel controls until their markup exists.
8. [x] Prove source, template, asset, and server lifecycle contracts now; run the first real Bootstrap browser interaction, focus, dropdown, and error-absence gate after the derived Bootstrap sample base and assets land in Phase 7.6.

## Phase 7.5: Complete Applicable Bootstrap Capabilities

1. [x] Implement Bootstrap list-column, favourites, row-action, selection, bulk-edit, async, inline-edit, and dependency presentation.
2. [x] Add the `bulk`, `async`, `inline`, and `favourites` declaration capabilities only after their templates, fragments, adapter behaviour, and focused tests are complete; columns and row actions remain list behaviours without separate declaration flags.
3. [x] Preserve saved state, selection state, capability dependencies, direct fragments, and shared service routes.
4. [x] Render Bootstrap-native disabled, loading, success, warning, error, conflict, progress, and empty states truthfully.
5. [x] Preserve native and crispy Bootstrap rendering for filter, inline, bulk, modal, and async form surfaces.
6. [x] Reach the same applicable capability set as the compatible DaisyUI declaration without copying core JavaScript or sample application code.
7. [x] Verify the expanded resources, fragments, templates, declaration, and shared server contracts now; execute the corresponding real Bootstrap browser checks after Phase 7.6 supplies the derived Bootstrap base and selected assets.

## Phase 7.6: Add The Bootstrap Sample Presentation

1. [x] Complete the minimal `tests.settings_bootstrap` overlay and add derived `config.settings_bootstrap` without changing default settings.
2. [x] Install only the Bootstrap app and crispy integration required by those overlays and select `powercrud.contrib.bootstrap5:template_pack` globally.
3. [x] Keep the same database, fixtures, models, URLs, views, permissions, roles, navigation destinations, and runtime metadata source.
4. [x] Add Bootstrap-specific sample base and presentation templates without copying the sample application or CRUD view families.
5. [x] Add a documented Bootstrap launch command and retain the unchanged default DaisyUI command.
6. [x] Document side-by-side startup on separate ports without adding an in-application, query-parameter, or per-view selector.
7. [x] Cover Bootstrap manual-static and Vite loading independently of Tailwind and DaisyUI assets.
8. [x] Verify settings isolation, shared-catalogue identity, asset ownership, launch configuration, and unchanged default presentation before integration.

## Phase 7.7: Reach Behavioural Parity And Inspect Visually

1. [x] Run the Phase 6 validator and shared server matrix under Bootstrap settings after full capability parity is declared.
2. [x] Run the presentation-independent shared browser matrix under Bootstrap settings.
3. [x] Cover list and HTMX navigation, filters, pagination, columns, favourites, row actions, modal CRUD, bulk, inline, detail, delete, and repeated lifecycle behaviour.
4. [x] Exercise responsive layouts, keyboard operation, focus movement, accessible names, modal relationships, and browser-error collection.
5. [x] Commit eight targeted desktop and narrow-viewport screenshots plus a capture manifest covering list controls, responsive list, dropdown, native validation, crispy modal validation, bulk, inline validation, and delete confirmation.
6. [x] Inspect screenshots for clipping, overflow, spacing, hierarchy, contrast, responsive failure, and inconsistent component states.
7. [x] Correct functional, responsive, and accessibility defects before presenting the Bootstrap sample for styling review.
8. [x] Record the commands, settings, scenarios, screenshots, and remaining visual observations before integration.
9. [x] Perform a read-only audit of PowerCRUD styling API points under Bootstrap: record supported hooks, DaisyUI-only assumptions, intentionally unsupported hooks, and any decisions required for styling refinement.
10. [x] Write the audit result as the separate `phase7-bootstrap-styling-api-audit-plan.md` before the Phase 7.8 review hand-off; do not use it to expand 7.1--7.7 implementation scope.

## Phase 7.8: Apply Accepted Styling Refinements

1. [x] Pause implementation for Michael to review the working Bootstrap sample and provide styling direction.
2. [x] Establish matched default-DaisyUI comparison evidence before choosing Bootstrap fixes.
    1. [x] Define a capture matrix for the eight existing Bootstrap evidence scenarios, including route, viewport, data state, visible interaction state, and capture boundary.
    2. [x] Reproduce each scenario under default DaisyUI settings through deterministic browser steps, using the existing Playwright capture flow where practical.
    3. [x] Store the corresponding DaisyUI evidence under `evidence/daisyui/` without replacing the accepted Phase 7.7 Bootstrap evidence.
    4. [x] Record a pack-by-pack comparison that separates functional, accessibility, responsive, objective presentation-quality, and subjective styling findings.
    5. [x] Group candidate corrections into proposed systemic component batches rather than treating each screenshot as an independent styling target; record retain-as-is and deferred recommendations explicitly.
    6. [x] Revisit the remaining styling-API decisions only after the matched baseline and candidate correction batches are clear.
    7. [x] Present the comparison register, proposed batch order, and styling-API decisions for Michael's review; lock the accepted repair programme before implementing any fixes.
3. [x] Convert the accepted 7.8.2 register into named, ordered repair batches before implementation begins.
    1. [x] Implement pack-owned extra-button and row-action presentation under 7.8.4.
    2. [x] Correct narrow Bootstrap sample-shell and list composition under 7.8.5.
    3. [x] Correct Bootstrap table density and semantic icon presentation under 7.8.6.
    4. [x] Correct Bootstrap inline editing and validation presentation under 7.8.7.
4. [x] Implement pack-owned extra buttons and row actions.
    1. [x] Keep `{% extra_buttons view %}` stable while rendering a neutral button view-model through pack-owned DaisyUI, legacy-facade, reference, and Bootstrap partials.
    2. [x] Give Bootstrap a compact native-`details` dropdown, Bootstrap initial disabled/tooltips, and legible small row-action controls without changing shared action semantics.
    3. [x] Run focused default and Bootstrap server/browser checks; replace the affected canonical Bootstrap screenshots through Windows Chrome.
    4. [x] Commit and push, then continue to the next approved batch unless a bounded blocker requires review.
5. [x] Correct narrow Bootstrap sample-shell and list composition.
    1. [x] Use one fluid Bootstrap sample container, remove the nested list container, and reduce avoidable navigation/list spacing without changing routes or metadata.
    2. [x] Preserve table-local horizontal overflow and prevent page-level horizontal overflow at 640×720; keep the compact view controls actionable when a detached chooser overlaps the narrow toolbar.
    3. [x] Run focused responsive browser checks; replace the desktop and narrow canonical Bootstrap screenshots.
    4. [x] Commit and push, then continue to the next approved batch unless a bounded blocker requires review.
6. [x] Correct Bootstrap table density and semantic icon presentation.
    1. [x] Add framework-neutral semantic icon hooks and size Bootstrap boolean/action SVGs to `1rem` without changing DaisyUI presentation.
    2. [x] Retain conventional Bootstrap `table-sm` behaviour; measure ordinary rows after the icon correction and make no arbitrary padding override.
    3. [x] Run focused cross-pack table/browser checks; replace the affected list, row-action, and inline Bootstrap screenshots.
    4. [x] Commit and push, then continue to the next approved batch unless a bounded blocker requires review.
7. [x] Correct Bootstrap inline editing and validation presentation.
    1. [x] Render inline widgets through the internal Bootstrap field helper in small-control mode, including Bootstrap invalid classes and existing accessible error relationships.
    2. [x] Add Bootstrap-owned active/error row treatment using Bootstrap variables without consuming DaisyUI palette controls.
    3. [x] Run focused inline lifecycle/browser checks; replace the canonical Bootstrap inline-validation screenshot.
    4. [x] Commit and push, then continue to the next approved batch unless a bounded blocker requires review.
8. [x] Complete the accepted Phase 7.8 regression and evidence refresh.
    1. [x] Rerun affected default and Bootstrap server/browser checks and rebuild generated assets with explicit implementation approval.
    2. [x] Recapture all eight canonical Bootstrap states through Windows Chrome 150, including the isolated native-form override, and leave DaisyUI evidence unchanged.
    3. [x] Record the final evidence, exact commands, accepted outcomes, and bounded deviations; retain the before state at commit `03dd1565`.
    4. [x] Commit and push the final evidence/doc reconciliation.
9. [x] Run the Phase 7.8 quality-control reset and remediation without an intermediate review gate.
    1. [x] Reopen the visual-evidence status, establish clean browser/server provenance, and record a considered defect register for every matched pair.
    2. [x] Correct the confirmed Bootstrap shell/table, modal/form, inline, and row-action presentation defects within pack-owned boundaries.
    3. [x] Reconcile affected cross-pack tests so no known failure is carried forward as an unexplained Bootstrap exception.
    4. [x] Recapture all sixteen matched canonical images and one supplemental wide-list pair through clean Windows Chrome sessions.
    5. [x] Perform a fresh adversarial final inspection, record exact validation, and commit/push the reconciliation.
10. [x] Obtain Michael's final Phase 7.8 acceptance before moving the accepted repairs into the Phase 7.9 integration gate.

## Phase 7.9: Pass The Distribution Gate And Ratify

1. [x] Run focused declaration, namespace, fragment, settings, form, adapter, asset, and shared-catalogue tests.
2. [x] Run the complete shared server and browser matrices under default, reference, and Bootstrap settings where applicable.
3. [x] Run the complete canonical default server and Playwright regression because Phase 7 changes runtime and asset composition.
4. [x] Rebuild generated assets only with fresh explicit approval and verify Bootstrap and default manual-static/Vite loading.
5. [x] Build wheel and sdist only with fresh explicit approval and add Bootstrap to the isolated installed-resource harness.
6. [x] Prove the installed declaration, templates, fragments, adapter modules, static assets, native forms, and crispy integration from `site-packages`.
7. [x] Reconcile the child plan, child notes, master plan, and master notes with accepted evidence.
8. [x] Decide Bootstrap production-support status separately rather than treating implementation completion as automatic support promotion.
9. [x] Retain the provisional DaisyUI reference pack until the separate Phase 8 cleanup gate.
10. [x] Mark Master Phase 7 complete only after parity, review, compatibility, and distribution evidence are accepted.
