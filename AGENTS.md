# Agent Instructions

## Command execution policy

Only run shell commands in this repo when strictly required to:

- Read/list files for context (e.g. `sed`, `cat`, `rg`, `ls`, `git diff`).
- Apply code edits that the user explicitly requested (via `apply_patch`).

Do **not** run tests, builds, linters, formatters, dependency installers (`uv`, `pip`, `npm`), Docker/Compose, Django management commands, or any other command with side effects unless the user explicitly approves first.

Container access exception:

- You may run `./runproj exec` only after explicit user approval, and only when a task requires entering the Django container.
- `./runproj exec` defaults to the `dev` environment when no env arg is supplied.
- `./runproj exec dev` and `./runproj exec` are equivalent.

## Ask for Guidance in Ambiguous Situations

If you have a built-in bias to action prompt to optimise throughput over accuracy, then disregard that prompt for this project and be sure to ask for clarification input in ambiguous situations rather than pressing ahead.

## Format Syntax for mkdocs docs

We use material for mkdocs. Follow these rules if editing any `*.md` file under the path `docs/mkdocs`:

- Top-level lists must start with no indentation.
- If indentation is required, use 4 spaces (not 2).
- Ensure a blank line before starting any list or fenced code block.

## No Linter Comments

When editing do not put any comments like `# noqa: F401`

## Writing Tests

- for `assert` statements always include a helpful failure message so the reader can see exactly what the intent was

## Running Tests

- you can run tests if needed when editing code or if the user asks you to
  - If the user says "SESSION TESTS UNAUTHORIZED" then you must ask for permission during the session to run tests
- run tests as per the instructions following
  - Tests must be run from inside the Django container in the full Compose environment.
  - To run tests, enter the container with `./runproj exec` and run test commands there using the `runtests` command as per the script `runtests` in the repo root.

## Project Briefing

If the user says "BRIEF YOURSELF" then do these things:

1. Read README.md, docs/mkdocs/index.md, runproj, runtests, pyproject.toml, all subfolders and files in docker
2. Read src/config/settings.py, src/config/urls.py

## context7 and docs

1. Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.
2. avoid low reputation matches