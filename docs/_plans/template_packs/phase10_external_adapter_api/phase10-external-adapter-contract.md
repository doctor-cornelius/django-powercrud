# Phase 10.2 External Adapter Contract

## Status

**Accepted.** This document is the public contract for the Phase 10 implementation.

## What this contract is for

A template-pack author must be able to publish a normal Django package that provides:

- PowerCRUD templates;
- server-side presentation choices such as framework classes;
- optional browser behaviour where the framework needs it;
- package-owned CSS and JavaScript; and
- enough metadata for PowerCRUD to validate and load the package.

PowerCRUD must not contain a list of permitted framework names. DaisyUI and Bootstrap 5 must use exactly the same public interfaces as an independently installed package.

This proposal deliberately uses DaisyUI and Bootstrap 5 as the two concrete framework examples. The small `example_powercrud_pack` snippets prove only that the package can live outside PowerCRUD; they do not introduce or promise another maintained framework pack.

## Recommended decisions

| Area | Recommendation |
| --- | --- |
| Pack declaration | Publish the redesigned declaration as template-pack contract version 1. The current staging-only shape is unreleased and may be replaced directly. |
| Server presentation | Load one pack-supplied Python adapter from an import path. It returns typed semantic presentation values rather than registering a framework name. |
| Browser presentation | Load at most one selected pack adapter before the stable PowerCRUD runtime entry. Missing optional hooks use framework-neutral defaults. |
| Templates | Keep semantic `data-powercrud-*` and `data-inline-*` hooks public. Do not make DaisyUI or Bootstrap classes public contracts. |
| Assets | Declare package-owned styles, adapter modules, copy roots, and vendor requirements once in the pack declaration. |
| Vite | Keep the downstream application responsible for its Vite entry. A pack declares importable source resources; it does not require an entry in PowerCRUD's manifest. |
| Compatibility | Preserve the existing selectors, default DaisyUI choice, stable JavaScript entry and globals, template overrides, lifecycle ordering, and separate manual-static/Vite loading paths. |

## Contract versions

Use three independent version numbers:

```python
TEMPLATE_PACK_CONTRACT_VERSION = 1
SERVER_ADAPTER_API_VERSION = 1
BROWSER_ADAPTER_API_VERSION = 1
```

They have separate purposes:

- the template-pack version controls the Python declaration shape;
- the server-adapter version controls the Python presentation interface; and
- the browser-adapter version controls the JavaScript interface.

PowerCRUD requires an exact supported version. An unsupported version is a configuration error and must report the selected pack, the received version, and the supported version.

The current `TEMPLATE_PACK_CONTRACT_VERSION = 1` shape on `staging/main` has never been released. It is not a legacy public API. Phase 10 may replace that shape directly, and the redesigned declaration remains version 1 as the first public contract. No declaration migration is required.

## Public Python declaration

The public declarations live in `powercrud.template_packs`. The names below are the proposed public API.

```python
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class PackageResource:
    """Identify one resource inside an importable Python package."""

    package: str
    path: str


@dataclass(frozen=True, slots=True)
class VendorRequirement:
    """Describe a dependency supplied by the consuming application."""

    name: str
    purpose: str
    global_name: str | None = None
    vite_import: str | None = None
    manual_static_note: str = ""


@dataclass(frozen=True, slots=True)
class BrowserAdapterSpec:
    """Describe an optional pack-owned browser adapter module."""

    api_version: int
    static_path: str
    source: PackageResource


@dataclass(frozen=True, slots=True)
class PackAssets:
    """Describe assets owned by the pack, excluding third-party vendors."""

    stylesheets: tuple[str, ...] = ()
    copy_roots: tuple[PackageResource, ...] = ()
    browser_adapter: BrowserAdapterSpec | None = None
    vendor_requirements: tuple[VendorRequirement, ...] = ()


@dataclass(frozen=True, slots=True)
class CrispyIntegration:
    """Describe one Crispy Forms template-pack integration."""

    template_pack: str
    dependency: str | None = None


@dataclass(frozen=True, slots=True)
class TemplatePack:
    """Declare one selectable PowerCRUD template pack."""

    identity: str
    contract_version: int
    template_namespace: str
    template_package: str
    template_resource_root: str
    server_adapter: str
    capabilities: frozenset[str]
    supports_native_forms: bool
    django_app: str | None
    assets: PackAssets = PackAssets()
    crispy_integrations: tuple[CrispyIntegration, ...] = ()
    unsupported_presentation_options: frozenset[str] = frozenset()
    legacy_copy_destination: str | None = None
```

### Field meanings

- `identity` is a diagnostic and ownership name. It is not matched against a PowerCRUD whitelist.
- `server_adapter` uses the existing `module.path:attribute` grammar and must resolve to a server adapter object.
- `template_namespace`, `template_package`, and `template_resource_root` keep their present meanings.
- `capabilities` continues to describe PowerCRUD features supplied by the templates. The public capability vocabulary remains `list`, `form`, `detail`, `delete`, `filters`, `modal`, `bulk`, `async`, `inline`, and `favourites`. This is a feature contract, not a framework whitelist.
- `assets` contains only files owned by the pack. Bootstrap, HTMX, Tom Select, Tippy, or similar third-party libraries remain application dependencies.
- `crispy_integrations` replaces the hard-coded Crispy-name/dependency map. A pack may name the Crispy template pack it supports and the importable dependency that proves the integration is installed.
- `legacy_copy_destination` exists only for the current compatibility command path and must not influence runtime adapter selection.

`framework_adapter` and `variant_adapter` do not exist in the public version 1 contract. The selected declaration supplies its actual adapters, so PowerCRUD no longer needs either name.

## Public server adapter

The server adapter translates semantic PowerCRUD presentation needs into classes and CSS variables. It does not render templates, perform CRUD work, handle HTMX requests, or choose browser assets.

### Public value types

```python
from dataclasses import dataclass, field
from typing import Literal, Mapping, Protocol


FilterWidgetKind = Literal[
    "text", "select", "multiselect", "date", "number", "time", "default"
]
ActionRole = Literal["view", "edit", "delete", "extra"]


@dataclass(frozen=True, slots=True)
class ServerAdapterContext:
    """Stable semantic context supplied for one configured view."""

    modal_id: str
    modal_target_id: str
    use_htmx: bool
    use_modal: bool


@dataclass(frozen=True, slots=True)
class ActionPresentation:
    """Framework presentation for links and action controls."""

    base_classes: str = ""
    role_classes: Mapping[ActionRole, str] = field(default_factory=dict)
    group_item_classes: str = ""
    extra_default_classes: str = ""
    list_cell_link_classes: str = ""


@dataclass(frozen=True, slots=True)
class ServerPresentation:
    """Complete server-side presentation for one view."""

    filter_widget_attrs: Mapping[FilterWidgetKind, Mapping[str, str]] = field(
        default_factory=dict
    )
    actions: ActionPresentation = ActionPresentation()


class PowerCRUDServerAdapter(Protocol):
    """Public server-adapter interface."""

    api_version: int

    def get_presentation(
        self, context: ServerAdapterContext
    ) -> ServerPresentation:
        """Return framework presentation for one configured view."""

    def get_view_help_variables(self, color: str) -> Mapping[str, str]:
        """Return the five documented PowerCRUD view-help CSS variables."""
```

`BaseServerAdapter` is a public convenience implementation. Its presentation contains no framework classes. Its view-help method returns neutral PowerCRUD variables. An author may subclass it and override either method.

`get_presentation()` is required. `get_view_help_variables()` is optional in a third-party object because the resolver supplies the base implementation when it is absent. Returning unknown keys is permitted only inside template-owned class/attribute dictionaries; the outer `ServerPresentation` shape is fixed.

The modal trigger's semantic attributes are owned by PowerCRUD templates and core. A server adapter must not inject framework JavaScript such as DaisyUI's current inline `showModal()` call. Opening and closing a modal belongs to the browser adapter.

### First-party mapping

| Proposed value | DaisyUI today | Bootstrap 5 today |
| --- | --- | --- |
| `filter_widget_attrs` | Input/select classes from `get_daisyui_framework_styles()` | Form-control/form-select classes from `get_bootstrap5_framework_styles()` |
| `actions.base_classes` | `btn` | `btn` |
| `actions.role_classes` | `btn-info`, `btn-primary`, `btn-error` | `btn-info`, `btn-primary`, `btn-danger` |
| `actions.group_item_classes` | `join-item` | Empty |
| `actions.extra_default_classes` | `btn-accent` | `btn-success` |
| `actions.list_cell_link_classes` | `link link-info` | `link-primary text-decoration-underline` |
| `get_view_help_variables()` | DaisyUI theme variables | Bootstrap CSS variables |

Bootstrap-only form rendering and alignment filters remain inside Bootstrap templates and template tags. They are not promoted into the general server adapter.

## Public browser adapter

PowerCRUD has one process-wide selected pack, so the browser API also has one selected adapter. It does not need a registry of framework names.

### Registration and loading

If a pack supplies `BrowserAdapterSpec`, its ES module must run before `powercrud/js/powercrud.js` and assign one public slot:

```javascript
window.PowerCRUDAdapter = Object.freeze({
    apiVersion: 1,
    identity: 'bootstrap5',
    create(context) {
        return createBootstrapAdapter(context);
    },
});
```

Before either module, PowerCRUD's asset-loading helper emits a non-executable configuration element:

```html
<script id="powercrud-runtime-config" type="application/json">
{"identity":"bootstrap5","browser_adapter_required":true,"api_version":1}
</script>
```

The stable entry reads this element to verify that the browser adapter matches the server-selected pack. Every public version 1 declaration uses this runtime configuration. Existing first-party loading paths remain working while DaisyUI and Bootstrap migrate, but that temporary implementation bridge is not a separate public declaration contract.

The stable PowerCRUD entry reads this slot once, validates it, creates the adapter, and then installs the existing core runtime. If no browser adapter is declared, PowerCRUD uses its neutral default adapter.

This replaces the private `window.__powercrudPrivateDeferInstall` mechanism. It does not replace `powercrud/js/powercrud.js`, `window.initPowercrud`, or the existing public helper globals.

Manual-static load order is:

1. the PowerCRUD runtime configuration element;
2. application-owned vendor dependencies;
3. declared pack stylesheets, in declaration order;
4. the declared pack browser-adapter module, if any; and
5. `powercrud/js/powercrud.js`.

A downstream Vite entry uses the same order through imports. The application imports vendor packages, pack stylesheet/source resources, the adapter source, and finally the stable PowerCRUD entry. A third-party pack is never added to PowerCRUD's own Vite manifest.

### Factory context

The `create(context)` function receives only stable services:

```javascript
{
    apiVersion: 1,
    window,
    document,
    selectors,              // public semantic PowerCRUD selectors
    isElementVisible,
    schedule(callback, delayMs),
    nextFrame(callback),
    warnMissingDependency(name, detail),
}
```

It does not receive private feature runtimes or first-party adapter modules.

### Returned hook groups

The factory returns an object containing any of the groups below. Every group and method is optional. PowerCRUD deep-merges the result with its neutral default adapter.

```javascript
{
    fragment: {
        init(root),
        destroy(root),
    },
    searchableSelects: {
        init(root),
        destroy(root),
        syncValues(root),
    },
    tooltips: {
        init(root),
        hide(root),
        destroy(root),
    },
    modals: {
        applyTrigger(trigger, modal),
        bindClose(root),
        cleanupDuplicates(root),
        show(modal),
        closeAll(root),
        dispose(root),
    },
    controls: {
        setDisabled(element, {disabled, reason}),
        setBusy(element, {busy, kind}),
        syncSelectionAction(element, {enabled, reason}),
    },
    floatingPanels: {
        clone(kind, template),
        prepare(kind, {trigger, panel}),
        position(kind, {trigger, panel}),
        show(kind, {trigger, panel}),
        hide(kind, {trigger, panel}),
        focusFirst(kind, panel, selector),
        setOptionDisabled(kind, option, disabled),
    },
    inline: {
        resolveFocusTarget(root),
        presentFocus(element),
        setSaving(root, saving),
        showErrors(root),
        destroyErrors(root),
        removeOrphanedErrors(root),
        repositionErrors(root),
    },
    filters: {
        setPanelOpen(panel, open),
        setFavouritesOpen(panel, open),
        setAddFilterVisible(container, visible),
        showFavouritesToolbar(toolbar),
        syncFilterToggle(trigger, active),
        syncFavouriteTrigger(trigger, {label, dirty}),
    },
}
```

`kind` is one of `list-columns`, `filter-favourites`, or `row-actions`. Additional kinds require a browser API version change.

### Neutral defaults

| Hook group | Default behaviour |
| --- | --- |
| `fragment` | No-op. |
| `searchableSelects` | Leave native selects unchanged. |
| `tooltips` | Leave native `title`/accessible text unchanged. |
| `modals` | Use native `<dialog>` methods when present; otherwise no-op without inventing framework classes. |
| `controls` | Maintain `disabled`, `aria-disabled`, and `aria-busy`; do not add framework spinner markup. |
| `floatingPanels` | Keep the server-rendered panel in place; do not clone or reposition it. |
| `inline` | Use normal focus and native validation text; do not create framework popovers. |
| `filters` | Use `hidden` and `aria-expanded` attributes, not framework classes. |

A pack implements only the groups where its presentation differs from these defaults. DaisyUI and Bootstrap need several groups because they currently use different modal, tooltip, busy-control, widget, and floating-panel behaviour. A simple external package may require no browser module at all.

### Lifecycle ordering

PowerCRUD core retains the established order:

1. initialise searchable controls;
2. initialise PowerCRUD object-list state;
3. initialise tooltips;
4. call `fragment.init()`;
5. before an HTMX swap, call `fragment.destroy()` and then tear down widget, tooltip, modal, and inline instances;
6. after the swap and settle events, repeat the normal initialisation order.

Adapters must be safe to call more than once for the same fragment. Core owns listener registration, HTMX sequencing, state, persistence, selection, and request behaviour.

## Template and DOM contract

Templates own markup and framework classes. Core and adapters communicate through semantic attributes.

The following attribute families are public when the corresponding feature is rendered:

| Feature | Public semantic hooks |
| --- | --- |
| List root and navigation | `data-powercrud-object-list`, list URL/state metadata, `data-powercrud-list-toolbar`, `data-powercrud-pagination` |
| Forms and actions | `data-powercrud-form`, modal-trigger metadata, action-control and disabled-state metadata |
| Modal | `data-powercrud-modal`, `data-powercrud-modal-box`, `data-powercrud-modal-content`, close and refresh metadata |
| Selection and bulk actions | `data-powercrud-row-select`, `data-powercrud-select-all`, `data-powercrud-selection-aware`, bulk-action and clear-selection metadata |
| Filters and favourites | filter-toggle/form/reset/add/remove hooks, favourites toolbar/panel/template/trigger hooks |
| List columns and row actions | list-column trigger/template/panel/option hooks and row-action trigger/template/panel hooks |
| Searchable controls and tooltips | `data-powercrud-searchable-*`, placeholder metadata, and `data-powercrud-tooltip*` |
| Inline editing | `data-inline-row`, `data-inline-field`, save/cancel/action/dependency/error metadata |

The complete attribute names already exercised by the current runtime become exported selector constants and conformance-test inputs during implementation. Removing or changing one requires a compatibility decision.

These are not public presentation contracts:

- DaisyUI, Tailwind, Bootstrap, or application CSS classes;
- `hidden`, `d-none`, `show`, `is-active`, or colour/state classes;
- a particular modal, dropdown, or floating-panel HTML structure; and
- fixed IDs such as `filterCollapse`, except where an ID is explicitly supplied as an HTMX target or ARIA relationship by the view context.

Core modules that currently rely on these classes or fixed IDs must move that work to semantic hooks or adapter methods. Existing IDs remain recognised as compatibility aliases while DaisyUI and Bootstrap migrate.

Template lookup remains unchanged: model/view overrides are tried before the selected pack, and `template_override_complete=True` keeps nested includes in the complete override tree. Assets remain app/base-template-wide and are not model-specific.

## Asset contract

`PackAssets` describes ownership; it does not install vendors or edit a Vite configuration.

- `stylesheets` contains Django static paths in load order.
- `copy_roots` contains package-resource directories copied by project-owned asset tooling. Relative imports inside those roots must remain valid.
- `browser_adapter.static_path` is the manual-static module URL resolved by Django staticfiles.
- `browser_adapter.source` is the source resource that downstream Vite tooling can copy or alias into an application-owned entry.
- `vendor_requirements` explains what the consuming application must install and load before the adapter. It never causes PowerCRUD to copy third-party code.

The same declaration drives validation, manual-static guidance, project-owned asset copying, and downstream Vite guidance. There are no identity branches for DaisyUI or Bootstrap.

A copied asset tree remains a complete snapshot with no per-file fallback. The selected package-owned entry and application-owned snapshot must not both be loaded on one page.

## Validation and errors

### Django-side validation

Resolution or the template-pack validator must reject:

- a malformed selector or declaration;
- an unsupported template-pack or server-adapter version;
- a server adapter that cannot be imported or lacks `api_version` or `get_presentation()`;
- a missing declared Django app, template resource, required capability template/fragment, stylesheet, adapter module, or copy root;
- a declared Crispy dependency that cannot be imported; and
- unsafe absolute or traversal paths.

It must not reject an identity or adapter because its framework name is unknown.

Error messages name the selector, pack identity, field or resource, received value, and required action. Validation gathers independent resource/template errors where practical rather than failing after only the first missing file.

### Browser validation

Before installing global listeners, the stable entry rejects:

- a declared adapter module that did not set `window.PowerCRUDAdapter`;
- an adapter identity that differs from the server-emitted selected identity;
- an unsupported browser API version;
- a missing or non-callable `create` function;
- a factory that throws or returns a non-object; and
- a second different adapter or runtime installation on the same page.

Missing optional hook groups are not errors because neutral defaults fill them. A browser contract error aborts PowerCRUD initialisation and logs one direct `PowerCRUD adapter ...` error rather than silently loading DaisyUI.

## Illustrative declarations

These examples show the proposed declaration shape. They are not implementation patches.

### DaisyUI

```python
template_pack = TemplatePack(
    identity="daisyui",
    contract_version=1,
    template_namespace="powercrud/packs/daisyui",
    template_package="powercrud",
    template_resource_root="templates/powercrud/packs/daisyui",
    server_adapter="powercrud.packs.daisyui.adapter:server_adapter",
    capabilities=ALL_POWERCRUD_CAPABILITIES,
    supports_native_forms=True,
    django_app="powercrud",
    assets=PackAssets(
        stylesheets=("powercrud/packs/daisyui/css/daisyui.css",),
        copy_roots=(
            PackageResource("powercrud", "static/powercrud/packs/daisyui"),
        ),
        browser_adapter=BrowserAdapterSpec(
            api_version=1,
            static_path="powercrud/packs/daisyui/js/adapter.js",
            source=PackageResource(
                "powercrud", "static/powercrud/packs/daisyui/js/adapter.js"
            ),
        ),
        vendor_requirements=(
            VendorRequirement(
                name="DaisyUI and Tailwind CSS",
                purpose="Framework styling",
                manual_static_note="Load the application's compiled stylesheet first.",
            ),
            VendorRequirement(
                name="Tippy",
                purpose="Enhanced tooltips",
                global_name="tippy",
                vite_import="tippy.js",
            ),
        ),
    ),
    crispy_integrations=(
        CrispyIntegration("tailwind", "crispy_tailwind"),
    ),
    legacy_copy_destination="daisyUI",
)
```

### Bootstrap 5

```python
template_pack = TemplatePack(
    identity="bootstrap5",
    contract_version=1,
    template_namespace="powercrud/packs/bootstrap5",
    template_package="powercrud",
    template_resource_root=(
        "contrib/bootstrap5/templates/powercrud/packs/bootstrap5"
    ),
    server_adapter="powercrud.contrib.bootstrap5.adapter:server_adapter",
    capabilities=ALL_POWERCRUD_CAPABILITIES,
    supports_native_forms=True,
    django_app="powercrud.contrib.bootstrap5",
    assets=PackAssets(
        stylesheets=("powercrud/contrib/bootstrap5/css/bootstrap5.css",),
        copy_roots=(
            PackageResource(
                "powercrud",
                "contrib/bootstrap5/static/powercrud/contrib/bootstrap5",
            ),
        ),
        browser_adapter=BrowserAdapterSpec(
            api_version=1,
            static_path="powercrud/contrib/bootstrap5/js/adapter.js",
            source=PackageResource(
                "powercrud",
                "contrib/bootstrap5/static/powercrud/contrib/bootstrap5/js/adapter.js",
            ),
        ),
        vendor_requirements=(
            VendorRequirement(
                name="Bootstrap 5",
                purpose="Framework styling and modal/tooltip behaviour",
                global_name="bootstrap",
                vite_import="bootstrap",
            ),
        ),
    ),
    crispy_integrations=(
        CrispyIntegration("bootstrap5", "crispy_bootstrap5"),
    ),
)
```

### Minimal independently installed package

This example uses neutral browser defaults. Its arbitrary identity proves that PowerCRUD does not require a framework-name registration.

```python
template_pack = TemplatePack(
    identity="example-pack",
    contract_version=1,
    template_namespace="example_powercrud_pack/powercrud",
    template_package="example_powercrud_pack",
    template_resource_root="templates/example_powercrud_pack/powercrud",
    server_adapter="example_powercrud_pack.adapter:server_adapter",
    capabilities=frozenset({"list", "form", "detail", "delete"}),
    supports_native_forms=True,
    django_app="example_powercrud_pack",
    assets=PackAssets(
        stylesheets=("example_powercrud_pack/powercrud.css",),
        copy_roots=(
            PackageResource(
                "example_powercrud_pack", "static/example_powercrud_pack"
            ),
        ),
    ),
)
```

It supplies templates, a small server adapter containing its CSS classes, and one stylesheet. It does not implement modal libraries, enhanced tooltips, searchable widgets, floating panels, or pack-specific JavaScript.

## First-party adapter skeletons

These skeletons show how the maintained packs fit the public interfaces. The helper names represent pack-private implementation modules; they are not extra public APIs.

### Server adapters

```python
class DaisyUIServerAdapter(BaseServerAdapter):
    api_version = 1

    def get_presentation(self, context):
        return ServerPresentation(
            filter_widget_attrs=DAISYUI_FILTER_WIDGET_ATTRS,
            actions=ActionPresentation(
                base_classes="btn",
                role_classes={
                    "view": "btn-info",
                    "edit": "btn-primary",
                    "delete": "btn-error",
                    "extra": "btn-accent",
                },
                group_item_classes="join-item",
                extra_default_classes="btn-accent",
                list_cell_link_classes="link link-info",
            ),
        )

    def get_view_help_variables(self, color):
        return daisyui_view_help_variables(color)


class Bootstrap5ServerAdapter(BaseServerAdapter):
    api_version = 1

    def get_presentation(self, context):
        return ServerPresentation(
            filter_widget_attrs=BOOTSTRAP5_FILTER_WIDGET_ATTRS,
            actions=ActionPresentation(
                base_classes="btn",
                role_classes={
                    "view": "btn-info",
                    "edit": "btn-primary",
                    "delete": "btn-danger",
                    "extra": "btn-success",
                },
                extra_default_classes="btn-success",
                list_cell_link_classes=(
                    "link-primary text-decoration-underline"
                ),
            ),
        )

    def get_view_help_variables(self, color):
        return bootstrap5_view_help_variables(color)


server_adapter = DaisyUIServerAdapter()       # DaisyUI package
server_adapter = Bootstrap5ServerAdapter()    # Bootstrap package
```

Each module exports only its own final `server_adapter` assignment; the two assignments are shown together solely for comparison.

### Browser adapters

```javascript
// DaisyUI adapter module
window.PowerCRUDAdapter = Object.freeze({
    apiVersion: 1,
    identity: 'daisyui',
    create(context) {
        return {
            searchableSelects: createDaisyuiSearchableSelects(context),
            tooltips: createDaisyuiTooltips(context),
            modals: createDaisyuiModals(context),
            controls: createDaisyuiControls(context),
            floatingPanels: createDaisyuiFloatingPanels(context),
            inline: createDaisyuiInlinePresentation(context),
            filters: createDaisyuiFilterPresentation(context),
        };
    },
});
```

```javascript
// Bootstrap 5 adapter module
window.PowerCRUDAdapter = Object.freeze({
    apiVersion: 1,
    identity: 'bootstrap5',
    create(context) {
        return {
            searchableSelects: createBootstrap5SearchableSelects(context),
            tooltips: createBootstrap5Tooltips(context),
            modals: createBootstrap5Modals(context),
            controls: createBootstrap5Controls(context),
            floatingPanels: createBootstrap5FloatingPanels(context),
            inline: createBootstrap5InlinePresentation(context),
            filters: createBootstrap5FilterPresentation(context),
        };
    },
});
```

The framework-neutral external example does not supply a browser module, so the neutral defaults are used without another adapter skeleton.

## End-to-end traces

### Selection and rendering

1. Django reads `POWERCRUD_TEMPLATE_PACK`.
2. The selector imports the version 1 declaration.
3. PowerCRUD validates the declaration and imports `server_adapter`.
4. View configuration resolves the declared template namespace.
5. The server adapter returns presentation values for the view.
6. Template lookup tries model/view overrides, then the selected pack.
7. Templates emit semantic PowerCRUD attributes and their own framework classes.

### Manual-static browser loading

1. The base template emits the server-selected runtime configuration.
2. It loads application-supplied vendors.
3. It loads declared pack stylesheets.
4. It loads the selected pack adapter module, if declared.
5. It loads `powercrud/js/powercrud.js`.
6. The stable entry validates and creates the selected adapter.
7. Core installs its existing lifecycle and global helpers.

### HTMX replacement

1. Core receives `htmx:beforeSwap`.
2. Core calls adapter teardown hooks for the outgoing fragment.
3. HTMX replaces the fragment.
4. Core initialises searchable controls, list state, and tooltips in order.
5. Core calls the optional fragment hook and repeats layout-sensitive work after settle.

### Failure

1. A declaration, resource, or adapter fails validation.
2. PowerCRUD reports the selected pack and exact failing contract.
3. It does not fall back to DaisyUI or another installed pack.
4. Browser contract failures occur before listeners are installed and produce one actionable console error.

## Audit-question trace

| Phase 10.1 question | Proposed answer |
| --- | --- |
| Which server presentation belongs in an adapter? | Filter-widget attributes, action/link classes, and view-help CSS variables. CRUD, HTMX, configuration, and template rendering stay in core. |
| Which browser hooks become public? | The semantic hook groups above. Core state, requests, listener order, and persistence remain private core behaviour. |
| Which IDs and classes are contracts? | Semantic data attributes and explicit target/ARIA relationships are contracts. Framework/state classes and incidental fixed IDs are not. |
| How is CSS divided? | Core keeps only framework-neutral structural CSS; each pack owns framework and vendor-integration CSS. The actual split is Phase 10.3 work. |
| How are manual and Vite assets exposed? | One declaration identifies static paths and source resources. Manual tags and an app-owned Vite entry load the same logical assets. |
| How is an external package installed? | As a normal Django package/app with shipped templates/static resources and a declaration selected by `module.path:attribute`. |
| Where do author tests live? | In the external package repository, using a later reusable PowerCRUD conformance kit. |
| How does project copying become generic? | Later tooling consumes declaration resources and assets rather than a DaisyUI/Bootstrap selector dictionary. |

## Compatibility checklist

- [x] An absent selector can continue to resolve the built-in DaisyUI pack.
- [x] The existing full Bootstrap selector can remain unchanged.
- [x] The unreleased staging declaration may be replaced directly by the first public version 1 contract.
- [x] Template override precedence and complete-override behaviour are unchanged.
- [x] Model-specific template ownership remains separate from app-wide assets.
- [x] `powercrud/js/powercrud.js` and existing public globals remain stable.
- [x] Semantic data attributes and lifecycle order remain stable.
- [x] DaisyUI and Bootstrap use the same proposed public contracts.
- [x] Manual-static and Vite loading remain separate and application-controlled.
- [x] Framework identities are not whitelisted.

## Decisions requested in review

The contract version is settled: the redesigned declaration is the first public version 1 contract, with no compatibility shim for the unreleased staging shape.

The proposal recommends confirming these four architectural choices before implementation:

1. Replace `framework_adapter` and `variant_adapter` with a direct Python `server_adapter` import path and optional browser-adapter resource.
2. Use one process/page-wide `window.PowerCRUDAdapter` slot loaded before the stable runtime, rather than a registry of named frameworks.
3. Make browser hook groups optional and merge them with useful neutral defaults so simple packs do not implement irrelevant behaviour.
4. Treat semantic data attributes as public while keeping framework classes and incidental IDs private to templates/adapters.

After these are accepted or revised, this document can be marked `Accepted` and Phase 10.2 can close. Implementation planning begins only after that.
