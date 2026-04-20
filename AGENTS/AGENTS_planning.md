# Planning Documents (`docs/_plans`)

This guidance applies when working on temporary engineering plan documents under `docs/_plans/`.

This area exists to capture in-flight engineering work in a way that is:

- easy to collaborate on while requirements are moving
- easy to hand over to another developer later
- safe to delete/archive once the stable truth is promoted into `docs/mkdocs/`

These pages are intended for the MkDocs dev server and internal collaboration. They are not the official long-lived documentation set.

## Core rules

- Treat `docs/mkdocs/` as the long-lived documentation source of truth.
- Treat `docs/_plans/` as temporary and allowed to be messier, but still readable.
- Do not delete historical material unless the user explicitly asks.
- Do not edit anything under `docs/_plans/_archive/` unless explicitly asked.

## Where plans belong

- Active/current plans live under `docs/_plans/<feature>/`.
- Completed/old plans are archived under `docs/_plans/_archive/`.

## File naming conventions

Each feature folder should contain:

- `<feature>-plan.md`
- `<feature>-notes.md`

Optional, only when needed:

- `<feature>-adr-draft.md`

## What goes in each file

`<feature>-plan.md`:

- phased tasks with checkboxes
- clear `Status` and `Next` sections
- tasks phrased as testable outcomes

Follow a checkbox-oriented layout with explicit phases, for example:

```md
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

- discovery notes
- constraints
- links
- open questions
- decisions made and why, in plain English
- the minimum detail needed to later promote stable content into `docs/mkdocs/`

## Navigation

Every feature folder should have a `.nav.yml` with short labels in the nav:

```yaml
title: "Feature Name"
nav:
  - Plan: <feature>-plan.md
  - Notes: <feature>-notes.md
```

Also ensure `docs/_plans/.nav.yml` includes the feature folder so it appears in the dev server nav.

## Promotion workflow

When a plan is complete enough to become permanent documentation:

1. Promote the distilled stable content into `docs/mkdocs/`.
2. Keep the plan and notes for context until the user chooses to archive them.
3. Archive old plans into `docs/_plans/_archive/` when they are no longer active.

## Markdown formatting rules

When editing any `*.md` under `docs/mkdocs/` or `docs/_plans/`:

- Top-level lists must start with no indentation.
- If indentation is required, use 4 spaces, not 2.
- Ensure a blank line before starting any list or fenced code block.
