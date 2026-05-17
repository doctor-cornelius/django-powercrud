# Phase 5 Handover: Cross-Control Coupling Cleanup

## Current State

Branch: `js_cleanup/phase_5`

Phase 5 is complete:

1. Current list-view state now has narrow helpers for query capture, stored optional filters, reset-view clearing, and reset-filter orchestration.
2. Saved-favourite selected and dirty state now has a favourite-owned helper boundary.
3. Visible-column state and reset-view coordination now have list-column-owned helpers.
4. Bulk-selection state now has bulk-owned helpers for selection controls, checked ids, mass checking, presentation sync, clearing, persistence, and hydration.
5. Inline-row state now has inline-owned helpers for pending focus/highlight capture, locked width state, active form-row activation, and layout cleanup.
6. No broad state-management abstraction was introduced.

The agreed packaging decision remains active. Bundled/Vite users continue to use the manifest. Manual users keep the stable entry path and must use `type="module"`:

```html
<script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>
```

## Required Reading

Read these files before planning the next slice:

1. `AGENTS/AGENTS.md`
2. `AGENTS/AGENTS_planning.md`
3. `docs/_plans/js_cleanup/js_cleanup-plan.md`
4. `docs/_plans/js_cleanup/js_cleanup-notes.md`
5. `docs/_plans/js_cleanup/phase5-plan.md`
6. `docs/_plans/js_cleanup/phase5-handover.md`
7. `docs/_plans/js_cleanup/phase6-plan.md`
8. `docs/_plans/js_cleanup/powercrud-js-behaviour-inventory.md`
9. `docs/_plans/js_cleanup/powercrud-js-contract-map.md`
10. `docs/_plans/js_cleanup/powercrud-js-listeners-and-dependencies.md`
11. `docs/_plans/js_cleanup/powercrud-js-test-coverage-map.md`
12. `docs/_plans/template_packs/template_packs-plan.md` and `docs/_plans/template_packs/template_packs-notes.md`

Every read-only planning sub-agent must read all JS cleanup audit files, not just the main plan and notes.

## Next Phase

Start Phase 6: prove the future template-pack boundary.

Phase 6 should begin with a renewed core-versus-current-template-versus-presentation-library boundary review against the current post-Phase-5 runtime. Do not create `powercrud_daisyui`, separate pack JavaScript, or `initPowercrudPack(fragment)` until the shared-versus-pack boundary is proven and the template-pack plan is updated.

Likely Phase 6 starting questions:

1. Which `data-*` contracts are neutral shared PowerCRUD runtime contracts?
2. Which behaviours can later move to DaisyUI pack JavaScript without moving shared semantics?
3. Which boundary behaviours need a neutral core event or a pack hook?
4. What needs to be reflected in `docs/_plans/template_packs/` before implementation starts?

## Orchestration Protocol

Proceed one slice at a time:

1. Brief one read-only sub-agent to plan that slice only.
2. The sub-agent must read all required JS cleanup plan and audit files.
3. The sub-agent must not edit files.
4. Review the slice plan before editing.
5. Implement only the accepted slice.
6. Run focused tests for the touched behaviour area.
7. Run broader browser coverage when a change touches shared startup, lifecycle, module imports, or cross-feature state.
8. Update `js_cleanup-plan.md`, `js_cleanup-notes.md`, and the active handover when phase state changes.
9. Commit and push that slice before moving on.

If a test failure exposes ambiguous intended behaviour, stop and report before broadening scope.

## Compatibility And Non-Goals

Keep these contracts stable:

1. Public entry path: `powercrud/js/powercrud.js`
2. Manual loading form: `<script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>`
3. Bundled/Vite manifest entry: `config/static/js/main.js`
4. Existing public globals, including `window.initPowercrud`, searchable-select helpers, tooltip helpers, and `getCurrentFilters`
5. Existing `data-powercrud-*` and `data-inline-*` contracts unless Michael explicitly approves a contract change
6. Existing HTMX event names and body custom events

Michael owns changelog updates. Do not edit `CHANGELOG.md`.

## Briefing Instruction

At the end of the briefing, tell Michael what you learned in a succinct summary and stand by for his instructions.
