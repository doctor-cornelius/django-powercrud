#!/bin/bash

# Make a commit to trigger creation of a new release during CI process

# Test that user is on main branch, otherwise abort
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ $BRANCH != main ]]; then
  echo "You must be on the main branch to create a new release."
  exit 1
fi
# Require %1 is patch|minor|major otherwise abort
if [[ $1 != "patch" && $1 != "minor" && $1 != "major" ]]; then
  echo "You must specify patch, minor or major as the first parameter."
  exit 1
fi

# Check if current environment is within the poetry shell venv
# meaning the venv is equal to $PWD/.venv
if [[ $VIRTUAL_ENV != $PWD/.venv ]]; then
  echo "You must be within the poetry shell venv to create a new release."
  exit 1
fi

# Check that there are no unstaged files
if [[ -n $(git status -s) ]]; then
  echo "You have unstaged files. Please commit or stash them before creating a release."
  exit 1
fi

BUMP_TYPE=$1

# increment version number
poetry version $BUMP_TYPE

# create new changelog
cz changelog --unreleased-version=$(poetry version -s)

# Note scope (release) is what will trigger the release job
git add -A
git commit -m "release($BUMP_TYPE): create release $(poetry version -s)"

# create a tag to reflect the release number
git tag -a $(poetry version -s) -m "Release $(poetry version -s)"

# push the commit and tag to origin
git push origin main --tags

echo "Creation of new $BUMP_TYPE release triggered in CI: $(poetry version -s)"