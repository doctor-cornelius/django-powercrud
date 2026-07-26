# Phase 9.5 Override Layers And Project Root Selection Plan

## Status

Complete — 2026-07-16.

## Next

Resume the remaining Phase 9.3 documentation and acceptance work; project-root selection guidance is now available.

## Phase 9.5.1: Add One-Root Project Copies

1. [x] Allow a plain app target to select list, detail, form, or delete from the chosen source pack.
2. [x] Copy the selected `object_*.html` file into the existing project override root.
3. [x] Keep `--all`, the default four-root scope, and independent `--assets` behaviour unchanged.

## Phase 9.5.2: Explain The Override Layers

1. [x] Add a plain-English overview of focused, model, view, project-root, complete-pack, and asset ownership.
2. [x] Add an initially collapsed project-command choices table and link the detailed reference.
3. [x] Reconcile the management-command reference with the new app-level selectors.

## Phase 9.5.3: Validate And Handoff

1. [x] Add focused tests for single-root DaisyUI and Bootstrap project copies and their asset combination.
2. [x] Pass the standard full regression gate.
3. [x] Record the final command and documentation contract in the matching notes.
