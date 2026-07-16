# Phase 4 Implementation Audit Record

## Status

Preserved evidence. The initial Phase 4.0 read-only audits informed the ratified contract. Later, bounded read-only implementation audits checked the Phase 4.2 resolver seams, Phase 4.3 runtime boundary, and Phase 4.4 legacy-facade transition. They are retained separately from the concise plan so later work can distinguish observed constraints and review recommendations from design decisions and verified outcomes.

## Audit Boundaries

1. The Phase 4.0 Python audit inspected configuration, template resolution, style lookup, copy workflows, package layout, and distribution behaviour.
2. The Phase 4.0 runtime audit inspected JavaScript composition, manual-static and Vite loading, frontend packaging, browser coverage, and unsupported assumptions.
3. The later slice audits reviewed the proposed implementation boundaries and compatibility risks before their associated gate; they did not edit code, run tests, or select public APIs.
4. The Phase 4.0 contract and child plan remain the decision authorities. Passing test and artifact evidence belongs in the phase notes after the corresponding gate completes.

## Python, Templates, And Packaging Audit

1. `ConfigMixin.templates_path` and `pcrud_mktemplate.Command.template_prefix` currently read settings during class or module import. Selected-pack resolution, view namespaces, and copy sources must be calculated at use time rather than cached at import.
2. Four existing behaviours require separate resolver seams:
    1. View templates preserve explicit `templates_path`, then selected pack, then legacy global-setting precedence.
    2. Inclusion tags select from the selected pack before the legacy global setting; `templates_path` has never controlled those tags.
    3. Style lookup uses the selected pack framework identity before the legacy global setting.
    4. Copy sources use the selected pack package-resource root, while the legacy destination segment remains stable.
3. Outer templates retain explicit `template_name`, then app/model convention, then the effective namespace. Focused components retain model-first then effective-namespace precedence. The HTMX redisplay path must use resolved configuration rather than the class attribute.
4. List and detail inclusion-tag templates are currently fixed during import. They need render-time selection while retaining their present Python context behaviour and direct-Python test seams.
5. `HtmxMixin.get_framework_styles()` is an existing public override point. Phase 4 can route its default through a pack but must retain that method and its override contract.
6. The current default tree contains 45 templates. Thirty-one are focused components. Eight source files define 25 server-addressable named partials: `object_list`, `object_form`, `object_detail`, `object_confirm_delete`, `bulk_edit_form`, `crispy_partials`, `partial/list`, and `partial/bulk_edit_errors`.
7. A simple legacy `{% include %}` or `{% extends %}` façade cannot expose named fragments under the legacy filename. Each partial-bearing legacy file must re-declare every old partial name and delegate it to the corresponding new partial. This was checked against the supported Django template behaviour, including Django 5.2 and 6.
8. Hatch currently packages `src/powercrud` into wheels and includes `src/powercrud/**` in sdists. This is promising but does not replace clean installed-artifact verification after the physical relocation.

## Runtime, Assets, And Loading Audit

1. `powercrud/js/powercrud.js` is the stable public entry. It currently imports and constructs all eight DaisyUI factories. Any extraction must retain the duplicate guard, globals, staged initialization, HTMX lifecycle, and teardown behaviour.
2. The smallest safe runtime change is a private DaisyUI composition module. It must preserve construction order because the filters and favourites work depends on core-created searchable-select and tooltip functions.
3. The browser has no Django settings transport. Phase 4 may validate a selected supported declaration in Python, but it must not claim runtime browser-side pack selection or add a public loader without a real requirement.
4. Manual-static pages load the vendor dependencies plus stable PowerCRUD CSS and JavaScript paths. The Vite entry imports those same stable paths and emits the current manifest entry. The default pack must require no new script tag, base-template change, installed app, or vendor loader.
5. Existing packaging and manual-static tests observe the private adapter paths and `powercrud/css/powercrud.css`. They stay in place during template relocation unless a separate, proven static compatibility façade becomes necessary.
6. Existing relevant coverage includes frontend asset-packaging tests, Playwright manual-static tests, and Vite loading coverage. A full canonical suite is not required for the behaviour-preserving private runtime extraction; it is required with the final server/template relocation gate.

## Consequences For The Numbered Slices

1. Phase 4.1 can introduce an immutable public declaration and dynamic discovery only. It must not alter default rendering, class-import resolution, or frontend loading.
2. Phase 4.2 must replace the identified import-time resolution points and prove each resolver seam, including tags, styles, fragments, and copy sources, before its full non-Playwright checkpoint.
3. Phase 4.3 may isolate the existing factory composition privately while leaving the stable public JavaScript and CSS entries intact.
4. Phases 4.4–4.5 remain one atomic transition: move the real template source, keep legacy facades—including named-fragment facades—verify both loading modes, and test clean wheel and sdist installations.

## Phase 4.2 Resolver-Seam Audit

This read-only review checked the dynamic-selection implementation before its compatibility gate.

1. `ConfigMixin` must resolve the effective namespace while building a real configuration namespace. Setting only a class-level default to `None` would break ordinary `config()` calls, not merely a test shim.
2. The selected adapter key `daisyui` cannot be assumed to exist in public `get_framework_styles()` overrides. Explicit pack selection must prefer the canonical key but fall back to the established `daisyUI` key; with no new selector, legacy framework lookup remains exact.
3. A third-party pack without a declared legacy copy destination needs a clear whole-tree-copy error. Silently deriving a destination from its namespace would create an unratified public contract.
4. List and detail tags require real template rendering tests across a settings change in one process. Direct calls to decorated Python functions cannot prove that inclusion-tag template selection is no longer frozen at import time.
5. The review recommended direct assertions for HTMX redisplay, selection, bulk, and async fragment targets, alongside existing behaviour tests, because suffix-only checks could miss a stale namespace.
6. It also required package-resource copy tests that construct a command once, change selection between invocations, and distinguish real selected-pack sources from the legacy custom-framework fallback.

## Phase 4.3 Runtime-Composition Audit

This read-only review established the smallest safe boundary for the DaisyUI adapter composition extraction.

1. The stable public `powercrud/js/powercrud.js` entry must import only a private `runtime/daisyui-composition.js` factory for DaisyUI presentation construction. It continues to own public globals, duplicate-load protection, startup listeners, lifecycle, and durable feature-runtime construction.
2. The private factory constructs the searchable-select adapter and semantic runtime first, then tooltip, modal, action-selection, inline-presentation, list-column, filter/favourites, and row-action-menu presentation in dependency order.
3. Filter/favourites depends on searchable-select and tooltip functions. Current-template depends on modal, action-selection, and row-menu adapters; inline editing depends on searchable-select functions. Those dependencies make construction order a compatibility requirement.
4. Manual-static must retain vendor scripts before the unchanged module entry. Vite must retain its vendor globals and the same entry import. Neither mode needs a new script tag, loader, setting-to-browser transport, public initializer, or static path.
5. The review specified focused asset assertions for the private composition module and browser assertions for manual-static URL requests, public globals, idempotent initialization, Vite loading, tooltips, and browser errors.

## Phase 4.4 Legacy-Facade And Relocation Audit

This read-only review checked the physical location and compatibility mechanics of the named atomic transition.

1. The permanent source tree must be `src/powercrud/templates/powercrud/packs/daisyui/`. Django's current `APP_DIRS=True` discovery does not find `src/powercrud/packs/daisyui/templates/` without an unwanted application/configuration change.
2. The transition moves all 45 current template paths into that source tree and restores all 45 `powercrud/daisyUI/<relative-path>` files as facades. Every literal include within the moved source must point at `powercrud/packs/daisyui/...`.
3. Thirty-seven ordinary facades may be a one-line include of the corresponding new source. They must retain the caller context, so the façade must not use `only`.
4. Eight legacy files define 25 server-addressable named partials and cannot be preserved by a plain include or inheritance. Each must load `powercrud_partials`, include the new full template for normal rendering, and re-declare every historic partial name by including the matching new `#partial` target.
5. The required partial-bearing facades are `object_list.html` (10 fragments), `object_form.html` (3), `object_detail.html` (1), `object_confirm_delete.html` (3), `bulk_edit_form.html` (2), `crispy_partials.html` (2), `partial/list.html` (2), and `partial/bulk_edit_errors.html` (2).
6. With no new selector and canonical legacy `POWERCRUD_CSS_FRAMEWORK == "daisyUI"`, `pcrud_mktemplate` must copy from the new real source while retaining its `daisyUI` destination. A genuinely custom legacy framework must keep its existing fallback.
7. The recommended atomic-gate checks are matching inventories of 45 source and 45 facade paths; compilation/loading of old and new roots plus all old and new named partials; representative fragment rendering; default and explicit-pack resolution; real-source copy output; and wheel/sdist verification containing both source and facades.

## Phase 4.5 Independent Atomic-Diff Review

The final read-only review examined the complete `template_pack/4.4` diff and its gate evidence.

1. It confirmed the permanent source has 45 templates, contains no legacy literal includes, and all 45 legacy paths are forwarding facades.
2. It confirmed the eight partial-bearing facades expose all 25 historic server-addressable fragment names, then required `powercrud_partials` to be loaded before each legacy `partialdef` for cross-version safety. The facades were hardened accordingly.
3. It confirmed canonical unconfigured DaisyUI resolves to the relocated built-in source while genuinely custom legacy framework values retain their fallback, and `pcrud_mktemplate` copies from the real source while keeping legacy destinations.
4. It confirmed the pack-owned style provider retains the public `HtmxMixin.get_framework_styles()` override contract, and the stable manual-static and Vite entry paths remain unchanged with the regenerated manifest asset present.
5. It required a focused explanation and test for the filter-panel marker repair that the full browser gate exposed. The renamed shell-return browser test proves preservation across its intended list refresh and clearing across an unrelated shell navigation.
6. The final review found no remaining implementation blocker. It noted only a harmless trailing-blank-line removal in `partial/bulk_form.html`.

## Related Decision Records

1. The reconciled contract and its required acceptance gates are in [Phase 4.0 Pack Contract Audit](phase4.0-pack-contract-audit.md).
2. The approved execution checklist is in [Phase 4 Default DaisyUI Pack Plan](phase4-default-pack-plan.md).
3. The decision rationale and compatibility matrix are in [Phase 4 Default DaisyUI Pack Notes](phase4-default-pack-notes.md).
