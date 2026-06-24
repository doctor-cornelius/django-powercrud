# Temporary Plan Documents (`docs/_plans`)

This folder exists to capture in-flight engineering work in a way that is:

- easy to collaborate on while requirements are moving
- easy to hand over to another developer later
- safe to delete/archive once the stable truth is promoted into `docs/mkdocs/`

These pages are temporary planning pages. They are internal engineering notes only. They are not part of the MkDocs documentation tree and are not published by the docs site.

## Core rules (for AI assistants)

- Treat `docs/mkdocs/` as the long-lived documentation source of truth.
- Treat `docs/_plans/` as temporary and allowed to be messier, but still readable.
- Do not delete historical material unless the user explicitly asks.
- Do not edit anything under `docs/_plans/_archive/` unless explicitly asked.

## Where plans belong

- Active/current plans live under `docs/_plans/<feature>/`.
- Completed/old plans are archived under `docs/_plans/_archive/`.

## Master plan versus feature plans

This repo has no default master plan for `docs/_plans/`. Do not create a root master plan folder or file unless the user explicitly asks for one.

A master plan is a different kind of document from the feature plans. Only create or use a feature-local master plan when the user explicitly asks for one or an existing feature folder already has that structure. A feature-local master plan may live under a feature folder, for example:

```text
docs/_plans/<feature>/
├── master/
├── <plan-1>/
└── <plan-2>/
```

Do not automatically create a `master/`, `plan1/`, `plan2/`, or similar child-folder structure merely because the user asks for a feature-local master plan. Follow the exact structure the user requests, or ask if the structure is not clear.

When a master plan exists, keep it as a terse roadmap. Use one short line per phase or subphase so the whole project shape remains scannable. Do not add nested implementation checklists, design rationale, deferred-register details, or evidence lists to the master plan. Put that detail in the relevant feature plan, feature notes, or master notes file.

Good master-plan shape:

```md
### Phase 5: Workflow Spine MVP

- [x] Phase 5.1 Implement case creation, case triage, and truthful submission to `AwaitingApproval`.
- [x] Phase 5.2 Implement approval outcomes and post-approval DDMS workflow truth.
- [x] Phase 5.3 Implement execution preparation, Uptick reflection, and first reflected-state observation recording for the narrow happy path.
- [ ] Phase 5.4 Implement first non-Uptick execution entry semantics after the first Uptick monitoring path is settled.
- [x] Phase 5.5 Implement monitoring and recommendation layer for the same happy path.
- [ ] Phase 5.6 Prepare senior-management demo checkpoint before resuming deeper workflow automation.
- [ ] Phase 5.7 Implement business-confirmed status propagation and closure/write-back automation.
```

Do not expand those master entries like this:

```md
- [x] Phase 5.5 Implement monitoring and recommendation layer for the same happy path.
    - [x] Record Analytics and Uptick observations without broad canonical workflow mutation.
    - [x] Surface status tension and recommendation categories through attention codes, positive health flags, filters, and workflow timeline events.
    - [x] Defer DDMS-local closure automation and external write-back until business confirmation.
```

Those bullets belong in the relevant feature plan, feature notes, or master notes file, not in the master roadmap.

## File naming conventions

Each feature folder should contain:

- `<feature>-plan.md`
- `<feature>-notes.md`

Optional, only when needed:

- `<feature>-adr-draft.md` (temporary; later moved into the stable decisions/docs area if it becomes a real ADR)

## What goes in each file

`<feature>-plan.md`:

- phased tasks with checkboxes
- clear `Status` and `Next` sections
- tasks phrased as testable outcomes (what "done" looks like)

Follow a checkbox-oriented layout with explicit phases, for example:

```md
## ✅ Phase A: Establish the First Proof Path

1. [x] Lock the MVP rules that the first implementation will follow.
    1. [x] Keep local `attention_codes` row-local and code-owned.
    2. [x] Keep soft workflow concerns as summary or review flags.
    3. [x] Persist only hard blockers as blocker rows in `4.1`.
2. [x] Lock the first naming and model decisions needed before code changes.
    1. [x] Choose the blocker model name as `BlockingIssue`.
    2. [x] Choose the blocker type model name as `BlockingIssueType`.
    3. [x] Confirm the first `DDMAction` summary fields to support in code.
```

`<feature>-notes.md`:

- discovery notes, constraints, links, open questions
- decisions made and why, in plain English
- the minimum detail needed to later promote stable content into `docs/mkdocs/`

When a feature plan needs both a succinct checklist and room for working detail, keep `<feature>-plan.md` terse and put the detail in `<feature>-notes.md` under a `## Plan Phases` section.

In that case:

- create matching `### Phase ...` headers in the notes for each plan phase
- keep the plan as checkbox tasks and subtasks only
- put rationale, evidence, phase-specific notes, deferred debate, and implementation discussion under the matching notes phase header
- do not expand the plan with long explanatory paragraphs when matching notes phase headers exist

## Navigation (`mkdocs-awesome-nav`)

Do not create or maintain `.nav.yml` files for `docs/_plans/`.

Planning documents are outside the MkDocs `docs_dir`, so MkDocs navigation files are not needed for active plans or archived plans.

## Promotion workflow (what "finished" means)

When a plan is complete enough to become permanent documentation:

1. Promote the distilled stable content into `docs/mkdocs/`.
2. Keep the plan and notes for context until the user chooses to archive them.
3. Archive old plans into `docs/_plans/_archive/` when they are no longer active.

## Markdown formatting rules

When editing any `*.md` under `docs/mkdocs/` or `docs/_plans/`:

- Top-level lists must start with no indentation.
- If indentation is required, use 4 spaces, not 2.
- Ensure a blank line before starting any list or fenced code block.
