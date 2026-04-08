---
date: 2025-10-23
categories:
  - git
---
# Soft resets beat `merge --squash`

`merge --squash` looked clean on paper but kept biting me with detached histories, lost commit metadata, and surprise conflicts that were hard to replay. The workflow that finally stuck is even simpler: fast-forward `main`, soft-reset the feature branch to that point, and create the single commit I actually want.
<!-- more -->
`git reset --soft main` rewinds the branch pointer while keeping every change staged. One fresh commit later, `main` can be fast-forwarded with `git merge --ff-only feature`. I still have the old commits in the reflog if I need them, but day to day I land tidy, intentional changes without fighting the interactive rebase todo list.

## TL;DR workflow

1. `git switch main && git pull --ff-only origin main`
2. `git switch feature && git reset --soft main`
3. `git commit -m "feat: describe the one thing you just built"`
4. `git switch main && git merge --ff-only feature`

That’s it—no detached commits, no accidental merges, no editing dozens of `pick` lines.

## Why `merge --squash` kept hurting

- It strands the branch tip, so you can’t reuse the branch or push it upstream after the squash.
- A forgetful `git push` from the feature branch recreates the unsquashed history in the remote, confusing reviewers.
- You lose the direct link between the squashed commit and its branch, which makes bisects and release notes harder.
- The more you rely on squashes, the more likely you are to re-type the same commands (and mistakes) every time.

## Why the soft reset is calmer

- The staging area contains every change immediately after `git reset --soft main`, so you see exactly what is landing.
- You get a brand-new commit with a fresh hash, author date, and message—but only one command produced it.
- Need to adjust the message? Amend. Need the old commits back? `git reflog` still knows about them.
- Fast-forwarding `main` keeps the history linear and mirrors what will hit `origin/main`.

## Example: Branch A then Branch B

Same setup as before: `branch_a` sits on `main` with three commits, `branch_b` stacks another three commits on top.

```
main:     A --- B --- C
                       \
branch_a:               D --- E --- F
                                    \
branch_b:                            G --- H --- I
```

### Step 1: land `branch_a`

```
git switch main
git pull --ff-only origin main     # make sure C is current

git switch branch_a
git reset --soft main              # stage D/E/F as one blob
git commit -m "feat(async): land async manager core"

git switch main
git merge --ff-only branch_a       # main now points at F'
```

Result:

```
main:     A --- B --- C --- F'
                             \
branch_b:                     G --- H --- I
```

### Step 2: land `branch_b`

```
git switch branch_b
git reset --soft main
git commit -m "feat(async): extend async API"

git switch main
git merge --ff-only branch_b       # main now points at I'
```

History stays linear:

```
main: A --- B --- C --- F' --- I'
```

Both branches produced exactly one commit, and I didn’t touch `merge --squash` or juggle interactive rebase instructions.

## When I still reach for interactive rebase

`git rebase -i` remains great when I need to:

- Reshape multiple commits while keeping some of them separate.
- Fold follow-up fixes with `git commit --fixup <hash>` and `git rebase -i --autosquash main`.
- Reorder commits because reviewers want the dependency story told differently.

Even then I avoid repetitive editing. `git commit --fixup` marks the commits ahead of time, and `--autosquash` converts the todo list for me. If I truly need to squash everything manually, a quick `:2,$s/^pick /squash /` inside `vim` flips the entire buffer after the first line.

## Quick checklist before merging

- [ ] `git fetch --all --prune`
- [ ] `git switch main && git pull --ff-only origin main`
- [ ] `git switch feature && git reset --soft main`
- [ ] `git commit` once, amend if needed
- [ ] `git switch main && git merge --ff-only feature`
- [ ] `git push origin main`

This keeps `main` pristine, gives every pull request a single, intentional commit, and saves me from ever typing `merge --squash` again.
