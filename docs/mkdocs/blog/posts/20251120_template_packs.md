---
date: 2025-11-20
categories:
  - styling
  - templates
  - enhancement
---
# Plan for Modular Template Packs

<!-- more -->

## **Objective**

Enable PowerCRUD to support multiple frontend presentation layers (DaisyUI, Tailwind-base, Bootstrap, Bulma, etc.) by introducing a **modular template-pack architecture**. The goal is to decouple PowerCRUD’s functional logic from its visual layer so that projects can adopt any CSS framework without rewriting PowerCRUD internals.

## **Risk and Worth**

It is a substantial refactor with real complexity and risk. The payoff depends on whether:

* PowerCRUD aspires to be a widely adopted enabling framework
* Third-party adoption and community contribution is a goal
* Long-term maintainability and clean architecture matter

If the intent for PowerCRUD is:

* general-purpose OSS library with real extensibility value
* showcase engineering quality for credibility and adoption
* enable plug-and-play customization

Then it **is** worth the effort.

The key to making it safe is the sequence:
**contract → extract JS → extract CSS → refactor DaisyUI → add tests → only then build new packs**


## **Reason for Template Packs**

The current implementation embeds DaisyUI-specific HTML, CSS, and JavaScript directly inside core templates (e.g., `object_list.html`). This creates tight coupling that prevents:

* switching UI frameworks
* supporting different styling variants
* enabling community-authored packs
* controlling regression risk during visual changes
* maintaining clean separation between UX details and core behaviors

A template-pack system allows PowerCRUD to:

* standardize rendering through a stable contract of template names, partials, block definitions, and context variables
* isolate pack-specific CSS/JS
* minimize maintenance surface area
* offer future extensibility with lower risk

## **Framework Approach**

At a high level, the work breaks down into:

* defining a clear contract for templates and JavaScript
* splitting shared “core” behavior from per-template-pack behavior
* turning the existing DaisyUI implementation into the first pack
* adding a clean way to select packs and test them

The list below is the concrete checklist we will actually follow.

## **High-Level Task List**

1. [X] Define template + JavaScript contract  
    
    - [X] 1.1 Inventory existing templates (list, form, modal, partials), context variables, HTMX snippets, and how `partialdef` / inline partials are used today.  
    - [X] 1.2 Critically review the current template architecture: inline `partialdef` vs separate partial files with `{% include %}`, how filters and other sub-components are structured, and how easy this is for future template-pack authors to understand.  
    - [X] 1.3 Evaluate `HtmxMixin.get_framework_styles` and consider strategy for template-pack modularisation.  
    - [X] 1.4 Decide on the standard structure for template packs: which templates, blocks, and partials must exist, where they live (inline vs separate files), and naming conventions.  
    - [X] 1.5 Specify the JavaScript API: core init (`initPowercrud(fragment)`), pack init (`initPowercrudPack(fragment)`), and any custom events/hooks.  
    - [X] 1.6 Decide template-pack packaging and discovery strategy (where packs live, naming conventions, how core locates templates/styles).  

2. [ ] Implement core vs template-pack JavaScript split  
    
    - [ ] 2.1 Move the existing inline `<script>` from `object_list.html` into `powercrud/static/powercrud/powercrud.js` and expose `window.initPowercrud(fragment)`.  
    - [ ] 2.2 Update the real base template to load `powercrud.js` once using `{% static 'powercrud/powercrud.js' %}`.  
    - [ ] 2.3 Remove inline `<script>` tags from swapped fragments and add `hx-on="htmx:load: initPowercrud(this)"` (or equivalent) on the fragment root.  
    - [ ] 2.4 Extract DaisyUI-specific code from `powercrud.js` into `powercrud_daisyui/static/powercrud_daisyui/daisyui.js` as `window.initPowercrudPack(fragment)`.  
    - [ ] 2.5 Decide whether the fragment calls both initializers (`hx-on="htmx:load: initPowercrud(this); initPowercrudPack(this)"`) or core JS calls `initPowercrudPack` if present.  

3. [ ] Turn DaisyUI into the first template pack  
    
    - [ ] 3.1 Move DaisyUI templates into a `powercrud_daisyui` template namespace.  
    - [ ] 3.2 Update paths and `{% extends %}` / `{% include %}` usage to go through the template-pack contract.  
    - [ ] 3.3 Remove DaisyUI-specific markup from core templates; keep only framework-neutral structure and blocks.  
    - [ ] 3.4 Verify the DaisyUI pack conforms to the contract (templates, blocks, context, JS hooks).  
    - [ ] 3.5 implement refactor of get_framework_styles in line with strategy from 1.3 above.

4. [ ] Add template-pack selection and discovery  
    
    - [ ] 4.1 Introduce a `POWERCRUD_TEMPLATE_PACK` setting, with DaisyUI as the default.  
    - [ ] 4.2 Implement loader helpers that resolve template names and `pack_js_path` based on the selected pack.  
    - [ ] 4.3 Load the active pack JS explicitly in the base template:  
        `<script src="{% static 'powercrud/powercrud.js' %}"></script>`  
        `<script src="{% static pack_js_path %}"></script>`  

5. [ ] Build and extend tests (including Playwright)  
    
    - [ ] 5.1 Add/extend unit tests to check that required templates and blocks exist for each pack.  
    - [ ] 5.2 Add a small Playwright smoke suite per pack (at least CRUD list + form) to verify the JS lifecycle and visual wiring.  
    - [ ] 5.3 Ensure CI runs the core test suite and a minimal Playwright matrix for the default pack.  
    - [ ] 5.4 Implement a `validate_template_pack()` helper (and optional management command) that checks a pack for contract compliance (required templates/partials, `PACK_STYLES` presence, etc.), and wire it into the test suite.  
    - [ ] 5.5 Define and document guidance for template-pack authors on testing: which central PowerCRUD tests they should run to validate their pack, when to use `validate_template_pack()`, and when they should add their own pack-specific tests (e.g. for custom JS or UX behavior).  

6. [ ] Documentation and cookbook  
    
    - [ ] 6.1 Update the PowerCRUD docs to explain template packs, the contract, and how to switch packs.  
    - [ ] 6.2 Write a short “create your own template pack” cookbook, including the JS structure (`powercrud.js` + per-pack JS) and Playwright test patterns.  

7. [ ] Dogfood with a Bootstrap 5 template pack  
    
    - [ ] 7.1 Implement a minimal Bootstrap 5 pack using the same contract as DaisyUI (templates + JS file) to prove the design works beyond DaisyUI.  
    - [ ] 7.2 Fix any issues the Bootstrap pack reveals in the contract (missing hooks, leaky DaisyUI assumptions).  
    - [ ] 7.3 Evolve the Bootstrap 5 pack from “minimal demo” to a production-ready alternative: cover the full CRUD surface (lists, forms, filters, modals, bulk actions, inline editing) with Bootstrap-styled templates.  
    - [ ] 7.4 Add Bootstrap 5 to tests and docs as a concrete, production-quality example of a second pack, and use it in the sample app as a real dogfooding target.  
    - [ ] 7.5 Checkpoint: after completing 7.2, decide whether 7.3–7.4 happen in this refactor phase or are deferred to a follow-up phase (possibly after documentation is in place).  
    - [ ] 7.6 Update or amend the documentation from step 6 based on what we learn building and using the Bootstrap 5 pack (clarify the contract, add gotchas, extend the cookbook with Bootstrap-specific examples).  

## **Template-Pack Contract Working Notes**

This section is a living scratchpad while we work through the tasks above. As we complete 1.x, 2.x, 5.x, and 7.x, we capture the concrete decisions here so we can later fold them into the official docs and cookbook.

### Templates & blocks (per Task 1.1)

- DaisyUI core views:  
    
    - `powercrud/daisyUI/object_list.html`  
        - Partials:  
            - `pcrud_content`  
            - `bulk_selection_status`  
            - `filtered_results`  
            - `pagination`  
    
    - `powercrud/daisyUI/object_form.html`  
        - Partials:  
            - `pcrud_content`  
            - `conflict_detected`  
            - `normal_content`  
    
    - `powercrud/daisyUI/object_detail.html`  
        - Partials:  
            - `pcrud_content`  
    
    - `powercrud/daisyUI/object_confirm_delete.html`  
        - Partials:  
            - `pcrud_content`  
            - `conflict_detected`  
            - `normal_content`  

- Shared partial templates:  
    
    - `powercrud/daisyUI/partial/list.html`  
        - Partials:  
            - `inline_row_display`  
            - `inline_row_form`  
    
    - `powercrud/daisyUI/partial/detail.html`  
        - Behavior:  
            - detail layout partial (no `partialdef` defined inside; used via `{% partial %}` / `{% include %}`)  
    
    - `powercrud/daisyUI/partial/bulk_edit_errors.html`  
        - Partials:  
            - `bulk_edit_error`  
            - `bulk_edit_conflict`  
    
    - `powercrud/daisyUI/crispy_partials.html`  
        - Partials:  
            - `load_tags`  
            - `crispy_form`  
    
    - `powercrud/daisyUI/bulk_edit_form.html`  
        - Partials:  
            - `full_form`  
            - `async_queue_success`  

### Framework styles and `get_framework_styles` (task 1.3)

- How it works today  
    
    - `HtmxMixin.get_framework_styles()` (`src/powercrud/mixins/htmx_mixin.py`) returns a dict keyed by framework name (currently only `'daisyUI'`).  
    - For `'daisyUI'` it provides:  
        - `base`: base CSS class for buttons (e.g. `"btn "`).  
        - `filter_attrs`: widget `attrs` for different field types (`text`, `select`, `multiselect`, `date`, `number`, `time`, `default`) used by `FilteringMixin` when auto-building filter forms.  
        - `actions`: mapping of action names (`"View"`, `"Edit"`, `"Delete"`) to button classes.  
        - `extra_default`: default class for “extra” buttons.  
        - `modal_attrs`: DaisyUI-specific modal trigger markup (`onclick="...showModal()"`) built using `get_modal_id()`.  
    - Call sites:  
        - `FilteringMixin.get_filterset()` (`src/powercrud/mixins/filtering_mixin.py`) pulls `filter_attrs` to choose widget attributes per Django field type.  
        - `action_links` and `extra_buttons` in `src/powercrud/templatetags/powercrud.py` use `base`, `actions`, `extra_default`, and `modal_attrs` to build list-view buttons.  
        - Tests provide small `get_framework_styles()` stubs (e.g. in `test_form_filter_template_mixins.py`, `test_templatetags_powercrud.py`).  

- Issues / limitations  
    
    - Framework-specific and centralised: the DaisyUI configuration lives in a core mixin; adding another pack means overriding `get_framework_styles` or forking the mixin.  
    - Mixed concerns: one dict carries filter widget attrs, button styling, and modal JS behaviour; these evolve at different times and for different reasons.  
    - JS embedded in styles: `modal_attrs` hardcodes DaisyUI’s `showModal()` JS in Python, which is awkward when packs should own their own JS.  
    - Tight coupling to global settings: it assumes a single `POWERCRUD_CSS_FRAMEWORK` rather than per-pack style modules discoverable by name.  
    - Not obviously “pack-local”: there is no clear place for a pack (e.g. `powercrud_bootstrap5`) to ship its own styles; everything routes through the core mixin.  

- Refactoring direction  
    
    - Move style data into pack modules: each template pack will provide a small Python module (e.g. `powercrud_daisyui.styles`) exporting a `PACK_STYLES` dict or similar structure. Core will become a consumer: `HtmxMixin.get_framework_styles()` will delegate to a helper such as `get_pack_styles(active_pack_name)`.  
    - Split concerns inside style data:  
        - `filter_attrs` used by `FilteringMixin` to build filter widgets.  
        - `buttons` for base button class + per-action classes + extra button default.  
        - `modal` describing neutral modal-trigger attributes (e.g. `data-pc-open-modal`) rather than raw JS.  
    - Let pack JS handle modal behaviour: packs will listen for neutral attributes (e.g. `data-pc-open-modal`) in their own JS (`powercrud_daisyui/daisyui.js`, `powercrud_bootstrap5/bs5.js`) and translate that to framework-specific calls (such as DaisyUI’s `showModal()`).  
    - Align with the future widget registry: over time, extend `PACK_STYLES` to include a `widgets` section, as sketched in `20251114_widget_registry.md`, so packs can define per-field/per-context widget templates and classes. `filter_attrs` then becomes part of that wider registry rather than a one-off.  
    - Keep the API simple for pack authors: they provide a Django app with templates, static assets, and a `styles.py` module; PowerCRUD will resolve the active pack name (future `POWERCRUD_TEMPLATE_PACK` setting) and import `pack_name -> styles_module` via a small registry or naming convention.  

### Template structure principles

- One orchestrator template per view  
    
    - Keep a single main template for each CRUD view type (`object_list.html`, `object_form.html`, `object_detail.html`, `object_confirm_delete.html`) that defines the overall layout and calls partials.  
    - View-specific logic that only makes sense in that context can live as inline `partialdef` blocks inside that file.  

- Extract large or reusable partials into dedicated files  
    
    - When a `partialdef` grows large (filters, table rendering, pagination, inline rows, bulk edit forms) or is a natural override point for packs, move its implementation into a separate `partial/*.html` file and have the `partialdef` include it.  
    - Example pattern:  
        `{% partialdef filtered_results %}{% include 'powercrud/daisyUI/partial/list.html' %}{% endpartialdef %}`  

- Prefer separable partials for pack authors  
    
    - Pieces like filter UI, table body, pagination, bulk actions, and inline row templates should each have their own named partial so a pack can override them independently.  
    - The goal is that a pack author can focus on a small set of clearly named templates/partials instead of editing a single huge file.  

- Base template is owned by the project  
    
    - PowerCRUD does **not** provide a full HTML base shell; every project must define its own site base (navigation, `<head>`, assets) and set `base_template_path` on each CRUD view to point at it.  
    - Template packs are responsible only for the inner CRUD templates/partials; they assume the project base template already loads HTMX, JS, and CSS as needed.  

### Template/partial placement plan (Task 1.4)

- This section records, per template, which `partialdef` blocks stay inline vs move into dedicated `partial/*.html` files so packs share a consistent override surface.  

- DaisyUI core views:  
    
    - `powercrud/daisyUI/object_list.html`  
        
        - `pcrud_content` – stays inline; orchestrator wrapper that wires header, filter controls, bulk-selection status, table, pagination, and the modal shell together.  
        - `bulk_selection_status` – move main markup to a dedicated `partial/bulk_actions.html` file; keep this partial as a thin wrapper that `{% include %}`s it so packs can override bulk actions without copying the entire list template.  
        - `filtered_results` – stays inline as a thin wrapper that calls the list/table partial and then `pagination`; no separate file needed.  
        - `pagination` – move pagination markup to `partial/pagination.html`; keep this partial as a thin wrapper include so packs can override pagination independently of the table.  
    
    - `powercrud/daisyUI/object_form.html`  
        
        - `pcrud_content` – stays inline; view-level orchestrator for conflict vs normal form content.  
        - `conflict_detected` – stays inline; small view-specific message, not reused elsewhere.  
        - `normal_content` – stays inline; form layout is inherently view-specific and usually overridden at the whole-template level.  
    
    - `powercrud/daisyUI/object_detail.html`  
        
        - `pcrud_content` – stays inline; simple wrapper around `{% object_detail object view %}` and layout chrome.  
    
    - `powercrud/daisyUI/object_confirm_delete.html`  
        
        - `pcrud_content` – stays inline; orchestrator that chooses between conflict vs normal delete content.  
        - `conflict_detected` – stays inline; small, view-specific banner.  
        - `normal_content` – stays inline; delete-confirmation layout is view-specific and not reused.  

- Shared partial templates:  
    
    - `powercrud/daisyUI/partial/list.html`  
        
        - Main table markup + inline-edit wiring stay in this partial file; it is already the natural override point for list rows.  
        - `inline_row_display` – stays in this file; tightly coupled to the main table markup and header structure.  
        - `inline_row_form` – stays in this file; shares structure and data attributes with the display row and uses the same table skeleton.  
    
    - `powercrud/daisyUI/partial/detail.html`  
        
        - Stays as a single simple partial; no internal `partialdef` blocks, and the detail layout is already neatly isolated.  
    
    - `powercrud/daisyUI/partial/bulk_edit_errors.html`  
        
        - `bulk_edit_error` – stays in this partial file; specific to bulk operations.  
        - `bulk_edit_conflict` – stays in this partial file; specific to bulk operation conflict state.  
    
    - `powercrud/daisyUI/crispy_partials.html`  
        
        - `load_tags` – stays here; tiny and only used by crispy-aware forms.  
        - `crispy_form` – stays here; packs that use crispy can override this partial file as a unit.  
    
    - `powercrud/daisyUI/bulk_edit_form.html`  
        
        - `full_form` – stays inline; this template is itself the orchestrator for the bulk-edit modal, and there is no other caller.  
        - `async_queue_success` – stays inline; conceptually part of the bulk-edit modal flow and only used from this template.  

### Context variables

- List / table (primarily from `object_list.html` + `partial/list.html`):  
    
    - `object_list`, `object_verbose_name`, `object_verbose_name_plural`, `headers`, `row.cells`, `row.actions`, `row.inline_url`, `row.inline_allowed`, `row.inline_blocked_reason`, `row.inline_blocked_label`.  
    - Pagination: `is_paginated`, `paginator`, `page_obj`, `page_size_options`, `default_page_size`.  
    - Selection / bulk edit: `enable_bulk_edit`, `selected_ids`, `selected_count`, `all_selected`, `some_selected`, `list_view_url`, `selection_key_suffix`, `keyBase`.  
    - Filtering/sorting: `filterset`, `filter_params`, `table_max_col_width`, `table_max_height`, `table_pixel_height_other_page_elements`, `table_classes`, `request.GET`.  
    - HTMX wiring: `use_htmx`, `use_modal`, `original_target`, `htmx_target`, `header_title`.  
- Forms / detail / delete:  
    
    - Form views: `form`, `use_crispy`, `use_modal`, `update_view_url`, `create_view_url`, `list_view_url`, `object`, `object_verbose_name`, `conflict_detected`, `conflict_message`, `filter_params`.  
    - Bulk edit: `bulk_fields`, `field_info`, `selected_ids`, `selected_count`, `model_name_plural`, `enable_bulk_delete`, `task_name`, `message`.  

### JavaScript lifecycle & hooks

- Current state (before refactor):  
    
    - Large inline `<script>` in `object_list.html` handles:  
        - Tooltips via `tippy(...)` and `initializeTooltips()`.  
        - Filter form behavior (`resetFilterForm`, `initializeFilterToggle`, `removeEmptyFields`, preservation of `filterExpanded` state via `localStorage`).  
        - Bulk selection and bulk edit events (`toggleAllSelection`, `handleRowSelectionChange`, `clearSelectionOptimistic`, `updateBulkActionsCounter`), using `htmx.ajax` calls to toggle selection and refresh `#bulk-actions-container`.  
        - Global event listeners on `document.body` for `bulkEditSuccess`, `bulkEditQueued`, `refreshTable`, `inline-row-locked`, `inline-row-forbidden`, `inline-row-error`, and several `htmx:*` events (`htmx:beforeRequest`, `htmx:afterRequest`, `htmx:responseError`, `htmx:afterSwap`, `htmx:beforeSwap`).  
        - Inline editing helpers (row locking, width snapshots, focus management, notice banners, dependency endpoints, save/cancel spinners).  
    - Additional inline `<script>` in `bulk_edit_form.html` controls toggling of bulk-edit field inputs and delete confirmation UI.  
- Target state (for contract):  
    
    - Core JS moved into `powercrud/static/powercrud/powercrud.js` with a single entrypoint `initPowercrud(fragment)` wired via HTMX lifecycle (`htmx:load`).  
    - Per-pack JS (e.g. DaisyUI) moved into `powercrud_daisyui/static/powercrud_daisyui/daisyui.js` exposing `initPowercrudPack(fragment)`.  
    - No inline `<script>` blocks inside swapped templates; all behavior initialized through the core/pack initializers and HTMX events.  

- JS API and events (Task 1.5):  
    
    - Core initializer: `initPowercrud(fragment)`  
        
        - Exposed on `window` by `powercrud.js`.  
        - `fragment` is either `document` (for full-page loads) or the root element of an HTMX swap (for partial updates).  
        - May be called multiple times; it must be idempotent for a given fragment and guard any once-per-page wiring with an internal flag.  
        - Must not reset filter values or other user-entered state; it only attaches behaviour based on the current DOM and any stored state.  
        - Responsibilities:  
            - One-time global wiring on `document` / `document.body` (HTMX event listeners, inline-edit helpers, bulk-selection helpers, form spinners).  
            - Per-fragment wiring that searches inside `fragment` for PowerCRUD hooks such as:  
                - `data-powercrud-form="object"` (form submit spinner / error handling).  
                - Inline-editing hooks: `tr[data-inline-row="true"]`, `data-inline-field`, `data-inline-save`, `data-inline-cancel`, `data-inline-dependent-field`, `data-inline-endpoint`.  
                - Bulk-selection hooks: `.row-select-checkbox`, `#select-all-checkbox`, and the bulk-actions container that listens for `bulkSelectionChanged`.  
            - It should rely on data attributes and semantic IDs where possible so packs can restyle markup without changing behaviour.  
    
    - Pack initializer: `initPowercrudPack(fragment)`  
        
        - Exposed on `window` by each pack’s JS (e.g. `powercrud_daisyui/daisyui.js`).  
        - Optional, but recommended for packs that need framework-specific behaviour.  
        - Called with the same `fragment` as `initPowercrud`, after the core initializer has run.  
        - Responsibilities are strictly framework-specific, for example:  
            - Implementing neutral modal triggers (e.g. listening for `data-pc-open-modal` from templates and mapping that to DaisyUI’s `.showModal()` or Bootstrap’s `Modal.show()`).  
            - Attaching framework-specific tooltips or toasts in response to core events (e.g. `inline-row-error`, `bulkEditSuccess`).  
            - Any pack-only UX embellishments that do not change the semantics of core events or data attributes.  
        - Must be safe to call multiple times and should avoid re-registering global listeners without guards.  
    
    - Wiring strategy:  
        
        - Full-page loads: the real project base template includes `powercrud.js` (and the active pack’s JS) and calls `initPowercrud(document)` on `DOMContentLoaded`. If a pack JS file is present and defines `initPowercrudPack`, it is called with `document` immediately after.  
        - HTMX swaps: CRUD fragments use `htmx:load` to initialise JS.  
            - **Preferred**: `powercrud.js` registers a single global `htmx:load` listener and calls `initPowercrud(event.detail.elt)` (and `initPowercrudPack(event.detail.elt)` if present). `initPowercrud` must be cheap and defensive so that when `event.detail.elt` is not a PowerCRUD fragment it quickly returns without doing work.  
            - **Alternative**: templates attach `hx-on="htmx:load: initPowercrud(this); if (window.initPowercrudPack) { initPowercrudPack(this); }"` on the fragment root to opt in explicitly. This keeps the same API but spreads the wiring logic into templates.  
        - The contract for packs is that `initPowercrud` always runs first; packs should not assume they need to rewire or duplicate core behaviours.  
    
    - Events and hooks:  
        
        - HTMX events that core JS listens to on `document.body`:  
            - `htmx:beforeRequest`, `htmx:afterRequest`, `htmx:afterSwap`, `htmx:beforeSwap`, `htmx:responseError`.  
            - These are used for inline-edit guards, table refresh behaviour, form spinners, and error handling.  
        - Custom DOM events fired on `document.body` as part of the PowerCRUD lifecycle:  
            - `bulkEditSuccess` – indicates a bulk operation completed successfully; core currently closes the bulk-edit modal and clears selection, packs may also listen to show notifications.  
            - `bulkEditQueued` – indicates a bulk operation has been queued; packs can use this to show a “queued” message.  
            - `refreshTable` – tells the list view to refresh `#filtered_results` using current filters and sort; packs should not override this behaviour but may listen to react visually.  
            - `inline-row-locked`, `inline-row-forbidden` – guard events raised when inline editing is blocked (e.g. by locks or permissions); detail payload includes at least row identifiers and messages.  
            - `inline-row-error` – indicates an inline save failed; detail payload includes a `row_id` (where possible) and message; core scrolls/focuses the failing row and shows an inline notice.  
            - `bulkSelectionChanged` – logical event that causes the bulk-actions container to re-evaluate visibility and counts (via `hx-trigger="bulkSelectionChanged from:body"`); any JS can trigger it via `htmx.trigger(document.body, 'bulkSelectionChanged', detail)`.  
        - HX-Trigger keys used by the server to coordinate with JS:  
            - Form-related: `formError`, `modalFormSuccess`, `refreshList`, `refreshUrl`.  
            - Bulk-related: `bulkEditSuccess`, `refreshTable` (e.g. from async bulk operations), plus any pack-agnostic triggers added later.  
            - Packs should treat these as high-level signals only and avoid depending on low-level HX header details.  
    
    - Contract for packs consuming the JS API:  
        
        - Packs can assume `initPowercrud` wires all behaviours tied to PowerCRUD’s `data-*` attributes and does not depend on specific CSS classes.  
        - Packs may define `initPowercrudPack` to:  
            - Implement modal opening/closing and other framework-specific UI concerns based on neutral attributes and events.  
            - Listen for the documented custom events (`bulkEditSuccess`, `inline-row-error`, etc.) to show framework-specific notifications or visual feedback.  
        - Packs must not change the semantics of these events (e.g. reusing `bulkEditSuccess` for unrelated purposes), but they are free to add additional pack-specific events under their own names.  

### Testing expectations for packs

- (to be filled from 5.2–5.4 and 7.x)  

### Template-pack packaging & repository strategy (task 1.6 – initial thoughts)

- Where packs live  
    
    - Each template pack is a **Django app**. The canonical naming convention is `powercrud_<packname>` (e.g. `powercrud_daisyui`, `powercrud_bootstrap5`).  
    - Core will treat the DaisyUI pack as a first-class app (e.g. `powercrud_daisyui`) that ships in the same wheel as `powercrud` and is added to `INSTALLED_APPS` alongside it. This is different from the `sample` app, which remains dev-only and is not included in the published package.  
    - Additional “official” packs (e.g. a Bootstrap 5 pack) can also live in this repo as separate Django apps, or in their own repos as pip-installable packages, as long as they follow the same conventions below.  
    - The template-pack loader must not assume packs are co-located with core; as long as the app can be imported and is in `INSTALLED_APPS`, it should be discoverable.  

- Pack app structure (per-pack layout)  
    
    - Every pack app provides, at minimum:  
        - **Templates** under a stable namespace:  
            
            - Orchestrator templates at the root of the namespace:  
                - `powercrud_<packname>/templates/powercrud_<packname>/object_list.html`  
                - `powercrud_<packname>/templates/powercrud_<packname>/object_form.html`  
                - `powercrud_<packname>/templates/powercrud_<packname>/object_detail.html`  
                - `powercrud_<packname>/templates/powercrud_<packname>/object_confirm_delete.html`  
            - Shared partials grouped under a `partial/` folder:  
                - `powercrud_<packname>/templates/powercrud_<packname>/partial/list.html`  
                - `powercrud_<packname>/templates/powercrud_<packname>/partial/detail.html`  
                - `powercrud_<packname>/templates/powercrud_<packname>/partial/bulk_edit_errors.html`  
                - `powercrud_<packname>/templates/powercrud_<packname>/partial/bulk_edit_form.html` (optional wrapper for bulk-edit flows).  
                - `powercrud_<packname>/templates/powercrud_<packname>/partial/crispy_partials.html` (crispy helpers; conceptually a partial even if today’s DaisyUI path is `crispy_partials.html` at the root).  
            - Existing DaisyUI templates will be migrated toward this “orchestrators at root, shared pieces in `partial/`” pattern; when we move files (e.g. `crispy_partials.html`), we will update the corresponding call sites in views/templates at the same time.  
        - **Static assets** in the usual Django layout:  
            
            - `powercrud_<packname>/static/powercrud_<packname>/js/...` (e.g. `daisyui.js` implementing `initPowercrudPack`).  
            - `powercrud_<packname>/static/powercrud_<packname>/css/...` (if the pack ships its own CSS helpers).  
        - A **styles module**:  
            
            - `powercrud_<packname>/styles.py` exporting `PACK_STYLES`, as described in the framework styles section (`filter_attrs`, button styles, modal metadata, and future widget/widget-registry definitions).  
    - DaisyUI’s current templates live under `powercrud/daisyUI/...`; the long-term plan (Task 3.x) is to migrate them into a proper `powercrud_daisyui` app using the structure above. Until then, core will support a legacy path for the built-in pack.  

- Pack selection and discovery  
    
    - Core will use a single setting to choose the active pack, e.g.:  
        
        - `POWERCRUD_TEMPLATE_PACK = "daisyui"` (default) or `"bootstrap5"`, `"mycorp_theme"`, etc.  
    - By convention, a pack name maps to:  
        
        - App label / Python package: `powercrud_<PACK>` (e.g. `"daisyui" -> "powercrud_daisyui"`).  
        - Template prefix: `templates/powercrud_<PACK>/...`.  
        - Styles module: `powercrud_<PACK>.styles` providing `PACK_STYLES`.  
    - Core will provide small helpers (internal API) to resolve the active pack:  
        
        - `get_active_pack()` → `"daisyui"`.  
        - `get_pack_app_label()` → `"powercrud_daisyui"`.  
        - `get_pack_template_prefix()` → `"powercrud_daisyui"`.  
        - `get_pack_styles()` → imports `powercrud_daisyui.styles.PACK_STYLES`.  
    - If a configured pack cannot be imported or is not present in `INSTALLED_APPS`, core should raise a clear `ImproperlyConfigured` error indicating that `POWERCRUD_TEMPLATE_PACK='...'` requires the corresponding app to be installed and added to `INSTALLED_APPS`.  

- Central vs decentralised repos  
    
    - Centralised “official” packs (DaisyUI, Bootstrap 5) living in this repo simplify versioning, documentation, and CI. These packs are shipped in the same PyPI distribution as `powercrud` but remain separate Django apps.  
    - Decentralised third-party packs (separate repos, pip-installable apps) follow the same conventions: they define a Django app with the expected templates, static assets, and `styles.py`, and projects enable them via `INSTALLED_APPS` and `POWERCRUD_TEMPLATE_PACK`.  
    - The loader logic deliberately does not care whether a pack lives in this repo or elsewhere; that distinction is about governance and maintenance, not the technical interface.  

- Compatibility and future widget work  
    
    - In the short term (0.x releases), we are comfortable making breaking changes to template-pack loading, as long as they are clearly documented and users can pin older versions if needed.  
    - When we migrate the built-in DaisyUI templates into `powercrud_daisyui`, we will:  
        
        - Introduce the new pack-loader,  
        - Maintain a compatibility layer for existing `POWERCRUD_CSS_FRAMEWORK` usage where feasible, and  
        - Document the new `POWERCRUD_TEMPLATE_PACK` setting and required `INSTALLED_APPS` entries.  
    - Future widget-registry work (`20251114_widget_registry.md`) will extend `PACK_STYLES` with a `widgets` section but does not change the basic packaging story: widgets remain per-pack configuration within the same `styles.py` file.  

- Integration in downstream projects  
    
    - Projects enable a pack by:  
        - Adding the core app and pack app(s) to `INSTALLED_APPS` (e.g. `["powercrud", "powercrud_daisyui", ...]`).  
        - Setting `POWERCRUD_TEMPLATE_PACK` to the desired pack name (e.g. `"daisyui"`).  
    - The real project base template (owned by the downstream project) is responsible for:  
        - Loading core JS once, e.g. `{% static 'powercrud/powercrud.js' %}`.  
        - Loading the active pack’s JS (and any CSS helpers), e.g. `{% static 'powercrud_daisyui/js/daisyui.js' %}`.  
        - Providing the actual HTML `<head>`, navigation, and global assets; pack templates only render the inner CRUD views/partials.  

- Template-pack validator (contract compliance)  
    
    - Core will provide a small, developer-facing validation API to check that a pack complies with the template/JS/styles contract:  
        - A Python helper such as `validate_template_pack(pack_name="daisyui")` that:  
            - Verifies the pack app (`powercrud_<packname>`) is importable and present in `INSTALLED_APPS`.  
            - Verifies that required templates exist under the expected namespace (orchestrators and key partials like `partial/list.html`, `partial/detail.html`, `partial/bulk_edit_errors.html`, `bulk_edit_form.html`, `crispy_partials.html` / `partial/crispy_partials.html`).  
            - Optionally inspects templates for required `partialdef` names where core depends on them (e.g. `pcrud_content`, `inline_row_display`, `inline_row_form`, `full_form`, `async_queue_success`).  
            - Verifies that `styles.py` exists and exports `PACK_STYLES` with at least the required top-level sections (`filter_attrs`, button styles, modal metadata).  
        - An optional management command wrapper (e.g. `python manage.py validate_powercrud_pack d aisyui`) that projects and CI can run explicitly.  
    - The full validator is intended for development and tests, not as a heavy runtime check:  
        - The pack loader will still perform a lightweight runtime check (import app + styles) and raise `ImproperlyConfigured` if the pack cannot be loaded.  
        - The richer “are all templates and partials present?” checks run via `validate_template_pack()` and are wired into the test plan (Task 5.4) so official packs and community packs can assert contract compliance.  

### **Related Future Work: Pluggable Form Widgets**

This plan focuses on template packs and JavaScript structure. A closely related but separate project will be to make form and inline-form widgets pluggable (for example, the default HTML5 widgets and CSS classes currently configured in `FormMixin.get_form_class()`).

The intent is:

* keep the existing widget behavior stable during this refactor  
* avoid introducing new hard-coded framework-specific classes into core templates or mixins  
* design the template-pack contract so a future “widget policy” (per-pack or per-project) can control widget classes/attributes without breaking the public API  

That future work would likely add a small, overridable hook (e.g. a `get_default_widgets()` / “widget policy” function) that template packs or projects can customize, building on top of the template-pack machinery defined here.  
