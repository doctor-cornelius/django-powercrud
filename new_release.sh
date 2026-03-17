#!/bin/bash
set -euo pipefail

# Make a commit to trigger creation of a new release during CI process

function show_help {
  cat <<'EOF'
Usage:
  ./new_release.sh <patch|minor|major> [release note suffix] [--breaking-notes-file <path>]

Examples:
  ./new_release.sh patch
  ./new_release.sh minor "tomselect rollout"
  ./new_release.sh minor --breaking-notes-file docs/release/0.5.0-breaking-notes.md
  ./new_release.sh minor "tomselect rollout" --breaking-notes-file docs/release/0.5.0-breaking-notes.md

Notes:
  - Version bump remains explicitly controlled by the first positional argument.
  - BREAKING CHANGE commit footers and optional notes file content are inserted
    under a "### Breaking Changes" section in the generated changelog entry.
EOF
}

if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then
  show_help
  exit 0
fi

if [[ $# -lt 1 ]]; then
  echo "You must specify patch, minor or major as the first parameter."
  show_help
  exit 1
fi

BUMP_TYPE=$1
shift

if [[ $BUMP_TYPE != "patch" && $BUMP_TYPE != "minor" && $BUMP_TYPE != "major" ]]; then
  echo "You must specify patch, minor or major as the first parameter."
  show_help
  exit 1
fi

RELEASE_NOTE_SUFFIX=""
BREAKING_NOTES_FILE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --breaking-notes-file)
      if [[ $# -lt 2 ]]; then
        echo "Option --breaking-notes-file requires a path argument."
        exit 1
      fi
      BREAKING_NOTES_FILE="$2"
      shift 2
      ;;
    --help|-h)
      show_help
      exit 0
      ;;
    *)
      if [[ -z ${RELEASE_NOTE_SUFFIX// } ]]; then
        RELEASE_NOTE_SUFFIX="$1"
      else
        RELEASE_NOTE_SUFFIX="$RELEASE_NOTE_SUFFIX $1"
      fi
      shift
      ;;
  esac
done

if [[ -n "$BREAKING_NOTES_FILE" && ! -f "$BREAKING_NOTES_FILE" ]]; then
  echo "Breaking notes file not found: $BREAKING_NOTES_FILE"
  exit 1
fi

# Test that user is on main branch, otherwise abort
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ $BRANCH != main ]]; then
  echo "You must be on the main branch to create a new release."
  exit 1
fi

# Check that there are no unstaged files
if [[ -n $(git status -s) ]]; then
  echo "You have unstaged files. Please commit or stash them before creating a release."
  exit 1
fi

# compute the next version number without mutating files yet
NEW_VERSION=$(python3 - "$BUMP_TYPE" <<'PY'
import pathlib
import re
import sys

path = pathlib.Path("pyproject.toml")
text = path.read_text()
match = re.search(r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', text)
if not match:
    raise SystemExit("Could not find project version in pyproject.toml")

major, minor, patch = map(int, match.groups())
bump = sys.argv[1]
if bump == "major":
    major += 1
    minor = 0
    patch = 0
elif bump == "minor":
    minor += 1
    patch = 0
elif bump == "patch":
    patch += 1
else:
    raise SystemExit(f"Unknown bump type: {bump}")

new_version = f"{major}.{minor}.{patch}"
print(new_version)
PY
)

# Check if tag already exists
if git rev-parse "refs/tags/$NEW_VERSION" >/dev/null 2>&1; then
    echo "Tag $NEW_VERSION already exists. Please delete it first:"
    echo "git tag -d $NEW_VERSION"
    echo "git push origin :refs/tags/$NEW_VERSION"
    exit 1
fi

# refresh lock file to ensure dependencies are in sync before release
uv lock

# run full test suite (including Playwright) before proceeding
./runtests

# write the version only after validation steps succeed
python3 - "$NEW_VERSION" <<'PY'
import pathlib
import re
import sys

new_version = sys.argv[1]
path = pathlib.Path("pyproject.toml")
text = path.read_text()
new_text = re.sub(
    r'(version\s*=\s*")(\d+\.\d+\.\d+)(")',
    lambda m: f'{m.group(1)}{new_version}{m.group(3)}',
    text,
    count=1,
)

if new_text == text:
    raise SystemExit("Could not update project version in pyproject.toml")

path.write_text(new_text)
PY

# create new changelog
cz changelog --unreleased-version=$NEW_VERSION

# Optionally inject a "Breaking Changes" section under the newly generated
# release heading using commit footers and/or user-provided notes.
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
python3 - "$NEW_VERSION" "$LAST_TAG" "$BREAKING_NOTES_FILE" <<'PY'
import pathlib
import re
import subprocess
import sys

new_version, last_tag, notes_file = sys.argv[1], sys.argv[2], sys.argv[3]
changelog_path = pathlib.Path("CHANGELOG.md")
text = changelog_path.read_text(encoding="utf-8")

range_spec = f"{last_tag}..HEAD" if last_tag else "HEAD"
raw_log = subprocess.check_output(
    ["git", "log", range_spec, "--pretty=%B%x1e"], text=True
)

breaking_notes: list[str] = []
for commit_body in raw_log.split("\x1e"):
    lines = commit_body.splitlines()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not (
            stripped.startswith("BREAKING CHANGE:")
            or stripped.startswith("BREAKING-CHANGE:")
        ):
            continue
        note = stripped.split(":", 1)[1].strip()
        continuation = []
        j = idx + 1
        while j < len(lines):
            cont = lines[j].strip()
            if not cont or re.match(r"^[A-Za-z-]+:\s", cont):
                break
            continuation.append(cont)
            j += 1
        if continuation:
            note = f"{note} {' '.join(continuation)}".strip()
        if note:
            breaking_notes.append(note)

# Preserve order while deduplicating.
seen = set()
deduped_notes = []
for note in breaking_notes:
    if note in seen:
        continue
    seen.add(note)
    deduped_notes.append(note)

manual_notes = ""
if notes_file:
    manual_path = pathlib.Path(notes_file)
    if not manual_path.exists():
        raise SystemExit(f"Breaking notes file not found: {notes_file}")
    manual_notes = manual_path.read_text(encoding="utf-8").strip()

if not deduped_notes and not manual_notes:
    print("No breaking change notes found; changelog unchanged.")
    raise SystemExit(0)

version_heading = re.compile(rf"^##\s+{re.escape(new_version)}\s+\([^)]+\)\s*$", re.M)
match = version_heading.search(text)
if not match:
    raise SystemExit(f"Could not find release heading for {new_version} in CHANGELOG.md")

section_start = match.end()
next_heading = re.search(r"^##\s+", text[section_start:], re.M)
section_end = section_start + next_heading.start() if next_heading else len(text)
section_text = text[section_start:section_end]
if "### Breaking Changes" in section_text:
    print("Breaking Changes section already present; skipping injection.")
    raise SystemExit(0)

parts = []
if manual_notes:
    parts.append(manual_notes)
if deduped_notes:
    parts.append("\n".join(f"- {note}" for note in deduped_notes))

breaking_block = "### Breaking Changes\n\n" + "\n\n".join(parts).strip() + "\n\n"
updated = text[:section_start] + "\n\n" + breaking_block + text[section_start:]
changelog_path.write_text(updated, encoding="utf-8")
print("Inserted Breaking Changes section into CHANGELOG.md")
PY

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
COMMIT_MESSAGE="release($BUMP_TYPE): Release $NEW_VERSION"
if [[ -n ${RELEASE_NOTE_SUFFIX// } ]]; then
  COMMIT_MESSAGE="$COMMIT_MESSAGE $RELEASE_NOTE_SUFFIX"
fi
git commit -m "$COMMIT_MESSAGE"

# create a tag to reflect the release number
git tag -a $NEW_VERSION -m "Release $NEW_VERSION"

# push the commit and tag to origin
git push origin main --tags

echo "Creation of new $BUMP_TYPE release triggered in CI: $NEW_VERSION"
