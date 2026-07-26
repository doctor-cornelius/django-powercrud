# Phase 10 External Framework Adapter API Notes

## Purpose

Phase 10 restores the fundamental product requirement that independent authors can implement and publish PowerCRUD packs for other presentation systems without changing PowerCRUD itself.

The accepted direction is a pack-supplied adapter declaration. PowerCRUD supplies durable CRUD and lifecycle behaviour. The pack supplies its templates, server-side presentation translation, optional framework-specific browser behaviour, CSS, JavaScript, capabilities, packaging, and tests.

The initial plan was created without a code audit. Phase 10.1 has now completed
the read-only inventory described below. The evidence-backed findings are in
[`phase10-external-adapter-api-audit.md`](phase10-external-adapter-api-audit.md);
the categories in this notes file remain planning context, not a substitute for
that findings document.

## Decisions

1. Independent new-framework packs are a required product capability, not an optional extension.
2. Pack declarations identify their own versioned Python and JavaScript adapters; PowerCRUD does not maintain a whitelist of permitted framework names.
3. Any conforming pack may declare package-owned CSS and JavaScript.
4. DaisyUI and Bootstrap must use the same public contracts as third-party packs.
5. Framework-neutral CRUD, HTMX, state, persistence, and lifecycle behaviour remains in PowerCRUD core.
6. Adapter hooks are semantic and may be optional when a framework does not need special browser behaviour.
7. External author tests live in the external package repository and use a reusable PowerCRUD-supplied test kit.
8. A separately packaged new-framework proof is required before the API is accepted.
9. Manual-static support and downstream Vite support both require explicit, honest contracts.
10. Phase 10 documentation must follow the direct author journey demonstrated by mature template-pack ecosystems: start from a working pack, adapt it, run it, test it, publish it, and show consumers how to install and select it.

## Plain-Language Target Workflow

A pack author should be able to:

1. generate or copy a starter package;
2. change templates and framework classes;
3. provide small server and browser translations only where their framework needs them;
4. declare CSS and JavaScript owned by the package;
5. run the supplied conformance tests in the package's own repository;
6. publish a wheel and source distribution to PyPI; and
7. tell users to install the Django app and select `package.module:template_pack`.

A consumer should not edit PowerCRUD, register a framework name upstream, or depend on internal PowerCRUD test files.

## Public Contract Intent

The server adapter translates semantic presentation requests into framework output. For example, PowerCRUD may ask for a primary or destructive button presentation; the adapter supplies the appropriate classes or attributes.

The browser adapter translates semantic lifecycle requests into framework behaviour. For example, PowerCRUD may ask to open or close a modal; a pack can use its framework's component API or update the relevant DOM state. Frameworks that need no special operation use the default no-op hook.

The asset contract lets the pack declare CSS and JavaScript it owns. PowerCRUD is responsible for deterministic selection and supported loading mechanisms, not for compiling every third-party entry into PowerCRUD's own build manifest.

## Compatibility Requirements

- Existing unconfigured projects continue to receive DaisyUI automatically.
- Existing Bootstrap selection continues to work.
- `powercrud/js/powercrud.js`, `window.initPowercrud`, semantic data attributes, and established lifecycle ordering remain stable unless an explicitly accepted compatibility transition replaces them.
- Existing manual-static and packaged Vite consumers remain supported during migration.
- A pack cannot claim support for behaviour its templates or adapters do not implement.
- Contract-version failures and missing hooks/assets must produce direct, actionable errors.
- First-party packs cannot use private adapter paths unavailable to external packages.

## Audit Planning Boundary

Phase 10.1 was a read-only audit. Its evidence sources, workstream boundaries,
and reconciled findings are recorded in
[`phase10-external-adapter-api-audit.md`](phase10-external-adapter-api-audit.md).

Suitable bounded audit workstreams may include:

- Python declaration, discovery, presentation, and validation;
- JavaScript core, composition, lifecycle, and adapter boundaries;
- templates and semantic hooks;
- manual-static, Vite, package assets, and installed distributions;
- tests, author tooling, public documentation, and external-package workflow.

Weaker-model sub-agents such as Luna may perform those bounded inventories after a stronger planning pass supplies precise questions and expected output. They must report evidence, not make architecture decisions. The primary agent owns cross-workstream reconciliation, contract recommendations, and any conclusion that changes scope.

## Plan

### Phase 10.1: Audit The Extension Surfaces

Completed as a read-only inventory. The findings document covers current
ownership, hard-coded DaisyUI/Bootstrap behaviour, template and runtime
contracts, asset and packaging boundaries, test coverage, compatibility
obligations, and unresolved questions. No API implementation or architecture
decision was made during the audit.

### Phase 10.2: Lock The Public Adapter Contracts

Convert the accepted product requirement and audited evidence into small versioned Python and JavaScript contracts. Keep hooks semantic, distinguish required from optional behaviour, and test the design against DaisyUI, Bootstrap, and the proposed independent proof before coding the migration.

The complete contract is accepted in
[`phase10-external-adapter-contract.md`](phase10-external-adapter-contract.md).
It is public version 1. The unreleased staging declaration shape may be replaced
directly; no declaration migration layer is required.

### Phase 10.3: Make Asset Ownership Framework-Neutral

Completed in implementation batch `4c02c940`. `PackAssets` and
`BrowserAdapterSpec` identify generic package resources, static paths, vendor
requirements, and copy roots. The template tags provide deterministic
manual-static ordering: runtime configuration, application vendors, selected
adapter, then the stable entry. Snapshots preserve the existing no-fallback
ownership rule. Vite remains deliberately application-owned: a project imports
the pack's documented assets before the stable entry rather than expecting
PowerCRUD to alter its manifest.

### Phase 10.4: Implement The Generic Adapter Runtime

Completed in implementation batch `4c02c940`. The stable
`powercrud/js/powercrud.js` entry reads the server-emitted pack identity,
validates `window.PowerCRUDAdapter`, and composes semantic hook groups with
neutral defaults. CRUD/HTMX/state/lifecycle behaviour remains in core.
`window.initPowercrud` and the stable entry path remain unchanged.

### Phase 10.5: Migrate DaisyUI And Bootstrap

DaisyUI and Bootstrap now declare public server/browser adapters and assets,
and both adapters return the public semantic hook shape. The final browser
matrix passed for the default DaisyUI pack (84 passed, 5 skipped) and Bootstrap
(78 passed, 12 skipped). The skips are explicitly pack-specific checks, such as
DaisyUI's Tippy integration, rather than silently relaxed shared behaviour.

### Phase 10.6: Prove Independent Pack Authoring

`pcrud_starttemplatepack` now generates a repository-shaped, separately
packaged starter outside the PowerCRUD namespace. Its generated project owns
distribution metadata and a conformance test, and focused tests build its
wheel/source distribution and validate the generated declaration in a separate
Django process. Clean installations from both the wheel and source distribution
pass. A separate external-app settings fixture then loads the declared browser
adapter and asserts its selected identity, static asset, stable runtime, and
lifecycle hook in a browser. Together these prove the distribution and browser
boundaries without placing the fixture in the PowerCRUD package namespace.

### Phase 10.7: Publish And Accept The External Author Workflow

The public documentation now follows the plain create, adapt, test, publish,
install, and select journey. It states the manual-static route, the
application-owned Vite boundary, and the distinction between project overrides
and a publishable pack. The final normal regression gate passed with 1023
passed and 14 skipped tests (plus 90 deliberately deselected browser tests).
Phase 10 is accepted: an independent package can now use the same public
declaration, adapter, asset, validation, packaging, and author-test paths as
the first-party packs.
