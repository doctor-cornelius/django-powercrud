# Phase 9.4 Project-Owned Asset Snapshot Plan

## Status

Complete — 2026-07-16.

## Next

Resume the remaining Phase 9.3 documentation and acceptance work; the asset-snapshot contract is now available.

## Phase 9.4.1: Copy Supported Pack Assets

1. [x] Add plain-app `--assets` support alongside existing template scopes.
2. [x] Copy DaisyUI shared assets and Bootstrap shared-plus-contrib assets into the application static namespace.
3. [x] Preserve the Bootstrap entry's relative shared-runtime import and retain destination-only files.
4. [x] Reject model-scoped, role, and focused-component asset operations.

## Phase 9.4.2: Publish Ownership Guidance

1. [x] Document generated manual-static activation snippets and vendor dependency order.
2. [x] State replacement-not-addition, no-fallback, application scope, and Vite limits.
3. [x] Update runtime ownership guidance without changing the stable public entry.

## Phase 9.4.3: Validate And Handoff

1. [x] Pass focused management-command and runtime packaging tests.
2. [x] Pass the standard full regression gate.
3. [x] Record accepted evidence and remaining Vite work in the matching notes.
