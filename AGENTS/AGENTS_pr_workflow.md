# Pull Request Workflow

Use this workflow when the user asks to create a pull request, merge a feature branch, finish a branch, or leave the repository clean on `main`.

## Scope

- Use GitHub CLI (`gh`) for pull request creation, inspection, and merge operations.
- Default to the current branch when the user says to use the current branch.
- If the user names a branch, use that branch.
- Never create or merge a pull request from `main`.
- Never force-push, rewrite shared history, bypass branch protection, or use admin merge flags unless the user explicitly asks for that.

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
    gh pr create --base main --head <feature-branch> --fill
    ```

    If `--fill` produces an unsuitable title or body, use a concise semantic title and a short body that summarizes the user-visible change and verification.

5. Inspect the PR:

    ```bash
    gh pr view
    gh pr checks
    ```

    If checks fail and the fix is obvious and within the current task scope, fix it on the feature branch, commit, push, and re-check. If the failure is ambiguous or broad, stop and discuss with the user.

6. Squash merge the PR into `main` and delete the remote feature branch:

    ```bash
    gh pr merge --squash --delete-branch
    ```

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

## Conflict handling

If GitHub reports conflicts, fetch the latest `main` and attempt a normal local resolution only when the conflict is small and clearly within the files changed for the task:

```bash
git fetch origin main
git merge origin/main
```

After resolving simple conflicts, run the relevant verification, commit the merge resolution, push, and continue the PR flow.

If conflicts span unrelated files, require product judgment, or make the intended behavior unclear, stop and ask the user before continuing.
