# DaisyUI Comparison Screenshot Manifest

## Capture Boundary

These images are the default DaisyUI counterparts to the eight Phase 7.7 Bootstrap engineering-review images. They are targeted comparison evidence, not visual-regression baselines or pixel-diff fixtures. Each image is a viewport screenshot, not a full-page screenshot, and uses a `daisyui-` filename corresponding to its Bootstrap counterpart in the parent evidence directory.

The seven development-data captures used the ordinary DaisyUI sample at:

```text
http://127.0.0.1:8001/sample/bigbook/
```

The server was started from the repository root with:

```bash
./runproj exec "cd src && ./manage.py runserver 0.0.0.0:8001"
```

The corresponding Bootstrap source used `config.settings_bootstrap` on the Vite-backed sample at port 8001; the DaisyUI counterparts use the unchanged `config.settings` default. All seven replacement captures, plus the preserved bulk-modal capture, use the installed Windows Google Chrome 150 browser through its Chrome DevTools Protocol endpoint, with device scale factor 1. The six ordinary development-data captures use the default server on port 8001. The native-form capture uses a temporary isolated `tests.settings` live-server bridge with `BookCRUDView.use_crispy = False` applied only for that test process. The authenticated captures use the sample runtime login menu and the `sample-manager` role.

For the Windows Chrome captures, Chrome was launched from Windows PowerShell with:

```powershell
& "$env:ProgramFiles\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="$env:TEMP\powercrud-chrome-debug"
```

Automation connected to port 9222 from Windows Node, created a fresh isolated browser context and tab for each state, reproduced the asserted interaction state, and used `Page.captureScreenshot`. The temporary capture helper and native live-server bridge were removed after the images were generated.

The native-form capture uses the isolated pytest database and an explicit temporary `BookCRUDView.use_crispy = False` override. The temporary capture test was run with:

```bash
./runproj exec "cd src && PHASE78_NATIVE_URL_PATH=/home/devuser/django_powercrud/.phase78-native-url PHASE78_NATIVE_OUTPUT_PATH=/home/devuser/django_powercrud/docs/_plans/template_packs/phase7_bootstrap_pack/evidence/daisyui/daisyui-native-validation-modal.png DJANGO_SETTINGS_MODULE=tests.settings pytest -s -m playwright --liveserver=0.0.0.0:8001 tests/playwright/test_phase7_8_capture_native.py"
```

That capture-only test was removed after the image was generated. It set `form.noValidate = true` before submitting the empty form so server-side bound validation, rather than browser-native validation, was captured.

## Screenshot Matrix

| Bootstrap source | DaisyUI capture | Settings and data | Viewport | Reproduction steps and capture assertions |
| --- | --- | --- | --- | --- |
| [`bootstrap-list-controls-desktop.png`](../bootstrap-list-controls-desktop.png) | [`daisyui-list-controls-desktop.png`](daisyui-list-controls-desktop.png) | `config.settings`; anonymous; existing development sample database | 1280×720 | Open `/sample/bigbook/`; wait for `networkidle`; assert the list table and collapsed feature-help summary are visible; capture the viewport without scrolling. |
| [`bootstrap-list-responsive-narrow.png`](../bootstrap-list-responsive-narrow.png) | [`daisyui-list-responsive-narrow.png`](daisyui-list-responsive-narrow.png) | `config.settings`; anonymous; existing development sample database | 640×720 | Open `/sample/bigbook/`; wait for `networkidle`; assert the list table is visible at the narrow viewport; capture the viewport without scrolling. |
| [`bootstrap-row-actions-dropdown-desktop.png`](../bootstrap-row-actions-dropdown-desktop.png) | [`daisyui-row-actions-dropdown-desktop.png`](daisyui-row-actions-dropdown-desktop.png) | `config.settings`; `sample-manager`; existing development sample database | 1280×900 | Log in through the runtime `Login` summary as manager; wait for the list; set `.table-max-height.scrollLeft = scrollWidth`; click the first `[data-powercrud-row-actions-trigger='true']`; assert one visible `[data-powercrud-row-actions-floating-panel='true']` containing `Normal Edit`; capture the viewport. |
| [`bootstrap-native-validation-modal.png`](../bootstrap-native-validation-modal.png) | [`daisyui-native-validation-modal.png`](daisyui-native-validation-modal.png) | `tests.settings`; `sample-manager`; isolated pytest database with fixture books; `BookCRUDView.use_crispy = False` only for capture | 1280×720 | Open `/sample/bigbook/`; log in as manager; open `Create book`; set the object form `noValidate` property; submit empty; assert the modal and `This field is required` feedback; capture the viewport. |
| [`bootstrap-crispy-validation-modal.png`](../bootstrap-crispy-validation-modal.png) | [`daisyui-crispy-validation-modal.png`](daisyui-crispy-validation-modal.png) | `config.settings`; `sample-manager`; existing development sample database; normal crispy default | 1280×900 | Log in as manager; open `Create book`; set the object form `noValidate` property; submit empty; assert the modal and `This field is required` feedback; capture the viewport at the resulting validation scroll position. |
| [`bootstrap-bulk-modal.png`](../bootstrap-bulk-modal.png) | [`daisyui-bulk-modal.png`](daisyui-bulk-modal.png) | `config.settings`; `sample-manager`; existing development sample database; Windows Google Chrome 150 via CDP | 1280×900 | Log in as manager; select the first `input.row-select-checkbox`; assert `#selected-items-counter` is `1`; click the visible `Bulk Edit 1` action in `#bulk-actions-container`; assert `#powercrudBaseModal[open]` is visible and contains `Bulk Edit 1 books`; capture the viewport. |
| [`bootstrap-inline-validation.png`](../bootstrap-inline-validation.png) | [`daisyui-inline-validation.png`](daisyui-inline-validation.png) | `config.settings`; `sample-manager`; existing development sample database | 1280×900 | Log in as manager; assert the inline-enabled table; open the first row's title trigger; clear `input[name='title']`; click `[data-inline-save]`; assert the inline validation popover contains `This field is required`; capture the viewport. |
| [`bootstrap-delete-confirmation-modal.png`](../bootstrap-delete-confirmation-modal.png) | [`daisyui-delete-confirmation-modal.png`](daisyui-delete-confirmation-modal.png) | `config.settings`; `sample-manager`; existing development sample database | 1280×900 | Log in as manager; locate the first table row's `Delete` link; click it; assert `#powercrudBaseModal` is visible and contains the first book title; capture the viewport without submitting the destructive action. |

## Validation

- The directory contains exactly these eight PNG files and this manifest.
- Each DaisyUI filename has a corresponding Bootstrap source with the same semantic suffix in the parent evidence directory.
- PNG dimensions are `1280×720` for the desktop list and native validation captures, `640×720` for the narrow list, and `1280×900` for the remaining five states.
- Every generated image was checked for the intended route, authentication state, interaction state, visible validation/modal/menu state, viewport, and capture boundary.
- No Bootstrap evidence, application code, settings, assets, or runtime behaviour was changed by this capture slice.
