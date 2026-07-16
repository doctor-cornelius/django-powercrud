# Phase 1.2–1.5 Template-Pack Contract Analysis

## Status

Complete and ratified. This records the accepted Phase 1.2–1.5 contract baseline.

## Purpose And Scope

This document completes the remaining Phase 1 analysis in one pass. It defines recommended contracts for:

1. Pack-owned templates and focused downstream overrides.
2. Core, framework-adapter, and variant-adapter JavaScript ownership.
3. Asset loading and form-rendering capabilities.
4. Official-pack distribution, metadata, validation, and test gates.

It does not add a pack resolver, move templates, introduce a public adapter API, change package contents, change loading paths, or edit application code.

## Binding Inputs

1. The ratified compatibility contract: [`phase1.1-compatibility-resolution-audit.md`](phase1.1-compatibility-resolution-audit.md).
2. The current runtime architecture: [`src/powercrud/static/powercrud/js/README.md`](../../../../src/powercrud/static/powercrud/js/README.md).
3. The JavaScript ownership map: [`phase6-boundary-findings.md`](../../_archive/js_cleanup/phase6-boundary-findings.md).
4. The current templates, rendering call sites, static entry points, packaging configuration, sample integrations, tests, and public documentation.

The Phase 1.1 contract is binding: ordinary built-in DaisyUI users remain compatible indefinitely; full-template legacy customisation remains through 0.x and receives a v1.0 removal target only after the replacement ships.

## Executive Findings

1. A neutral core HTML fallback would become an accidental third framework. Core should own rendering resolution, context, semantics, and validation; packs should own presentation templates.
2. Current direct `#partial` rendering means the legacy façade must retain server-addressable names while focused overrides are extracted behind it.
3. A complete pack is compositional: template namespace, framework adapter, optional variant adapter, capability declarations, form support, and optional assets. It is not one indivisible JavaScript/CSS bundle.
4. The standard DaisyUI implementation must remain automatically composed through both existing loading paths while the JavaScript boundary is extracted.
5. The default pack needs zero new installed-app, setting, or script-tag requirements. Optional future packs may require explicit opt-in configuration.
6. The current wheel and sdist include only `src/powercrud`; any sibling optional Django app requires deliberate build configuration and clean-artifact verification.
7. Pagination is the recommended first Phase 2 slice because it has a bounded list-only context and no current JavaScript ownership. It remains a ratification decision rather than a completed conclusion.

## Phase 1.2: Template And Focused-Override Contract

### Ownership Model

Core owns:

1. View context production and template resolution.
2. Server-rendered fragment names required by Python and HTMX.
3. Semantic `data-powercrud-*` and `data-inline-*` meanings.
4. Event, request, URL, storage, and validation contracts.
5. Pack capability validation.

Packs own all rendered CRUD presentation templates and their framework-specific markup, classes, layout, visual IDs, and component files. Core does not supply a neutral visual fallback.

The current `powercrud/daisyUI` namespace remains the compatible default-pack façade during 0.x. It is the only default path required for ordinary existing projects.

### Capability Matrix

| Surface | Target classification | Required contract |
|---|---|---|
| List | Baseline | `object_list.html`, list rendering component, `#pcrud_content`, `#filtered_results` |
| Form | Baseline | `object_form.html`, normal form content, `#pcrud_content` |
| Detail | Baseline | `object_detail.html`, detail rendering component, `#pcrud_content` |
| Delete | Baseline | `object_confirm_delete.html`, normal delete content, `#pcrud_content` |
| Modal | Capability-dependent | Modal shell, modal target, `data-powercrud-modal` hooks |
| Bulk edit/delete | Capability-dependent | Bulk shell, errors/conflicts, selection status, bulk form hooks |
| Async conflict/bulk | Capability-dependent | Conflict fragments and queued-result surface |
| Inline editing | Capability-dependent | Display/edit row fragments, dependency widget, inline field/error hooks |
| Crispy forms | Capability-dependent | Crispy partials and declared crispy integration |
| Favourites | Add-on integration | Pack insertion and semantic-hook contract while retaining the existing `powercrud.contrib.favourites` service, routes, context, and toolbar surface |

The current legacy façade retains all existing server-consumed named fragments through 0.x. A future pack must provide every baseline fragment and every fragment required by capabilities it declares.

### Legacy Fragment Compatibility Matrix

The following names remain available from the legacy façade through 0.x. A future pack must provide the applicable names where its declared capability causes current Python or HTMX code to render them.

| Surface | Server-addressable legacy fragments | Capability |
|---|---|---|
| List | `#pcrud_content`, `#filtered_results`, `#pagination` | Baseline list |
| Selection | `#bulk_selection_status` | Bulk selection or bulk edit |
| Form | `#pcrud_content`, `#conflict_detected`, `#normal_content` | Baseline form; conflict is async/conflict |
| Detail | `#pcrud_content` | Baseline detail |
| Delete | `#pcrud_content`, `#conflict_detected`, `#normal_content` | Baseline delete; conflict is async/conflict |
| Bulk | `#full_form`, `#bulk_edit_error`, `#bulk_edit_conflict`, `#async_queue_success` | Bulk; queued result is async bulk |
| Inline | `#inline_row_display`, `#inline_row_form` | Inline editing |
| Crispy | `#load_tags`, `#crispy_form` | Crispy rendering |

`partial/inline_field.html` and `partial/modal.html` are direct template targets rather than named partial fragments and remain available for their declared inline and modal capabilities.

### Focused Override Contract

The target supported override areas are:

1. List toolbar and actions.
2. Filters and optional-filter controls.
3. Table shell, headers, rows, and row actions.
4. Bulk-selection status and bulk actions.
5. Pagination.
6. Modal shell and content.
7. Form shell, field content, and form actions.
8. Detail shell and content.
9. Delete shell, content, and actions.
10. Bulk field controls, errors, conflicts, and queued state.
11. Inline display rows, edit rows, dependency widgets, and validation state.

Every promoted focused override must document only the context it consumes, its capability requirement, its server-rendered partial name if any, and its semantic hooks. It must not promise current DaisyUI classes, floating-panel markup, icon markup, arbitrary DOM nesting, or visual IDs that no core behaviour consumes.

### Focused Override Matrix

| Override area | Minimum context | Semantic requirements | Legacy bridge |
|---|---|---|---|
| Toolbar and actions | `view`, CRUD URLs, permissions, HTMX/modal settings | Object-list root and action hooks | None initially |
| Filters | `filterset`, filter parameters, list URL, visible-filter state | `#filter-form`, filter toggle, list refresh hooks | Rendered inside list fragments |
| Table shell and rows | headers, rows, list/table state, visible columns | object-list root, `#filtered_results`, row-action hooks | `partial/list.html` and inline fragments |
| Bulk selection and actions | selected IDs/count, all/some-selected, bulk URLs | select-all, row-select, bulk-form and bulk-action hooks | `#bulk_selection_status` |
| Pagination | paginator, page object, page sizes, current filters | page-size and list-refresh hooks | `#pagination` |
| Modal | modal IDs, targets, classes, current object/action context | modal and modal-box hooks | `partial/modal.html` |
| Form shell and actions | form, object, create/update URLs, display items, HTMX state | object-form hook and target semantics | `object_form.html#pcrud_content` |
| Detail shell and content | object, fields/properties, view context | detail rendering semantics | `object_detail.html#pcrud_content`, `partial/detail.html` |
| Delete shell and actions | object, list URL, delete action, HTMX/modal state | delete form/target semantics | `object_confirm_delete.html#pcrud_content` |
| Bulk form and outcomes | bulk fields, field metadata, task/message, errors | bulk-form and result-event hooks | bulk fragments in the matrix above |
| Inline rows and dependency widgets | row/object, form fields, dependencies, inline URLs/errors | inline row/field/save/cancel/dependency hooks | inline fragments and `partial/inline_field.html` |

### Semantic Hooks To Preserve

The initial contract preserves semantic hooks already consumed by current runtime or server behaviour, including:

1. List roots, URLs, filtering, results, page-size, list-column, and row-action hooks.
2. Bulk selection, bulk form, select-all, and bulk-action hooks.
3. Modal targets, modal box hooks, and object-form hooks.
4. Inline row, field, save, cancel, dependency, endpoint, and error hooks.
5. Current custom events and server triggers, including bulk, refresh, inline-result, and form-error semantics.

Focused overrides may change presentation markup freely where these semantic requirements remain true.

### Legacy Copy Workflow

`pcrud_mktemplate` retains its current root-template and whole-tree copy modes through 0.x as the legacy full-template workflow.

The replacement is a future pack-resolved focused-component copy mode. It copies a supported focused override and emits its supported-context and semantic-hook instructions; it does not create another model-specific root-template fork. The exact manifest or metadata format remains deferred until a concrete component extraction proves the need. This mode ships only after Phase 2 has extracted and characterized the corresponding component.

## Phase 1.3: JavaScript Layers And Pack Composition

### Ownership Boundaries

| Layer | Owns | Does not own |
|---|---|---|
| Core | Durable CRUD semantics, list refresh, HTMX/request rules, state persistence, filters, favourites, columns, selection, inline lifecycle, public globals, events, semantic attributes, stable runtime entry | Framework classes, library setup, floating geometry, modal APIs, visual shells |
| Framework adapter | Reusable DaisyUI or Bootstrap presentation behaviour, library integration, dialogs, tooltips, searchable selects, spinners, visual disabled/error states, geometry where shared by the framework templates | Core request/state/event semantics |
| Variant adapter | A genuinely novel interaction needed by one template variant | Copies of core or framework adapter behaviour |

### Composition And Lifecycle

Each selected pack composes:

```text
template namespace + framework adapter + (no variant JS | hook extension | variant adapter)
```

The required lifecycle is:

```text
once-only core listeners
    -> repeatable core fragment work
    -> framework adapter fragment work
    -> optional variant fragment work
```

On HTMX replacement, every layer must scope work to the fragment, preserve semantic state, avoid duplicate page listeners, tear down attached library instances before replacement, and reinitialize after swap/settle through the existing lifecycle.

### Stable And Deferred Interfaces

Remain stable:

1. `powercrud/js/powercrud.js` and `window.__powercrudRuntimeLoaded`.
2. `window.initPowercrud(fragment)` and current public compatibility globals.
3. Stable semantic data attributes, public custom events, server trigger meanings, storage keys, URL/query behaviour, and list-root semantics.
4. Current manual and bundled loading contracts.

Remain internal until a real extraction slice proves them:

1. Adapter injection mechanism.
2. A possible `initPowercrudPack(fragment)` or equivalent initializer.
3. New pack JavaScript paths and loader helpers.
4. Exact Python metadata or declaration classes.

During incremental extraction, the compatible DaisyUI adapter remains implicitly composed behind both existing runtime entries. No ordinary merge adds a required script tag, public static path, or user setting.

## Phase 1.4: Assets And Form Rendering

### Asset Ownership

The downstream project continues to own the complete base template, `<head>`, global styling, and the choice of manual versus bundled integration.

The target contract is:

1. Every integration loads the stable core entry through its existing manual or bundled path.
2. The built-in default DaisyUI behaviour adds no new downstream loading requirement.
3. An opt-in non-default pack may declare additional manual and bundled assets; its selected integration supplies them through a future pack-assets mechanism in the downstream base template.
4. Inner CRUD templates do not inject global scripts or silently load a second frontend pipeline.
5. A variant may declare no extra assets and reuse the existing DaisyUI/Tailwind stack and framework adapter.
6. In manual mode, the downstream project supplies HTMX, Tom Select, Tippy, and their vendor CSS before the stable PowerCRUD module and package CSS, following the current documented order.
7. In bundled/Vite mode, `config/static/js/main.js` supplies those vendor libraries and globals before importing PowerCRUD CSS and the stable runtime entry.
8. Framework adapters must consume the applicable mode's existing vendor dependency rather than independently loading a duplicate.
9. Manual and bundled modes remain mutually exclusive on one page, as current public documentation already directs.

The exact template-tag or loader API for non-default pack assets remains deferred until Phase 3 or Phase 4 has an actual selected-pack implementation to drive it.

### Form Capabilities

Every official pack that declares form support must support native Django form rendering with `use_crispy=False`.

Crispy support is capability-declared, with an additional official-pack rule:

1. The default DaisyUI pack retains its existing crispy-forms and `crispy-tailwind` compatibility.
2. Every official framework pack with a maintained crispy integration includes and tests it, naming the required crispy template pack and dependency.
3. A pack that does not declare crispy support must render native forms correctly and must not claim crispy rendering for any form-related surface it has not tested.
4. The full-parity Bootstrap dogfood includes a maintained crispy-Bootstrap integration. Form, filter, inline-edit, bulk-edit, modal, and async support are independently declared capabilities rather than implied by a pack name.

## Phase 1.5: Distribution, Metadata, And Validation

### Official-Pack Distribution

The recommended distribution model is:

1. Co-distribute official packs with `django-powercrud` for shared versioning, release control, documentation, and CI.
2. Keep the compatible default DaisyUI implementation within the installed `powercrud` application so ordinary users do not add an app to `INSTALLED_APPS`.
3. Ship Bootstrap as an optional contrib-style Django app or package in the same distribution, enabled only by explicit selection.
4. Allow third-party packs to ship as separately installed Django apps that satisfy the same declared contract.

Any optional co-distributed package requires explicit Hatch wheel and sdist inclusion. Its templates and static assets must be proven from clean installed artifacts.

### Pack Metadata

Every future selected pack declares, in an internal representation initially:

1. Contract version.
2. Template namespace.
3. Framework adapter identity.
4. Optional variant-adapter identity or no-variant declaration.
5. Declared baseline and optional capabilities.
6. Native and optional crispy form support.
7. Optional manual and bundled assets.

The exact module, class, function, or settings schema is deferred. Phase 1 locks required information, not a speculative public implementation API.

### Validation Model

Runtime selection performs lightweight checks only: selected-pack identity, importability where applicable, contract-version compatibility, and a clear configuration error when the selected pack is unavailable.

Development and CI use a fuller pack validator that verifies:

1. Required baseline templates and capability-dependent templates.
2. Required server-addressable partials for declared capabilities.
3. Declared adapter and asset metadata.
4. Form-rendering declarations and dependencies.
5. Contract version compatibility.
6. Artifact template and static discovery.

For every official-pack release and the atomic default-pack repackaging checkpoint, build wheel and sdist artifacts and install each into a clean environment before running the applicable checks. This is not a gate for every documentation change or small internal extraction slice.

The validator should prefer rendering and behaviour checks over brittle template-source parsing. Named partial inspection is permitted only where Python directly renders that name.

### Test And Merge Gates

Every applicable pack must pass shared core behaviour and browser contracts for the capabilities it declares. Validation includes:

1. Focused source-level configuration, template, fragment, command, and asset tests.
2. Browser coverage for list/HTMX, modal form, bulk, inline, row actions, tooltips, and both asset modes where claimed.
3. Added characterization for downstream focused overrides, bundled-mode loading, detail/delete, and the Phase 6 boundary safeguards before moving related behaviour.
4. Built wheel and sdist installation in clean environments before official pack release or default-pack repackaging.

Ordinary work merges one characterized slice at a time. The default DaisyUI repackaging gate additionally requires legacy namespaces and named fragments, copy workflow, tag/style resolution, artifact contents, default adapter composition, and both loading modes to pass together.

## Ratified Decision Register

| ID | Recommendation |
|---|---|
| D11 | Packs own all presentation templates; core owns resolver, context, semantic contracts, and validation. |
| D12 | Baseline packs support list, form, detail, and delete; modal, bulk, async, inline, crispy, and favourites are capability-dependent. |
| D13 | Focused override points are the eleven areas and minimum context/hook requirements in the Phase 1.2 matrices; only those consumed contracts are stable. |
| D14 | Existing server-addressable fragments remain the 0.x legacy façade; focused component filenames become public only after characterized extraction. |
| D15 | `pcrud_mktemplate` retains root and whole-tree copying through 0.x, then gains pack-resolved focused-component copying and generated usage instructions after each component ships; its metadata format remains deferred. |
| D16 | Core, framework adapter, and variant adapter have the ownership boundaries and lifecycle order defined above. |
| D17 | A pack composes template namespace, framework adapter, and none/hooks/variant adapter; multiple template packs reuse one framework adapter. |
| D18 | Existing runtime globals, semantic hooks, events, storage, URLs, and two asset modes remain stable; exact adapter and metadata APIs stay deferred. |
| D19 | The default DaisyUI pack adds no new base-template, installed-app, setting, or script requirement; non-default packs may declare opt-in assets. |
| D20 | Native Django forms are mandatory for declared form support. Every official framework pack with a maintained crispy integration includes and tests it; the Bootstrap full-parity dogfood includes crispy-Bootstrap. |
| D21 | Official packs are co-distributed: compatible DaisyUI remains in `powercrud`, while Bootstrap is an optional contrib-style app or package in the same distribution; third-party packs remain separately installable. |
| D22 | Pack metadata contains contract version, namespace, adapters, capabilities, form support, and optional assets, while its concrete API remains deferred. |
| D23 | Runtime checks are lightweight; a developer/CI validator performs contract, capability, adapter, asset, dependency, and artifact validation. |
| D24 | Shared capability-driven source and browser tests are mandatory; clean wheel/sdist installation is mandatory before official-pack release or default-pack repackaging, not every small slice. |
| D25 | Phase 2 starts by extracting pagination into a pack-local component while retaining the existing `#pagination` legacy fragment and unchanged default behaviour. |

## Verification

Static source, template, runtime, packaging, documentation, and test inventories were completed for this analysis.

The previous Phase 1.1 focused unit command was blocked because `powercrud_django_dev` was stopped. This pass does not claim any test result. Before Phase 2 implementation begins, rerun the existing focused unit and browser baseline from the Phase 1.1 audit, then add the characterization required for the selected pagination slice.

## Ratification Completion

The user accepted D11 through D25, with the Bootstrap distribution, full-parity, and crispy refinements recorded above. The corresponding Phase 1.2–1.5 tasks are complete, Phase 1.6 records the baseline, and Master Phase 2 is next.
