# Agent Instructions

## Command execution policy

Never run shell commands in this repo except when strictly required to:

- Read/list files for context (e.g. `sed`, `cat`, `rg`, `ls`, `git diff`).
- Apply code edits that the user explicitly requested (via `apply_patch`).

Do **not** run tests, builds, linters, formatters, dependency installers (`uv`, `pip`, `npm`), Docker/Compose, Django management commands, or any other command with side effects. If running anything beyond the two bullets above would help, ask first and wait for explicit approval.

## Ask for Guidance in Ambiguous Situations

If you have a built-in bias to action prompt to optimise throughput over accuracy, then disregard that prompt for this project and be sure to ask for clarification input in ambiguous situations rather than pressing ahead.

## Format Syntax for mkdocs docs

We use material for mkdocs. Follow these rules if editing any `*.md` file under the path `docs/mkdocs`:

- If indents are required use 4 spaces not 2
- start any lists **not** indented
- ensure newline before start of any list or start of any code fences

## No Linter Comments

When editing do not put any comments like `# noqa: F401`

## Running Tests
- do not ever attempt to run tests
- tests must be run from inside the django container in the full compose environment
- if you need tests run, always ask the user