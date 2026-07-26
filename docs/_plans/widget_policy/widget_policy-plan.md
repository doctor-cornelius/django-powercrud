# Widget Policy Plan

## Status

- ✅ Create the feature planning folder.
- ✅ Record the agreed scope, ownership boundary, and expected project outcome.
- ✅ Separate the behaviour-preserving widget-policy work from the later visible M2M improvement.
- ✅ Begin Phase 1 only after the plan is approved for implementation.

## Next

1. ✅ Interpret the inventory into stable semantic widget categories and ownership decisions.
2. 🔳 Resolve the recorded runtime ambiguities and capture the current pack behaviour baseline.
3. 🔳 Lock the ownership and precedence rules before Phase 2 architecture work starts.

## Phase 1: Lock the Current Contract and Baseline

1. ✅ Inventory every visible control PowerCRUD or a first-party template pack currently specifies.
2. ✅ Convert the inventory into an agreed semantic and ownership matrix.
3. 🔳 Resolve the inventory's unverified behaviour and capture the current DaisyUI and Bootstrap parity baseline.
4. 🔳 Lock the public widget-policy ownership and precedence contract.

## Phase 2: Introduce the Pack Widget-Policy Architecture

1. 🔳 Add a context-aware widget-policy contract for PowerCRUD-generated controls.
    1. 🔳 Distinguish normal form, inline, filter, and bulk surfaces.
    2. 🔳 Supply semantic field and control information without exposing framework-specific assumptions in core.
2. 🔳 Add neutral resolution and fallback behaviour for packs that do not provide a specialised presentation.
3. 🔳 Keep Django and PowerCRUD responsible for values, choices, querysets, validation, submission semantics, and HTMX lifecycle.
4. 🔳 Keep application-supplied custom forms and their widget choices outside the new policy.
5. 🔳 Ensure the generic layer does not name or depend on DaisyUI, Bootstrap, Tom Select, or another presentation library.

## Phase 3: Migrate DaisyUI and Bootstrap Without Frontend Change

1. 🔳 Move the current DaisyUI widget choices, attributes, rendering decisions, and enhancement requests into the DaisyUI pack policy.
2. 🔳 Move the current Bootstrap widget choices, attributes, rendering decisions, and enhancement requests into the Bootstrap pack policy.
3. 🔳 Remove superseded pack-sensitive widget presentation decisions from generic form, inline, filtering, and bulk code.
4. 🔳 Preserve current native and supported Crispy output for both packs.
5. 🔳 Preserve current searchable-select, dependency refresh, validation, accessibility, and HTMX replacement behaviour.

## Phase 4: Ratify the Behaviour-Preserving Architecture

1. 🔳 Add shared server-side acceptance coverage for all in-scope widget categories and surfaces under both packs.
2. 🔳 Add or update shared browser coverage for presentation and lifecycle parity under both packs.
3. 🔳 Validate the public pack contract, packaged assets, and installed-package behaviour affected by the new policy.
4. 🔳 Update stable template-pack and form-control documentation without claiming a visible feature change.
5. 🔳 Confirm that Phase 1 through Phase 4 produce no intended frontend change.

## Phase 5: Prove the Policy With an Improved Inline M2M Control

1. 🔳 Define the compact inline ManyToMany experience as the first intentional visible widget-policy enhancement.
2. 🔳 Implement the M2M choice through the new pack policy rather than a generic PowerCRUD special case.
3. 🔳 Implement appropriate DaisyUI and Bootstrap presentation and browser behaviour.
4. 🔳 Preserve normal Django multi-value submission, validation, queryset dependency, and HTMX lifecycle behaviour.
5. 🔳 Add focused server and browser coverage under both packs.
6. 🔳 Document the visible M2M improvement and the supported application override boundary.
