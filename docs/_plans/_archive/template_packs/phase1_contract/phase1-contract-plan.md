# Phase 1 Template-Pack Contract Plan

## Status

Complete. The Phase 1 contract baseline is accepted. Phase 2 begins with the pagination override-point slice while keeping the default DaisyUI experience working on `main`.

## Next

Create the Phase 2 child plan and characterize pagination before extracting it.

## Phase 1.1: Lock Compatibility And Resolution

1. [x] Define precedence for explicit per-view `templates_path`, new pack selection, and legacy `POWERCRUD_CSS_FRAMEWORK` configuration.
2. [x] Define how existing `powercrud/daisyUI/...` template paths remain usable during the migration period.
3. [x] Preserve existing manual-module and bundled/Vite runtime-loading contracts.
4. [x] Define the compatibility period and the decision process for any later deprecation.
5. [x] Define characterization outcomes that freeze the current default DaisyUI experience.
6. [x] Define the invariant that every ordinary implementation PR leaves legacy-compatible default behaviour working on `main`.
7. [x] Identify transitions that require an explicit atomic compatibility checkpoint.

## Phase 1.2: Lock The Template And Override Contract

1. [x] Classify orchestrator templates and partials as required, optional, or capability-dependent.
2. [x] Define focused override points for list, form, detail, delete, bulk, inline-edit, and modal surfaces.
3. [x] Define the context variables, partial names, semantic `data-powercrud-*` hooks, and events each override point must preserve.
4. [x] Decide whether core ships neutral rendering templates or only rendering contracts and fallback resolution.
5. [x] Define how `pcrud_mktemplate` supports focused downstream overrides.
6. [x] Require each override-point extraction to be independently testable and mergeable.

## Phase 1.3: Lock JavaScript Layers And Pack Composition

1. [x] Define framework-independent core responsibilities.
2. [x] Define reusable framework-adapter responsibilities.
3. [x] Define optional variant-adapter responsibilities.
4. [x] Define initialization order, repeatability, listener guards, state preservation, and teardown requirements.
5. [x] Define how multiple template packs reuse one framework adapter.
6. [x] Define how a variant declares no JavaScript, hook-based extensions, or an optional variant adapter.
7. [x] Keep exact adapter-injection, event, and initializer APIs internal until an extraction slice proves them.
8. [x] Require the compatible default framework adapter to remain automatically composed after every merged extraction slice.

## Phase 1.4: Lock Assets And Form Rendering

1. [x] Define downstream base-template responsibilities.
2. [x] Define manual-static and bundled/Vite asset-loading responsibilities.
3. [x] Define ownership of HTMX, Tom Select, Tippy, and their CSS.
4. [x] Allow packs that ship no additional CSS or JavaScript.
5. [x] Define native Django-form rendering requirements for official packs.
6. [x] Define optional crispy-forms integrations and dependency declarations.
7. [x] Define form, filter, inline-edit, and bulk-edit capability declarations.
8. [x] Prevent asset or form changes from requiring existing projects to update before a complete compatibility path has merged.

## Phase 1.5: Lock Packaging And Validation

1. [x] Decide whether each official pack is co-distributed or separately distributed.
2. [x] Define pack identity, template namespace, framework adapter, optional variant adapter, assets, capabilities, and form-rendering metadata.
3. [x] Define contract-version requirements for third-party packs.
4. [x] Define lightweight runtime configuration checks and errors.
5. [x] Define full development-time validation.
6. [x] Require clean installed-wheel and installed-sdist validation.
7. [x] Define shared unit and browser tests that every applicable pack must pass.
8. [x] Define reusable merge gates for ordinary slices and the atomic default-pack repackaging checkpoint.

## Phase 1.6: Ratify The Contract Baseline

1. [x] Resolve or explicitly defer every open Phase 1 decision.
2. [x] Confirm the contract supports the default DaisyUI pack and a structurally different DaisyUI variant.
3. [x] Confirm optional co-distributed Bootstrap full-parity dogfooding, including crispy support, uses the same contract without Bootstrap-specific assumptions in core.
4. [x] Record the first Phase 2 characterization and override-point slice.
5. [x] Record the intended sequence of independently mergeable implementation slices.
6. [x] Record every known atomic transition and its full acceptance gate.
7. [x] Mark Master Phase 1 complete after the contract baseline is accepted.
