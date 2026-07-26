# Phase 4.0 Pack Contract Audit

## Status

Complete. Two fresh read-only audits were reconciled into the Phase 4 implementation contract on `template_pack/4.0`.

## Scope And Method

The first audit stream mapped Python configuration, template resolution, styles, copy workflows, package layout, and distribution compatibility. The second mapped runtime composition, manual-static and Vite loading, frontend packaging, browser coverage, and genuine gaps.

Neither audit edited files, ran tests or builds, selected public APIs independently, or created a competing plan. The main agent reconciled their findings with the accepted Phase 1 contracts and completed Phase 2–3 evidence.

## Ratified Outcomes

1. Phase 4 first makes pack architecture work with the active DaisyUI implementation remaining at `powercrud/daisyUI`.
2. The completed end-state is one atomic relocation of the real template source to `powercrud/packs/daisyui`, with the old namespace retained as a 0.x compatibility façade.
3. The new selector is `POWERCRUD_SETTINGS["POWERCRUD_TEMPLATE_PACK"]`. The built-in identity is `daisyui`; third-party declarations use `module.path:attribute`.
4. A public immutable `TemplatePack` declaration must contain the contract version, identity, Django template namespace, package-resource template root, legacy copy destination where applicable, framework and optional variant adapter identities, capabilities, form support, optional Django app identity, and additional asset declarations.
5. Phase 4 supports only the `daisyui` framework adapter with no variant adapter. The built-in pack declares no additional assets. Unsupported adapter, variant, or required-asset declarations must fail clearly rather than imply dynamic browser selection.
6. Per-view pack selection is not needed. Existing explicit `templates_path` remains the supported view-level custom-template mechanism.
7. The stable runtime entry and CSS path remain unchanged. Phase 4 groups the eight existing private DaisyUI factories behind a private composition module; it does not create a public registry, global configuration object, or initializer.

## Python And Template Findings

1. `ConfigMixin.templates_path` and `pcrud_mktemplate.Command.template_prefix` currently resolve settings at module/class import. Both must become invocation-time or resolved-config values; caching the new selector at import time is unsafe.
2. Resolution cannot use one universal namespace helper without changing legacy behaviour. It needs four seams:
    1. View templates: explicit `templates_path`, then selected pack, then legacy global setting.
    2. Inclusion tags: selected pack, then legacy global setting.
    3. Styles: selected pack framework identity, then legacy global setting.
    4. Copy sources: selected pack package-resource root, while legacy copy destinations stay stable.
3. Outer-template precedence remains explicit `template_name`, then app/model convention, then the effective view namespace. Focused components remain model-first, then that effective view namespace. The HTMX redisplay bypass must use resolved configuration rather than a class attribute.
4. List and detail inclusion tags are currently fixed at import time. They need render-time template selection while keeping their existing Python context behaviour.
5. `HtmxMixin.get_framework_styles()` is a public override point. Phase 4 may route default styles through the pack, but must retain that method’s compatibility contract.
6. The current default tree has 45 templates, including 31 focused components. Eight files define 25 server-addressable named partials. Simple `{% include %}` or `{% extends %}` facades do not expose partial definitions under the old file name.
7. Ordinary legacy files may forward to their new counterparts. The eight partial-bearing legacy files must re-declare every old partial name and delegate its body to the corresponding new partial.
8. `pcrud_mktemplate` must copy real selected-pack source files after relocation while preserving the existing `daisyUI` destination segment for legacy whole-tree copying.

## Runtime And Asset Findings

1. `powercrud/js/powercrud.js` is the stable public entry and current composition shell. It imports and constructs all eight private DaisyUI adapter factories while preserving globals, listener ordering, fragment initialization, and HTMX teardown.
2. The smallest safe Phase 4 runtime slice is one private DaisyUI composition module. It must preserve the current staged construction order because filter/favourites depends on core-created searchable-select and tooltip functions.
3. The browser has no settings-to-JavaScript transport. Phase 4 can validate that Python selected a supported DaisyUI declaration, but must not claim dynamic client-side pack selection.
4. Manual-static and Vite both already load the same stable PowerCRUD JS/CSS entries and vendor stack. The built-in pack adds no new script tag, installed app, vendor loader, or base-template requirement.
5. The current private adapter module paths and `powercrud/css/powercrud.css` are observed by packaging and manual-static tests. They remain in place through Phase 4 unless a separately proven static compatibility façade becomes necessary.
6. Hatch already packages the entire `src/powercrud` tree in wheel and sdist scope. New in-package Python, template and static files need no extra build target, but source-tree tests do not prove installed artifacts.

## Required Checkpoints

1. Phase 4.1 uses focused declaration, selector, import/error, and no-cache tests only.
2. Phase 4.2 uses focused resolver, tag, style, fragment and copy tests, then the full non-Playwright regression before integration because it touches the complete server rendering surface.
3. Phase 4.3 uses focused frontend packaging, manual-static, and Vite browser loading checks. No canonical full regression is required for that behaviour-preserving private composition extraction.
4. The atomic Phase 4.4–4.5 gate runs the complete server and Playwright suites, manual-static and Vite checks, clean wheel and sdist installation checks, and an independent compatibility review.

## Confirmed Stop Conditions

Stop if a required new default-pack installed app, setting, script tag, or base-template change emerges; if named-fragment facades cannot preserve server rendering; if the selected-pack contract requires unproved browser transport; if installed artifacts omit required files; or if a deterministic compatibility regression remains unexplained.
