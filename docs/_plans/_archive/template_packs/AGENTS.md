# Template Packs Planning Instructions

These instructions apply to all work under `docs/_plans/template_packs/`.

## Required Briefing

Before advising on or changing this project, read in order:

1. The repository-level `AGENTS.md` and `AGENTS/AGENTS.md`.
2. `AGENTS/AGENTS_planning.md`.
3. `template_packs-master-plan.md`.
4. `template_packs-master-notes.md`.
5. The plan and notes for the active master phase.
6. Any source documents linked by the active phase notes that are relevant to the requested work.

## Authority And Tracking

1. The master plan controls programme scope, order, and master-phase status.
2. Master notes hold cross-cutting rationale, decisions, evidence, dependencies, and phase handovers.
3. Each master phase receives a child plan only when it approaches active work.
4. A child plan controls execution within its master phase but may not silently expand or redefine the master plan.
5. Child notes hold the detailed reasoning and evidence for their child plan.
6. Mark a master phase complete only after its child plan outcomes have been accepted.
7. Do not create plans for distant phases merely to make the tree look complete.

## Plan And Notes Shape

1. Plan files contain only concise status, next action, phases, and nested checkbox tasks.
2. Keep rationale, alternatives, evidence, code examples, inventories, and implementation discussion in the corresponding notes file.
3. After its introductory material, every notes file must contain a `## Plan` section.
4. Under `## Plan`, add one `###` heading for every phase in the corresponding plan, using exactly the same phase title and order.
5. Update a plan and its corresponding notes together whenever phase structure changes.

## Delivery Invariant

This is a long-running background programme. Do not accumulate implementation on a long-lived project branch.

After every implementation merge, `main` must retain a working compatible default DaisyUI experience. Existing supported settings, template paths, stable runtime entry points, and asset-loading modes remain usable unless a complete and tested compatibility transition lands atomically in the same merge.

Use this default sequence:

```text
characterize one behaviour -> implement one bounded slice -> verify compatibility -> merge to main -> begin the next slice from updated main
```

For ordinary slices:

1. Keep the default DaisyUI behaviour automatically selected and wired.
2. Do not require users to adopt unfinished settings, installed apps, template paths, or script entries.
3. Keep new packs and variants opt-in.
4. Add focused characterization before moving behaviour.
5. Run proportionate central and browser regression coverage before merge.

For an unavoidable atomic transition:

1. Name the transition and acceptance gate in the active plan and notes before implementation.
2. Do not merge an intermediate state that breaks legacy resolution or runtime loading.
3. Merge only when compatibility paths, packaging, adapter loading, supported asset modes, and required behaviour pass together.

Default DaisyUI repackaging is the known likely atomic transition. Resolver helpers, tests, and dormant infrastructure may merge earlier, but legacy template paths must not disappear before the compatible default pack is fully packaged and loadable.

## Architectural Boundaries

1. Core JavaScript owns durable PowerCRUD semantics.
2. Framework adapters own reusable presentation-framework behaviour.
3. Optional variant adapters own only interaction behaviour unique to a template variant.
4. Multiple template packs may reuse one framework adapter.
5. Focused downstream template overrides must not require copied PowerCRUD JavaScript.
6. DaisyUI theme and brand configuration are outside this project's scope.
7. The first proof is a structurally different internal DaisyUI variant; Bootstrap is the later optional co-distributed contrib-style, full-parity cross-framework proof, including maintained crispy support.
