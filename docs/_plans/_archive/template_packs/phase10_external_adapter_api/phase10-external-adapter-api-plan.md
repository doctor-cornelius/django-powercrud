# Phase 10 External Framework Adapter API Plan

## Status

Phase 10 is complete. The accepted public contract is implemented and proven
against the first-party packs and an independently packaged external fixture.

## Next

Hand the completed branch to normal review and merge workflow. Any future pack
capability should begin from a new, bounded plan rather than reopening Phase 10.

## Phase 10.1: Audit The Extension Surfaces

1. [x] Inventory the server-side pack declaration, resolution, presentation, and validation surfaces that must accept external adapters.
2. [x] Inventory the browser runtime, framework composition, lifecycle, and semantic-hook surfaces that must become a public adapter contract.
3. [x] Inventory manual-static, downstream Vite, packaging, installation, and asset-loading surfaces without designing from unverified assumptions.
4. [x] Inventory reusable and first-party-only test infrastructure, author tooling, and documentation dependencies.
5. [x] Produce one reconciled findings document mapping each surface to its current owner, compatibility risk, test obligations, and unresolved questions.

## Phase 10.2: Lock The Public Adapter Contracts

1. [x] Define a versioned pack-supplied Python adapter contract for server-side presentation translation.
2. [x] Define a versioned pack-supplied JavaScript adapter contract for framework-specific browser behaviour.
3. [x] Define required, optional, and no-op adapter hooks so simple frameworks do not implement irrelevant behaviour.
4. [x] Define declaration, capability, compatibility-error, and contract-version rules without framework-name whitelists.
5. [x] Ratify the contracts against DaisyUI, Bootstrap, and the intended independent new-framework proof before implementation.

## Phase 10.3: Make Asset Ownership Framework-Neutral

1. [x] Allow any conforming pack to declare its package-owned CSS and JavaScript resources.
2. [x] Provide a generic manual-static loading path with deterministic ordering and duplicate-load protection.
3. [x] Define a safe downstream Vite integration contract that does not require third-party entries in PowerCRUD's own manifest.
4. [x] Validate installed wheel and source-distribution assets through generic package-resource rules.

## Phase 10.4: Implement The Generic Adapter Runtime

1. [x] Load the selected pack's Python adapter through the public declaration contract.
2. [x] Load and compose the selected pack's browser adapter through the stable PowerCRUD runtime.
3. [x] Keep durable CRUD, HTMX, selection, persistence, and lifecycle behaviour in framework-neutral core code.
4. [x] Remove privileged framework branches only after equivalent public adapter paths are working.
5. [x] Preserve stable public runtime entry points and existing manual/Vite loading paths throughout the transition.

## Phase 10.5: Migrate DaisyUI And Bootstrap

1. [x] Move DaisyUI onto the public Python, browser, and asset contracts without presentation or behaviour changes.
2. [x] Move Bootstrap onto the same public contracts without presentation or behaviour changes.
3. [x] Remove any first-party-only adapter privileges that an external pack cannot use.
4. [x] Run shared server and browser behaviour gates against both migrated packs.

## Phase 10.6: Prove Independent Pack Authoring

1. [x] Create a separately packaged new-framework fixture that does not live inside the PowerCRUD package namespace.
2. [x] Prove installation, Django app registration, selector resolution, templates, server translation, browser hooks, and assets.
3. [x] Provide a reusable author test kit that runs from the external pack's own repository.
4. [x] Add straightforward scaffolding for copying a maintained pack into a new distributable package layout.
5. [x] Prove wheel and source-distribution installation in clean environments.

## Phase 10.7: Publish And Accept The External Author Workflow

1. [x] Rewrite the authoring guide as a plain-language create, copy, adapt, test, publish, install, and select journey.
2. [x] Document the public Python, JavaScript, template, asset, capability, and compatibility contracts at the level authors need.
3. [x] Document manual-static and downstream Vite integration without implying PowerCRUD edits are required.
4. [x] Pass focused contract, external-package, installed-artifact, and browser tests followed by the normal full regression gate.
5. [x] Accept Phase 10 only when an independent new-framework package works without PowerCRUD source changes.
