# Phase 7.7 Bootstrap Screenshot Manifest

## Capture Boundary

Final Phase 7.8.8 recapture completed on 2026-07-14 from the local Vite-backed Bootstrap sample. Seven ordinary PNGs use `config.settings_bootstrap` at `http://127.0.0.1:8001/sample/bigbook/`; the native-form PNG uses an isolated `tests.settings_bootstrap` bridge at port 8002 with `BookCRUDView.use_crispy = False` applied only to that temporary capture process. All eight current PNGs use the installed Windows Google Chrome 150 browser through its Chrome DevTools Protocol endpoint at port 9222, with device scale factor 1 and the source viewport dimensions. These are targeted engineering-review images, not visual-regression baselines or pixel-diff fixtures.

The ordinary captures used:

```bash
./runproj exec "cd src && ./manage.py runserver --settings=config.settings_bootstrap 0.0.0.0:8001"
```

The native-form capture used a temporary isolated `tests.settings_bootstrap` live-server bridge on `0.0.0.0:8002`, with `BookCRUDView.use_crispy = False` applied only to that capture process. Windows Node created a fresh isolated Chrome target for each state, reproduced the browser assertions, and wrote the viewport through `Page.captureScreenshot`; the temporary helpers and bridge were removed afterward.

The normal sample form uses crispy-bootstrap5. The native-form validation capture used the same Bootstrap test overlay with BookCRUDView.use_crispy temporarily disabled only for that capture; it did not change the sample default.

## Screenshots

1. [Desktop list controls](bootstrap-list-controls-desktop.png) — anonymous list controls, table, and collapsed help.
2. [Narrow responsive list](bootstrap-list-responsive-narrow.png) — 640px list layout and table-local horizontal overflow.
3. [Row-actions dropdown](bootstrap-row-actions-dropdown-desktop.png) — manager row actions detached above the responsive table wrapper.
4. [Native validation modal](bootstrap-native-validation-modal.png) — bound native Django fields and feedback in the Bootstrap modal host.
5. [Crispy validation modal](bootstrap-crispy-validation-modal.png) — bound crispy-bootstrap5 fields and feedback in the Bootstrap modal host.
6. [Bulk modal](bootstrap-bulk-modal.png) — manager bulk-edit presentation after selection.
7. [Inline validation](bootstrap-inline-validation.png) — inline row validation feedback after an invalid save.
8. [Delete confirmation](bootstrap-delete-confirmation-modal.png) — manager modal confirmation before destructive action.

## Inspection Outcome

The review found and corrected three functional presentation defects: legacy DaisyUI modal classes could replace Bootstrap's required dialog, detached Bootstrap dropdowns were present but hidden, and detached panels were positioned from a zero-size hidden box. It also corrected filter action visibility and restored table-local horizontal overflow on narrow screens.

The resulting sample is a conventional Bootstrap functional baseline: tables may scroll horizontally on narrow viewports, menus and dialogs stay in the viewport, and validation remains readable. It intentionally does not attempt the bespoke spacing, density, or visual-identity refinement reserved for Michael's Phase 7.8 review.
