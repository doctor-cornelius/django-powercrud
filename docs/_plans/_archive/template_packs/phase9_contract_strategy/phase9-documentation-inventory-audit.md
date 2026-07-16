# Phase 9 Stable Documentation Inventory Audit

## Status

Inventory complete on template_pack/9a-contract-strategy. The resulting contract decisions are now recorded in the Phase 9 notes. This was a read-only review of existing documentation and the accepted Phase 7 product API audit; it did not change stable documentation, product code, tests, assets, or the Phase 8 reference-pack implementation.

## Purpose And Boundaries

This document identifies where the durable template-pack contract is already documented, where it is missing or misleading, and which pages should be reconciled during Phase 9.

It does not re-audit Bootstrap implementation behaviour. The completed phase7-bootstrap-product-api-audit-plan.md remains the source for current API classifications, evidence, verification gaps, and follow-up recommendations.

The inventory uses these classifications:

- **Keep** — current wording is useful and does not need a Phase 9 policy change.
- **Update** — the page should be corrected or extended when the contract is accepted.
- **Link** — the page should point to one authoritative contract page rather than duplicate policy.
- **Consolidate** — overlapping wording should be reduced to one authority.
- **Defer** — the page concerns post-Phase-8 mechanics or a Phase 8-sensitive implementation path.

## Executive Summary

1. The public docs describe DaisyUI as the maintained or built-in styling path, but do not explain the Bootstrap pack as a supported-pack candidate or state its final support status.
2. reference/config_options.md is the broadest API inventory, but its defaults and descriptions are often DaisyUI-centric and it contains no DaisyUI/Bootstrap support classification.
3. guides/setup_core_crud.md and reference/complete_example.md document the new portable modal and view-help APIs, but some wording still describes DaisyUI markup or colours as universal.
4. reference/deprecations.md is the clearest authority for legacy modal class warnings and semantic replacements; future edits should link to it rather than duplicate the policy.
5. guides/advanced/customisation_tips.md and reference/mgmt_commands.md explain focused and whole-tree copying generically, but do not state the Bootstrap whole-tree limitation or the selected-pack override boundary.
6. reference/sample_app.md correctly documents process-startup Bootstrap selection and the provisional status of the DaisyUI reference presentation, but it is sample guidance rather than a product support contract.
7. reference/testing.md documents the project-wide three-layer test model, but not the per-pack server matrix, targeted browser obligations, or installed wheel/sdist resource gate required for a supported pack.
8. Crispy guidance is spread through form and sample documentation; no page explains that the application chooses use_crispy and the compatible Crispy integration rather than the template pack silently forcing one.
9. The durable strategy needs one authoritative cross-pack page, with existing API, deprecation, customization, sample, and testing pages linking to it.
10. No stable documentation should be removed or rewritten until the Phase 9 policy decisions below are accepted.

## Stable Documentation Inventory

| Page | Current coverage | Finding | Phase 9 action |
| --- | --- | --- | --- |
| guides/styling_tailwind.md | DaisyUI/Tailwind setup, table controls, CSS assets, custom-framework copying | Calls DaisyUI the maintained path and presents styling controls as if class values were portable; does not describe the official Bootstrap pack, semantic translations, or raw-class boundary. | Update and link |
| reference/config_options.md | Alphabetical public option reference, including table geometry, view help, modals, actions, templates_path, use_crispy, and framework selection | Strong API detail, but defaults and descriptions such as “daisyUI classes” are not consistently qualified; no pack support status or classification column. | Update and link |
| guides/setup_core_crud.md | Main setup walkthrough, portable modal mapping, view help, list presentation, links, actions, filters, and forms | Portable modal contract is documented well. view_help still calls the disclosure a DaisyUI disclosure, and some examples imply DaisyUI-native presentation is universal. | Update and link |
| reference/deprecations.md | Legacy modal classes, warnings, semantic replacement, disabled hooks, tooltip-hook deprecation | Good single authority for modal deprecation and warning behaviour. It should be linked from the cross-pack contract and may need only small cross-pack clarification. | Keep as authority; link |
| guides/advanced/customisation_tips.md | Focused component overrides, whole-tree copying, semantic hooks, and script-free customization | Explains the override model clearly but uses {framework} generically and does not state that Bootstrap focused overrides are supported while its whole-tree copy destination is unavailable. | Update and link |
| reference/mgmt_commands.md | pcrud_mktemplate commands, component names, destinations, context, and compatibility hooks | Command reference documents both whole-tree and focused operations without pack-specific limits or a link to the supported-pack contract. | Update and link |
| reference/sample_app.md | Default, focused, provisional reference, and Bootstrap process-startup presentations | Correctly says Bootstrap is optional/co-distributed and the reference presentation is not production-supported. It does not replace a product-level support decision or API matrix. | Keep sample facts; link |
| reference/testing.md | Full suite, Playwright smoke/full layers, focused commands, and distribution-oriented local workflow | Does not define the shared server baseline, pack-specific sentinels, browser-only risk boundary, or installed wheel/sdist resource requirements for supported packs. | Update and link |
| reference/complete_example.md | Feature-rich view example with portable modal, view help, links, actions, and styling | Example is useful, but explanatory text refers to DaisyUI semantic colours and tooltip defaults without distinguishing portable semantics from selected-pack rendering. | Update and link |
| guides/getting_started.md | Installation, default DaisyUI configuration, assets, and frontend dependencies | Appropriate default onboarding, but no route to Bootstrap or explanation that alternative packs are opt-in process-startup configurations. | Update and link |
| guides/concepts.md | Conceptual model for presentation, styling, compatibility, and defaults | Useful vocabulary but lacks the durable distinction between core behaviour, template pack, framework adapter, optional variant adapter, and focused override. | Update and link |
| reference/dockerised_dev.md | Development containers, assets, and a brief DaisyUI/Bootstrap switching note | Mentions framework testing but gives no product contract or support boundary. | Link only |
| guides/forms.md | Form configuration and Crispy usage | Covers form behaviour but does not explain pack-owned native/Crispy requirements or that Crispy selection remains application-controlled. | Update and link |
| guides/bulk_edit_sync.md | Bulk form, selection, outcomes, and presentation behaviour | Relevant API guidance but no cross-pack classification; should link to the contract instead of duplicating pack policy. | Link |
| guides/inline_editing.md | Inline controls, dependencies, validation, and lifecycle behaviour | Relevant shared behaviour; no pack-specific contract is stated. | Link |
| guides/structured_api/poweractions.md | Structured action declarations and portable modal fields | Useful API detail; should link to the portable/raw-class and support rules. | Link |
| guides/structured_api/recipes.md | Structured declaration recipes | No direct cross-pack policy; retain as example material and link if needed. | Keep or link |
| guides/advanced/recipes.md | Broader recipes including modal configuration | Useful examples, but portable/raw-class and pack-specific claims should follow the authoritative contract. | Link |
| reference/poweractions.md | Reference API for PowerAction and PowerButton, including portable modal fields and legacy class compatibility | Useful structured-action authority; should link to the cross-pack classification and deprecation authority. | Link |
| reference/hooks.md | Hook signatures and behaviour contracts | Shared hook authority; semantic presentation hooks should link to the support matrix. | Link |
| index.md | High-level feature summary mentioning DaisyUI/Tailwind styling | Default-oriented summary is acceptable, but should not imply that DaisyUI is the only supported presentation path once Bootstrap support is accepted. | Update or link |

## Cross-Cutting Gaps

### Supported-pack strategy and terminology

There is no stable page that defines the relationships among the framework-neutral core, template pack, framework adapter, optional variant adapter, focused override, compatibility façade, and selected assets/forms. guides/concepts.md is the best conceptual starting point, but a dedicated contract page should own the complete vocabulary.

The default DaisyUI pack is documented as the built-in/maintained path. The docs need to distinguish “compatible default and behavioural baseline” from “only supported framework”. Bootstrap's production-support status must be recorded explicitly from merged evidence rather than inferred from sample-app commands.

### API support and classifications

The API reference lists relevant settings, including table_classes, table_max_height, table_pixel_height_other_page_elements, table_max_col_width, table_header_min_wrap_width, column_alignments, view_help, modal presentation, actions, and form settings. It does not say whether each setting is:

- portable semantic;
- framework-translated;
- framework-specific raw input; or
- genuinely unsupported by a selected pack.

The Phase 7 audit is the evidence source for the first DaisyUI/Bootstrap matrix. Stable docs should summarize that matrix rather than duplicate the full audit table.

Raw class settings need explicit selected-framework wording. A Bootstrap pack can honour a raw class string as passthrough without translating a DaisyUI/Tailwind class vocabulary. The current docs do not consistently make that distinction.

### Unsupported settings and silent handling

The Phase 7 audit establishes the no-silent-ignore expectation and identifies the Bootstrap whole-tree pcrud_mktemplate boundary as an intentional/documentation gap. Stable docs should state that a supported pack must expose a limitation through declaration/validation, warning or configuration error where appropriate, and documentation. “Accepted but ignored” must not be presented as a supported contract.

### Compatibility and deprecations

The modal deprecation page is already substantially aligned with the intended policy: legacy raw classes remain compatible, emit FutureWarning, are targeted for v1.0 removal, and cannot be mixed with the semantic mapping. The cross-pack page should link to that authority and add only the portable-versus-framework-specific interpretation needed for pack selection.

### Crispy ownership

The docs mention Crispy in forms, sample, and customization material, but do not establish one rule: the selected pack declares compatible form resources and integrations; the downstream application chooses use_crispy and its installed Crispy pack. Template-pack selection must not silently force Crispy or prevent a downstream developer from trying a compatible integration.

### Validation obligations

reference/testing.md gives good general commands but not a supported-pack acceptance model. Phase 9 should add or link guidance covering:

1. the shared server behaviour matrix using default DaisyUI as baseline;
2. pack-specific server sentinels for translation, resources, forms, and explicit limits;
3. targeted Playwright for browser lifecycle, HTMX reinitialization, focus, modal/dropdown ownership, geometry, and responsive overflow;
4. installed wheel and sdist resource validation; and
5. when complete canonical regression, selected-pack regression, manual-static, Vite, or visual evidence is material.

Identical DOM, class lists, or pixels should not be documented as the cross-pack parity target unless a semantic contract requires them.

### Phase 8-sensitive material

reference/sample_app.md explicitly labels the DaisyUI reference presentation as provisional, which is correct. Any future documentation must avoid treating its namespace, launch command, or whole implementation as a permanent supported-pack authoring path. Phase 9 should document final authoring mechanics only after Phase 8 settles them.

## Recommended Documentation Shape

The smallest coherent Phase 9 documentation shape is:

1. Create one authoritative cross-pack strategy/support page, preferably under docs/mkdocs/guides/ (candidate: guides/template_packs.md). It should contain the pack vocabulary, DaisyUI/Bootstrap support matrix, API classifications, unsupported-setting rule, Crispy ownership, and acceptance model.
2. Keep reference/config_options.md as the detailed option reference, correcting DaisyUI-only wording and linking each relevant group to the strategy page.
3. Keep reference/deprecations.md as the warning/deprecation authority and link it from the strategy page and modal/action references.
4. Update guides/advanced/customisation_tips.md and reference/mgmt_commands.md for focused overrides, selected-pack resolution, and the Bootstrap whole-tree limit.
5. Update reference/testing.md with the supported-pack validation obligations, then link from the strategy page.
6. Add concise links from setup, styling, concepts, sample, forms, and complete-example pages rather than repeating the full policy.

The exact stable page path remains a Phase 9 decision; this inventory does not create it.

## Decision Outcomes

1. Bootstrap is a supported production pack but is not the default; DaisyUI remains the supported default and compatibility baseline.
2. Template Packs receives its own top-level documentation section and authoritative strategy/support page.
3. Semantic settings are documented as portable and pack-translated; raw classes remain selected-framework inputs.
4. Public docs state product support classifications, while internal verification gaps remain engineering evidence.
5. Focused overrides are the supported customization route. Plain-app DaisyUI whole-tree copying is deprecated for v1.0 removal; Bootstrap and future packs need not support it.

## Suggested Phase 9 Writing Order

1. Draft the authoritative strategy/support page from the Phase 7 audit, the accepted decisions, and this inventory.
2. Reconcile the option reference, setup/styling wording, modal deprecation links, and customization/management-command boundaries.
3. Add the supported-pack acceptance model to testing guidance and cross-link the affected pages.
4. Validate claims and links against the merged implementation before reviewing Phase 8 removals.

## Sources Reviewed

Primary planning/evidence sources:

- phase9-contract-strategy-plan.md
- phase9-contract-strategy-notes.md
- phase7-bootstrap-product-api-audit-plan.md
- phase7-bootstrap-styling-api-audit-plan.md

Stable pages screened or read for this inventory are the pages listed in the table above. No other stable page matched the inventory search terms without being listed or explicitly treated as shared API material.
