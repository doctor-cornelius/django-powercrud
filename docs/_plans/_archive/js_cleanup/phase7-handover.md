# Phase 7 Handover: JavaScript Runtime Closeout

## Current State

Branch: `js_cleanup/phase_7`

JavaScript cleanup Phases 1 through 7 are complete. Phase 7 did not expose public MkDocs content; the durable internal runtime guide lives beside the JavaScript source:

```text
src/powercrud/static/powercrud/js/README.md
```

Current runtime truth:

1. `powercrud/js/powercrud.js` remains the stable public entry.
2. Manual users load it with:

    ```html
    <script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>
    ```

3. Bundled/Vite users continue through `src/config/static/js/main.js`.
4. `window.initPowercrud(fragment)` exists and is the public fragment initializer.
5. `initPowercrudPack(fragment)` remains future.
6. Hook creation remains deferred until template-pack extraction or extraction-prep starts.
7. No `powercrud_daisyui`, separate pack JS, loader code, or new public static paths were created.
8. Michael owns `CHANGELOG.md`.

## What Phase 7 Added

1. `src/powercrud/static/powercrud/js/README.md` documents the internal runtime shape, public contracts, lifecycle ordering, ownership boundaries, and future template-pack boundary.
2. Targeted maintainer comments now mark non-obvious lifecycle, state, and adapter-boundary invariants in the JavaScript runtime.
3. Template-pack planning docs point future extraction work to the JS README and Phase 6 boundary findings.

## Validation

Phase 7 validation passed:

1. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.
2. `./runproj exec --command "./runtests --playwright"` passed, 48 selected tests.
3. `git diff --check` passed.

The backend regression suite was not run because Phase 7 did not change Python, templates, rendered `data-*` attributes, or server-side template contracts.

## Next Work

Actual template-pack extraction remains deferred. The next implementation phase should start with extraction-prep, not by creating a pack app.

Before moving code:

1. Read `src/powercrud/static/powercrud/js/README.md`.
2. Read `docs/_plans/js_cleanup/phase6-boundary-findings.md`.
3. Read `docs/_plans/template_packs/template_packs-plan.md` and `template_packs-notes.md`.
4. Pick one mixed boundary.
5. Add or confirm focused characterization coverage.
6. Design the smallest hook, neutral event, or injected adapter needed for that movement.
7. Preserve the stable public entry and manual module-script contract.
