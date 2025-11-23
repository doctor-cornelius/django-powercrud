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

If PowerCRUD remains a one-client internal tool, this level of abstraction is not worth it.

If the intent is:

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

1. [ ] Define template + JavaScript contract  
   - [ ] 1.1 Inventory existing templates (list, form, modal, partials), context variables, HTMX snippets, and how `partialdef` / inline partials are used today.  
   - [ ] 1.2 Critically review the current template architecture: inline `partialdef` vs separate partial files with `{% include %}`, how filters and other sub-components are structured, and how easy this is for future template-pack authors to understand.  
   - [ ] 1.3 Decide on the standard structure for template packs: which templates, blocks, and partials must exist, where they live (inline vs separate files), and naming conventions.  
   - [ ] 1.4 Specify the JavaScript API: core init (`initPowercrud(fragment)`), pack init (`initPowercrudPack(fragment)`), and any custom events/hooks.  
   - [ ] 1.5 Write this contract and structural guidance up in docs so future packs can follow it.  

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
   - [ ] 5.4 Define and document guidance for template-pack authors on testing: which central PowerCRUD tests they should run to validate their pack, and when they should add their own pack-specific tests (e.g. for custom JS or UX behavior).  

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

### Templates & blocks

- (to be filled from 1.1–1.3 and 3.x)  

### Context variables

- (to be filled from 1.1–1.3 and view mixin analysis)  

### JavaScript lifecycle & hooks

- (to be filled from 1.4, 2.x, and DaisyUI/Bootstrap pack work)  

### Testing expectations for packs

- (to be filled from 5.2–5.4 and 7.x)  

### **Related Future Work: Pluggable Form Widgets**

This plan focuses on template packs and JavaScript structure. A closely related but separate project will be to make form and inline-form widgets pluggable (for example, the default HTML5 widgets and CSS classes currently configured in `FormMixin.get_form_class()`).

The intent is:

* keep the existing widget behavior stable during this refactor  
* avoid introducing new hard-coded framework-specific classes into core templates or mixins  
* design the template-pack contract so a future “widget policy” (per-pack or per-project) can control widget classes/attributes without breaking the public API  

That future work would likely add a small, overridable hook (e.g. a `get_default_widgets()` / “widget policy” function) that template packs or projects can customize, building on top of the template-pack machinery defined here.  
