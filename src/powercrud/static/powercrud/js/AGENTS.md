# Agent Instructions

Before editing JavaScript in this folder, read `README.md`.

Changes must preserve the documented runtime architecture unless the task explicitly updates that architecture too.

In particular:

1. Keep `powercrud/js/powercrud.js` as the stable public entry.
2. Preserve `window.initPowercrud(fragment)` and the manual `type="module"` loading contract.
3. Keep shared PowerCRUD semantics separate from current-template and presentation-library adapter behaviour.
4. Do not introduce `initPowercrudPack(fragment)`, separate pack JavaScript, new public static paths, or template-pack loader code unless the active task explicitly approves template-pack extraction work.
5. If changing lifecycle, HTMX, storage, public globals, or `data-powercrud-*` / `data-inline-*` contracts, update `README.md` and run the relevant packaging/browser tests.
