# Testing and Accepting a Template Pack

A supported pack needs evidence that it preserves PowerCRUD's behaviour as well as its own presentation and assets. Equivalent behaviour matters; identical HTML, CSS classes, or pixels do not.

## Start with declaration validation

The declaration must have a valid identity, contract version, template package and resource root, adapter information, capability set, form support, and asset metadata. Its server adapter must implement the current action and widget-presentation methods. Validation should fail clearly when a declaration is malformed, uses an old adapter contract, or claims an unsupported presentation exception.

Run the public helper from the pack's own test project after adding the pack app to `INSTALLED_APPS`:

```python
from powercrud.template_pack_testing import assert_template_pack_conforms


def test_pack_contract():
    assert_template_pack_conforms(
        "my_powercrud_pack.template_pack:template_pack"
    )
```

It validates shipped templates, declared static resources, adapter imports, claimed capabilities, and optional Crispy dependencies without relying on PowerCRUD's internal first-party fixtures.

## Cover shared behaviour and pack-specific details

Every supported pack is expected to pass the shared server behaviour matrix for the standard CRUD surfaces. Add pack-specific server checks for translated presentation settings, declared resources, and any pack-owned templates or assets.

Portable presentation options must keep their promised meaning across the maintained packs. Framework-specific class settings may differ by framework, but they should not become silent no-ops.

Use this matrix to choose evidence for the widget policy:

| Area | Minimum evidence |
| --- | --- |
| Contract | The declaration and adapter conform; an old server adapter fails clearly instead of entering a compatibility path. |
| Surfaces | Normal forms, inline forms, generated filters, and bulk value controls receive the intended semantic defaults and surface variants. |
| Rendering | Native rendering and every declared Crispy integration preserve values, validation, errors, required/disabled state, and policy markers. |
| Ownership | Neutral presentation keeps Django's compatible widget; silent model-backed custom-form fields may receive the policy; explicit application widgets remain unchanged. |
| Temporal controls | Generated and custom filters, normal and inline forms, and bulk controls render exactly one native date/time type, use HTML-compatible values, and preserve seconds for time and datetime-local controls. |
| Selects | Default, explicitly enabled, and explicitly disabled searchable-select intent resolve correctly. |
| Multiselects | Standard and compact variants preserve checked state, mouse and keyboard toggling, clear-all, submitted values, placement, and the compact selected count. |
| Browser lifecycle | HTMX replacement reinitialises controls, modal timing and dropdown ownership are correct, and successful inline save does not flash the native control. |
| Row-action columns | Default actions remain at end; start placement keeps selection outermost; header, display, and inline rows share the same order; HTMX replacements retain it; sticky actions remain visible and usable during horizontal scrolling at either logical edge. |
| Row-action menus | Buttons and extras-only dropdown modes remain compatible on wider screens; both dropdown scopes use compact accessible kebabs; icon-only controls retain accessible names and semantic tooltips; direct custom SVG actions render icon plus text by default and icon-only when requested; all-dropdown follows the canonical labelled View, Edit, configured extras, Delete order. A menu gets one shared icon gutter only when at least one currently rendered action provides `icon_html`; every menu row keeps its label. At the pack's narrow breakpoint, all modes expose only the canonical responsive all-actions menu. Menu items are neutral except for restrained destructive treatment; configured extra-button fills stay out of menus; Delete has no orphaned divider; inline Save/Cancel remain visible. Lazy state, disabled reasons, guards, modal/HTMX behavior, and replacement rows remain intact. |
| Selection column | Select-all, normal-row, active-inline, and HTMX-replaced selection cells remain pinned at logical start by default. With sticky start actions, selection stays outermost and actions pin immediately after it; sticky end actions can remain visible at the opposite edge. Selection and action controls remain usable after horizontal scrolling. |

Server tests should prove semantics and adapter decisions. Use browser tests only for behaviour that requires layout, focus, events, vendor code, or an actual HTMX/modal lifecycle. For row actions, assert resolved order, permission filtering, accessible names, destructive markers, lazy-state indices, and the shared custom-icon gutter decision on the server, then use a small browser test to exercise horizontal scrolling, both floating-menu scopes, native and configured action activation, icon-only semantic tooltips, Delete confirmation, and inline Save/Cancel. Do not encode pixel tolerances, whitespace expectations, snapshots, or framework-class inventories as the portable contract.

## Check the installed distribution

Test the built wheel and source distribution, not only the source checkout. Confirm that template resources and declared assets are present after installation and that the selected pack resolves successfully in that environment.

For an independent pack, put the clean-install check in that package repository: install its built artifact alongside the intended PowerCRUD release, configure a minimal Django project, and run the same conformance helper. This must cover both wheel and source distribution. PowerCRUD does not need to know the package name in advance.

## Use browser tests for browser risks

Use focused Playwright coverage where a server test cannot see the problem: HTMX reinitialisation, modal or dropdown ownership, focus, responsive overflow, and asset loading are typical examples.

Run the broad project suite for release preparation and use focused test selections while developing a bounded pack change. The full commands and environment notes are in [Testing PowerCRUD](../reference/testing.md).

## Acceptance checklist

- The declaration resolves and reports accurate capabilities, form support, and assets.
- Shared server behaviour passes for every supported surface.
- Pack-specific presentation and resource checks pass.
- Installed wheel and source-distribution resources are present and usable.
- Browser-only risks have focused Playwright evidence where relevant.
- Documentation tells users how to select the pack, load its assets, align Crispy Forms, and meet any vendor requirements.
- Widget policy is covered across every supported surface, rendering mode, fallback, and application-override boundary.
- A version-4 pack honours list-toolbar width/alignment plus version-3 row-action placement and horizontal stickiness across header, display, inline, and HTMX replacement rows, and renders both dropdown scopes with the canonical action semantics.
