# Phase 6 Reusable Pack Validation Notes

## Purpose

These notes support [`phase6-validation-plan.md`](phase6-validation-plan.md), which implements Phase 6 of the [`template_packs-master-plan.md`](../template_packs-master-plan.md).

Phase 6 turns the one-off declaration, inventory, fragment, behaviour, and installed-package checks from Phases 4 and 5 into reusable gates. It is deliberately a short consolidation phase before Bootstrap implementation begins. It does not build Bootstrap, broaden pack selection, or repeat every compatibility proof already accepted for the compatible DaisyUI implementation.

## Binding Inputs

1. Phase 1 separated lightweight runtime selection from fuller development and CI validation.
2. Phase 1 defined baseline and capability-dependent templates, server-addressable fragments, adapters, forms, assets, and installed-artifact discovery as validation concerns.
3. Phase 4 established the public frozen `TemplatePack` declaration, dynamic selector resolution, the compatible default DaisyUI pack, the legacy façade, and clean wheel and sdist evidence.
4. Phase 5 established a complete provisional reference namespace, same-adapter reuse, shared sample presentation settings, and representative default/reference behaviour evidence.
5. The default and reference declarations currently advertise the same list, form, detail, delete, filters, modal, bulk, async, inline, and favourites capabilities; both support native forms and crispy-tailwind, and neither declares additional pack assets or a variant adapter.
6. Phase 7 owns Bootstrap templates, adapter loading, assets, crispy-bootstrap5, and any runtime change needed to select that implementation.
7. Phase 8 may remove the visible reference implementation only after Phase 6 leaves an independent test-only same-adapter proof.

## Recommended Validation Shape

The reusable validator is a development and CI tool over a resolved `TemplatePack`. It is not invoked on every request and does not replace the existing lightweight selector checks. Runtime selection should continue to reject adapters, variant adapters, or asset-loading combinations that the running PowerCRUD version cannot actually compose.

The validator should use data-driven contract tables for:

1. Recognized capabilities and their dependencies.
2. Baseline and capability-dependent template paths.
3. Server-addressable named fragments required by those capabilities.
4. Known framework and variant adapter identities available to the validator.
5. Native and crispy form requirements.
6. Manual-static and Vite resource declarations.

This structure gives Phase 7 an extension point inside the existing validation machinery without pre-registering a Bootstrap implementation that does not exist yet. If implementation shows that these tables require a new public registry or a change to the frozen declaration schema, stop for guidance rather than silently creating that API.

Validation should identify all useful failures from one run where practical. An error should name the pack and the failing declaration field, capability, template, fragment, adapter, form integration, or asset. The validator should prefer package-resource lookup, Django template loading, focused rendering, and shared behaviour tests over template-source parsing.

Semantic hooks are behaviour contracts, not a generic source-text vocabulary. The validator may prove a named fragment exists because Python renders that fragment directly. Hooks, HTMX attributes, accessibility relationships, repeated initialization, and teardown-sensitive behaviour belong in rendered server tests and the shared browser matrix unless a stable machine-readable contract already exists.

## Shared Behaviour Matrix

The shared matrix is a reusable set of scenarios, not a second copy of the complete test suite. The same test code should run in separate processes under the default and reference settings configurations. A declared capability determines whether a scenario applies; a pack identity must not select a separate implementation of the test.

Server assertions should concentrate on presentation-independent truth:

1. The same models, URLs, views, fixtures, permissions, request methods, and persistence outcomes are used.
2. Normal and HTMX responses resolve through the selected namespace and retain required direct fragments.
3. Native and declared crispy form paths retain fields, validation, CSRF ownership, and transport semantics.
4. List, filter, sort, page, column, favourite, row-action, bulk, async, inline, create, update, detail, delete, and modal outcomes remain available where their capabilities are declared.

Browser assertions should use the same user actions and outcome checks while allowing each pack to own its markup and visual hierarchy. The matrix should cover the high-value lifecycle seams: list replacement, modal replacement, repeated initialization, teardown-sensitive widgets, state preservation, the stable public runtime entry, and browser error collection.

The complete canonical DaisyUI suite and all manual-static/Vite application checks do not need to run again under every pack. Phase 4 already proved both loading modes and clean installed default resources; Phase 5 proved the reference presentation over the shared runtime. Phase 6 repeats only the focused behaviour needed to establish the reusable matrix, plus any broader gate justified by files actually changed during implementation.

## Same-Adapter Fixture

The visible `daisyui-reference` pack is intentionally provisional. Tests that name its declaration, templates, settings, or sample presentation will be removed with it in Phase 8, so those tests cannot be the permanent proof that multiple packs may reuse one framework adapter.

Phase 6 therefore adds a test-only declaration and the minimum valid resource set needed for its declared capabilities. It should delegate presentation leaves where appropriate, remain absent from sample settings and navigation, and contain no functional JavaScript or pack-specific assets. Its identity, namespace, and tests must not depend on `daisyui-reference` names.

The durable assertion is architectural: two different pack identities may both declare the standard `daisyui` framework adapter, validate successfully, and resolve their own template resources without copying the framework adapter. The fixture is not another supported or visible pack and does not join the shared sample catalogue.

## Installed-Resource Boundary

The installed-resource gate proves that source-checkout success has not hidden missing package contents. One reusable harness should build wheel and sdist artifacts, install them into separate clean environments, and run declaration plus resource validation against the installed distribution.

The environment must not import `powercrud` or its resources from the repository checkout. The gate should verify both co-distributed selectable packs while the reference pack exists. Phase 7 later adds Bootstrap to the same selector list; Phase 8 removes the reference selector after Bootstrap replaces it in the maintained cross-pack matrix.

This is intentionally narrower than the Phase 4 atomic gate. It does not rerun the sample application, both browser loading modes, or the full regression suite inside every clean environment. It proves that selected declarations import and that their declared templates, direct fragments, form resources, adapters, and assets are present and usable after installation.

Repository policy requires explicit approval before running build, dependency-installation, or environment-installation commands. Phase 6.5 planning does not authorize those commands; request approval when that implementation gate is ready to run.

## Delivery Rule

Phase 6.0 is the planning contract on `template_pack/6.0`. After the plan is accepted and integrated, each implementation phase begins from synchronized `staging/main` on its own `template_pack/6.x` branch, receives proportionate focused tests, and is integrated before the next independent phase begins. The compatible default pack remains automatically selected and unchanged throughout.

The branch already contains three accepted `6.0` roadmap-planning commits covering the shortened validation phase, reference-pack retirement, and the selectable Bootstrap sample. Preserve those commits. This child-plan slice adds one further `6.0` documentation commit; the one-commit rule applies individually to the later implementation subphases.

Each completed subphase should have one semantic commit whose subject contains the subphase number. The recommended subjects are:

1. `docs(template-packs): 6.0 plan reusable pack validation`
2. `feat(template-packs): 6.1 add reusable pack validator`
3. `test(template-packs): 6.2 add shared server behaviour matrix`
4. `test(template-packs): 6.3 add shared browser behaviour matrix`
5. `test(template-packs): 6.4 preserve same-adapter fixture`
6. `test(template-packs): 6.5 verify installed pack resources`
7. `docs(template-packs): 6.6 ratify reusable pack validation`

Do not add an in-application switcher, query-parameter selector, per-view pack selector, new stable runtime entry, Bootstrap implementation, or reference-pack retirement as part of these slices. Do not create a blocker register pre-emptively; create `phase6-blockers.md` only when the first genuine stop condition occurs.

## Stop Conditions

Stop for guidance before proceeding when implementation finds:

1. A need to change the frozen `TemplatePack` declaration schema or add a public adapter, validator, or capability registry not already implied by the accepted contract.
2. A capability whose required templates, fragments, or behaviour cannot be mapped without changing its existing meaning.
3. A need to parse incidental template markup or CSS classes as though they were public semantic contracts.
4. A need to allow selection of an adapter, variant adapter, or asset combination the runtime cannot yet compose.
5. A need to change unconfigured/default rendering, legacy paths, stable runtime entries, or existing manual-static/Vite loading.
6. A need to duplicate sample models, routes, views, data, permissions, navigation, or functional JavaScript for the shared matrix.
7. An installed artifact that cannot expose declared resources without a material packaging or distribution decision.
8. An unexplained deterministic regression, non-trivial conflict, unrelated worktree mutation, or unexpected movement of remote `staging/main`.

## Accepted Evidence To Reuse

Phase 4 accepted evidence includes 966 server tests, 78 Playwright tests across manual-static and Vite loading, and clean wheel and sdist installations containing 45 permanent templates, 45 legacy facades, the built-in declaration and styles, the manifest, and the stable runtime entry.

Phase 5 accepted evidence includes 982 canonical non-browser tests, 78 canonical Playwright tests with three intentional settings-specific skips, two reference-settings browser tests, and one focused-settings browser test. It also includes focused declaration, 45-template inventory, 25-fragment, native/crispy rendering, shared-catalogue, and script-ownership checks.

Phase 6 should cite and preserve this evidence rather than manufacturing a requirement to rerun every accepted gate. New focused evidence must prove that the extracted validator and matrices are genuinely reusable and that installed resources remain usable through the new gate.

## Plan

### Phase 6.0: Lock The Consolidation Contract

The planning slice fixes the reduced boundary: one reusable validator, one shared server matrix, one shared browser matrix, one durable same-adapter fixture, and one narrow installed-resource harness. It explicitly excludes Bootstrap implementation and broad regression repetition.

The validator remains outside request-time selection. Capability and resource contracts are data-driven, while hooks and lifecycle behaviour remain rendered or browser-tested. Each later slice can therefore integrate independently without changing default selection or presentation.

### Phase 6.1: Add The Reusable Pack Validator

Implement the complete development and CI validator as one bounded feature. Reconcile existing inventories from the default and reference tests into shared contract data instead of preserving pack-specific copies as the source of truth.

Positive coverage runs the default and reference declarations through the same validator. Negative fixtures isolate unknown capabilities, missing dependencies, missing resources and fragments, unsupported adapters, inconsistent form declarations, and missing declared assets. Runtime discovery remains lightweight and unchanged.

### Phase 6.2: Establish The Shared Server Behaviour Matrix

Extract presentation-independent scenarios from the current default and reference coverage. Run the same matrix under both settings modules and use capability declarations to determine applicability.

Keep reference-only visual structure and delegation assertions in focused tests for as long as that implementation exists. Shared outcome tests must not assert DaisyUI-reference-specific classes, text arrangement, or DOM hierarchy.

### Phase 6.3: Establish The Shared Browser Behaviour Matrix

Create one reusable browser module or equivalent scenario layer that is invoked under each selected presentation settings process. It should exercise representative flows across the declared capabilities without cloning the entire canonical browser suite.

The matrix becomes the Phase 7 entry gate: Bootstrap joins only after its implementation can satisfy the same applicable scenarios. Until then, the matrix contains default and reference configurations only.

### Phase 6.4: Preserve A Durable Same-Adapter Fixture

Add the smallest valid test-only pack that demonstrates a distinct pack identity and namespace reusing the standard DaisyUI adapter. Validate and resolve it without adding sample settings, navigation, screenshots, or a visible catalogue entry.

Name and locate the fixture so Phase 8 can delete every reference-specific file without touching it. A focused assertion should prove that the fixture and built-in pack share the adapter identity while retaining distinct pack identities and resources.

### Phase 6.5: Add The Installed-Resource Gate

Turn the Phase 4 manual artifact proof into a repeatable harness that can receive an artifact and a selector list. Run it against isolated wheel and sdist installations and validate default plus reference resources from the installed distribution.

Do not use repository paths as validation fallbacks. Record the exact approved commands, environment isolation, selectors, and results here after the gate runs.

Completed in `template_pack/6.5`. `scripts/verify_installed_template_pack_artifacts.py` accepts one or more built artifacts and creates one fresh temporary `uv` environment for each. It installs the artifact plus only the Django and crispy dependencies needed by the validator, then launches its own installed-package probe with Python isolated mode (`-I`). The probe rejects a `powercrud` import below the source checkout, configures the minimum Django app/template environment, and resolves plus validates both selectors: `daisyui` and `powercrud.packs.daisyui_reference:template_pack`.

The authorized gate ran:

```bash
uv build
python scripts/verify_installed_template_pack_artifacts.py \
    dist/django_powercrud-0.8.6-py3-none-any.whl \
    dist/django_powercrud-0.8.6.tar.gz
```

Both artifacts passed from distinct temporary `site-packages` paths. The wheel installed directly; the sdist was built during isolated installation. Each installed copy resolved and validated the default and reference declarations, including their required package resources, Django-loaded templates, fragments, native-form requirements, crispy-tailwind integration, adapter declarations, and asset declarations. The harness intentionally does not rerun the sample application or browser suite inside the temporary environments; those are covered by the Phase 6 shared matrices.

### Phase 6.6: Pass The Phase Gate And Ratify

Run the validator, shared server matrix, shared browser matrix, same-adapter fixture, and installed-resource harness. Broader regression and generated-asset rebuilds are conditional on the actual implementation diff, not automatic repetition of Phase 4 and Phase 5.

After acceptance, update the master roadmap and notes with the integrated commits and evidence. Phase 7 may then begin with reusable validator, behaviour-matrix, same-adapter, and installed-resource gates already available.

Completed in `template_pack/6.6`. The retained, separate semantic commits are `850be186` (6.0), `497e39fd` (6.1), `e2494fd5` (6.2), `172c9da3` (6.3), `45fe46ed` (6.4), `0a3a574c` (6.5), and this 6.6 ratification record. No Phase 6 implementation branch is collapsed or squashed.

Final focused evidence passed from the synchronized Phase 6.5 tip:

1. Default settings: `src/tests/test_template_pack_validation.py`, `src/tests/test_same_adapter_template_pack.py`, and `src/tests/test_template_pack_behaviour_matrix.py` — 13 passed.
2. Reference settings: `src/tests/test_template_pack_validation.py` and `src/tests/test_template_pack_behaviour_matrix.py` — 11 passed.
3. Default browser matrix: `src/tests/playwright/test_template_pack_behaviour_matrix.py` — 3 passed.
4. Reference browser matrix: the same browser matrix with `DJANGO_SETTINGS_MODULE=tests.settings_daisyui_reference` — 3 passed.
5. Final `uv build` followed by `scripts/verify_installed_template_pack_artifacts.py` against the fresh wheel and sdist — both isolated installed-resource probes passed for `daisyui` and `daisyui-reference`.

No full regression or asset rebuild was required: the new work is validation, test fixtures, documentation, and an artifact probe. It does not alter the shipped browser runtime, a pack template, static assets, or generated asset inputs. Phase 4 and Phase 5's accepted broader manual-static, Vite, application, and canonical-regression evidence remains the applicable compatibility baseline.

The compatible default DaisyUI selection and presentation remain unchanged. Phase 6 exposes no new in-application control for users to try; its browser value is that the existing high-value Book flows now have one reusable default/reference regression matrix. Phase 7 may add Bootstrap only by satisfying these established gates.
