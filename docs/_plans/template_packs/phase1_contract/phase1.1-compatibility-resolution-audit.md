# Phase 1.1 Compatibility And Resolution Audit

## Status

Audit complete and ratified as the Phase 1.1 compatibility contract.

## Scope And Method

This read-only audit records the current compatibility surface for template selection, template paths, partial rendering, template copying, and runtime loading. It does not change application code, settings, public APIs, or authoritative plan checkboxes.

Evidence came from the current package source, sample project, tests, public documentation, the archived JavaScript boundary findings, and the internal runtime guide. The focused test command could not run because the required `powercrud_django_dev` container was stopped; this is recorded under verification rather than treated as a passing result.

## Executive Findings

1. Current legacy compatibility is wider than the four CRUD root templates. It includes twelve files in `powercrud/daisyUI/`, server-rendered `#partial` names, template tags, the template-copy command, sample helpers, and public documentation.
2. `templates_path` is the primary view-level template namespace, but it is not universally authoritative. Some inclusion tags, framework styles, and the copy command derive from global `POWERCRUD_CSS_FRAMEWORK` instead.
3. Normal outer views prefer an app/model convention over the configured fallback, while HTMX list redisplay bypasses that outer-template choice and renders from `self.templates_path` directly.
4. Manual and bundled/Vite users have stable, distinct loading contracts that must remain usable through every ordinary merge.
5. The current default namespace and style key are `daisyUI` with capital letters, while some public documentation shows lowercase `daisyui`. This is a concrete case-sensitive-filesystem compatibility risk.
6. Default-pack repackaging is an atomic transition. Incremental work can still merge beforehand when it preserves the legacy namespace, existing paths, default runtime entry, and both asset modes.

## Current Resolution Map

### Global Framework Setting

`get_powercrud_setting()` reads `settings.POWERCRUD_SETTINGS` and falls back to internal defaults. The legacy `POWERCRUD_CSS_FRAMEWORK` default is exactly `"daisyUI"`.

| Surface | Current behaviour | Evidence |
|---|---|---|
| Global default | `POWERCRUD_SETTINGS["POWERCRUD_CSS_FRAMEWORK"]`, then internal default `"daisyUI"`. | [`conf.py`](../../../src/powercrud/conf.py) |
| Unconfigured Django settings | Uses library defaults and does not read user settings. | [`conf.py`](../../../src/powercrud/conf.py) |
| Validation | No pack identity, alias, installed-app, or template-existence validation exists. | [`conf.py`](../../../src/powercrud/conf.py) |
| Documentation mismatch | Some public docs show lowercase `"daisyui"`, which does not match the current default directory or style key. | [`getting_started.md`](../../../mkdocs/guides/getting_started.md), [`styling_tailwind.md`](../../../mkdocs/guides/styling_tailwind.md) |

### Outer Template Selection

| Priority | Current behaviour | Evidence |
|---|---|---|
| 1 | An explicit `template_name` is the only candidate. | [`url_mixin.py`](../../../src/powercrud/mixins/url_mixin.py) |
| 2 | Otherwise Django first tries `{app_label}/{model_name}_{role}.html`. | [`url_mixin.py`](../../../src/powercrud/mixins/url_mixin.py) |
| 3 | The fallback is `{resolved templates_path}/object_{role}.html`. | [`url_mixin.py`](../../../src/powercrud/mixins/url_mixin.py) |
| Rendering fallback | `HtmxMixin` probes the app/model candidate and falls back to the configured generic candidate if it does not exist. | [`htmx_mixin.py`](../../../src/powercrud/mixins/htmx_mixin.py) |

`templates_path` resolves differently in two code paths:

1. Full `ConfigMixin` configurations use the configured class or instance value.
2. The fallback configuration shim uses `source.templates_path` when truthy, otherwise dynamically derives `powercrud/{POWERCRUD_CSS_FRAMEWORK}`.

This difference is observable for empty or `None` values and must be resolved deliberately before introducing a pack selector.

### HTMX And Direct Fragment Rendering

`X-Redisplay-Object-List` renders `{self.templates_path}/object_list.html` directly, selecting `#pcrud_content` or `#filtered_results`. This bypasses the normal app/model outer-template candidate and explicit `template_name` for the emitted list fragment.

Several server paths construct names from `templates_path` directly. A new template namespace therefore needs all required fragments for the capabilities it claims; app/model root-template fallback does not protect these paths.

## Legacy Template And Partial Surface

The current namespace is `powercrud/daisyUI/` and includes:

| Category | Current paths or fragments |
|---|---|
| Root orchestrators | `object_list.html`, `object_form.html`, `object_detail.html`, `object_confirm_delete.html` |
| Capability orchestrators | `bulk_edit_form.html`, `crispy_partials.html` |
| Shared templates | `partial/list.html`, `partial/detail.html`, `partial/bulk_edit_errors.html`, `partial/inline_field.html`, `partial/modal.html`, `layout/inline_field.html` |
| List fragments | `#pcrud_content`, `#bulk_selection_status`, `#filtered_results`, `#pagination` |
| Form/delete fragments | `#pcrud_content`, `#conflict_detected`, `#normal_content` |
| Bulk fragments | `#full_form`, `#async_queue_success`, `#bulk_edit_error`, `#bulk_edit_conflict` |
| Inline fragments | `#inline_row_display`, `#inline_row_form` |
| Crispy fragments | `#load_tags`, `#crispy_form` |

The following code uses these surfaces directly:

1. HTMX list, form, delete, and conflict response rendering.
2. Bulk-edit, bulk-error, and async-queue rendering.
3. Inline-edit row and field rendering.
4. Selection endpoints that render `#bulk_selection_status`.
5. Root-template modal and crispy includes through `framework_template_path`.

Relevant call sites include [`htmx_mixin.py`](../../../src/powercrud/mixins/htmx_mixin.py), [`form_mixin.py`](../../../src/powercrud/mixins/form_mixin.py), [`inline_editing_mixin.py`](../../../src/powercrud/mixins/inline_editing_mixin.py), [`async_mixin.py`](../../../src/powercrud/mixins/async_mixin.py), and [`bulk_mixin`](../../../src/powercrud/mixins/bulk_mixin/).

Thin compatibility templates cannot be assumed safe until they prove that Django template partial names remain available through the chosen aliasing mechanism.

## Override And Copy Surface

### Existing Downstream Overrides

1. A model-specific template under `{app}/templates/{app}/{model}_{role}.html` overrides the generic outer template.
2. An explicit `template_name` overrides both the conventional and generic outer-template candidates.
3. A view `templates_path` changes the generic root templates and most direct fragments and includes.
4. The downstream project owns `base_template_path`, navigation, `<head>`, and global assets.

### `pcrud_mktemplate`

`pcrud_mktemplate app.Model --list|--detail|--form|--delete` copies one root orchestrator into the model-specific override location. `pcrud_mktemplate app.Model --all` copies the four root orchestrators. `pcrud_mktemplate app --all` copies the whole selected framework tree.

The command derives its source namespace from `POWERCRUD_CSS_FRAMEWORK` at import time. It has no focused partial-copy option and does not independently select a future pack.

The whole-tree copy is a legacy compatibility surface: copied templates can retain internal paths and partial references that would be stranded by an uncoordinated namespace move.

## Split Resolution Hazards

The current implementation mixes view-level template selection and global framework selection:

| Surface | Resolution source |
|---|---|
| Generic roots, HTMX fragments, modal and crispy includes, bulk and inline fragments | Resolved view `templates_path` |
| `object_list` and `object_detail` inclusion tags | Global `POWERCRUD_CSS_FRAMEWORK` at tag registration/import time |
| Filter widget attributes, action styles, and modal metadata | Global `POWERCRUD_CSS_FRAMEWORK` and `get_framework_styles()` |
| Template-copy command source | Global `POWERCRUD_CSS_FRAMEWORK` at command import/class definition time |

Consequently, changing only `templates_path` can produce a mixed page: custom root and direct partial templates together with globally selected list/detail inclusion-tag templates and framework styles. The Phase 1.1 contract must acknowledge this current behaviour before later phases decide whether and how to unify it.

## Runtime-Loading Contract

| Mode | Existing contract | Evidence |
|---|---|---|
| Manual static | Downstream base template loads vendor dependencies, package CSS, and the ES-module entry `powercrud/js/powercrud.js`. | [`getting_started.md`](../../../mkdocs/guides/getting_started.md), [`manual_static/base.html`](../../../src/sample/templates/sample/manual_static/base.html) |
| Bundled/Vite | Downstream base template loads the packaged Vite entry `config/static/js/main.js`; that entry exposes HTMX, Tom Select, and Tippy globals, then imports PowerCRUD CSS and the stable package entry. | [`main.js`](../../../src/config/static/js/main.js), [`daisyUI/base.html`](../../../src/sample/templates/sample/daisyUI/base.html) |
| Public runtime | `window.initPowercrud(fragment)` is idempotent for full pages and HTMX swaps. | [`powercrud.js`](../../../src/powercrud/static/powercrud/js/powercrud.js), [`README.md`](../../../src/powercrud/static/powercrud/js/README.md) |

The manual-static Playwright test asserts the stable module request, internal module imports, exposed vendor globals, repeated initialization, and absence of Vite assets. Frontend packaging tests assert the stable Vite manifest key, source imports, and packaged runtime files. Broad browser tests exercise bundled mode, but do not explicitly assert its hashed asset requests, public globals, or browser-console cleanliness.

The manual contract is currently characterized only on a list page. It does not yet prove modal form, bulk, inline, detail, delete, or HTMX navigation behaviour under manual loading.

## Existing Coverage And Gaps

Existing tests cover default name construction, numerous direct fragment paths, template-partials syntax compatibility, the template-copy command dispatch, frontend asset packaging, and broad browser behaviour.

Material missing characterization before an extraction or resolver change:

1. End-to-end precedence with app/model override present and absent, explicit `template_name`, and explicit `templates_path` for normal and HTMX requests.
2. The `X-Redisplay-Object-List` bypass of outer-template resolution.
3. The split between `templates_path` and globally resolved inclusion tags/styles.
4. The full legacy namespace and all server-consumed partial names in package artifacts.
5. Current command behaviour for whole-tree content, nested partials, overwrite, missing source, and configured framework source selection.
6. Case-sensitive handling of `daisyUI` versus documented `daisyui`.
7. Both loading modes after a compatibility resolver or pack-loading change.
8. Explicit bundled-mode browser loading: manifest assets, globals, runtime guard, and clean console/page errors.
9. A real downstream template override that survives normal rendering plus HTMX, modal, bulk, and inline behaviour where it claims those capabilities.
10. Representative detail, delete, and ordinary update browser flows; current browser coverage is strongest for lists, create-modal, bulk update, and inline editing.
11. Clean installed-wheel and installed-sdist artifact behaviour; current packaging checks inspect the source installation.

## Ratified Decision Register

| ID | Decision | Rationale |
|---|---|---|
| D1 | Treat `POWERCRUD_CSS_FRAMEWORK` as a legacy default presentation selector, not the future complete template-pack selector. | Today it drives styles, tags, and copy tooling as well as default paths; overloading it further would preserve accidental coupling. |
| D2 | Preserve existing outer-template precedence: explicit `template_name`, then app/model convention, then resolved generic namespace. | This is the documented downstream override path and has existing test coverage. |
| D3 | Give an explicit per-view `templates_path` precedence over any future pack selection for the templates and direct fragments it currently controls. | It is the existing per-view escape hatch; changing it would break bespoke project templates. |
| D4 | Place a future configured pack selection below explicit `templates_path` and above the legacy global default. | This adds pack choice without changing existing view overrides or unconfigured projects. |
| D5 | Keep the standard DaisyUI experience and legacy global setting indefinitely for projects without legacy template customisation. Support copied full templates, whole-tree copies, custom legacy namespaces, and direct `powercrud/daisyUI/...` dependencies through 0.x; once focused overrides and the compatible default pack ship, deprecate this legacy customisation model for removal in v1.0. | Ordinary consumers should not need to migrate, while template customisers need a clear transition away from the old full-template model. |
| D6 | Keep both current runtime entries and loading modes stable: manual `powercrud/js/powercrud.js` and bundled `config/static/js/main.js`. | Both are documented and characterized user-facing contracts. |
| D7 | Record default DaisyUI repackaging as atomic only when legacy paths, direct fragments, tag resolution, command copying, distribution contents, default adapter loading, and both asset modes pass together. | Any partial move can otherwise leave a mixed or broken installation. |
| D8 | Use canonical legacy spelling `daisyUI` internally and correct lowercase public documentation as a separate compatibility/documentation fix. Do not silently change the existing setting's meaning in Phase 1.1. | The current directory and style key are case-sensitive while documentation is inconsistent. |
| D9 | Add focused characterization before Phase 2 or 3 changes; no resolver or namespace migration may rely only on broad regression coverage. | The uncovered precedence and split-resolution paths are precisely the migration hazards. |
| D10 | Treat a future framework adapter as automatically composed by both existing loading modes until an explicit new mode is introduced. | Manual and bundled users must not add an interim script or lose DaisyUI, Tippy, or Tom Select behaviour during extraction. |

## Ratified Phase 1.1 Compatibility Contract

1. An unchanged project continues to receive the current DaisyUI implementation using existing settings, paths, and loading contracts.
2. Explicit `template_name` and app/model outer-template overrides retain their current precedence. The current HTMX list-redisplay bypass remains preserved through migration and is not silently changed as part of pack work.
3. Explicit per-view `templates_path` remains the authoritative legacy override for generic roots and direct partials that currently use it.
4. A future pack selector is additive: it does not alter existing projects and sits below explicit view overrides.
5. Legacy global framework selection remains available while the default DaisyUI pack is introduced; styles, tags, copy tooling, and templates may not be silently split into incompatible selections.
6. The standard DaisyUI presentation and legacy global selector remain compatible indefinitely for projects without legacy template customisation.
7. Copied full templates, whole-tree copies, custom legacy namespaces, and direct `powercrud/daisyUI/...` dependencies remain supported through 0.x. Their replacement is focused overrides or the compatible pack mechanism; after that replacement ships, these legacy customisation paths are deprecated with removal targeted for v1.0.
8. Both existing loading modes automatically compose the compatible default behaviour throughout adapter extraction.
9. Ordinary extraction slices merge only with unchanged compatible default behaviour. Default-pack repackaging is the identified atomic transition.

## Verification

### Completed

1. Static source, documentation, template, and test inventory completed.
2. Existing manual-static Playwright coverage inspected.
3. Existing package-asset, template-copy, fragment, and resolution test locations identified.

### Not Run

The focused test command was attempted:

```text
./runproj exec "runtests pytest src/tests/test_conf_logging_validators.py src/tests/test_url_mixin_extended.py src/tests/test_management_commands.py src/tests/test_template_partials_compat.py src/tests/test_form_filter_template_mixins.py"
```

It did not start because `powercrud_django_dev` is not running. No test result is claimed.

Before a later implementation slice relies on this audit's test baseline, rerun that focused unit set and:

```text
./runproj exec "runtests playwright src/tests/playwright/test_manual_static_assets.py"
```

## Completion

The user accepted D1 through D10 and the two-tier compatibility policy in the ratified contract above. The authoritative Phase 1.1 decisions are recorded in [`phase1-contract-notes.md`](phase1-contract-notes.md). Master Phase 1 remains open until its remaining child phases are complete.
