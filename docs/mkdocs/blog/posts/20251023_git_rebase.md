---
date: 2025-10-23
categories:
  - git
---
# Replacing the misery of `merge --squash` with `git rebase -i`

I have had so many problems with `merge --squash`. Turns out there is a better way...
<!-- more -->
`git rebase -i main` rewrites my feature commits so they replay on top of the latest `main`, and it opens a todo list that lets me squash, reword, or drop commits before they land. After the rebase I can fast-forward `main` with a plain `git merge feature`, keeping history linear without losing context or hiding branches the way squashes do.

## Worked Example

Starting point:

```
main:    A --- B --- C
             \
feature:      D --- E
```

Do the tidy-up on the feature branch:

```
git switch feature
git rebase -i main       # todo list opens with "pick D" / "pick E"
```

The editor shows a todo list like:

```
pick D add async manager
pick E finish dashboard wiring
```

Change it to squash the second commit into the first:

```
pick D add async manager
squash E finish dashboard wiring
```

Save, resolve any conflicts, and Git rewinds to commit `C`, replays `D` as `D'`, squashes `E` on top, and leaves the branch at `E'`:

```
main:    A --- B --- C
                     \
feature:              E'
```

Finish by fast-forwarding `main`:

```
git switch main
git merge feature       # no merge bubble, just moves main to E'
```

Final history:

```
main:    A --- B --- C --- E'
```

So I end up with one polished commit on `main`, but I never lose track of what happened. Way cleaner than the detached commit graph I got from `merge --squash`.
