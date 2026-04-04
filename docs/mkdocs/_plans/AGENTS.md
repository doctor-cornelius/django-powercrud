# Temporary Plan Documents (`docs/mkdocs/plans`)

This folder exists to capture in-flight engineering work in a way that is:

- easy to collaborate on while requirements are moving
- easy to hand over to another developer later
- safe to delete/archive once the “stable truth” is promoted into `docs/mkdocs/dev/`

These pages are intended for the MkDocs dev server (developer convenience) and are not meant to ship as the “official docs”.

## Core rules (for AI assistants)

- Treat `docs/mkdocs/dev/` as the long-lived documentation source of truth.
- Treat `docs/mkdocs/plans/` as temporary and allowed to be messy, but still readable.
- Do not delete historical material unless the user explicitly asks.
- Do not edit anything under `docs/mkdocs/plans/_archive/` unless explicitly asked.

## Where plans belong

- Active/current plans live under `docs/mkdocs/plans/<feature>/`.
- Future plans live under `docs/mkdocs/plans/future/<feature>/`.
- Completed/old plans are archived under `docs/mkdocs/plans/_archive/_oldplans/`.

## File naming conventions

Each feature folder should contain:

- `<feature>-plan.md`
- `<feature>-notes.md`

Optional (only when needed):

- `<feature>-adr-draft.md` (temporary; later moved into `docs/mkdocs/dev/decisions/` if it becomes a real ADR)

## What goes in each file

`<feature>-plan.md`:

- phased tasks with checkboxes
- clear “Status” and “Next” sections
- tasks phrased as testable outcomes (what “done” looks like)

Follow the layout with checkboxes for tasks and emoji checkbox for phases similar to below:

```
## ✅ Phase A: Establish the First Proof Path

1. [x] Lock the MVP rules that the first implementation will follow.
    - [x] Keep local `attention_codes` row-local and code-owned.
    - [x] Keep soft workflow concerns as summary or review flags.
    - [x] Persist only hard blockers as blocker rows in `4.1`.
2. [x] Lock the first naming and model decisions needed before code changes.
    - [x] Choose the blocker model name as `BlockingIssue`.
    - [x] Choose the blocker type model name as `BlockingIssueType`.
    - [x] Confirm the first `DDMAction` summary fields to support in code.
```

`<feature>-notes.md`:

- discovery notes, constraints, links, open questions
- decisions made and why (in plain English)
- the minimum detail needed to later promote stable content into `docs/mkdocs/dev/`

## Navigation (`mkdocs-awesome-nav`)

Every feature folder should have a `.nav.yml` which gives short labels in the nav:

```yaml
title: "Feature Name"
nav:
  - Plan: <feature>-plan.md
  - Notes: <feature>-notes.md
```

Also ensure `docs/mkdocs/plans/.nav.yml` includes the feature folder so it appears in the dev server nav.

## Promotion workflow (what “finished” means)

When a plan is complete enough that it should become permanent documentation:

1. Promote the distilled “stable truth” into `docs/mkdocs/dev/` (architecture/patterns/integrations/decisions).
2. Keep the feature plan/notes for context until the user chooses to archive it.
3. Archive old plans into `docs/mkdocs/plans/_archive/_oldplans/` when they are no longer active.

## Markdown formatting rules (Material for MkDocs)

When editing any `*.md` under `docs/mkdocs/`:

- Top-level lists must start with no indentation.
- If indentation is required, use 4 spaces (not 2).
- Ensure a blank line before starting any list or fenced code block.
