# Phase 9.4 Project-Owned Asset Snapshot Notes

## Purpose

This slice makes application ownership of supported pack assets explicit without changing package selection, public runtime APIs, or the existing package asset paths.

## Decisions

1. `pcrud_mktemplate app --assets` copies a manual-static snapshot in addition to the default four root templates; `--all --assets` copies complete templates and assets.
2. Asset snapshots are plain-app only. They are not model-specific because a base template loads assets for the whole page.
3. Copied assets have no per-file package fallback. The project replaces the package-owned entry and owns upgrade review.
4. DaisyUI copies the shared PowerCRUD CSS/runtime tree. Bootstrap also copies its contrib CSS/runtime tree so its relative import to the shared runtime remains valid.
5. Vendor dependencies and Vite integration remain downstream-owned. This slice does not generate or modify a Vite entry.

## Plan

### Phase 9.4.1: Copy Supported Pack Assets

The command must preserve the `powercrud` static-tree topology below `<app>/static/<app>/powercrud/`. This keeps the Bootstrap entry's existing relative import valid after copying. It must copy only PowerCRUD-owned CSS and JavaScript, overwrite matching files, retain destination-only files, and print the exact copied locations.

### Phase 9.4.2: Publish Ownership Guidance

The management-command reference is the source of truth for command combinations and activation tags. Template-pack selection and customisation pages explain the difference between template fallback and asset ownership. The runtime guide retains its stable-entry contract while documenting the opt-in snapshot boundary.

### Phase 9.4.3: Validate And Handoff

Focused tests cover both pack layouts, the preserved Bootstrap topology, output guidance, overwrite/retention, and rejection paths. Existing frontend packaging tests remain the evidence that source trees are package-owned. The standard full suite remains the final regression gate.

## Completion Evidence

Implemented on 2026-07-16. `pcrud_mktemplate app --assets` now copies the documented asset tree, prints the matching `{% static %}` tags and `POWERCRUD_TEMPLATE_PACK` selector, and rejects model-scoped operations. The focused command and frontend-asset packaging run passed 72 tests. One uninterrupted normal regression gate passed: 1,017 non-Playwright tests plus 14 skips, followed by 84 Playwright tests plus 5 skips.

No Vite scaffolding was added. A downstream Vite project still needs to own its frontend entry and must not place the generated manual-static snapshot alongside the packaged Vite entry.
