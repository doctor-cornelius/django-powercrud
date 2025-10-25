---
date: 2025-10-25
categories:
  - docs
---
# ✅ Refactoring the Docs

The docs were built up feature by feature and need a rewrite to be more helpful.
<!-- more -->

## Objectives

- Restructure the docs so the primary navigation follows the adoption flow (setup → bulk editing → async → styling) rather than a loose collection of feature pages.
- Keep a separate, reliable reference area for commands/settings so returning users can jump straight to lookups.
- Eliminate duplicated or outdated content (especially around async and styling) by folding it into the new guide chapters or consolidating it in reference pages.
- Provide a consistent tone and “next step” guidance on every page so readers always know where to go next.

## Approach

1. **Guided path first.** After “Getting Started”, the main navigation should list the practical topics in the order people typically need them:
   - 01 Setup & Core CRUD basics
   - 02 Bulk editing (synchronous)
   - 03 Bulk editing (async)
   - 04 Async manager (outside PowerCRUD)
   - 05 Async dashboard add-on
   - 06 Styling & Tailwind
   - 07 Customisation tips (optional)

   Each guide page will open with the outcome, list the prerequisites, walk through the steps, and end with a link to the next guide.

2. **Reference stays separate.** Commands, settings, template hooks, and API snippets remain under `reference/`, but we ensure every important lookup (e.g., `pcrud_cleanup_async`, `POWERCRUD_SETTINGS`) is documented there once, not sprinkled across guides.

3. **Landing pages funnel into the numbered topics.** `index.md` introduces the value and points to “01 Setup & Core CRUD basics”; `getting_started.md` covers installation & prerequisites and then hands readers straight into that chapter.

4. **Blog remains historical context**—optional reading linked where helpful but not part of the primary navigation.

## Plan

### ✅ Step 1 · Establish the guide skeleton

- Restructure navigation in `mkdocs.yml` so the sidebar lists “Getting Started” followed by the seven practical topics above.
- Update `index.md` and `getting_started.md` to point directly into “01 Setup & Core CRUD basics” as the next step.
- Create placeholder files (or rename existing ones) for each numbered topic so we can migrate content in later steps.

| Guide | Outcome | Sources to reuse |
|-------|---------|------------------|
| 01 Setup & Core CRUD basics | PowerCRUD installed, first view wired up. | `getting_started.md`, portions of `core_config.md`, `filtering.md`, `htmx_modals.md`, `pagination.md`. |
| 02 Bulk editing (synchronous) | Synchronous bulk edit/delete & template tweaks. | `bulk_operations.md` (synchronous sections), template notes from reference. |
| 03 Async manager (outside PowerCRUD) | Using `AsyncManager` + mixins in custom code. | Standalone helper sections from `async_processing.md`, sample snippets/tests. |
| 04 Bulk editing (async) | Async queueing, locks, progress polling. | PowerCRUD-specific sections of `async_processing.md`, cleanup command reference. |
| 05 Async dashboard add-on | Lifecycle hooks + dashboard manager configuration. | Dashboard portions of `async_processing.md`, sample app notes. |
| 06 Styling & Tailwind | CSS frameworks, safelist generation. | `styling.md`, Tailwind command docs. |
| 07 Customisation tips (optional) | Template copying, extending mixins. | Misc tips from existing pages or new content. |

### ✅ Step 2 · Rewrite guide content

- For each chapter:
  - Pull relevant sections from the existing configuration pages.
  - Trim detail that belongs in reference (e.g., full command options, exhaustive settings tables).
  - Add cross-links (“Next → 02 Bulk editing (synchronous)”, etc.) plus back-links to reference where readers can dig deeper.
  - Remove the old standalone configuration page once its content is migrated.

### ✅ Step 3 · Complete the reference shelf

- Expand `reference/mgmt_commands.md` to include `pcrud_cleanup_async` (usage, options, JSON output) and review other entries.
- Create or update a `reference/settings.md` (or similar) so all `POWERCRUD_SETTINGS` are described in one place.
- If needed, add `reference/templates.md`/`reference/hooks.md` to document customisation points.

### ✅ Step 4 · Navigation & tone pass

- Ensure every guide and reference page has consistent headings, intro summaries, and “Next steps”.
- Remove redundant warnings (e.g., duplicated Bootstrap caveats) as they are consolidated into the appropriate guide.
- Ensure consistent tone, etc
- Update `mkdocs.yml` to expose the new hierarchy clearly: Guides → Reference → Blog.

### ✅ Step 5 · Clean-up & validation

- Identify and list obsolete files that became fully subsumed by the new guides (DO NOT DELETE THEM YET) .
- Run `mkdocs serve` locally to verify navigation, links, and formatting.
- Update this blog post to reflect/ summarise the key changes made. 

---

## Progress snapshot

- Guides rebuilt around an adoption flow (setup → bulk sync → async manager → async bulk → dashboard → styling → customisation) with “Key options” tables in each.
- Async docs consolidated: `reference/async.md` now holds the architecture/deep-dive material, while config references point to the new guide sections.
- Navigation clarified via `.pages`; homepage/getting-started funnel into Section 01 directly.
- Management commands and settings references updated (async cleanup behaviour, cache/TTL options, etc.).


