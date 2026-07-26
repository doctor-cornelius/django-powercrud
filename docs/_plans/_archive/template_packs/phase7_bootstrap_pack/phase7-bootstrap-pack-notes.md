# Phase 7 Bootstrap 5 Pack Notes

## Purpose

These notes support [`phase7-bootstrap-pack-plan.md`](phase7-bootstrap-pack-plan.md), which implements Phase 7 of the [`template_packs-master-plan.md`](../template_packs-master-plan.md).

Phase 7 delivers the first serious cross-framework proof: an optional Bootstrap 5 pack with its own templates, assets, styles, private framework adapter, native forms, and maintained `crispy-bootstrap5` integration. It must reach the applicable shared CRUD parity already exercised by the compatible DaisyUI pack without changing unconfigured projects or copying PowerCRUD's functional JavaScript.

The intended delivery order is functional correctness first, internal browser and screenshot inspection second, and Michael's styling review third. Accessibility, responsive behaviour, truthful states, and component lifecycle are part of functional correctness and are not deferred as subjective polish.

## Binding Inputs

1. Phase 1 locked the core/framework/variant JavaScript boundary, opt-in asset declarations, native-form requirement, maintained crispy integration rule, co-distributed Bootstrap direction, and installed-artifact requirement.
2. Phase 2 established 31 focused template components and retained the generic roots, direct fragments, semantic hooks, and copy workflows.
3. Phase 3 extracted eight private DaisyUI presentation seams behind the stable `powercrud/js/powercrud.js` public entry.
4. Phase 4 established dynamic `TemplatePack` declarations, module-path selectors, selected namespaces, framework style lookup, the compatible DaisyUI default, and manual-static/Vite compatibility.
5. Phase 5 established derived presentation settings over one shared sample application and retained the provisional DaisyUI reference pack.
6. Phase 6 established the declaration/resource validator, shared server and browser matrices, durable same-adapter fixture, and isolated wheel/sdist resource harness.
7. The Bootstrap pack must eventually declare the same list, form, detail, delete, filters, modal, bulk, async, inline, and favourites capabilities as DaisyUI, but a capability is advertised only after its implementation passes.
8. The default and reference packs currently declare no additional assets, use the `daisyui` adapter, and support native plus crispy-tailwind forms.
9. Runtime resolution currently rejects every non-DaisyUI adapter and any manual or Vite asset declaration; the validator also knows only the DaisyUI adapter and crispy-tailwind dependency.
10. The stable browser entry currently constructs DaisyUI composition unconditionally. Bootstrap selection therefore requires a private composition and asset-loading extension while preserving the stable default entry and public globals.
11. `HtmxMixin.get_framework_styles()` currently supplies the DaisyUI style mapping, so Bootstrap style selection must become pack-aware without removing the public downstream override seam.
12. The compatible source contains 45 pack templates and 25 required server-addressable fragments across eight partial-bearing roots. Bootstrap must satisfy the same relevant resource and fragment contracts for every declared capability.

## Locked Decisions

### Pack Identity And Selection

Bootstrap is an optional contrib-style Django app inside the `django-powercrud` distribution. Its implementation module is `powercrud.contrib.bootstrap5`; its declaration uses identity and framework-adapter key `bootstrap5`, template namespace `powercrud/packs/bootstrap5`, package-owned template/static resources, no legacy copy destination, and no variant adapter.

The selector is `powercrud.contrib.bootstrap5:template_pack`. Phase 7 adds no built-in `bootstrap5` alias. A project opts in by adding the contrib app to `INSTALLED_APPS`, supplying its selected assets, and setting `POWERCRUD_SETTINGS["POWERCRUD_TEMPLATE_PACK"]` through process-startup settings. An absent selector continues to select the built-in DaisyUI pack, and the legacy `POWERCRUD_CSS_FRAMEWORK` fallback remains unchanged.

The pack initially advertises only the implemented baseline capabilities. Phase 7.5 expands the declaration to full parity only as each optional capability becomes usable. Runtime selection remains lightweight; the Phase 6 validator performs fuller template, fragment, adapter, form, asset, dependency, and artifact checks.

There is no in-application selector, URL/query-string selector, per-view pack selector, public pack registry, public browser adapter registry, or new public initializer. Explicit per-view `templates_path` remains the existing downstream override above global pack selection.

### Distribution And Dependency Boundary

The Bootstrap Python declaration, templates, private adapter modules, integration assets, and validation resources are co-distributed in the wheel and sdist. The Bootstrap-specific compiled Vite entry includes Bootstrap CSS and JavaScript in the package bundle, mirroring the existing packaged DaisyUI/Tailwind bundle. Because the contrib app is optional, unconfigured projects gain no new `INSTALLED_APPS` entry, CSS, JavaScript, or crispy dependency requirement.

The sample and test dependency groups add the maintained `crispy-bootstrap5` package and the Bootstrap npm package. The Python project's required dependency set remains unchanged. Bootstrap sample settings add `crispy_bootstrap5`, allow template pack `bootstrap5`, and select it for crispy rendering. Native forms remain mandatory and work when crispy rendering is disabled.

At planning time, Context7 exposes high-reputation Bootstrap 5.3 documentation under `/websites/getbootstrap_5_3`. The current maintained crispy integration is `crispy-bootstrap5` 2026.3 on PyPI, with Django settings app `crispy_bootstrap5` and template-pack name `bootstrap5`. Implementation should select repository-compatible bounded dependency ranges rather than hard-code the planning snapshot as an eternal version.

Authoritative references used for the contract are:

1. [Bootstrap 5.3 introduction](https://getbootstrap.com/docs/5.3/getting-started/introduction/).
2. [Bootstrap JavaScript guidance](https://getbootstrap.com/docs/5.3/getting-started/javascript/).
3. [Bootstrap Modal](https://getbootstrap.com/docs/5.3/components/modal/).
4. [Bootstrap Dropdowns](https://getbootstrap.com/docs/5.3/components/dropdowns/).
5. [crispy-bootstrap5](https://pypi.org/project/crispy-bootstrap5/).

### Asset Loading

The downstream project continues to own its base template and chooses manual-static or Vite integration. Bootstrap assets are opt-in and must never be injected by inner CRUD templates.

The Bootstrap declaration uses the existing `manual_assets` and `vite_assets` fields. They identify only package-owned Bootstrap integration CSS/runtime files and the Bootstrap Vite manifest entry; Bootstrap itself is not copied a second time as raw static vendor files. Phase 7.1 defines and validates their first working runtime meaning without changing the frozen `TemplatePack` field shape:

1. Manual-static integration requires the downstream project to load HTMX, Tom Select, Bootstrap CSS, and the Bootstrap JavaScript bundle with Popper before package-owned shared and Bootstrap presentation assets. This mirrors the existing manual DaisyUI path, whose vendor assets are also consumer-supplied.
2. Vite integration uses the package manifest entry `config/static/js/bootstrap5.js`, which imports Bootstrap CSS and JavaScript along with the required shared dependencies and then installs the private Bootstrap composition.
3. Bootstrap pages do not load Tailwind, DaisyUI, Tippy, or the DaisyUI sample theme controller.
4. DaisyUI pages retain their existing manual-static and Vite entries and do not load Bootstrap.
5. One page uses one presentation asset pipeline; manual-static and Vite remain mutually exclusive.

The selectable baseline is a named atomic gate because runtime resolution, style lookup, asset declarations, adapter composition, app installation, and a usable baseline namespace must agree. Dormant helpers may be developed within the slice, but the selected declaration must not merge in a state that fails when explicitly configured.

### JavaScript Composition And Lifecycle

Core retains durable CRUD semantics, requests, HTMX decisions, URL state, favourites, columns, selection, inline state, public globals, custom events, and stable semantic attributes. Bootstrap templates retain those hooks; the private Bootstrap framework adapter owns Bootstrap component construction, markup-specific geometry, visual state, and lifecycle.

The stable public contract remains `powercrud/js/powercrud.js`, `window.initPowercrud(fragment)`, the duplicate-load guard, and existing compatibility globals. The current runtime body moves into a private installer: the unchanged public entry invokes it with DaisyUI composition, while the Bootstrap pack-owned entry invokes it with Bootstrap composition. Phase 7 may add these private modules, but it must not publish a browser registry or make unconfigured users select an adapter separately from their server-side pack.

The Bootstrap composition covers the same presentation responsibilities as the current DaisyUI composition:

1. Bootstrap Modal for CRUD modal lifecycle.
2. Bootstrap Dropdown for row actions and suitable floating controls.
3. Bootstrap Tooltip for semantic and overflow help instead of Tippy.
4. Bootstrap-compatible Tom Select styling and lifecycle for searchable selects.
5. Bootstrap spinners, disabled presentation, inline validation/error presentation, list-column controls, favourites controls, and responsive placement.

Bootstrap 5.3 component instances are attached to DOM elements. Repeatable initialization uses `getOrCreateInstance()` where provided. Teardown checks `getInstance()` and calls `dispose()` before HTMX removes elements. Modal completion uses Bootstrap lifecycle events such as `hidden.bs.modal` so focus restoration, backdrop cleanup, list refresh, and replacement ordering do not race CSS transitions.

Initialization remains once-only core listeners followed by repeatable core and selected-framework work. Teardown is fragment-scoped. Repeated `window.initPowercrud()` calls must not duplicate listeners, instances, backdrops, menus, tooltips, or detached presentation nodes.

### Template And Style Boundary

Bootstrap owns its templates; it does not include DaisyUI templates as a presentation fallback. The baseline namespace supplies every template and named fragment required by its advertised capabilities before selection. Later slices add optional capability templates and declaration entries together.

Bootstrap templates preserve context, semantic hooks, named fragments, HTMX attributes, accessibility relationships, and focused override resolution. They use Bootstrap classes and component markup only. Tailwind utilities, DaisyUI classes, native `<dialog>` assumptions, and DaisyUI `details` dropdown structure are not carried into the Bootstrap namespace.

Framework style lookup becomes pack-aware while preserving `HtmxMixin.get_framework_styles()` as the downstream override. The built-in implementation supplies both recognized framework mappings or composes the selected mapping internally; downstream mappings using the existing DaisyUI keys remain valid. Bootstrap styles provide filter widget attributes, action classes, modal trigger data, disabled state, and spinner presentation without embedding durable request behaviour.

### Forms

Every Bootstrap form surface supports native Django rendering. Native templates preserve bound values, required indicators, help text, field and non-field errors, checkbox/select/file widgets, accessible label/control/error relationships, CSRF ownership, multipart encoding, and transport semantics.

The maintained crispy path uses `crispy-bootstrap5`, `CRISPY_ALLOWED_TEMPLATE_PACKS = ["bootstrap5"]`, and `CRISPY_TEMPLATE_PACK = "bootstrap5"` in Bootstrap settings. The declaration advertises crispy template pack `bootstrap5`, and the validator maps it to Python dependency `crispy_bootstrap5`. Crispy partials retain the historic `#load_tags` and `#crispy_form` fragment names and do not render a nested `<form>`.

Form, filter, modal, inline, bulk, async, validation, and conflict surfaces must work through native and crispy rendering where applicable. PowerCRUD continues to own helper configuration, persistence, conflict detection, requests, and success/error events.

### Shared Sample Presentation

`config.settings` and `tests.settings` remain DaisyUI. Phase 7.1 first introduces a minimal `tests.settings_bootstrap` overlay solely to exercise selected-pack installation and baseline rendering. Phase 7.6 completes that overlay and adds `config.settings_bootstrap`; both then select Bootstrap, install the optional app and crispy integration, choose the Bootstrap asset/base-template configuration, and set `SAMPLE_PRESENTATION = "Bootstrap 5 pack"`.

The Bootstrap presentation uses the existing sample models, database, fixtures, URLs, views, roles, permissions, navigation destinations, and context processor. Presentation-specific base and sample leaf templates are allowed; copied models, routes, view families, data, permissions, functional JavaScript, and navigation catalogues are not.

The documented startup shape is explicit settings selection. The exact commands use the existing project runner conventions and permit default DaisyUI and Bootstrap processes on different ports. Those commands document integration; running non-test servers still requires explicit approval under repository policy.

### Functional And Visual Acceptance

The first Bootstrap goal is a conventional, coherent Bootstrap 5 implementation: correct components, sensible hierarchy and spacing, responsive behaviour, keyboard access, focus handling, truthful state colours, and full applicable CRUD behaviour. It need not establish a bespoke visual identity before parity.

Phase 7.7 uses behavioural Playwright assertions as the durable contract. It also commits eight named screenshots and a capture manifest under the Phase 7 planning evidence directory for engineering inspection at desktop and narrow widths. They cover representative list, responsive, dropdown, native validation, crispy modal validation, bulk, inline-validation, and delete-confirmation states; they are not a pixel-diff regression suite.

Michael reviews the working sample after functional, responsive, and accessibility defects found by the agent have been corrected. Phase 7.8 records and applies accepted styling improvements. Subjective polish must not conceal a failing shared matrix or broaden Phase 7 into a general sample redesign.

### Production Support And Reference Retention

Completing the implementation does not automatically declare Bootstrap a supported production pack. Phase 7.9 records the implementation evidence and asks for the support-status decision separately. The provisional DaisyUI reference pack remains installed and testable throughout Phase 7; its removal belongs only to Phase 8 after Bootstrap parity is accepted.

## Delivery Rule

Phase 7.0 is the planning contract on `template_pack/7.0`. After acceptance and fast-forward integration, every later slice begins from synchronized `staging/main` on its own `template_pack/7.x` branch. Each slice receives proportionate focused server and browser verification, one semantic commit containing its `7.x` number, acceptance, fast-forward integration, a pushed `staging/main`, and local/remote slice-branch deletion before the next independent slice.

The required subjects are:

1. `docs(template-packs): 7.0 plan Bootstrap 5 pack`
2. `feat(template-packs): 7.1 add selectable Bootstrap baseline`
3. `feat(template-packs): 7.2 build Bootstrap list presentation`
4. `feat(template-packs): 7.3 build Bootstrap CRUD forms`
5. `feat(template-packs): 7.4 add Bootstrap adapter lifecycle`
6. `feat(template-packs): 7.5 complete Bootstrap capabilities`
7. `feat(sample): 7.6 add Bootstrap presentation`
8. `test(template-packs): 7.7 prove Bootstrap parity`
9. `style(template-packs): 7.8 refine Bootstrap presentation`
10. `docs(template-packs): 7.9 ratify Bootstrap pack`

Do not add unnumbered follow-up commits to an accepted slice. Correct a pre-integration problem by amending the slice commit. If a discovered issue requires a genuinely independent new slice, stop and add that numbered phase to both child documents before implementation.

Phase 7.1 is the only predeclared atomic gate. The later phases remain independently integratable because the Bootstrap pack is opt-in and must remain usable for its then-declared capabilities after every merge. Protected `main` is not changed; programme integration targets `staging/main` until the repository pull-request workflow is separately requested.

No sub-agents participate in Phase 7.0 planning. Later implementation may use bounded sub-agents only with Michael's authorization and non-overlapping ownership; the primary agent remains responsible for design, review, verification, commits, and integration.

Do not create a blocker register pre-emptively. Create `phase7-blockers.md` only after the first genuine stop condition, recording evidence, the affected slice, safe independent work, and the exact decision required.

## Stop Conditions

Stop for guidance before proceeding when implementation finds:

1. A need to change the frozen `TemplatePack` field schema, selector precedence, stable public runtime path, public initializer, or public browser registry.
2. A Bootstrap implementation that requires changing unconfigured DaisyUI selection, rendering, legacy facades, styles, or existing manual-static/Vite loading.
3. A need to place Bootstrap, Tailwind, or DaisyUI assumptions in core request, state, storage, URL, event, or service behaviour.
4. A need to duplicate sample models, data, routes, views, permissions, roles, navigation, or functional PowerCRUD JavaScript.
5. A required template or fragment contract that cannot support Bootstrap without changing its established semantic meaning.
6. A pack asset that cannot be represented by the existing manual/Vite declaration fields without a material public loading API decision.
7. A maintained crispy-bootstrap5 path that cannot preserve PowerCRUD's form, modal, inline, bulk, or validation semantics.
8. Bootstrap component instances, backdrops, focus, or listeners that cannot be safely initialized and disposed through the fragment lifecycle.
9. A requirement to retire the DaisyUI reference pack, which remains Phase 8 work.
10. An unexplained deterministic regression, non-trivial conflict, unrelated worktree mutation, unexpected remote `staging/main` movement, or missing installed artifact resource.

## Validation Boundary

Ordinary implementation slices run focused source, server, and browser coverage justified by the files and behaviour changed. They do not repeat full regressions, builds, installations, or every presentation matrix by habit.

Phase 7.7 runs the reusable Phase 6 validator and matrices under Bootstrap after parity, then performs the targeted visual and accessibility inspection. Phase 7.9 runs the broad compatibility and distribution gate because Phase 7 changes adapter selection, runtime composition, assets, templates, dependencies, and installed package contents.

Michael has authorized the dependency updates, Vite builds/rebuilds, and generated package-asset updates needed through Phase 7.7. Wheel/sdist builds, clean artifact environments, and non-test sample servers remain Phase 7.9 work and require fresh approval. Browser tests are normal tests and run according to repository test policy. Targeted screenshot capture is authorized as committed Phase 7 engineering evidence, but no broad screenshot catalogue or pixel-regression system is implied.

## Plan

### Phase 7.0: Lock The Bootstrap Delivery Contract

This planning slice fixes the package boundary, selection model, asset modes, private adapter lifecycle, template and form ownership, sample presentation, incremental delivery rule, visual-review checkpoint, stop conditions, and phase gate. It changes documentation only and runs no implementation tests, builds, browsers, or screenshots.

The plan is based on the current declaration and runtime truth: only DaisyUI is presently selectable, additional assets are rejected, framework styles default to DaisyUI, and the stable browser entry composes DaisyUI directly. Phase 7.1 must resolve those boundaries together rather than activating a declaration that cannot function.

Completed and integrated into `staging/main` as `8b9f383c` after the contract amendment recorded the mirrored bundled/manual Bootstrap asset boundary, minimal early Bootstrap test overlay, authorized Phase 7.1--7.7 dependency and asset work, and committed 7.7 screenshot evidence. No implementation tests, builds, browsers, or screenshots ran in this documentation-only slice.

### Phase 7.1: Establish The Selectable Bootstrap Baseline

Create the optional contrib app and its baseline-capability declaration, namespace, framework styles, private composition, and asset integration. Baseline templates cover list, form, detail, and delete plus every direct fragment those capabilities require. They use Bootstrap markup and native forms; later phases deepen presentation and add crispy plus optional capabilities.

Extend runtime checks and the Phase 6 validator only for combinations that now work. Preserve errors for unknown adapters, variants, assets, and crispy integrations. The default DaisyUI stable entry and both loading modes remain unchanged.

This slice is atomic: declaration selection does not land before its installed app, templates, styles, assets, and runtime composition can produce a valid baseline page. Focused tests prove explicit Bootstrap selection and default isolation without requiring the later full sample catalogue.

Implementation on `template_pack/7.1` adds the optional app, baseline declaration, eight package-owned Bootstrap templates (the seven validator resources plus row actions needed by a real list), native rendering, a minimal settings overlay, Bootstrap style mapping, package-owned manual integration files, and a second Vite manifest entry. The generated bundle contains Bootstrap CSS and JavaScript; manual integration retains the documented consumer-supplied Bootstrap dependency. The shared runtime has one private installer: the normal entry installs DaisyUI by default, while the Bootstrap entry supplies a private baseline composition whose optional-capability hooks are deliberately inert until Phase 7.4.

The focused default settings gate passed 53 tests across declaration, validator, and asset-packaging coverage. The Bootstrap-overlay gate passed five tests covering the exact declaration, selected namespace, package resources, direct fragments, validator, and real list/create/detail/delete rendering. The Vite build passed after separating the source-relative Vite import from the browser-relative manual module import; it retained the known upstream HTMX direct-`eval` warning. The slice was committed as `776eed33` and fast-forwarded into `staging/main`; `template_pack/7.2` starts from that integration point.

### Phase 7.2: Build The Bootstrap List And Navigation Presentation

Build the Bootstrap list-level page shell and complete baseline list presentation around the shared semantic hooks. The complete Bootstrap sample base and navigation remain Phase 7.6 work: the early test overlay intentionally inherits the existing sample base. Use responsive Bootstrap containers and tables, truthful neutral/status classes, accessible action names, and ordinary Bootstrap form controls.

Add the filters capability when its complete vertical path passes. Keep the later modal, bulk, async, inline, columns, row-menu, and favourites controls out of the presentation until their corresponding Phase 7.4/7.5 lifecycle and capability work is complete. Focused tests cover full-page and HTMX list rendering, filtering, sorting, pagination, row links, fragments, and default isolation.

Implementation on `template_pack/7.2` expands the package-owned namespace from eight to seventeen templates. Bootstrap now owns the list-level shell, action toolbar, filter controls, responsive table shell/header/rows, pagination, and page-size selector. Component paths continue to resolve through the existing focused-component context. The declaration truthfully adds only `filters`; the shared runtime gains only the minimal private filter-panel visibility and active-state presentation needed for that capability, while modal, dropdown, columns, favourites, bulk, async, and inline lifecycle seams remain unavailable.

The Bootstrap-overlay gate passed six focused tests covering the exact inventory, declaration, direct fragments, native CRUD baseline, list/filter/sort/pagination/HTMX state, and absence of later capability hooks. The default focused declaration, validator, and packaging gate passed 53 tests. The Vite build regenerated package assets successfully and retained the known upstream HTMX direct-`eval` warning. The inherited DaisyUI sample base can still render its own demo modal navigation in early test responses; that is intentionally outside the Bootstrap-owned list assertion and will be replaced by the Phase 7.6 Bootstrap sample base.

The slice was committed as `3e98c039` and fast-forwarded into `staging/main`; `template_pack/7.3` starts from that integration point.

### Phase 7.3: Build The Bootstrap CRUD And Form Presentation

Implement coherent Bootstrap form, detail, delete, conflict, and action shells. Add native field presentation and the maintained crispy-bootstrap5 dependency, settings, declaration mapping, and crispy partials.

Focused server coverage proves the template, transport, rendering, and validation contract at this slice. Browser modal and lifecycle coverage begins only after Phase 7.4 supplies the Bootstrap modal host and adapter. Default DaisyUI continues using crispy-tailwind.

Implementation on `template_pack/7.3` adds `crispy-bootstrap5>=2026.3,<2027` only to the mirrored test dependency surfaces, resolves it in `uv.lock`, and configures the Bootstrap test overlay with `crispy_bootstrap5`, an allowed Bootstrap template pack, and Bootstrap as the crispy default. The package declaration now truthfully advertises crispy `bootstrap5`; the unconfigured project remains free of the dependency. The Bootstrap namespace grows to 27 templates: native/crispy field rendering, focused form/detail/delete shells and leaves, conflict presentations, and all required server-addressable fragments.

Native fields use a private Bootstrap template tag to retain each Django widget while adding the correct Bootstrap control class and accessible help/error relationships. Form and delete shells preserve existing CSRF, multipart, query-state, HTMX, modal-compatible history, and list-redisplay semantics. The slice intentionally adds neither a modal host/lifecycle nor a derived sample settings module; those remain Phases 7.4 and 7.6.

The Bootstrap-overlay gate passed eight tests covering declaration and 27-template inventory, validator/fragment compilation, native and crispy bound validation rendering, full-page CRUD route rendering, form/delete transport, retained query state, and conflict return behavior. The default focused declaration, validator, template-partial, and frontend-asset gate passed 59 tests; `git diff --check` was clean. The active container needed the locked wheel installed into its `/usr/local` test interpreter after the normal project-level sync selected a different environment; this was an environment repair only, not a project dependency-surface change.

The slice was committed as `67215fff` and fast-forwarded into `staging/main`; `template_pack/7.4` starts from that integration point.

### Phase 7.4: Implement The Bootstrap Framework Adapter Lifecycle

Implement each Bootstrap presentation seam through the private selected-framework composition. Prefer Bootstrap's own Modal, Dropdown, Tooltip, spinner, focus, and lifecycle APIs. Keep Tom Select for searchable controls but give it Bootstrap-compatible presentation and fragment teardown.

Focused browser coverage repeatedly initializes and swaps list and modal fragments, opens and closes dropdowns, submits invalid and successful modal forms, and verifies instance disposal, focus restoration, state preservation, backdrop cleanup, and absence of console/page errors.

Implementation on `template_pack/7.4` adds the first renderable Bootstrap lifecycle vertical: package-owned Bootstrap modal shell/content templates, a modal-capability declaration, a create action that preserves the existing HTMX target, and private Bootstrap Modal, Tooltip, Tom Select, and spinner adapters. The stable runtime now asks the selected private modal adapter to show, bind its close event, and dispose owned component instances during HTMX teardown. DaisyUI retains its native-dialog behavior through the same private contract; no public browser selector or new global is introduced.

Bootstrap `getOrCreateInstance()` handles repeated initialization, while `getInstance()` plus `dispose()` runs for owned modals and tooltips before fragment removal. The Bootstrap adapter listens for `hidden.bs.modal` for close-to-list refresh, retains the established IDs/data hooks, and deliberately ignores existing DaisyUI/Tailwind modal sizing strings unless a requested class is a Bootstrap modal class. That compatibility limitation is a styling-API audit input, not a reason to place framework mapping in shared core.

The focused Bootstrap server gate passes nine tests covering declaration/resource validation, list/modal host rendering, create transport, forms, and filters. The default declaration/partial/asset gate passes 59 tests. The Vite rebuild resolves the Bootstrap lifecycle modules and generated assets, with the existing upstream HTMX direct-`eval` warning only; `git diff --check` passes. The early Bootstrap test overlay intentionally inherits the DaisyUI sample base, so it cannot honestly prove a Bootstrap browser lifecycle. The real browser interaction and console-error gate therefore begins immediately after the derived Bootstrap base and selected assets land in Phase 7.6; Phase 7.5 supplies the first PowerCRUD dropdown/column/favourites/row-action markup that needs that browser coverage.

The slice was committed as `bc2a2d78` and fast-forwarded into `staging/main`; `template_pack/7.5` starts from that integration point.

### Phase 7.5: Complete Applicable Bootstrap Capabilities

Add the remaining list-column, favourites, row-action, selection, bulk, async, inline, and dependency templates and presentation. Advertise capabilities only as each complete vertical path lands; the final declaration matches the compatible DaisyUI capability set.

Focused tests remain outcome-based. They use shared routes, services, state, events, and request semantics while allowing Bootstrap-specific markup and component lifecycle.

Implementation on `template_pack/7.5` expands the Bootstrap namespace with package-owned bulk selection/edit/error/outcome templates, async fragments, inline field/display/form/layout templates, a `<details>/<summary>` column chooser, a cloneable saved-favourites toolbar/panel, and row-action menus that preserve their required `li` structure. The Bootstrap object list, table shell/header/rows, and list partial activate each surface only when the shared context enables it. No Bootstrap template delegates presentation to DaisyUI or copies application routes, models, services, or runtime state logic.

The declaration now truthfully reaches the compatible capability set (`list`, `form`, `detail`, `delete`, `filters`, `modal`, `bulk`, `async`, `inline`, and `favourites`). Private Bootstrap adapters provide detached panel geometry, Bootstrap disabled/spinner state, selected-favourite state, Tom Select initialization, and inline focus/save feedback. Existing shared JavaScript retains selection, range selection, persistence, dependencies, URL state, HTMX request policy, polling, and lazy row-action decisions. Bootstrap templates use `data-bs-dismiss="modal"` for async outcome dismissal, not a native-dialog call.

The Bootstrap server/resource/asset gate passes 32 tests, the reusable shared server matrix passes five Bootstrap-selected scenarios, and the focused default declaration, partial, and asset gate passes 59 tests. The Vite rebuild produces the updated selected Bootstrap bundle with only the known upstream HTMX direct-`eval` warning, and `git diff --check` passes. As in Phase 7.4, the early test overlay inherits the DaisyUI sample base; actual Bootstrap browser coverage of these interactive surfaces starts directly after the derived Bootstrap presentation lands in Phase 7.6.

The slice was committed as `984e66aa` and fast-forwarded into `staging/main`; `template_pack/7.6` starts from that integration point.

### Phase 7.6: Add The Bootstrap Sample Presentation

Add derived development and test settings, Bootstrap sample base/presentation templates, runtime metadata, asset entries, and launch guidance. The overlay changes presentation only and retains the one shared application catalogue.

Document default and Bootstrap startup commands plus separate ports for side-by-side processes. Verify settings isolation, catalogue identity, template selection, manual-static/Vite asset independence, and no DaisyUI/Tailwind resources on Bootstrap pages.

Implementation adds `config.settings_bootstrap` and completes `tests.settings_bootstrap` as shallow, startup-only overlays. Both prepend `sample/templates_bootstrap`, install only `crispy_bootstrap5` and `powercrud.contrib.bootstrap5` beyond the compatible base, select the Bootstrap module-path declaration, and configure crispy's maintained `bootstrap5` pack. They retain the existing database, URL configuration, models, views, fixture source, routes, roles, and navigation targets. The Bootstrap template root supplies a Vite base plus a manual-static base, runtime metadata presentation, and sample-fragment presentation leaves; no sample application code is copied.

Use `./manage.py runserver 0:8001` for the unchanged default sample and `./manage.py runserver --settings=config.settings_bootstrap 0:8002` for Bootstrap. These can run concurrently on the named ports after entering separate development-container terminals. They are process-startup selections, not an in-application, URL, or per-view switch.

The Vite shell imports only `config/static/js/bootstrap5.js`; the manual-static shell loads Bootstrap CSS/bundle, Tom Select, HTMX, package-owned Bootstrap CSS, and the selected Bootstrap PowerCRUD entry through Django static tags. The focused Bootstrap settings/server gate passes 24 tests and the default-isolation gate passes 7 tests with one expected Bootstrap-runtime skip. `git diff --check` passes. An attempted first selected Playwright modal smoke reached collection but the current development container lacks the already-declared `playwright`/`pytest-playwright` optional test group (`ModuleNotFoundError: playwright`); no application failure was observed. Browser parity and screenshots remain Phase 7.7 work once that normal test environment is refreshed.

The slice was committed as `1d1abe90` and fast-forwarded into `staging/main`; `template_pack/7.7` starts from that integration point. The Phase 7.7 Bootstrap-selected server parity gate now passes 62 focused tests, covering package declaration/resource validation, shared list/form/detail/delete/bulk/async/inline behaviour, core selection compatibility, and asset packaging. Browser evidence remains pending only the declared Playwright test environment refresh.

### Phase 7.7: Reach Behavioural Parity And Inspect Visually

Run the Phase 6 validator and complete shared matrices under Bootstrap. Add only missing presentation-independent coverage or Bootstrap-specific lifecycle coverage justified by findings.

Capture the agreed bounded screenshot states at desktop and narrow widths. Inspect them directly and fix broken behaviour, accessibility, responsive layout, clipping, hierarchy, and inconsistent component states. Record evidence and then provide the working sample to Michael for visual review.

Before that styling-review hand-off, perform a separate read-only audit of the PowerCRUD styling API as it applies to Bootstrap. Write `phase7-bootstrap-styling-api-audit-plan.md` in this directory. It must distinguish hooks supported by the Bootstrap pack, hooks that remain DaisyUI-specific, hooks intentionally unavailable, and decisions that would need Michael's direction. This audit informs Phase 7.8; it is not authority to broaden or reopen accepted 7.1--7.7 implementation slices.

The Bootstrap-selected Phase 6 server matrix passes 62 focused tests. The refreshed test container now supplies Playwright, and the Bootstrap browser gate passes the shared three-scenario matrix plus focused create-modal, list-column, row-action, responsive-overflow, and Bootstrap modal-lifecycle coverage. The same shared browser matrix also passes under the unchanged default settings. The Vite build reports the pre-existing HTMX direct-eval advisory only; no browser console or page errors occurred in the Bootstrap modal regression.

Browser inspection found four connected Bootstrap defects and corrected them within the private pack boundary: legacy DaisyUI modal class input could overwrite the required Bootstrap dialog; detached dropdown clones did not receive Bootstrap's `.show` state; their geometry was measured while Bootstrap hid them; and the filter action shell retained a DaisyUI `hidden` class after opening. The Bootstrap table shell now owns narrow horizontal overflow through the stable `table-max-height` hook. The evidence directory contains eight review screenshots and its capture manifest. The evidence was recaptured in Windows Google Chrome 150 through CDP, with a temporary `tests.settings_bootstrap` native-form capture setting `BookCRUDView.use_crispy = False` only for that test, preserving the sample's normal crispy default.

The separate styling-API audit is recorded in `phase7-bootstrap-styling-api-audit-plan.md`. It identifies supported Bootstrap hooks and the deferred decision points without changing public API or reopening accepted implementation slices. Phase 7.7 now pauses for Michael's styling review after the final documentation and focused test checks complete.

### Phase 7.8: Apply Accepted Styling Refinements

Pause for Michael's review. Before selecting corrections, establish a matched default-DaisyUI evidence set for the same eight states already captured under Bootstrap. Use one capture matrix to record the route, viewport, data state, visible interaction state, and capture boundary for each scenario, then reproduce those states through deterministic browser steps under default settings. Store the resulting images under `evidence/daisyui/` and leave the accepted Phase 7.7 Bootstrap evidence in place. If the original Bootstrap capture conditions cannot be matched faithfully, decide separately whether a paired recapture is necessary rather than silently replacing the earlier evidence.

The first evidence sub-slice is complete. The eight-state matrix and reproduction recipes are recorded in [`evidence/daisyui/daisyui-screenshot-manifest.md`](evidence/daisyui/daisyui-screenshot-manifest.md). Six replacement captures use the unchanged default `config.settings` sample on port 8001 with the existing development data; the native-form replacement uses isolated `tests.settings`, the manager fixture, and a temporary `BookCRUDView.use_crispy = False` override. All eight DaisyUI PNGs use Windows Google Chrome 150 through CDP, use a clear `daisyui-` prefix with the Bootstrap semantic suffixes, retain the source viewport dimensions, and leave the Bootstrap evidence and application code unchanged. A temporary CDP helper and native live-server bridge were removed after capture. The capture review checked route, data/authentication state, visible interaction state, validation/modal/menu state, dimensions, and crop only; comparative findings remain deferred to 7.8.2.4.

Use DaisyUI as a comparison for functional density, hierarchy, and scenario parity, not as a visual design target for Bootstrap. Record comparison findings by category: functional, accessibility, responsive, objective presentation quality, and subjective styling preference. Each actionable finding should identify the visible problem, the Bootstrap-owned component boundary likely to own it, the intended outcome, and the browser state that will verify it. Group accepted work into systemic batches such as page shell/navigation rhythm, toolbar and floating controls, table density and cell presentation, narrow-screen composition, and form/modal/state presentation instead of styling screenshots independently.

The decision on `extra_buttons_mode="dropdown"` is settled: add an appropriate pack-owned presentation boundary and visibly demonstrate the same semantic control through suitable DaisyUI and Bootstrap markup in both sample presentations. This is accepted Phase 7.8 baseline work, not one of the remaining styling-API questions. Revisit modal sizing hooks, table geometry, inline colours, view-help styling, template-copy guidance, and initial disabled-button presentation only after the matched comparison and baseline correction batches make those decisions concrete.

#### Phase 7.8.2.4: Matched Comparison Register

The register below compares each Bootstrap image with the DaisyUI image carrying the same semantic filename suffix. DaisyUI is evidence for scenario parity, functional density, and hierarchy; it is not the visual target. Screenshot inspection cannot prove complete keyboard or assistive-technology behaviour, so the functional and accessibility disposition also relies on the passing Phase 7.7 browser assertions recorded above.

| ID | Evidence pair or pairs | Category | Observation | Recommendation and component boundary | Verification and confidence |
| --- | --- | --- | --- | --- | --- |
| C01 | All eight pairs | Functional and accessibility | The matched states show the intended page, authenticated state, modal or inline state, validation feedback, and destructive-action wording. No new functional or accessibility failure is demonstrated by the screenshots. | Retain the shared behaviour and semantic hooks. Treat affected Phase 7.7 browser assertions as mandatory regression checks for every later repair batch. | Existing browser assertions; high confidence for captured state, but screenshots alone do not extend the accessibility contract. |
| C02 | Desktop list, narrow list, row actions, inline validation, and the list behind each modal | Objective presentation quality | Bootstrap boolean cells render very large success/error symbols and its rows carry substantially more vertical space than their content requires. The symbols dominate the hierarchy, reduce scanability, and leave far fewer records visible. | Repair in Bootstrap-owned table, boolean-cell, and row presentation. Preserve semantic truth and accessible names while reducing icon and row scale to a conventional Bootstrap table density. | Recheck desktop, narrow, row-action, and inline states in Windows Chrome; high confidence. |
| C03 | Row-actions dropdown | Objective presentation quality | View, edit, delete, and `More` controls consume most of the actions column. Labels collide with the fixed button widths and the `More` triggers appear as unlabelled grey blocks, so the control group is difficult to scan even though its asserted menu behaviour passed. | Repair in the Bootstrap row-action/button-group presentation and the pack-owned floating-control boundary. Keep the action names legible without widening every row excessively. | Recheck the right-scrolled row-actions state and keyboard/browser assertions; high confidence for control geometry. |
| C04 | Desktop list, narrow list, row actions, inline validation, and delete confirmation background | Objective presentation quality | The list-toolbar `More` control is markedly taller than adjacent controls and uses a separate two-line geometry. This weakens toolbar alignment and consumes scarce narrow-screen height. | Repair through the pack-owned extra-action presentation boundary. The same boundary must also implement the already-settled cross-pack `extra_buttons_mode="dropdown"` requirement and correct initial disabled presentation. | Recheck anonymous, manager, narrow, and disabled states; high confidence. |
| C05 | Narrow list | Responsive and objective presentation quality | The responsive table continues to scroll locally, but the Bootstrap sample shell adds a wide content inset and its metadata/navigation consumes more vertical space before the list than the matched DaisyUI state. The result is a usable but unnecessarily constrained table viewport. | Repair Bootstrap sample shell, navigation wrapping, and list-container rhythm without changing routes or forcing the DaisyUI arrangement. Retain table-local horizontal overflow. | Recheck at 640×720 and one intermediate width; high confidence for the captured width. |
| C06 | Inline validation | Objective presentation quality | The invalid row is understandable, but its native controls, checkbox, multi-select, error message, and row geometry do not read as one coherent active/error state. The very large boolean symbols in surrounding rows further compete with the validation message. | Repair Bootstrap-owned inline form/control alignment and active/error-row presentation after the table-density correction. Do not translate DaisyUI's teal palette or raw colour hooks. | Recheck invalid save, focus, cancellation, and successful save; high confidence for hierarchy, browser verification required for lifecycle. |
| C07 | Native validation and crispy validation modals | Objective presentation quality | Both Bootstrap form variants provide conventional modal structure, readable field errors, internal scrolling, and clear form hierarchy. Their geometry differs from DaisyUI but the evidence does not show a defect requiring a public sizing or modal-body API. | Retain the Bootstrap modal structure and existing safe `modal_box_classes` handling. Allow only bounded pack-default tuning if a later accepted batch exposes a concrete problem. | Recheck both validation modes if modal CSS changes; high confidence. |
| C08 | Bulk and delete-confirmation modals | Functional, accessibility, and objective presentation quality | Bulk choices, primary/destructive separation, confirmation copy, and dismissal are clear. The Bootstrap layouts are framework-native and do not need to imitate DaisyUI. | Retain as-is, subject to regression checks when shared modal or table presentation changes. | Recheck bulk selection and delete dismissal/confirmation; high confidence. |
| C09 | Desktop and narrow lists | Objective presentation quality and subjective styling | Bootstrap's neutral help disclosure, controls, and navigation are usable. DaisyUI's colour, minimum-width, and compact visual identity are pack-specific preferences rather than missing Bootstrap semantics. | Retain Bootstrap-native help and control styling. Do not add a cross-framework view-help colour/min-width API. | Visual review only; medium-to-high confidence. |
| C10 | Row-actions dropdown | Evidence limitation | In both committed viewport images the asserted open floating panel is not visually distinguishable, although the capture recipe asserted a visible panel containing `Normal Edit`. The pair proves the surrounding right-scrolled action state but is not strong evidence for comparing the popup's styling. | Record no popup-style defect from this pair. Any accepted row-action repair must capture the open panel unambiguously and rerun its visibility assertion. | Browser assertion passed; low confidence for popup appearance, high confidence for the surrounding action controls. |
| C11 | All eight pairs | Subjective styling | The evidence supports objective hierarchy and density corrections, but does not establish a requirement to reproduce DaisyUI colours, borders, shadows, or component identity in Bootstrap. | Defer any purely subjective redesign until Michael gives explicit direction at the review gate. | Michael review required. |

#### Phase 7.8.2.5: Candidate Systemic Batches

No new functional or accessibility repair batch is justified by the screenshots. The Phase 7.7 behavioural assertions remain the correctness floor. Subject to Michael's review, the candidate programme is:

1. **Pack-owned extra and row actions** — implement the already-settled `extra_buttons_mode="dropdown"` boundary, correct initial disabled presentation, normalise the toolbar `More` control, and make row actions legible. Traces to C03 and C04.
2. **Narrow sample-shell and list composition** — reduce avoidable shell inset and navigation/metadata height while retaining table-local horizontal overflow. Traces to C05 and the retain decision in C09.
3. **Bootstrap table density and semantic cells** — reduce excessive row height and boolean-symbol scale across ordinary, selected, action, and inline rows. Traces to C02 and supports C03/C06.
4. **Inline editing and validation state** — align inline controls and provide a coherent pack-owned active/error treatment after table density is stable. Traces to C06.

Modal/form structure, view-help styling, and purely subjective visual identity are not candidate repair batches on current evidence. C07--C09 are retain-as-is recommendations and C11 is deferred. C10 requires clearer evidence only if an accepted action-control batch changes the floating panel.

These are proposed component boundaries and order only. They are not named Phase 7.8.3 tasks and do not authorize implementation before the Phase 7.8.2.7 review gate.

#### Phase 7.8.2.6: Styling-API Recommendations

| Audit decision | Recommendation for review | Rationale |
| --- | --- | --- |
| `extra_buttons_mode="dropdown"` | Implement in Phase 7.8 through a pack-owned presentation boundary, with suitable DaisyUI and Bootstrap markup. | This is already-settled baseline work and belongs with candidate batch 1, not a DaisyUI-only limitation. |
| Initial disabled extra-button presentation | Implement in Phase 7.8 through the same pack-owned boundary. | Shared DaisyUI classes and legacy Tippy attributes must not define Bootstrap's initial visual state. |
| `modal_classes` and `modal_body_classes` | Keep explicitly unsupported by Bootstrap; retain safe Bootstrap `modal_box_classes` and `bulk_modal_box_classes` only. | C07 and C08 show no evidence that warrants a new cross-framework public modal API. |
| DaisyUI-oriented table geometry controls | Keep explicitly unsupported by Bootstrap. Correct Bootstrap defaults inside its pack-owned table presentation instead. | C02 identifies a Bootstrap default problem, not a need to translate Tailwind/DaisyUI geometry values. |
| Inline highlight and palette controls | Keep explicitly unsupported by Bootstrap. Supply coherent Bootstrap-owned active/error defaults without translating raw DaisyUI colours. | C06 requires semantic state clarity, not palette equivalence. |
| View-help colour and minimum-width controls | Keep explicitly unsupported by Bootstrap. | C09 supports retaining conventional Bootstrap disclosure styling. |
| `pcrud_mktemplate` modal-copy guidance | Defer pack-aware generator guidance to a separately scoped tooling/documentation slice. | It is a real transferability limitation, but it does not block the evidence-led presentation repairs and should not expand their implementation boundary. |

Michael ratified these recommendations at the 7.8.2.7 review gate. The corresponding audit decisions are complete; implementation remains bounded by the named repair batches below.

#### Phase 7.8.2.7: Michael Review Gate

Michael accepted the C01--C11 dispositions, the four-batch order, and the styling-API recommendations as the implementation programme. C07--C09 remain retain-as-is, C11 remains deferred, and C10 authorizes only clearer row-menu evidence when that control is repaired. No styling implementation, new screenshots, or application changes were made through this review gate.

#### Phase 7.8.3: Weaker-Model Handoff Contract

Implement 7.8.4--7.8.7 sequentially on `template_pack/7.8`. For each batch, change only the named component boundary, run the focused server and browser checks, capture the affected canonical Bootstrap PNGs through Windows Chrome, update these notes, commit, and push before continuing to the next approved batch. Return for review only if a bounded blocker requires a decision or the implementation would expand the named boundary. Do not use sub-agents.

The implementation must preserve the public `{% extra_buttons view %}` call, settings interface, template-pack declaration contract, shared action semantics, stable JavaScript entrypoints, and unchanged DaisyUI presentation. Stop and return to a stronger model if an apparently visual repair requires lifecycle/data-flow changes, a new public API, a new `TemplatePack` field, or speculative shared-core branching.

The source causes and fixed boundaries are:

1. **7.8.4 extra and row actions:** move the current extra-button presentation behind pack-owned partials fed by a neutral view-model. Bootstrap keeps native `details` behaviour for the existing close-after-selection contract, uses a compact Bootstrap summary/menu, and owns Bootstrap disabled/tooltip attributes. Add semantic row-action icon/label hooks and size Bootstrap action icons to `1rem` while preserving accessible names.
2. **7.8.5 narrow composition:** change both Bootstrap sample bases to one `container-fluid px-3 py-3` main shell, remove the nested `container py-4` from the Bootstrap object-list section, and reduce the Vite navigation bottom margin to `mb-3`. At 640×720 the list begins within 24px of each viewport edge, the page has no horizontal overflow, and the table wrapper remains independently scrollable.
3. **7.8.6 table density:** add a semantic boolean-icon hook and size Bootstrap boolean SVGs to `1rem` square, inline and vertically aligned. Retain existing `table-sm` behaviour. Ordinary rows must not exceed 48px because of their icons; if they still do, record measurements and stop rather than adding unplanned padding rules.
4. **7.8.7 inline state:** extend the internal Bootstrap field renderer with an optional small-control mode and use it for inline inputs, selects, checkboxes, and invalid state. Add semantic active/invalid row classes and subtle Bootstrap primary/danger-variable treatment while preserving HTMX, focus, dependency, Tom Select, save/cancel, and error behaviour.

#### Phase 7.8.5: Narrow Bootstrap Composition

Batch 7.8.5 is complete on `template_pack/7.8`. Both Bootstrap sample bases now use one fluid `container-fluid px-3 py-3` shell; the Bootstrap object-list section no longer adds a nested `container py-4`; and the Vite navigation row uses `mb-3`. The Bootstrap pack CSS keeps the detached list-column chooser above the page content while placing `[data-powercrud-view-controls]` at the next stacking level, so the filter and other compact controls remain actionable at 640×720 when the chooser panel overlaps the toolbar row. No route, metadata, data, or DaisyUI presentation changed.

Focused validation passed:

- `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_bootstrap ./runtests --pytest src/tests/test_bootstrap_template_pack.py"` (10 passed).
- `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_bootstrap ./runtests --playwright src/tests/playwright/test_list_options.py::test_book_list_column_controls_fit_table_or_viewport src/tests/playwright/test_list_options.py::test_book_list_wide_table_scroll_stays_inside_table_wrapper"` (2 passed).
- `./runproj exec "./runtests --playwright src/tests/playwright/test_list_options.py::test_book_list_column_controls_fit_table_or_viewport"` (1 passed under default settings).

The affected canonical Bootstrap captures were replaced through Windows Google Chrome 150/CDP on port 9222 against the ordinary `config.settings_bootstrap` sample at `http://127.0.0.1:8001/sample/bigbook/`: `bootstrap-list-controls-desktop.png` (1280×720) and `bootstrap-list-responsive-narrow.png` (640×720). A temporary Windows-Node raw-CDP helper set the viewport, asserted the object-list root and viewport dimensions, captured the viewport, and was removed afterward. The capture server was an already-running Bootstrap sample process; the attempted duplicate start was rejected because port 8001 was occupied, and no additional server process was left running. Generated Vite assets were refreshed as part of Playwright and are included with the batch. DaisyUI evidence was unchanged.

#### Phase 7.8.4: Pack-Owned Extra And Row Actions

Batch 7.8.4 is complete on `template_pack/7.8`. The shared `{% extra_buttons view %}` tag now resolves a neutral button view-model through the selected pack's `partial/extra_buttons.html`, with DaisyUI, the legacy facade, the reference namespace, and Bootstrap resources present. Bootstrap owns its native `details` summary/menu markup and disabled/tooltip attributes; DaisyUI retains its existing disabled classes and Tippy attributes. Standard action SVGs now expose `pc-action-icon` and `pc-action-label` hooks, and the Bootstrap pack sizes those icons to `1rem` while preserving accessible names.

Focused validation passed with:

- `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_bootstrap ./runtests --pytest src/tests/test_bootstrap_template_pack.py"` (10 passed).
- `./runproj exec "./runtests --pytest src/tests/test_core_phase1.py::test_book_list_renders_selection_aware_extra_button src/tests/test_template_partials_compat.py"` (7 passed).
- `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_bootstrap ./runtests --playwright src/tests/playwright/test_bulk_selection.py::test_extra_buttons_more_dropdown_closes_after_option_click src/tests/playwright/test_row_actions_menu.py::test_row_actions_menu_stays_visible_for_top_and_bottom_rows"` (2 passed; Vite rebuilt the tracked package assets).

The affected canonical Bootstrap captures were replaced through Windows Google Chrome 150/CDP using the ordinary `config.settings_bootstrap` server on port 8001: `bootstrap-list-controls-desktop.png` (1280×720), `bootstrap-list-responsive-narrow.png` (640×720), and `bootstrap-row-actions-dropdown-desktop.png` (1280×900). The recipe asserted the right route, manager authentication for row actions, table scroll state, and an open panel containing `Normal Edit`; the committed row-action image retains the documented limitation that the detached panel is not visually distinguishable despite the passing DOM assertion. DaisyUI evidence was not changed. The temporary Windows-CDP helper was removed and the server was stopped.

#### Phase 7.8.6: Bootstrap Table Density And Boolean Icons

Batch 7.8.6 is complete on `template_pack/7.8`. The shared boolean SVG markup now carries the framework-neutral `pc-boolean-icon` hook while retaining the existing DaisyUI utility classes. Bootstrap owns the scoped `1rem` square, inline, vertically aligned presentation for that hook. No `table-sm` padding override was added: after the icon correction, ordinary Bootstrap rows measured within the 48px ceiling in the new browser assertion.

Focused validation passed:

- `./runproj exec "./runtests --pytest src/tests/test_templatetags_powercrud.py::test_object_list_renders_booleans_dates_and_selection src/tests/test_templatetags_powercrud.py::test_object_list_renders_queryset_annotation_field_cells src/tests/test_core_phase1.py::test_author_list_centers_boolean_icon_cells"` (3 passed under default settings).
- `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_bootstrap ./runtests --pytest src/tests/test_bootstrap_template_pack.py"` (10 passed under Bootstrap settings).
- `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_bootstrap ./runtests --playwright src/tests/playwright/test_list_options.py::test_book_list_boolean_icons_are_compact"` (1 passed).
- `./runproj exec "./runtests --playwright src/tests/playwright/test_list_options.py::test_book_list_boolean_icons_are_compact"` (1 passed under default settings).

The affected canonical Bootstrap captures were replaced through Windows Google Chrome 150/CDP on port 9222 against the ordinary `config.settings_bootstrap` sample at `http://127.0.0.1:8001/sample/bigbook/`: `bootstrap-list-controls-desktop.png` (1280×720), `bootstrap-list-responsive-narrow.png` (640×720), `bootstrap-row-actions-dropdown-desktop.png` (1280×900, authenticated manager with the first row-action panel open), and `bootstrap-inline-validation.png` (1280×900, authenticated manager with the first inline title cleared and server validation visible). A temporary Windows-Node raw-CDP helper asserted each interaction state and viewport before `Page.captureScreenshot`, then was removed. The resulting list evidence shows compact green/red indicators and ordinary row density; DaisyUI evidence was unchanged. Generated Vite assets were refreshed and are included with this batch.

#### Phase 7.8.7: Bootstrap Inline Editing And Validation States

Batch 7.8.7 is complete on `template_pack/7.8`. The internal Bootstrap field helper now supports compact inline controls, an explicit inline error-id suffix, optional help-text relationships, Bootstrap `is-invalid`, and a compact checkbox hook while preserving the normal form-rendering defaults. Bootstrap inline rows now carry semantic active/invalid classes with subtle primary/danger variable backgrounds. The Bootstrap inline presentation adapter now keeps its existing focus/save lifecycle, exposes the expected loading-spinner hook, and presents an accessible, dismissible validation callout linked to the inline error text.

Focused validation passed:

- `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_bootstrap ./runtests --pytest src/tests/test_bootstrap_template_pack.py"` (10 passed).
- `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_bootstrap ./runtests --playwright src/tests/playwright/test_inline_editing.py::test_inline_edit_happy_path src/tests/playwright/test_inline_editing.py::test_inline_edit_validation_error_recovers src/tests/playwright/test_inline_editing.py::test_inline_edit_validation_error_cancel_clears_popover"` (3 passed).
- `./runproj exec "./runtests --playwright src/tests/playwright/test_inline_editing.py::test_inline_edit_happy_path src/tests/playwright/test_inline_editing.py::test_inline_edit_validation_error_recovers src/tests/playwright/test_inline_editing.py::test_inline_edit_validation_error_cancel_clears_popover"` (3 passed under default settings).

The canonical `bootstrap-inline-validation.png` was replaced through Windows Google Chrome 150/CDP on port 9222 against the ordinary `config.settings_bootstrap` sample at `http://127.0.0.1:8001/sample/bigbook/`, using the authenticated manager, 1280×900 viewport, first-row title clear/save interaction, and an assertion for the visible `This field is required` callout. The temporary Windows-Node helper was removed. DaisyUI evidence was unchanged; generated Vite assets were refreshed and are included with this batch.

#### Phase 7.8.8: Final Regression And Evidence Reconciliation

Batch 7.8.8 is complete on `template_pack/7.8`. The eight canonical Bootstrap PNGs and manifest now describe the final 7.8.5–7.8.7 implementation state. Seven ordinary captures used `config.settings_bootstrap` on port 8001; the native-form capture used a temporary `tests.settings_bootstrap` server on port 8002 with `BookCRUDView.use_crispy = False`, then the server and temporary Windows-Node helpers were removed. Every capture used Windows Google Chrome 150/CDP, device scale factor 1, the manifest viewport, and an asserted route/state boundary. DaisyUI evidence was not changed.

Final validation recorded:

- Default focused server matrix: 112 passed, 10 skipped (`test_bootstrap_template_pack.py` skipped under default settings).
- Bootstrap pack/server checks: 10 passed in `test_bootstrap_template_pack.py`; the broader shared tag matrix is not settings-compatible under Bootstrap because many fixture stubs provide only the legacy DaisyUI style mapping. That run produced 43 passes and 79 such configuration/contract failures; no unrelated compatibility expansion was added to Phase 7.8.
- Default affected browser matrix: 40 passed across list options, row actions, bulk selection, inline editing, and modal CRUD.
- Bootstrap affected browser matrix: 27 passed. Thirteen remaining failures are bounded pack-specific expectations outside the accepted 7.8 repair boundaries (DaisyUI utility-class assertions, DaisyUI modal semantics, one wrapped-toolbar assumption, and a few shared tests whose fixture targets are not Bootstrap-compatible); the new Bootstrap inline, boolean-density, narrow-overflow, modal/bulk/delete capture recipes passed.
- `git diff --check` passed before reconciliation; the eight PNGs are non-empty and have the manifest dimensions (1280×720, 640×720, or 1280×900 as specified).

The final evidence/doc reconciliation is ready for the separate Phase 7.8 acceptance gate. Phase 7.8 item 9 and all Phase 7.9 work remain unchecked.

#### Phase 7.8.9: Quality-Control Reset And Remediation

The 7.8.8 recapture remains a historical record of the work performed, but its visual acceptance is superseded. The evidence scripts asserted routes, interaction state, viewport dimensions, and capture boundaries, but that is not sufficient proof that the whole page is well composed in a normal browser. In particular, a leaked CDP device-metrics override made a real Chrome window appear constrained to a 1280px document viewport, and the previous review accepted stale/dirty provenance and known weak visual evidence too readily.

This phase therefore runs without a Michael review checkpoint between diagnosis and repairs. It must first create a defect register for all eight matched DaisyUI/Bootstrap pairs, then correct every material capture, functional, responsive, accessibility, hierarchy, density, modal, inline, and row-action defect that remains within pack-owned boundaries. The register records ID, evidence, classification, severity, observable problem, component owner, correction, acceptance test, and final disposition. A pack-native visual difference may be retained only with an objective rationale; it cannot be used to dismiss a visible hierarchy, composition, density, overflow, accessibility, or evidence-quality failure.

All capture work must use fresh clean-commit servers and isolated Windows Chrome/CDP targets. Each state asserts the displayed commit and selected pack, exact viewport/DPR, route, data and interaction state, image dimensions, and horizontal-overflow ownership. The capture helper must clear device metrics, close every target it creates, and stop every server it starts even on failure. The canonical eight pairs will be replaced, and a supplementary 1920×1080 anonymous list-controls pair will prove normal wide-browser composition. The final review starts from the refreshed images rather than trusting the defect register's earlier conclusions.

The phase does not add a public API, alter the `TemplatePack` contract, change the stable JavaScript entrypoint, or make DaisyUI imitate Bootstrap. It does reconcile affected default/Bootstrap tests: a test that is genuinely pack-specific must say so explicitly, while a test intended to prove shared behaviour must exercise both packs without an unexplained failure. Phase 7.9 distribution, installed-artifact, and production-support work remains out of scope.

#### Defect Register And Repair Status

The following register is the considered pre-recapture assessment. It combines the eight previously committed matched pairs with the source templates, browser interaction checks, and the normal-browser provenance failure described above. `Final disposition` remains provisional until the clean Windows-Chrome recapture and adversarial image inspection are complete.

| ID | Matched evidence | Classification / severity | Observable problem and owner | Correction and acceptance test | Final disposition |
| --- | --- | --- | --- | --- | --- |
| Q01 | Desktop list controls | Evidence quality / high | The accepted image was stale/dirty and a CDP metrics override could make normal browser composition appear constrained. Owner: capture protocol. | Replace through a fresh target with cleared metrics, clean displayed commit/pack, exact 1280×720 viewport/DPR, route, and screenshot-dimension assertions. | Pending clean recapture. |
| Q02 | Narrow responsive list | Responsive hierarchy / high | Prior evidence did not reliably prove that the Bootstrap toolbar wraps into a usable second row or that the local table scroll owns overflow. Owner: Bootstrap list CSS. | The wrapped control row now resets Bootstrap's `ms-md-auto`, occupies its own row, and has a viewport-bound chooser assertion. Recheck at 640×720 and intermediate width. | Repaired; pending visual confirmation. |
| Q03 | Row-actions dropdown | Evidence quality and action hierarchy / high | The old image did not make the detached open menu visually distinguishable, even though DOM state passed. Owner: capture recipe and Bootstrap floating panel. | Reproduce an open panel containing `Normal Edit`, assert its bounding box is visible, and crop/frame it unambiguously in the replacement 1280×900 image. | Pending clean recapture. |
| Q04 | Native validation modal | Modal hierarchy / medium | The prior modal evidence could retain an exposed generic host heading above the operation heading. Owner: Bootstrap modal shell. | Generic host heading is visually hidden; operation heading remains visible. Assert the native bound-error state and inspect the clean capture. | Repaired; pending visual confirmation. |
| Q05 | Crispy validation modal | Modal hierarchy / medium | The same duplicated-heading risk applied to the normal crispy form. Owner: Bootstrap modal/form shells. | Use the same shell correction and assert visible crispy bound errors, scrollable body, and one operation heading. | Repaired; pending visual confirmation. |
| Q06 | Bulk-edit modal | Table density and modal hierarchy / high | The table background competed with the modal because text columns were too wide and old evidence had weak capture provenance. Owner: Bootstrap table/header and modal shell. | Bound ordinary text columns, strengthen header separation, and retain Bootstrap-native bulk semantics. Assert selected count and visible bulk modal before capture. | Repaired; pending visual confirmation. |
| Q07 | Inline validation | Inline density / high | Long inline labels could fail to truncate inside their Bootstrap table cell; the error state needed a clean hierarchy check. Owner: Bootstrap inline presentation CSS. | Block-constrain `.pc-inline-display-label` with ellipsis and run the invalid-save lifecycle assertion. Capture the visible callout and error row. | Repaired; pending visual confirmation. |
| Q08 | Delete confirmation | Modal hierarchy / medium | Delete confirmation relied on the same modal shell and stale image provenance. Owner: Bootstrap modal shell and capture protocol. | Assert first-book identity, one visible operation heading, and the clean 1280×900 capture boundary before non-destructive screenshot. | Repaired; pending visual confirmation. |

The correction and cross-pack reconciliation batch is commit `d0e4797e`. It adds Bootstrap-owned wrapped-toolbar and inline-label presentation corrections, and makes the affected Playwright checks explicit about equivalent Bootstrap semantics instead of treating DaisyUI utility classes, Tippy roots, modal dialog classes, or spinner markup as universal. Validation passed in one full affected run per pack:

- Bootstrap settings: 42 passed, 1 intentional DaisyUI-only modal-class test skipped.
- Default settings: 40 passed.

The remaining provenance and image-review work is blocked only by Windows Chrome/CDP: `http://127.0.0.1:9222/json/version` refused the connection on 2026-07-14. No Linux Chromium substitute will be used for committed evidence.

#### Phase 7.8.4--7.8.8: Validation And Evidence Protocol

Use focused Bootstrap pack/server assertions plus the existing extra-button, row-action, responsive-list, and inline Playwright scenarios under `tests.settings_bootstrap`. Rerun the affected shared scenarios under default `tests.settings` whenever shared tag or SVG markup changes. Playwright invokes the asset build; implementation approval must explicitly include that build and the regenerated package assets.

For batch review, replace only the affected canonical Bootstrap PNGs named in the manifest. After all four batches are accepted, recapture all eight Bootstrap states and update the manifest with the exact settings, commands, Chrome version, assertions, and deviations. The committed DaisyUI files remain the comparison surface and must not be replaced. The pre-repair Bootstrap state remains available at commit `03dd1565`, so no duplicate before/after directory is required.

Use the proven Windows-Node raw-CDP approach with Windows Chrome 150 on port 9222 and device scale factor 1. One temporary untracked helper may encode all eight manifest recipes; remove it after final capture. Assert state and viewport bounding boxes before every image, and make the open row-action panel visually unambiguous. If Windows CDP is unavailable, stop and request the documented PowerShell Chrome launch; do not substitute Linux Chromium for committed evidence. Stop every started server and remove temporary capture artifacts before committing.

Modal structure, view-help styling, purely subjective redesign, and pack-aware `pcrud_mktemplate` guidance remain outside Phase 7.8 implementation.

### Phase 7.9: Pass The Distribution Gate And Ratify

Phase 7.9 completed on `template_pack/7.9` through commits `9f416f4c`, `15abb4d8`, `b7be206a`, and `00410ab6`. The installed-resource harness now resolves the Bootstrap declaration, installs `crispy-bootstrap5`, checks every package-owned Bootstrap integration and adapter module, and renders native plus crispy validation forms from isolated installed artifacts. Its probe uses an in-memory empty URLConf so crispy form-action inspection does not pull in optional async dependencies.

Focused server validation passed 22 tests under `tests.settings_bootstrap` and 11 tests under `tests.settings_daisyui_reference`. The shared reference browser matrix passed 3 tests. The Bootstrap shared browser matrix plus the new manual-static loading smoke passed 4 tests; the smoke verified Bootstrap/HTMX/Tom Select globals, the selected Bootstrap runtime, repeated initialization without duplicate Tom Select wrappers, expected manual assets, no Vite requests, and no browser errors.

The complete canonical default gate passed in two parts: 1,001 server tests passed, 11 skipped, and 90 Playwright tests were deselected; then 83 Playwright tests passed, 7 skipped, and 1,012 server tests were deselected. The approved asset rebuild produced the deterministic Bootstrap/default manifest and hashed bundle updates committed in `15abb4d8`; the final rebuild produced no further diff. The only canonical failure was a stale assertion requiring double-quoted `href` markup; it was repaired to accept either valid quote style in `b7be206a` and the full gate passed on rerun.

`uv build` produced the wheel and sdist. The isolated installed-resource harness passed for both artifacts, importing from temporary `site-packages` paths and validating the default DaisyUI, DaisyUI reference, and Bootstrap declarations, templates, fragments, assets, adapters, native forms, and crispy integrations. Bootstrap is parity- and distribution-ratified but remains pre-production pending the Phase 9 support/documentation decision. The DaisyUI reference pack remains intentionally retained for Phase 8.
