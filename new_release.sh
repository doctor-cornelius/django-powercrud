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
NEW_VERSION=$(poetry version -s)

# Check if tag already exists
if git rev-parse "refs/tags/$NEW_VERSION" >/dev/null 2>&1; then
    echo "Tag $NEW_VERSION already exists. Please delete it first:"
    echo "git tag -d $NEW_VERSION"
    echo "git push origin :refs/tags/$NEW_VERSION"
    exit 1
fi

# create new changelog
cz changelog --unreleased-version=$NEW_VERSION

# Build CSS for production
# Use a subshell to ensure environment is properly set up
(
  # Ensure we're using the right Node.js environment
  export NODE_ENV=production
  
  # Ensure npm can find all dependencies
  export PATH="$PWD/node_modules/.bin:$PATH"
  
  # Run the build command with verbose output for debugging
  echo "Building assets with npm..."
  npm run build --verbose || {
    echo "npm build failed."
    # Uncomment the line below if you want to abort on build failure
    exit 1
    echo "Continuing with release process anyway."
  }
)

# Note scope (release) is what will trigger the release job
git add -A
git commit -m "release($BUMP_TYPE): Release $NEW_VERSION"

# create a tag to reflect the release number
git tag -a $NEW_VERSION -m "Release $NEW_VERSION"

# push the commit and tag to origin
git push origin main --tags

echo "Creation of new $BUMP_TYPE release triggered in CI: $NEW_VERSION"
