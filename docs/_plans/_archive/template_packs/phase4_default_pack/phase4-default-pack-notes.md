# Phase 4 Default DaisyUI Pack Notes

## Purpose

These notes support [`phase4-default-pack-plan.md`](phase4-default-pack-plan.md), which implements Phase 4 of the [`template_packs-master-plan.md`](../template_packs-master-plan.md).

Phase 4 turns the characterized current DaisyUI implementation into the automatically selected compatible default pack. It first proves selection, discovery, composition, and configuration while the implementation remains at `powercrud/daisyUI`; it then performs one atomic relocation to `powercrud/packs/daisyui` while retaining the legacy namespace as a 0.x compatibility façade.

## Binding Inputs

1. Phase 1 locked compatibility, resolution, composition, assets, forms, packaging, capability, validation, and atomic-transition contracts.
2. Phase 2 shipped 31 model-first focused components while retaining the legacy namespace, fragments, and copy workflows.
3. Phase 3 shipped eight automatically composed private DaisyUI presentation adapters behind the stable runtime entry.
4. The compatible DaisyUI pack remains inside the installed `powercrud` application and adds no installed-app requirement for existing users.
5. Official packs are co-distributed; full reusable validation remains Phase 6 work, while the default-pack transition requires clean wheel and sdist proof now.
6. The sample application will prove variants in Phase 5 and later phases; it must not dictate an otherwise unnecessary Phase 4 public API.
7. The reconciled Phase 4.0 evidence is preserved in [`phase4.0-pack-contract-audit.md`](phase4.0-pack-contract-audit.md).
8. The detailed read-only implementation findings—including the Phase 4.2 resolver, Phase 4.3 runtime, and Phase 4.4 legacy-facade reviews—are preserved in [`phase4-implementation-audits.md`](phase4-implementation-audits.md).

## Delivery Rule

Resolver helpers, dormant metadata, discovery, configuration checks, and compatible composition infrastructure may integrate independently only when they leave current default behaviour and every legacy path unchanged. During those independently integrated slices, `powercrud/daisyUI` remains both the active default-pack namespace and the physical implementation source.

The physical default-pack relocation and activation are one named atomic transition. They remain on one branch until `powercrud/packs/daisyui` is the active source of truth and template resolution, legacy facades, settings, styles, copy workflows, adapter loading, both asset modes, installed artifacts, and applicable browser behaviour pass together.

Every implementation slice begins from synchronized `staging/main`, receives proportionate characterization, is committed and pushed as a bounded slice, and is integrated before a later independent slice begins. Protected `main` is not changed by this child-plan workflow.

## Decision Boundaries

Phase 4.0 is complete. The agreed implementation contract is:

1. `POWERCRUD_SETTINGS["POWERCRUD_TEMPLATE_PACK"]` is the new selector. Its canonical built-in value is `"daisyui"`; an absent selector uses the compatible built-in pack, while legacy `POWERCRUD_CSS_FRAMEWORK` continues to select existing custom legacy namespaces only when the new selector is absent.
2. Official aliases resolve from a small built-in table. A third-party selector uses exact `module.path:attribute` syntax and imports one immutable `TemplatePack` declaration.
3. `TemplatePack` is the minimal public declaration contract for authors: identity, contract version, Django template namespace, package-resource template root, legacy copy destination where applicable, framework adapter, optional variant adapter, capabilities, native/crispy form support, optional Django app identity, and additional manual/Vite asset declarations.
4. The built-in declaration started at `powercrud/daisyUI` while the compatible resolver work landed, then the named atomic transition moved its active template namespace and physical source to `powercrud/packs/daisyui`. It declares framework adapter `daisyui`, no variant adapter, crispy-tailwind support, and no additional assets.
5. Pack resolution must remain dynamic. New pack selection, `templates_path`, and `pcrud_mktemplate` sources must never be frozen while Python classes or command modules import.
6. Four resolution seams stay distinct: view templates use explicit `templates_path` before pack selection; inclusion tags use selected pack before the legacy global; style lookup uses selected pack framework identity before the legacy global; copy sources use the selected pack's physical resource root while legacy copy destinations remain stable.
7. Phase 4 supports only the `daisyui` framework adapter and no variant adapter at runtime. Unsupported selected adapter, variant, or additional required asset declarations fail clearly rather than implying browser-side dynamic loading that does not yet exist.
8. Per-view pack selection remains out of scope. The namespace sequence is fixed: use `powercrud/daisyUI` first, then atomically relocate to `powercrud/packs/daisyui`.

A public declaration is justified because independently distributed third-party packs require it. Internal JavaScript composition remains private; the stable entry receives no pack registry, global configuration object, or public initializer in Phase 4.

## Compatibility Matrix For The Atomic Gate

The transition must cover at least:

1. Unconfigured projects receiving the same default DaisyUI behaviour.
2. The legacy `POWERCRUD_CSS_FRAMEWORK` default and canonical `daisyUI` spelling.
3. Explicit per-view `templates_path` and direct `template_name` behaviour.
4. App/model outer-template and focused-component precedence.
5. Existing `powercrud/daisyUI/...` roots, includes, direct targets, and server-addressable named fragments.
6. Template tags and framework-style lookup.
7. `pcrud_mktemplate` focused-component, root, model, and whole-tree modes.
8. Native and crispy-tailwind form paths.
9. Manual-static and bundled/Vite runtime loading.
10. Public globals, semantic hooks, HTMX lifecycle, state preservation, and adapter teardown.
11. Wheel and sdist discovery from clean installed artifacts.
12. Clear errors for unavailable, incompatible, or invalid explicitly selected packs.

## Stop Conditions

Stop implementation for a material public-API decision not settled in Phase 4.0, compatibility ambiguity, unexplained deterministic regression, incomplete artifact contents, a required new downstream installation step for the default pack, unexpected remote movement, unrelated worktree mutation, or a non-trivial conflict.

Create a Phase 4 blocker register only when the first genuine blocker occurs. Do not create one pre-emptively.

## Plan

### Phase 4.0: Confirm Evidence And The Implementation Contract

The completed first round used two fresh read-only sub-agent audits. One mapped Python-side settings, resolution, styles, copying, layout, and artifacts. The other mapped runtime composition, assets, loading modes, coverage, and genuine gaps. They found no blocker, but established that import-time resolution is unsafe, one universal resolver would break legacy precedence, simple template facades cannot preserve named partials, and clean artifact proof is missing.

The main agent reconciled both maps with the binding Phase 1 decisions and completed Phase 2–3 facts. The recorded contract above, the numbered branch sequence, and the named atomic-transition gate are now authoritative. Later audits may refine implementation mechanics but may not reopen these decisions without a genuine compatibility blocker.

### Phase 4.1: Introduce Dormant Pack Identity And Discovery

This phase established the public frozen `TemplatePack` declaration, the contract-version constant, the built-in `daisyui` alias, and third-party `module.path:attribute` discovery. The built-in declaration stays inside the existing `powercrud` application and describes the current `powercrud/daisyUI` source; no template, style, copy, mixin, tag, or JavaScript caller uses it yet.

Selector resolution is invocation-time only. An absent `POWERCRUD_SETTINGS["POWERCRUD_TEMPLATE_PACK"]` selects DaisyUI locally without adding the key to `conf.DEFAULTS`, so the next slice can still distinguish the legacy fallback. An explicit null or malformed selector now raises a contextual configuration error rather than silently becoming the default. Declarations are re-read on every lookup, while normal Python module caching remains harmless because the named attribute is fetched and validated each time.

The declaration checks immutable shape only for capabilities, deferring semantic capability vocabulary validation to the later validation phase. It does reject the Phase 4 runtime combinations that cannot work without new browser transport: a non-DaisyUI framework adapter, a variant adapter, or additional manual/Vite assets. Its legacy-copy destination is limited to one safe POSIX segment in preparation for Phase 4.2 copy-source work.

An independent read-only review found and the slice corrected the explicit-null selector bug, premature capability whitelisting, unsafe legacy-copy destination shape, incomplete built-in-contract coverage, and missing built-in-alias identity invariant. It also identified that the existing minimal-settings tests import sample models while their settings omitted the sample application. The fixture now includes those synchronous test models while continuing to omit async applications and `POWERCRUD_SETTINGS`.

Focused evidence: 89 default-settings declaration/configuration tests and 4 minimal-settings tests passed. The minimal run emitted a pre-existing Django-Q dependency warning but passed; no full regression, artifact build, or browser run was justified because this slice adds no rendering, package-resource movement, static, or runtime behaviour.

### Phase 4.2: Add Compatible Selection And Template Resolution

Selection remains distinct from the legacy CSS-framework setting. The absence-aware selected-pack resolver leaves `POWERCRUD_CSS_FRAMEWORK` authoritative when the new selector is absent; an explicit selected declaration supplies its namespace and package-resource root. The public `get_selected_template_pack()` still provides compatible DaisyUI for unconfigured callers, but resolver seams retain absence so legacy custom framework namespaces do not silently change.

`ConfigMixin` now resolves its default template namespace while building each config namespace, not at class import. Explicit per-view `templates_path`, explicit `template_name`, and model-first focused candidates remain ahead of that dynamic fallback. HTMX, async, form, and bulk direct-fragment callers now use the resolved configuration rather than a stale class attribute.

The list/detail inclusion tags receive a render-time template-candidate iterable, preserving their direct Python context builders while preventing module-import template freezing. Style lookup uses a central resolver: an explicit pack prefers the canonical adapter key, then accepts the established `daisyUI` key used by existing public `get_framework_styles()` overrides. With no new selector it continues to use the legacy setting exactly.

`pcrud_mktemplate` resolves its source package-resource directory at command invocation. Its built-in source remains the existing tree, and whole-tree copying keeps the legacy `daisyUI` destination. A selected third-party declaration without an explicit legacy copy destination fails clearly rather than inventing a public destination rule.

Focused resolver, management-command, template-tag, and form/template checks passed (215 tests). The required full non-Playwright checkpoint then passed with 962 tests and 78 Playwright tests intentionally deselected. The current `powercrud/daisyUI` files remain both source and namespace; relocation is still deferred to the named atomic transition.

### Phase 4.3: Add Compatible Runtime And Asset Composition

The stable public entry remains the loading contract. A new private `runtime/daisyui-composition.js` constructs the eight DaisyUI presentation adapters and the adapter-wired searchable-select runtime in their existing order. `powercrud.js` still owns durable feature runtime construction, public globals, listener installation, duplicate-load protection, fragment lifecycle, and the late-bound list/favourites relationship.

The private composition factory constructs searchable-select presentation before its semantic runtime; tooltip presentation before filter/favourites presentation; then modal, action, inline, list-column, filter/favourites, and row-action presentation. It returns the same adapter-shaped values that the public entry previously constructed inline. This keeps filter/favourites dependent on the already-created searchable-select and tooltip functions, without introducing a browser-side selector, registry, pack script, or new static path.

Manual-static and Vite continue loading the unchanged stable JavaScript and CSS entries. The focused package test passed with 16 tests. Rebuilding the Vite asset and running the focused manual-static and Vite Playwright checks passed with 2 tests: both loading modes retained public globals, normal initialization, and no browser errors. The Vite build emitted the existing upstream HTMX direct-`eval` warning only.

### Phase 4.4: Build The Atomic Default-Pack Transition

This is the named atomic transition. `template_pack/4.4` began from integrated Phase 4.3 and relocates the 45-file template source of truth and pack Python/style resources from `powercrud/daisyUI` to `powercrud/packs/daisyui`. The built-in declaration now names that permanent namespace and package-resource root. With no new selector, the canonical legacy `POWERCRUD_CSS_FRAMEWORK="daisyUI"` default resolves that built-in source; a genuinely custom legacy framework remains on the old fallback path.

Thirty-seven ordinary legacy files are thin forwarding includes. The eight files that define the 25 server-addressable named partials load `powercrud_partials` first, forward normal rendering to the permanent template, and re-declare every historical partial name as a corresponding new `#partial` include. This leaves one editable template source while retaining all 45 0.x paths and their named-fragment targets.

The built-in DaisyUI style mapping now lives in `powercrud.packs.daisyui.styles`; `HtmxMixin.get_framework_styles()` remains the public downstream override point. The eight private adapter modules, stable `powercrud/js/powercrud.js` entry, and stable `powercrud/css/powercrud.css` path remain in place. No downstream setting, installed app, base-template, or script-tag change is required.

The atomic browser gate exposed a deterministic lifecycle defect: a short-lived marker that keeps the filter panel open for a list refresh could survive an unrelated HTMX shell navigation. The marker is now consumed by the next marked list swap and cleared for other swaps. [`test_filter_panel_refresh_state_is_cleared_on_shell_return`](../../../src/tests/playwright/test_filter_favourites.py) proves that the refreshed list remains open through repeated initialization, while a return through the shell is closed. This is a compatibility repair rather than a new pack API or loading mechanism.

### Phase 4.5: Pass The Atomic Compatibility And Distribution Gate

Focused source/facade and command evidence passed with 86 tests. It includes the 45↔45 source/facade inventory, compilation of both namespaces and all 25 legacy and permanent named partial targets, canonical-default selection, style-provider delegation, configuration errors, and focused/root/model/whole-tree copy behaviour.

The final server regression passed with 966 tests (78 Playwright tests deselected). The complete Playwright gate passed with 78 tests, including manual-static and Vite loading, public globals, lifecycle, and browser-error coverage. The test environment used the isolated SQLite fallback because the shared Postgres test database was held by a separate interactive session; it did not change application code or configuration. The Vite build produced the regenerated `powercrud-37nk9Mzn.js` manifest entry and only the established upstream HTMX direct-`eval` warning.

`uv build` produced `django_powercrud-0.8.6-py3-none-any.whl` and `django_powercrud-0.8.6.tar.gz`. Each artifact was installed into a separate fresh temporary environment. Both installs contained 45 permanent templates, matching 45 legacy facades, the pack declaration and style provider, the manifest, and the stable runtime entry.

The fresh independent review rechecked public-contract drift, legacy paths, duplicate source risk, copy semantics, static loading, generated assets, and recorded evidence. It identified and corrected the named-partial load-order hardening and required the explicit lifecycle-regression characterization above. After those corrections it found no remaining implementation blocker and approved the atomic diff for integration.

### Phase 4.6: Ratify Phase 4

Ratification confirms the selected default pack is compatible, packaged, and sufficient for Phase 5 to build a real reference variant. `template_pack/4.4` was squash-integrated into `staging/main` as `c792c7f5` after the full server, browser, artifact, and independent-review gates, then retired locally and remotely. Protected `main` was not changed.

The master plan and notes now record Phase 4 as complete. No stable public documentation is promoted early: selection/author guidance remains Phase 8 work after the reference variant and cross-framework proof. Phase 5 is the next implementation phase when separately authorized.
