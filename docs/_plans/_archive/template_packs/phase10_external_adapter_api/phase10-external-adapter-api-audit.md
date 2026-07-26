# Phase 10.1 External Adapter API Audit Findings

## Purpose and boundaries

This is the read-only audit for Phase 10.1. It records what the current
PowerCRUD code already does, where DaisyUI and Bootstrap 5 are built in, and
which boundaries need decisions before an external framework adapter API can be
implemented.

The audit did not change production code, templates, tests, package metadata,
or published documentation. No containers, builds, installers, browser tests,
or full test suites were run. The findings below are evidence from static
inspection of the repository, existing tests, and current planning records.

This document does not choose the future adapter design. It is the evidence
that the next design and implementation plan must use.

## Current end-to-end flow

1. `POWERCRUD_SETTINGS["POWERCRUD_TEMPLATE_PACK"]` is read by
   `get_selected_template_pack()` and `get_configured_template_pack()` in
   `src/powercrud/template_packs.py:123-141`.
2. The absent selector resolves to the built-in DaisyUI declaration. An
   explicit third-party selector must use `module.path:attribute` syntax and
   is imported dynamically by `resolve_template_pack()` at
   `src/powercrud/template_packs.py:185-191,255-345`.
3. A view's default `templates_path` is the selected declaration's namespace.
   `get_template_name()` first tries an application/model override and then
   the selected pack; `get_framework_template_path()` uses the override root
   for nested includes only when `template_override_complete=True`
   (`src/powercrud/mixins/config_mixin.py:35-60,138-140,1870-1887`).
4. Server-side style data is built by `HtmxMixin.get_framework_styles()`,
   which imports and merges both first-party style providers
   (`src/powercrud/mixins/htmx_mixin.py:29-40`). Later lookup selects the
   current adapter key through `get_template_pack_styles()`.
5. The browser entry `powercrud.js` imports the DaisyUI composition by default.
   A private `createComposition` injection point lets the Bootstrap entry
   install its own composition (`src/powercrud/static/powercrud/js/powercrud.js:1-26,83-108,811-822`).
6. Both entries install the same core lifecycle: searchable controls, object
   lists, tooltips, HTMX handling, modal teardown, inline editing, selection,
   and public globals. The global listener order is defined in
   `src/powercrud/static/powercrud/js/runtime/startup.js:62-109`.
7. CSS and JavaScript are normally brought in by an application-owned Vite
   entry (`src/config/static/js/main.js:1-23` or `bootstrap5.js:1-24`) or by
   manual-static base templates
   (`src/sample/templates/sample/manual_static/base.html:12-20` and
   `src/sample/templates_bootstrap/sample/manual_static/base.html:12-19`).

## Surface inventory

| Surface | Current owner | Generic today? | Evidence and relevance |
| --- | --- | --- | --- |
| Selector and declaration import | `powercrud.template_packs` | Partly | Third-party declaration paths already import dynamically, but adapter identities are restricted to `bootstrap5` and `daisyui`; see `template_packs.py:13-18,185-191,255-345`. |
| Pack declaration shape | `TemplatePack` dataclass | Partly | The shape carries namespace, resources, capabilities, form support, Django app, and asset metadata (`template_packs.py:62-120`), but its adapter fields are not open-ended at runtime. |
| Server style translation | `HtmxMixin`, `packs/daisyui/styles.py`, `contrib/bootstrap5/styles.py` | No | Both first-party providers are imported unconditionally (`htmx_mixin.py:29-40`); `TableMixin` chooses Bootstrap otherwise DaisyUI (`table_mixin.py:41-51`). |
| Template lookup | `ConfigMixin`, URL mixins, template tags | Mostly | Override-first and selected-namespace lookup is generic (`config_mixin.py:35-60`; `url_mixin.py:106-116,432-526`), but some nested templates and fallback paths name DaisyUI directly. |
| Capability validation | `template_pack_validation.py` | No | Capability names, dependencies, required files, fragments, and Crispy dependencies are fixed constants (`template_pack_validation.py:17-160`). |
| Browser composition | `powercrud.js` and private pack compositions | No | The stable entry statically imports DaisyUI; Bootstrap bypasses the default through a private defer flag and an internal composition object (`powercrud.js:23-26,83-108,820-822`; Bootstrap composition `:1-108`). |
| Browser lifecycle hooks | Core runtime plus pack adapters | Partly | Core state and HTMX ordering are shared, but each composition supplies a large private object of modal, tooltip, widget, inline, panel, and action hooks. |
| Semantic DOM hooks | Core runtime and pack templates | Mostly | Stable `data-powercrud-*` and `data-inline-*` attributes are consumed across the runtime; some core modules still assume IDs or classes such as `#filterCollapse` and `hidden`. |
| CSS ownership | Shared PowerCRUD CSS plus pack CSS | No | Shared `powercrud.css` contains DaisyUI/Tailwind variables and Tippy selectors; Bootstrap has a separate stylesheet and a `.hidden` bridge (`powercrud.css:1-314`; Bootstrap CSS `:312-314,368-424,513-565`). |
| Manual-static assets | `pcrud_mktemplate` and declarations | No | The command copies shared assets for every pack and adds Bootstrap assets only when `identity == "bootstrap5"` (`pcrud_mktemplate.py:88-114,566-639`). It does not use arbitrary declaration asset metadata. |
| Vite assets | PowerCRUD manifest and app entries | No | Validation reads only `powercrud/assets/manifest.json` (`template_pack_validation.py:255-274`); the Vite config emits first-party `main` and `bootstrap5` entries (`vite.config.mjs:14-29`). |
| Project template copying | `pcrud_mktemplate` | No | `--source-template-pack` choices and selector mapping are hard-coded to DaisyUI and Bootstrap (`pcrud_mktemplate.py:19-22,204-210`). |
| Model/focused template copying | `pcrud_mktemplate` and view config | Partly | Model-specific copying can resolve the configured namespace, while project-level copying is first-party-only; `--assets` is intentionally app-level (`pcrud_mktemplate.py:247-270,728-809`). |
| Package discovery | Django app/static/template loaders | Partly | The selector can import an external declaration, and validation uses package resources plus Django loaders (`template_pack_validation.py:291-340`), but external package installation and static discovery are not tested as a supported workflow. |
| Test and acceptance tooling | Repository tests and installed-artifact script | No | Tests and the installed-artifact probe enumerate built-in DaisyUI/Bootstrap paths and selectors; no separately distributed new-framework fixture exists. |

## Confirmed findings by area

### 1. Server-side selection and presentation

- The resolver already has the beginning of an external-pack seam: a package
  can expose a `TemplatePack` declaration and a consumer can select it with a
  full `module.path:attribute` string. The built-in `daisyui` alias is the only
  short alias; Bootstrap is also selected through its full declaration path
  (`template_packs.py:13-18`; `contrib/bootstrap5/__init__.py:6-37`).
- The resolver still rejects any framework adapter other than the fixed set
  `{bootstrap5, daisyui}` and rejects every non-null `variant_adapter`
  (`template_packs.py:307-345`). The validator repeats those restrictions
  (`template_pack_validation.py:160,223-235`). This is the direct reason an
  independent pack cannot currently declare its own
  adapter.
- `HtmxMixin.get_framework_styles()` imports both first-party style modules,
  regardless of the selected declaration. `get_template_pack_styles()` then
  chooses one mapping by adapter key. A third-party declaration can reuse an
  existing adapter key, as demonstrated by
  `src/tests/test_same_adapter_template_pack.py:16-55`, but cannot supply a
  new style provider through the declaration.
- `TableMixin._view_help_style_vars()` branches to Bootstrap and otherwise
  assumes DaisyUI (`src/powercrud/mixins/table_mixin.py:41-51`). The filtering
  mixin is more generic in shape but still consumes the selected style mapping.
- `_prepare_htmx_response()` contains a DaisyUI-specific modal comment and
  emits a `showModal` trigger (`src/powercrud/mixins/htmx_mixin.py:215-238`).
  The selected Bootstrap runtime has to coexist with this server-side hook;
  the current code does not obtain the trigger contract from a pack adapter.
- The legacy `POWERCRUD_CSS_FRAMEWORK` setting remains separate from
  `POWERCRUD_TEMPLATE_PACK` (`src/powercrud/conf.py:5-18`; `template_packs.py:131-169`).
  Sample-app pages still choose `sample/{POWERCRUD_CSS_FRAMEWORK}` in
  `src/sample/views.py:39-47,1071-1155`. An external pack selector therefore
  does not automatically select every application-owned presentation.

### 2. Template lookup and template contracts

- The useful generic contract is already clear: a model/view can specify a
  `template_override_path`; lookup tries that path before the selected pack,
  while `template_override_complete=True` makes nested includes stay inside
  the copied tree (`config_mixin.py:35-60`; URL context construction in
  `url_mixin.py:432-526`).
- Focused component paths are assembled from the model/view and selected pack
  namespace (`url_mixin.py:106-116`). This is a model-specific template
  ownership mechanism, independent of browser assets.
- The canonical DaisyUI templates contain many direct includes such as
  `powercrud/packs/daisyui/...` (for example
  `src/powercrud/templates/powercrud/packs/daisyui/object_list.html` and
  `object_form.html`). The Bootstrap tree owns its own template files and
  uses `framework_template_path` in several nested locations. A conformant
  external pack therefore cannot be assumed to inherit all nested includes
  through the selected namespace; transitive include ownership must be
  checked explicitly.
- The `extra_buttons` tag uses the context-selected namespace but catches a
  missing template and falls back directly to a DaisyUI partial
  (`src/powercrud/templatetags/powercrud.py:1893-1913`). That fallback is not
  framework-neutral.
- The validator checks a fixed set of capability files and fragments, then
  compiles them through Django (`template_pack_validation.py:276-340`). It
  does not prove that every transitive include, custom template tag, or
  external static dependency is available.

### 3. Browser runtime and JavaScript adapters

- `powercrud.js` is the stable manual ES-module entry, but it statically
  imports `createDaisyuiComposition` and uses it as the default
  (`powercrud.js:1,23-26`). The only injection point is the exported
  `installPowercrudRuntime({createComposition})` function.
- Bootstrap reaches that injection point through a private choreography:
  set `window.__powercrudPrivateDeferInstall`, dynamically import the stable
  entry, install the Bootstrap composition, then remove the flag
  (`src/config/static/js/bootstrap5.js:17-24`; package entry equivalent at
  `contrib/bootstrap5/static/.../bootstrap5.js:8-15`). This is an internal
  first-party mechanism, not a versioned external-pack API.
- The composition object is large. The stable runtime consumes searchable
  select, tooltip, modal, action-selection, inline presentation, list-column,
  filter/favourites, and row-action APIs (`powercrud.js:83-223,243-296`).
  DaisyUI and Bootstrap implement parallel private compositions with
  different classes, widget APIs, and teardown rules.
- The core lifecycle is reusable and has important ordering requirements:
  `initPowercrud()` initialises searchable controls, lists, and tooltips;
  HTMX `beforeSwap` tears down widgets before `afterSwap` and `afterSettle`
  reinitialise them (`powercrud.js:282-297,697-749`). The startup module
  registers the full event order (`runtime/startup.js:62-109`). Any future
  adapter boundary must preserve idempotence, teardown, and late DOM-ready
  behaviour.
- Stable semantic hooks exist in `runtime/selectors.js` and the templates,
  including object-list, modal, selection, filter, searchable-select,
  tooltip, list-column, row-action, and inline-edit attributes. However,
  shared modules still depend on presentation details such as `#filterCollapse`,
  `hidden`, `d-none`, and selected state classes. Examples are
  `runtime/list-view-state.js:140-155,426-464,638-654`,
  `runtime/bulk-actions.js:62-89`, and
  `runtime/filter-favourites.js:1127-1145`.
- DaisyUI adapters own native dialog calls, Tippy setup, Tom Select styling,
  Daisy loading/disabled classes, and floating-panel classes. Bootstrap
  adapters own Bootstrap modal/tooltip APIs, `d-none`/`show`, spinner classes,
  and equivalent widget behaviour. These are first-party presentation
  implementations, not interchangeable generic modules.

### 4. CSS, assets, and build loading

- The shared stylesheet at `src/powercrud/static/powercrud/css/powercrud.css`
  is not fully framework-neutral. It contains DaisyUI/Tailwind colour and
  radius variables, Tippy theme selectors, and Tom Select rules. Bootstrap
  manual-static pages intentionally load the Bootstrap stylesheet instead of
  this shared CSS.
- DaisyUI's declaration has no `manual_assets` or `vite_assets`; the command
  infers shared CSS/JS from the PowerCRUD package. Bootstrap declares two
  manual assets and one Vite input, but the command still routes assets by
  identity rather than declaration metadata
  (`packs/daisyui/__init__.py:6-32`; `contrib/bootstrap5/__init__.py:6-37`;
  `pcrud_mktemplate.py:88-114`).
- `--assets` copies a complete application-owned snapshot, warns against
  loading both entries, and supports manual-static loading only
  (`pcrud_mktemplate.py:566-639`). It has hard-coded DaisyUI-versus-Bootstrap
  activation guidance and indexes a fixed selector dictionary. An external
  identity would not have a supported project asset path.
- Vite builds are application-owned for the current sample project. The
  manifest contains `main` and `bootstrap5` entries
  (`src/vite.config.mjs:14-29`; `src/powercrud/assets/manifest.json:24-61`).
  The validator checks Vite keys only in PowerCRUD's manifest
  (`template_pack_validation.py:255-274`), so it cannot certify a pack-owned
  Vite manifest or entry.
- The duplicate-load guard is global and first-load wins:
  `window.__powercrudRuntimeLoaded` is checked in `powercrud.js:30-35`.
  This makes entry selection and load order a real compatibility surface.

### 5. Packaging, Django discovery, and management commands

- PowerCRUD's own Hatch configuration includes `src/powercrud/**` in the sdist
  and packages `src/powercrud` for the wheel (`pyproject.toml:53-65`). There is
  no entry-point registry, external-pack scaffold, or reusable package-data
  template for third-party authors.
- An external declaration can be imported and its template resource root can
  be inspected using `importlib.resources`; validation then asks Django to
  load the declared namespace (`template_pack_validation.py:291-340`). The
  audit found no installed-wheel or source-distribution test for an external
  package, and the command converts resources to `Path`, so non-filesystem
  resource behaviour is untested.
- `pcrud_mktemplate` project-level selectors are explicitly limited to
  `daisyui` and `bootstrap5` (`pcrud_mktemplate.py:19-22,204-210`). Its project
  template destination is identity-based, and its asset destination and
  activation output are first-party-specific. Model-scoped template copying
  is more dynamic, but `--assets` is correctly app-level and no external-pack
  model-copy tests exist.
- Static discovery for an external package depends on normal Django app
  registration or equivalent project static/template configuration. The
  current declarations make `django_app` optional, but the supported install
  and loader requirements are not expressed as an external-package workflow.

### 6. Tests and author-facing documentation

- Resolver tests cover built-in aliases, local test declarations, invalid
  declarations, and a same-adapter fixture (`test_template_packs.py` and
  `test_same_adapter_template_pack.py`). The fixture is inside the PowerCRUD
  test package and reuses DaisyUI; it is not a separately installed new
  framework.
- Validation tests cover the fixed capability inventory, first-party assets,
  and Crispy dependencies. Management tests cover only DaisyUI and Bootstrap
  source choices, paths, output, and asset snapshots
  (`src/tests/test_management_commands.py:1022-1284`).
- Frontend packaging tests assert stable PowerCRUD paths, private adapter file
  names, DaisyUI CSS tokens, Bootstrap files, and the PowerCRUD manifest
  (`src/tests/test_frontend_asset_packaging.py:9-155,373-450`). The installed
  artifact probe also enumerates only DaisyUI and Bootstrap
  (`scripts/verify_installed_template_pack_artifacts.py:15-35,52-155`).
- Shared server and browser matrices use the absent selector or the exact
  Bootstrap declaration path. There is no external wheel/sdist/browser
  fixture, no external author test kit, and no generic asset-packaging test.
- The authoring page currently states the product gap plainly: new framework
  adapters are unavailable and independent packages may only reuse the two
  shipped behaviour layers (`docs/mkdocs/template_packs/authoring-and-publishing.md:3-9,39-53`).
  The testing page requires evidence but explicitly limits its harness to the
  first-party packs (`testing-and-acceptance.md:5-34`).

## Current contracts that must be preserved during later work

These are observed compatibility obligations, not new design decisions:

- An absent selector continues to select DaisyUI.
- The explicit selector remains process-wide and is resolved before rendering.
- `template_override_path` remains model/view-owned; copied assets remain
  app/base-template-owned rather than model-specific.
- `powercrud/js/powercrud.js`, `window.initPowercrud`, existing public helper
  globals, semantic data attributes, and lifecycle ordering remain stable.
- Manual-static and Vite loading remain distinct paths, and duplicate runtime
  loading remains prevented.
- DaisyUI and Bootstrap retain their current appearance, server behaviour,
  browser lifecycle, and package loading behaviour while they are migrated.

## Risks and unresolved questions for the next planning phase

1. Which server-side presentation requests must be expressed as an external
   adapter contract, and which current style values remain application/view
   configuration?
2. Which parts of the private composition object become semantic public hooks,
   and which should remain framework-neutral core behaviour?
3. Which current IDs/classes (`hidden`, `d-none`, `#filterCollapse`, modal
   structure, floating-panel structure) are accidental implementation details
   versus required template contracts?
4. Should shared CSS be split into a genuinely neutral core and pack-owned
   framework CSS, and how should third-party vendor CSS be declared and loaded?
5. How should an external pack expose manual-static assets and an optional
   Vite entry without depending on PowerCRUD's manifest?
6. What Django app, template-loader, staticfiles, and package-data rules must
   an independently published pack document and test?
7. What reusable conformance test kit can run from an external pack repository,
   and which browser checks require a real installed external package?
8. How should `pcrud_mktemplate` discover and copy an external pack's complete
   template tree and declared assets without first-party identity branches?

## Audit conclusion

PowerCRUD already has a useful declaration and namespace mechanism, plus a
stable core lifecycle and semantic DOM vocabulary. It does not yet have an
external adapter API. The remaining boundaries are hard-wired in server style
providers, validation, private browser composition, CSS ownership, asset/Vite
discovery, project-copy tooling, and first-party-only tests.

The next Phase 10 plan should turn these findings into explicit contract
decisions and a migration sequence. It should not repeat this inventory.
