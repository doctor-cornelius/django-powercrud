# Phase 9.5 Override Layers And Project Root Selection Notes

## Purpose

This slice removes an unnecessary difference between model-scoped and project-root copying, then makes the available override boundaries understandable before a developer reaches detailed command reference material.

## Decisions

1. Plain app targets accept the existing root selectors: `--list`, `--detail`, `--form` (including the create/update aliases), and `--delete`.
2. A selected root is copied to `<app>/templates/<app>/powercrud/<pack>/object_*.html`; it applies only to views configured with that project root.
3. Missing roots, components, and nested templates continue to use the selected package. Only `--all` uses `template_override_complete = True`.
4. `--assets` remains independent, so a project can copy one root and the application-owned runtime in one command.
5. The customisation page contains the decision overview and short collapsed choices table; Management Commands remains the detailed command source of truth.

## Plan

### Phase 9.5.1: Add One-Root Project Copies

The existing role parser already resolves list, detail, form, and delete. Plain app handling should reuse that resolved role rather than treating it as model-only. The source must be the explicitly selected DaisyUI or Bootstrap pack, not the configured runtime pack.

### Phase 9.5.2: Explain The Override Layers

The overview must state the scope of each layer in ordinary language and distinguish model-wide, view-only, project-root, complete-pack, and asset ownership. It must not portray the sample application's focused overrides as another template pack.

### Phase 9.5.3: Validate And Handoff

Focused tests establish destination, source-pack choice, fallback guidance, and `--assets` independence. The normal regression gate remains the final compatibility check.

## Completion Evidence

Implemented on 2026-07-16. Plain-app `--list`, `--detail`, `--form`, `--create`, `--update`, and `--delete` now copy the selected root from DaisyUI or Bootstrap into the existing project override root. The customisation page begins with the supported override layers and includes an initially collapsed project-command choices table; Management Commands remains the detailed authority.

The focused management-command and frontend asset-packaging run passed 79 tests. One uninterrupted normal regression gate passed: 1,024 non-Playwright tests plus 14 skips, followed by 84 Playwright tests plus 5 skips.
