# Pull Request Workflow

Use this workflow when the user asks to create a pull request, merge a feature branch, finish a branch, or leave the repository clean on `main`.

## Scope

- Use GitHub CLI (`gh`) for pull request creation, inspection, and merge operations.
- The GitHub Codex plugin may be used to inspect GitHub state when available, but `gh` remains the canonical, portable workflow.
- Default to the current branch when the user says to use the current branch.
- If the user names a branch, use that branch.
- Never create or merge a pull request from `main`.
- `main` is protected by the `protect_main` repository ruleset. It requires a pull request, squash-only merge, strict required status checks, and deletion/non-fast-forward protection.
- Never force-push, rewrite shared history, bypass branch protection, or use admin merge flags unless the user explicitly asks for that.
- `git push --force-with-lease` is allowed only when an intentional rebase of the feature branch was required to keep the PR clean, such as after an earlier dependent branch was squash-merged.

## Hard stops

Stop and discuss with the user before continuing if any of these occur:

- the working tree has uncommitted changes that are not clearly part of the requested branch finish
- the feature branch is `main`
- the target branch is unclear
- conflicts are non-trivial
- CI/check failures are not straightforward to fix
- branch protection blocks the squash merge
- `gh` authentication or permissions are missing
- the merge would require deleting a branch the user did not intend to retire
- a force-with-lease push would overwrite remote work that was not just produced by the current workflow

## Standard flow

1. Confirm the starting state:

    ```bash
    git status --short --branch
    git branch --show-current
    ```

2. Confirm the branch is not `main`. If the current branch is `main` and the user did not name a feature branch, ask which branch to use.

    If the user named a feature branch and it is not currently checked out, switch to it:

    ```bash
    git switch <feature-branch>
    ```

3. Push the feature branch and set upstream if needed:

    ```bash
    git push -u origin <feature-branch>
    ```

4. Create the pull request against `main`:

    ```bash
    gh pr create --base main --head <feature-branch> --title "<clear PR title>" --body-file -
    ```

    Use a concise PR title and a short body that summarizes the user-visible change and verification. Avoid relying on `--fill` for broad or multi-commit branches unless the generated title and body are already clear.

5. Inspect the PR:

    ```bash
    gh pr view
    gh pr checks --required
    ```

    To wait for checks, prefer:

    ```bash
    gh pr checks <pr-number> --required --watch --fail-fast
    ```

    Older GitHub CLI versions may not support `gh pr checks --watch`. If that fails with an unknown flag, use the Actions run id from the check URLs and watch the run directly:

    ```bash
    gh run watch <run-id> --exit-status
    ```

    If checks fail and the fix is obvious and within the current task scope, fix it on the feature branch, commit, push, and re-check. If the failure is ambiguous or broad, stop and discuss with the user.

6. Squash merge the PR into `main` and delete the remote feature branch:

    ```bash
    gh pr merge <pr-number> --squash --delete-branch --subject "<type>(<scope>): <subject>"
    ```

    The PR title can be human-readable, but the squash commit subject must follow this repo's Commitizen schema from `cz.yaml`, for example `feat(actions): add structured action declarations` or `docs(agents): refine pr workflow`. Do not rely on GitHub's default squash subject if the PR title is not already a valid semantic commit subject.

7. Return local checkout to a clean, current `main`:

    ```bash
    git fetch --prune origin
    git switch main
    git pull --ff-only origin main
    ```

8. Delete the local feature branch if it still exists:

    ```bash
    git branch --delete <feature-branch>
    ```

    Use `git branch -D <feature-branch>` only when the branch was successfully squash-merged and Git refuses the safe delete because the local branch tip is not an ancestor of `main`.

9. Verify the final state:

    ```bash
    git status --short --branch
    git branch --show-current
    gh pr view <pr-number> --json state,mergedAt,mergeCommit
    ```

10. Report the PR number, merge result, final local branch, and whether the worktree is clean.

## Multiple dependent branches

When the user asks to finish multiple branches as separate PRs, check whether later branches include earlier branch commits:

```bash
git log --oneline --decorate --graph main..<branch>
```

If branch B is stacked on branch A, finish branch A first. After branch A is squash-merged into `main`, update local `main`, then rebase branch B onto the new `main` so the second PR does not re-include branch A's commits:

```bash
git switch main
git pull --ff-only origin main
git switch <branch-b>
git rebase --onto main <branch-a-tip-before-merge> <branch-b>
git push --force-with-lease origin <branch-b>
```

Use this only when the dependency is clear. If the old base tip is uncertain, inspect the graph first and stop if the branch relationship is ambiguous.

## Release pull requests

Use `new_release.sh` for package releases rather than hand-rolling release commits:

```bash
git switch main
git pull --ff-only origin main
./new_release.sh --prepare <patch|minor|major>
# Review and edit CHANGELOG.md on release/<version>.
./new_release.sh --publish
```

The release script creates a `release/<version>` branch, opens a release PR, waits for required checks, squash-merges with a semantic subject like `chore(release): publish 0.4.0`, updates local `main`, creates an annotated version tag on the merged `main` commit, and pushes only the tag. The tag push triggers the PyPI and documentation release workflows.

If `--publish` fails after creating the release commit, PR, or merge, rerun it before attempting manual cleanup. It records progress in `.git/new_release_state.json` and resumes from the last completed phase.

Hard stop and discuss with the user if the release PR checks fail, the release PR has non-trivial conflicts, tag creation points at an unexpected commit, or a partially published release needs manual cleanup.

## Conflict handling

If GitHub reports conflicts, fetch the latest `main` and attempt a normal local resolution only when the conflict is small and clearly within the files changed for the task:

```bash
git fetch origin main
git merge origin/main
```

After resolving simple conflicts, run the relevant verification, commit the merge resolution, push, and continue the PR flow.

If conflicts span unrelated files, require product judgment, or make the intended behavior unclear, stop and ask the user before continuing.
