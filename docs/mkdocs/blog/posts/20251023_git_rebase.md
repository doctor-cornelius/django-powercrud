---
date: 2025-10-23
categories:
  - git
---
# Replacing the misery of `merge --squash` with `git rebase -i`

I have had so many problems with `merge --squash`. Turns out there is a better way...
<!-- more -->
`git rebase -i main` rewrites my feature commits so they replay on top of the latest `main`, and it opens a todo list that lets me squash, reword, or drop commits before they land. After the rebase I can fast-forward `main` with a plain `git merge feature`, keeping history linear without losing context or hiding branches the way squashes do.

## Branch A then Branch B

Here’s the pattern I hit most: `main` is behind two stacked feature branches. `branch_a` is three commits long, and `branch_b` adds another three commits on top of that work.

```
main:     A --- B --- C
                       \
branch_a:               D --- E --- F
                                    \
branch_b:                            G --- H --- I
```

### 1. Rebase + squash `branch_a`

```
git switch branch_a
git rebase -i main
```

The todo list shows the three commits:

```
pick D groundwork for async manager
pick E wire up progress cache
pick F add cleanup scheduler
```

Change the second and third lines to `squash` so they fold into the first commit:

```
pick D groundwork for async manager
squash E wire up progress cache
squash F add cleanup scheduler
```

Save and exit. Git replays the trio on top of `C`, then drops you into the commit-message editor. By default you’ll see all three messages stacked together:

```
groundwork for async manager

# This is a combination of 3 commits.
# The first commit's message is:
groundwork for async manager

# This is the commit message #2:
wire up progress cache

# This is the commit message #3:
add cleanup scheduler
```

Edit this buffer to whatever you want the final message to be (for example, keep only the bullet list below) and save:

```
feat(async): land async manager core

- cache-backed progress updates
- scheduled cleanup helper
```

That leaves you with one new commit `F'` on `branch_a`. Fast-forward `main`:

```
git switch main
git merge branch_a       # moves main to F'
```

Now the history looks like:

```
main:     A --- B --- C --- F'
                             \
branch_b:                     G --- H --- I
```

### 2. Rebase + squash `branch_b`

`branch_b` still points to the old stack, so bring it up to date with the new `main`:

```
git switch branch_b
git rebase -i main
```

Todo list:

```
pick G extend async API
pick H hook progress into dashboard
pick I tidy docs
```

Again, keep the first line and squash the rest:

```
pick G extend async API
squash H hook progress into dashboard
squash I tidy docs
```

When Git opens the commit-message editor, trim the combined text to the final message you want (e.g. leave only the summary and bullets). Save to finish the rebase, giving you a single commit `I'` ahead of `main`.

Fast-forward `main` a second time:

```
git switch main
git merge branch_b       # moves main to I'
```

Final graph:

```
main: A --- B --- C --- F' --- I'
```

No merge bubbles, no mystery squashed history—just two clean commits representing `branch_a` and `branch_b`. The interactive rebase steps made it easy to squash each stack, pick the final commit messages in the editor, and land them on `main` without the `merge --squash` chaos.
