# Abstract Surface Plan

## Status

PowerField design is accepted as the next implementation direction, with strict inheritance rules and legacy primitive behaviour preserved.

Fifth slice is complete on `powerfield`: public PowerField guide/reference docs now present PowerField as a core Field Intent helper, linked from concepts, config reference, sample app docs, and the docs home page.

## Next

1. Evaluate one DDMS-style surface as a private downstream proof.

## Phase 1: Config Resolver Standardisation

1. [x] Identify class-time, init-time, and runtime consumers of primitive Field Intent config.
2. [x] Introduce a class-time primitive config snapshot for URL and list-options registration.
3. [x] Extend the normalized primitive config path through instance initialization and runtime helpers.
4. [x] Keep the current primitive-view test suite passing with minimal or no changes.

## Phase 2: PowerField Compiler

1. [x] Add `PowerField` and `PowerOverride` declarations for Field Intent only.
2. [x] Add primitive-extraction helpers and aggregate compiler behaviour.
3. [x] Finalize the narrow declaration semantics before public export.
4. [x] Enforce strict coexistence and inheritance rules.

## Phase 3: Startup Integration And Sample Spike

1. [x] Wire compiled config into URL registration, instance validation, and runtime helpers.
2. [x] Add a PowerField-based Book sample view variant.
3. [x] Add the sample variant to the sample app navigation in a discoverable but non-disruptive way.

## Phase 4: Validation And Edge Cases

1. [x] Cover excludes, overrides, defaults, links, tooltips, properties, and list defaults.
2. [x] Prove PowerField absence semantics do not fall through to legacy primitive defaults.
3. [x] Prove primitive and PowerField inheritance chains cannot mix Field Intent config.
4. [x] Prove the PowerField Book sample resolves to the same primitive Field Intent config as `BookCRUDView`.
5. [x] Prove class-time generated form intent is still available before custom `form_class` runtime handling clears `form_fields`.

## Phase 5: Docs And Reality Check

1. [x] Document primitive API and PowerField side by side.
2. [x] Use the Book sample variant as the public demonstration path.
3. [ ] Evaluate one DDMS-style surface as a private downstream proof.
