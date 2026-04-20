#!/bin/bash
set -euo pipefail

STATE_FILE=".git/new_release_state.json"

function show_help {
    cat <<'EOF'
Usage:
  ./new_release.sh --prepare <patch|minor|major> [--prerelease <alpha|beta|rc>] [--breaking-notes-file <path>]
  ./new_release.sh --publish
  ./new_release.sh --abort
  ./new_release.sh --help

Workflow:
  1. Run --prepare with an explicit bump level.
  2. Review and manually edit CHANGELOG.md to add release narrative.
  3. Run --publish to create one release commit, tag it, and push both refs.
  4. If you change your mind after --prepare, run --abort.

Examples:
  ./new_release.sh --prepare patch
  ./new_release.sh --prepare minor --prerelease beta
  ./new_release.sh --prepare major --breaking-notes-file docs/release/1.0.0-breaking-notes.md
  ./new_release.sh --publish
  ./new_release.sh --abort

Notes:
  - --prepare must be run from a clean main branch.
  - The bump level remains explicitly controlled by you; the script does not
    infer patch/minor/major from commit history.
  - Commitizen is used only to generate the changelog entry.
  - Ordinary release narrative should be edited directly in CHANGELOG.md after
    --prepare and before --publish.
EOF
}

function die {
    echo "Error: $*" >&2
    exit 1
}

function current_branch {
    git rev-parse --abbrev-ref HEAD
}

function require_main_branch {
    local branch
    branch=$(current_branch)
    if [[ "$branch" != "main" ]]; then
        die "you must be on the main branch."
    fi
}

function require_clean_worktree {
    if [[ -n "$(git status --short)" ]]; then
        die "working tree is not clean. Commit, stash, or discard changes first."
    fi
}

function require_state_absent {
    if [[ -f "$STATE_FILE" ]]; then
        die "a prepared release is already in progress. Run --publish or --abort first."
    fi
}

function require_state_present {
    if [[ ! -f "$STATE_FILE" ]]; then
        die "no prepared release state found. Run --prepare first."
    fi
}

function load_state_value {
    local key="$1"
    python3 - "$STATE_FILE" "$key" <<'PY'
import json
import pathlib
import sys

state = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
key = sys.argv[2]
value = state.get(key, "")
if not isinstance(value, str):
    raise SystemExit(f"State key {key!r} is not a string value")
print(value)
PY
}

function load_state_paths {
    local key="$1"
    python3 - "$STATE_FILE" "$key" <<'PY'
import json
import pathlib
import sys

state = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
for path in state.get(sys.argv[2], []):
    sys.stdout.buffer.write(path.encode("utf-8"))
    sys.stdout.buffer.write(b"\0")
PY
}

function list_current_tracked_paths {
    git diff --name-only -z HEAD --
}

function list_current_untracked_paths {
    git ls-files --others --exclude-standard -z
}

function restore_current_worktree {
    local tracked_paths=()
    local untracked_paths=()

    mapfile -d '' -t tracked_paths < <(list_current_tracked_paths)
    mapfile -d '' -t untracked_paths < <(list_current_untracked_paths)

    if ((${#tracked_paths[@]})); then
        git restore --source=HEAD --staged --worktree -- "${tracked_paths[@]}"
    fi

    if ((${#untracked_paths[@]})); then
        rm -rf -- "${untracked_paths[@]}"
    fi
}

function cleanup_state {
    rm -f "$STATE_FILE"
}

function validate_prepare_args {
    if [[ -z "$BUMP_TYPE" ]]; then
        die "--prepare requires patch, minor, or major."
    fi

    if [[ -n "$BREAKING_NOTES_FILE" && ! -f "$BREAKING_NOTES_FILE" ]]; then
        die "breaking notes file not found: $BREAKING_NOTES_FILE"
    fi
}

function validate_non_prepare_args {
    if [[ -n "$BUMP_TYPE" ]]; then
        die "$MODE does not accept patch, minor, or major."
    fi

    if [[ -n "$PRERELEASE_KIND" ]]; then
        die "$MODE does not accept --prerelease."
    fi

    if [[ -n "$BREAKING_NOTES_FILE" ]]; then
        die "$MODE does not accept --breaking-notes-file."
    fi
}

function validate_state_context {
    local action="$1"
    local branch
    local head_sha
    local expected_branch
    local expected_head

    branch=$(current_branch)
    head_sha=$(git rev-parse HEAD)
    expected_branch=$(load_state_value branch)
    expected_head=$(load_state_value head)

    if [[ "$branch" != "$expected_branch" ]]; then
        die "$action must be run from branch $expected_branch."
    fi

    if [[ "$head_sha" != "$expected_head" ]]; then
        die "$action requires the same HEAD commit used during --prepare."
    fi
}

function require_only_prepared_paths {
    local require_complete="$1"
    local prepared_tracked=()
    local prepared_untracked=()
    local current_tracked=()
    local current_untracked=()
    local prepared_paths=()
    local current_paths=()
    local extra_paths=()
    local missing_paths=()

    mapfile -d '' -t prepared_tracked < <(load_state_paths tracked_files)
    mapfile -d '' -t prepared_untracked < <(load_state_paths untracked_files)
    mapfile -d '' -t current_tracked < <(list_current_tracked_paths)
    mapfile -d '' -t current_untracked < <(list_current_untracked_paths)

    prepared_paths=("${prepared_tracked[@]}" "${prepared_untracked[@]}")
    current_paths=("${current_tracked[@]}" "${current_untracked[@]}")

    if ((${#prepared_paths[@]} == 0)); then
        die "prepared release state is empty; abort and prepare again."
    fi

    declare -A prepared_lookup=()
    declare -A current_lookup=()
    local path

    for path in "${prepared_paths[@]}"; do
        prepared_lookup["$path"]=1
    done

    for path in "${current_paths[@]}"; do
        current_lookup["$path"]=1
        if [[ -z ${prepared_lookup["$path"]+x} ]]; then
            extra_paths+=("$path")
        fi
    done

    if [[ "$require_complete" == "true" ]]; then
        for path in "${prepared_paths[@]}"; do
            if [[ -z ${current_lookup["$path"]+x} ]]; then
                missing_paths+=("$path")
            fi
        done
    fi

    if ((${#extra_paths[@]})); then
        printf 'Error: release state does not cover these changed paths:\n' >&2
        printf '  %s\n' "${extra_paths[@]}" >&2
        exit 1
    fi

    if ((${#missing_paths[@]})); then
        printf 'Error: prepared release files are no longer modified:\n' >&2
        printf '  %s\n' "${missing_paths[@]}" >&2
        exit 1
    fi
}

function compute_next_version {
    python3 - "$BUMP_TYPE" "${PRERELEASE_KIND:-}" <<'PY'
import pathlib
import re
import sys

text = pathlib.Path("pyproject.toml").read_text(encoding="utf-8")
match = re.search(
    r'^version\s*=\s*"(?P<version>\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?)"\s*$',
    text,
    re.M,
)
if not match:
    raise SystemExit("Could not find project version in pyproject.toml")

version_text = match.group("version")
parsed = re.fullmatch(
    r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:(?P<pre_kind>a|b|rc)(?P<pre_num>\d+))?",
    version_text,
)
if not parsed:
    raise SystemExit(f"Unsupported version format: {version_text}")

major = int(parsed.group("major"))
minor = int(parsed.group("minor"))
patch = int(parsed.group("patch"))
current_pre_kind = parsed.group("pre_kind")
current_pre_num = parsed.group("pre_num")
is_prerelease = current_pre_kind is not None

bump = sys.argv[1]
requested_prerelease = sys.argv[2]
requested_suffix = {"": "", "alpha": "a", "beta": "b", "rc": "rc"}[requested_prerelease]
prerelease_order = {"a": 0, "b": 1, "rc": 2}

if bump == "major":
    target = (major + 1, 0, 0)
elif bump == "minor":
    target = (major, minor + 1, 0)
elif bump == "patch":
    if is_prerelease:
        target = (major, minor, patch)
    else:
        target = (major, minor, patch + 1)
else:
    raise SystemExit(f"Unknown bump type: {bump}")

if not requested_suffix:
    print(".".join(str(part) for part in target))
    raise SystemExit(0)

pre_num = 1
same_target_as_current = target == (major, minor, patch)
if same_target_as_current and current_pre_kind:
    if prerelease_order[requested_suffix] < prerelease_order[current_pre_kind]:
        raise SystemExit(
            "Cannot move prerelease sequence backwards for the same release line"
        )
    if requested_suffix == current_pre_kind:
        pre_num = int(current_pre_num) + 1

print(f"{target[0]}.{target[1]}.{target[2]}{requested_suffix}{pre_num}")
PY
}

function update_project_version {
    local new_version="$1"
    python3 - "$new_version" <<'PY'
import pathlib
import re
import sys

new_version = sys.argv[1]
path = pathlib.Path("pyproject.toml")
text = path.read_text(encoding="utf-8")
new_text = re.sub(
    r'(version\s*=\s*")(\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?)(")',
    lambda m: f'{m.group(1)}{new_version}{m.group(3)}',
    text,
    count=1,
)
if new_text == text:
    raise SystemExit("Could not update project version in pyproject.toml")
path.write_text(new_text, encoding="utf-8")
PY
}

function insert_breaking_notes {
    local new_version="$1"
    local last_tag="$2"
    python3 - "$new_version" "$last_tag" "$BREAKING_NOTES_FILE" <<'PY'
import pathlib
import re
import subprocess
import sys

new_version, last_tag, notes_file = sys.argv[1], sys.argv[2], sys.argv[3]
changelog_path = pathlib.Path("CHANGELOG.md")
text = changelog_path.read_text(encoding="utf-8")

range_spec = f"{last_tag}..HEAD" if last_tag else "HEAD"
raw_log = subprocess.check_output(
    ["git", "log", range_spec, "--pretty=%B%x1e"],
    text=True,
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

deduped_notes = []
seen = set()
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
    raise SystemExit(0)

parts = []
if manual_notes:
    parts.append(manual_notes)
if deduped_notes:
    parts.append("\n".join(f"- {note}" for note in deduped_notes))

breaking_block = "### Breaking Changes\n\n" + "\n\n".join(parts).strip() + "\n\n"
updated = text[:section_start] + "\n\n" + breaking_block + text[section_start:]
changelog_path.write_text(updated, encoding="utf-8")
PY
}

function ensure_release_section_has_content {
    local new_version="$1"
    python3 - "$new_version" <<'PY'
import pathlib
import re
import sys

new_version = sys.argv[1]
changelog_path = pathlib.Path("CHANGELOG.md")
text = changelog_path.read_text(encoding="utf-8")

version_heading = re.compile(rf"^##\s+{re.escape(new_version)}\s+\([^)]+\)\s*$", re.M)
match = version_heading.search(text)
if not match:
    raise SystemExit(f"Could not find release heading for {new_version} in CHANGELOG.md")

section_start = match.end()
next_heading = re.search(r"^##\s+", text[section_start:], re.M)
section_end = section_start + next_heading.start() if next_heading else len(text)
section_text = text[section_start:section_end].strip()

if section_text:
    raise SystemExit(0)

maintenance_note = (
    "\n\nMaintenance release with internal-only or tooling-only changes; "
    "no curated user-facing changelog entries.\n"
)
updated = text[:section_start] + maintenance_note + text[section_end:]
changelog_path.write_text(updated, encoding="utf-8")
PY
}

function write_release_state {
    local new_version="$1"
    local tag_name="$2"
    local head_sha
    local branch

    head_sha=$(git rev-parse HEAD)
    branch=$(current_branch)

    python3 - "$STATE_FILE" "$new_version" "$tag_name" "$BUMP_TYPE" "${PRERELEASE_KIND:-}" "$BREAKING_NOTES_FILE" "$branch" "$head_sha" <<'PY'
import json
import pathlib
import subprocess
import sys

state_file, version, tag_name, bump_type, prerelease, notes_file, branch, head_sha = sys.argv[1:9]

tracked_raw = subprocess.check_output(["git", "diff", "--name-only", "-z", "HEAD", "--"])
tracked_files = [path for path in tracked_raw.decode("utf-8").split("\0") if path]

untracked_raw = subprocess.check_output(
    ["git", "ls-files", "--others", "--exclude-standard", "-z"]
)
untracked_files = [path for path in untracked_raw.decode("utf-8").split("\0") if path]

state = {
    "version": version,
    "tag": tag_name,
    "bump_type": bump_type,
    "prerelease": prerelease,
    "breaking_notes_file": notes_file,
    "branch": branch,
    "head": head_sha,
    "tracked_files": tracked_files,
    "untracked_files": untracked_files,
}

path = pathlib.Path(state_file)
path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
PY
}

function build_assets {
    (
        export NODE_ENV=production
        export PATH="$PWD/node_modules/.bin:$PATH"
        echo "Building assets with npm..."
        npm run build --verbose
    )
}

function prepare_release {
    local new_version
    local last_tag
    local prepare_failed="true"

    require_main_branch
    require_clean_worktree
    require_state_absent
    validate_prepare_args

    trap 'if [[ "$prepare_failed" == "true" ]]; then echo "Prepare failed; restoring working tree." >&2; restore_current_worktree; cleanup_state; fi' ERR

    new_version=$(compute_next_version)
    if git rev-parse "refs/tags/$new_version" >/dev/null 2>&1; then
        die "tag $new_version already exists."
    fi

    ./runproj exec ./runtests
    build_assets
    uv lock

    update_project_version "$new_version"
    cz changelog --incremental --unreleased-version="$new_version"

    last_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
    insert_breaking_notes "$new_version" "$last_tag"
    ensure_release_section_has_content "$new_version"
    write_release_state "$new_version" "$new_version"

    prepare_failed="false"
    trap - ERR

    cat <<EOF
Prepared release $new_version.

Next steps:
  1. Review and edit CHANGELOG.md.
  2. Run ./new_release.sh --publish when ready.
  3. Run ./new_release.sh --abort if you want to discard the prepared release.
EOF
}

function publish_release {
    local version
    local tag_name
    local prepared_paths=()
    local prepared_untracked=()

    require_state_present
    validate_non_prepare_args
    validate_state_context "--publish"
    require_only_prepared_paths "true"

    version=$(load_state_value version)
    tag_name=$(load_state_value tag)

    if git rev-parse "refs/tags/$tag_name" >/dev/null 2>&1; then
        die "tag $tag_name already exists."
    fi

    mapfile -d '' -t prepared_paths < <(load_state_paths tracked_files)
    mapfile -d '' -t prepared_untracked < <(load_state_paths untracked_files)
    prepared_paths+=("${prepared_untracked[@]}")

    if ((${#prepared_paths[@]} == 0)); then
        die "prepared release state is empty; abort and prepare again."
    fi

    git add -- "${prepared_paths[@]}"
    if git diff --cached --quiet; then
        die "there is nothing staged for the release commit."
    fi

    git commit -m "chore(release): publish $version"
    git tag -a "$tag_name" -m "Release $version"
    cleanup_state
    git push --atomic origin main "$tag_name"

    echo "Published release $version."
}

function abort_release {
    local tracked_paths=()
    local untracked_paths=()

    require_state_present
    validate_non_prepare_args
    validate_state_context "--abort"
    require_only_prepared_paths "false"

    mapfile -d '' -t tracked_paths < <(load_state_paths tracked_files)
    mapfile -d '' -t untracked_paths < <(load_state_paths untracked_files)

    if ((${#tracked_paths[@]})); then
        git restore --source=HEAD --staged --worktree -- "${tracked_paths[@]}"
    fi

    if ((${#untracked_paths[@]})); then
        rm -rf -- "${untracked_paths[@]}"
    fi

    cleanup_state
    echo "Aborted prepared release state."
}

MODE=""
BUMP_TYPE=""
PRERELEASE_KIND=""
BREAKING_NOTES_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prepare|--publish|--abort)
            if [[ -n "$MODE" ]]; then
                die "specify exactly one of --prepare, --publish, or --abort."
            fi
            MODE="$1"
            shift
            ;;
        patch|minor|major)
            if [[ -n "$BUMP_TYPE" ]]; then
                die "bump level specified more than once."
            fi
            BUMP_TYPE="$1"
            shift
            ;;
        --prerelease)
            if [[ $# -lt 2 ]]; then
                die "--prerelease requires alpha, beta, or rc."
            fi
            case "$2" in
                alpha|beta|rc)
                    PRERELEASE_KIND="$2"
                    ;;
                *)
                    die "--prerelease must be one of alpha, beta, or rc."
                    ;;
            esac
            shift 2
            ;;
        --breaking-notes-file)
            if [[ $# -lt 2 ]]; then
                die "--breaking-notes-file requires a path."
            fi
            BREAKING_NOTES_FILE="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            die "unknown argument: $1"
            ;;
    esac
done

if [[ -z "$MODE" ]]; then
    echo "You must specify one of --prepare, --publish, or --abort." >&2
    show_help
    exit 1
fi

case "$MODE" in
    --prepare)
        prepare_release
        ;;
    --publish)
        publish_release
        ;;
    --abort)
        abort_release
        ;;
esac
