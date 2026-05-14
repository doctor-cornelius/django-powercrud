# Abstract Surface Plan

## Status

Concepts guide and current-API recipes draft landed in public docs.

## Next

1. Review the recipes for usefulness, scope, and whether they reveal helper candidates.

## Phase 1: Settle The Direction

1. [x] Capture the other AI brief as source material.
2. [x] Add a Codex brief grounded in the live PowerCRUD API.
3. [x] Record notes on concepts, naming, precedence, and list-options boundaries.
4. [x] Add an internal config audit using live PowerCRUD config and read-only DDMS evidence.
5. [x] Confirm abstract-surface work should start as documentation only.

## Phase 2: Name The Concepts

1. [x] Draft a concise concepts page for `docs/mkdocs/`.
2. [x] Explain that explicit view configuration remains the primary API.
3. [x] Define the core concepts without introducing unimplemented helpers.
4. [x] Place filtering, sorting, pagination, and table state under Surface.

## Phase 3: Refine The Config Audit

1. [x] Map current config options to concept buckets.
2. [x] Identify overlapping or confusing option names.
3. [x] Record compatibility-sensitive defaults.
4. [x] Decide which audit findings belong in public docs.

## Phase 4: Add Current-API Recipes

1. [x] Draft a small recipe set using only existing PowerCRUD config.
2. [x] Keep recipes practical and copyable.
3. [x] Avoid recipe classes or new helper APIs.

## Phase 5: Design Helper Candidates Later

1. [ ] Write a `PowerField` design note only after the audit.
2. [ ] Define the explicit-config-wins rule precisely.
3. [ ] Decide whether implementation should proceed or remain deferred.
