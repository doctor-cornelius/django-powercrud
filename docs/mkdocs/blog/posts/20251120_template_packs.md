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

1. **Define a rendering contract**

   * required templates & partials
   * required block names
   * required context variables

2. **Separate Core Assets vs Adapter Assets**

   * core framework-agnostic JS and optional CSS
   * pack-specific adapter JS/CSS located inside each pack
   * replace direct JS calls with custom events + pack listeners

3. **Refactor DaisyUI into the first pack**

   * extract embedded JS into adapter and core
   * extract embedded CSS if any
   * enforce contract conformance through tests

4. **Add pack discovery + selection**

   * setting similar to `CRISPY_TEMPLATE_PACK`

5. **Pack conformance tests**

   * ensure required templates/blocks exist
   * example CRUD rendering as smoke tests

## **High-Level Task List**

1. Audit current templates, JS, CSS → produce inventory map
2. Identify invariant template structure and context contract
3. Define template-pack contract document
4. Build core JS/CSS bundle and event adapter pattern
5. Extract pack-specific JS/CSS from DaisyUI templates
6. Convert DaisyUI into the reference pack following the contract
7. Introduce `POWERCRUD_TEMPLATE_PACK` setting + loader mechanism
8. Build pack compliance tests and CI enforcement
9. Create minimal demonstration second pack (e.g., plain Tailwind) to validate design
10. Publish cookbook guide

