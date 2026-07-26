# Phase 1 Template-Pack Contract Notes

## Purpose

These notes support [`phase1-contract-plan.md`](phase1-contract-plan.md), which implements Phase 1 of the [`template_packs-master-plan.md`](../template_packs-master-plan.md).

Phase 1 defines testable boundaries and compatibility outcomes. It should avoid publishing exact Python or JavaScript APIs until the first implementation slice proves them.

## Current Facts

1. The current default templates live under `powercrud/daisyUI/`.
2. `ConfigMixin` derives the default template path from `POWERCRUD_CSS_FRAMEWORK`, while individual views can override `templates_path`.
3. `powercrud/js/powercrud.js` is the stable public runtime entry.
4. `window.initPowercrud(fragment)` already supports repeated full-page and HTMX fragment initialization.
5. Manual users load the public entry as an ES module; bundled/Vite users import it through `config/static/js/main.js`.
6. The current wheel configuration packages `src/powercrud`; a sibling official Django app would require an explicit build-configuration change.
7. Current form rendering can use crispy forms with the maintained `crispy-tailwind` path.
8. PowerCRUD does not own the downstream project's complete base template.

## Agreed Principles

1. Existing users receive the compatible DaisyUI experience by default.
2. Compatibility is protected by characterization and regression tests, not a permanent duplicate implementation.
3. Focused template overrides must not require copied PowerCRUD JavaScript.
4. Core JavaScript, reusable framework adapters, and optional variant adapters are separate responsibilities.
5. Multiple template packs may reuse the same framework adapter.
6. Most template variants should require no variant JavaScript.
7. DaisyUI theme and brand configuration are outside scope.
8. The first proof is a structurally different internal DaisyUI variant; Bootstrap is the later cross-framework proof.

## Delivery Invariant

The project will run alongside unrelated work and must support frequent integration into `main`.

Every ordinary implementation slice must begin from current `main`, preserve the compatible default DaisyUI experience, pass proportionate characterization and regression coverage, and merge before the next slice begins. A slice must not require existing users to change settings, template paths, base-template assets, or installed apps merely because the broader programme is incomplete.

An atomic transition is permitted only where an intermediate state would necessarily break compatibility. The transition must be named in advance and must merge only when all associated compatibility, packaging, loading, and browser gates pass together.

## Inputs

1. Template inventory and original reasoning: [`docs/archive/blog/posts/20251120_template_packs.md`](../../../archive/blog/posts/20251120_template_packs.md).
2. JavaScript boundary findings: [`docs/_plans/_archive/js_cleanup/phase6-boundary-findings.md`](../../_archive/js_cleanup/phase6-boundary-findings.md).
3. Current runtime architecture: [`src/powercrud/static/powercrud/js/README.md`](../../../../src/powercrud/static/powercrud/js/README.md).

## Plan

### Phase 1.1: Lock Compatibility And Resolution

The accepted evidence and full decision record are in [`phase1.1-compatibility-resolution-audit.md`](phase1.1-compatibility-resolution-audit.md).

The ratified contract is:

1. `POWERCRUD_CSS_FRAMEWORK` remains the legacy default presentation selector. A future template-pack selector is separate and must not overload it.
2. Outer-template precedence remains explicit `template_name`, then app/model convention, then the resolved generic namespace. The current HTMX list-redisplay bypass remains preserved through migration and is not silently changed as part of pack work.
3. Explicit per-view `templates_path` remains the authoritative legacy override for the generic roots and direct fragments it currently controls. A future pack selector sits below it and above the legacy global default.
4. Projects using the standard DaisyUI presentation without legacy template customisation continue to work indefinitely. The legacy global setting remains a compatibility alias for that default unless a separate future decision changes it.
5. Projects with copied full templates, whole-tree copies, custom legacy namespaces, or direct dependencies on `powercrud/daisyUI/...` remain supported through the 0.x migration period. Once focused overrides and the compatible default pack have shipped, this legacy customisation model is deprecated with removal targeted for v1.0.
6. Existing `powercrud/daisyUI/...` paths and every server-consumed named partial remain available until that v1.0 migration decision is implemented. Any compatibility alias mechanism must prove named partial behaviour.
7. Both current runtime-loading contracts remain stable: manual `powercrud/js/powercrud.js` and bundled/Vite `config/static/js/main.js`. They automatically compose the compatible default behaviour during adapter extraction.
8. `daisyUI` is the canonical current spelling. Lowercase public documentation must be corrected in a separate documentation change; this phase does not silently change the legacy setting's meaning.
9. Ordinary extraction work starts from current `main`, proves unchanged default behaviour, and merges as one bounded slice. Focused characterization is required before later resolver, namespace, or adapter changes.
10. Default DaisyUI repackaging is the identified atomic transition. It cannot merge until legacy paths and named fragments, tag/style resolution, template copying, artifacts, default adapter loading, and both asset modes pass together.

The focused unit and manual-static browser commands recorded in the audit remain an operational readiness check because the Django container was stopped during the audit. They must run before a later implementation slice relies on the audit's test baseline.

### Phase 1.2: Lock The Template And Override Contract

The detailed ratified contract is in [`phase1.2-1.5-template-pack-contract-analysis.md`](phase1.2-1.5-template-pack-contract-analysis.md).

1. Packs own presentation templates; core owns resolution, context, semantic contracts, and validation. Core ships no neutral visual fallback.
2. List, form, detail, and delete are baseline surfaces. Modal, bulk, async, inline, crispy, and favourites integration are capability-dependent.
3. The eleven focused override areas and their minimum context, semantic hooks, and legacy bridges are the supported customisation surface. Classes and incidental markup are not contractual.
4. Server-addressable legacy fragments remain available through 0.x. A focused component name becomes public only after its characterized extraction.
5. `pcrud_mktemplate` retains root and whole-tree copying through 0.x. After a focused component ships, it gains pack-resolved component copying with usage instructions; its exact metadata format remains deferred.
6. Each focused override is independently characterized, extracted, verified, and merged before the next slice begins. Pagination is the first Phase 2 slice.

### Phase 1.3: Lock JavaScript Layers And Pack Composition

The detailed ratified contract is in [`phase1.2-1.5-template-pack-contract-analysis.md`](phase1.2-1.5-template-pack-contract-analysis.md).

1. Core owns durable PowerCRUD state, requests, storage, URLs, HTMX, selection, filtering, favourites, columns, inline lifecycle, semantic attributes, events, and the stable public entry.
2. A framework adapter owns reusable DaisyUI or Bootstrap presentation-framework behaviour and assigned library integration, never core request or state semantics.
3. A variant adapter owns only interaction genuinely unique to one template variant. Most variants declare no JavaScript and reuse the framework adapter.
4. Composition is template namespace plus framework adapter plus no variant JavaScript, hook extensions, or a variant adapter. Multiple template packs may reuse one framework adapter.
5. Initialization is once-only core listeners, repeatable core fragment work, framework adapter work, then optional variant work. All layers preserve state, guard listeners, and tear down swapped-fragment instances.
6. Existing runtime entries, globals, semantic hooks, events, storage, URLs, and manual/Vite loading remain stable. Exact adapter and metadata APIs remain internal until an extraction proves them.

### Phase 1.4: Lock Assets And Form Rendering

The detailed ratified contract is in [`phase1.2-1.5-template-pack-contract-analysis.md`](phase1.2-1.5-template-pack-contract-analysis.md).

1. Downstream projects own their base template and choose manual-static or bundled/Vite integration. The default DaisyUI pack adds no new app, setting, base-template, or script requirement.
2. Manual mode supplies vendor libraries and CSS before the stable PowerCRUD entry; Vite supplies them from `config/static/js/main.js` before importing the stable entry. Adapters reuse those dependencies rather than loading duplicates.
3. Non-default packs may declare opt-in assets. A DaisyUI variant may reuse the standard DaisyUI/Tailwind stack and framework adapter with no extra assets.
4. Native Django form rendering is mandatory for every official pack that claims form support.
5. Every official framework pack with a maintained crispy integration must include and test it. The Bootstrap full-parity dogfood includes a maintained crispy-Bootstrap integration; DaisyUI retains its crispy-tailwind path.
6. Form, filter, inline, bulk, modal, and async support are separately declared capabilities. No new requirement reaches existing projects before its complete compatibility path has merged.

### Phase 1.5: Lock Packaging And Validation

The detailed ratified contract is in [`phase1.2-1.5-template-pack-contract-analysis.md`](phase1.2-1.5-template-pack-contract-analysis.md).

1. Official packs are co-distributed. Compatible DaisyUI remains in `powercrud`; Bootstrap is an optional contrib-style Django app or package in the same distribution. Third-party packs remain separately installable.
2. A pack declares its contract version, namespace, framework and optional variant adapters, capabilities, native and crispy form support, and optional manual/Vite assets. The concrete metadata API remains deferred.
3. Runtime selection does only identity, import, version, and clear-error checks. A developer/CI validator checks templates, required fragments, capabilities, adapters, assets, form dependencies, and artifact discovery.
4. Shared capability-driven source and browser tests apply to every pack. Clean wheel and sdist installation is required for official-pack releases and the atomic default-pack repackaging checkpoint, not for every small implementation pull request.
5. Ordinary slices use focused characterization and applicable central tests. Default DaisyUI repackaging additionally gates legacy resolution, fragments, copy workflow, assets, artifacts, adapter composition, and both loading modes.

### Phase 1.6: Ratify The Contract Baseline

Ratification is complete. D11 through D25 were accepted with two refinements: Bootstrap is an optional co-distributed contrib-style full-parity dogfood pack, and every official framework pack with a maintained crispy integration must include and test it.

1. Compatibility and resolution are unambiguous, including the v1.0 target for legacy full-template customisation after replacements exist.
2. Template surfaces, JavaScript layers, composition, assets, forms, packaging, capabilities, and validation have defined, testable outcomes.
3. The first Phase 2 slice is pagination: characterize it, extract it as a pack-local component, retain `#pagination`, prove unchanged default behaviour, and merge it independently.
4. Ordinary delivery remains one characterized slice at a time; default DaisyUI repackaging remains the named atomic checkpoint with its full compatibility, packaging, loading, and browser gate.

Master Phase 1 is complete. Exact public APIs remain subject to proof by later extraction slices unless already identified as stable.
