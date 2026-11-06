"""Exercise runtests routing using isolated command stubs."""

import os
import shutil
import signal
import subprocess
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _run_runtests(
    tmp_path,
    *arguments,
    inherited_settings=None,
    pytest_exit=0,
    coordinator_sentinel=False,
    combined_sentinel=False,
    pytest_terminate=False,
    omit_data="",
):
    """Run a copied runner in a temporary directory with harmless command stubs."""
    run_dir = tmp_path / f"run-{len(list(tmp_path.glob('run-*')))}"
    bin_dir = run_dir / "bin"
    bin_dir.mkdir(parents=True)
    shutil.copy2(REPOSITORY_ROOT / "runtests", run_dir / "runtests")
    if coordinator_sentinel:
        (run_dir / ".test-artifacts/coverage/coordinator").mkdir(parents=True)
        (run_dir / ".test-artifacts/coverage/coordinator/.coverage").write_text("preserve coordinator data")
    if combined_sentinel:
        (run_dir / ".test-artifacts/coverage/combined").mkdir(parents=True)
        (run_dir / ".test-artifacts/coverage/combined/.coverage").write_text("preserve combined data")
    log_path = run_dir / "commands.log"
    commands = {
        "pytest": '''#!/bin/sh
echo "pytest|${DJANGO_SETTINGS_MODULE:-}|${COVERAGE_FILE:-}|$*" >> "$RUNNER_LOG"
case " $* " in *" --collect-only "*) exit "${PYTEST_EXIT:-0}" ;; esac
if [ "${PYTEST_TERMINATE:-0}" = 1 ]; then
    kill -TERM "$PPID"
    exit 143
fi
if [ "$COVERAGE_FILE" != "${PYTEST_OMIT_DATA:-}" ]; then
    mkdir -p "$(dirname "$COVERAGE_FILE")"
    printf 'stub data' > "$COVERAGE_FILE"
fi
exit "${PYTEST_EXIT:-0}"
''',
        "python": '#!/bin/sh\necho "python|${DJANGO_SETTINGS_MODULE:-}|$*" >> "$RUNNER_LOG"\n',
        "coverage": '#!/bin/sh\necho "coverage|${COVERAGE_FILE:-}|$*" >> "$RUNNER_LOG"\n',
        "npm": '#!/bin/sh\necho "npm|$*" >> "$RUNNER_LOG"\n',
    }
    for name, contents in commands.items():
        executable = bin_dir / name
        executable.write_text(contents)
        executable.chmod(0o755)
    environment = os.environ.copy()
    environment["PATH"] = f"{bin_dir}{os.pathsep}{environment['PATH']}"
    environment["RUNNER_LOG"] = str(log_path)
    environment["PYTEST_EXIT"] = str(pytest_exit)
    environment["PYTEST_TERMINATE"] = "1" if pytest_terminate else "0"
    environment["PYTEST_OMIT_DATA"] = omit_data
    environment.pop("COVERAGE_FILE", None)
    if inherited_settings is None:
        environment.pop("DJANGO_SETTINGS_MODULE", None)
    else:
        environment["DJANGO_SETTINGS_MODULE"] = inherited_settings
    result = subprocess.run(
        ["bash", "./runtests", *arguments],
        cwd=run_dir,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    log = log_path.read_text() if log_path.exists() else ""
    return result, log


def test_coordinator_selection_overrides_inherited_consumer_settings(tmp_path):
    """Coordinator routing always uses its independent configuration and data."""
    result, log = _run_runtests(
        tmp_path,
        "--suite", "coordinator", "--pytest", "src/coordinator_tests/test_suite_isolation.py",
        inherited_settings="tests.settings",
    )
    assert result.returncode == 0, "Coordinator test routing should succeed"
    assert "pytest|coordinator_tests.settings|.test-artifacts/coverage/coordinator/.coverage|" in log, "Coordinator settings and coverage must be selected"
    assert "-c pytest-coordinator.ini" in log, "Coordinator selection should use its own pytest config"


def test_coordinator_path_inference_accepts_plain_and_dot_paths(tmp_path):
    """Coordinator ownership should be inferred from normalized focused paths."""
    for path in ("src/coordinator_tests/test_suite_isolation.py", "./src/coordinator_tests/test_suite_isolation.py"):
        result, log = _run_runtests(tmp_path, path)
        assert result.returncode == 0, "Plain focused coordinator invocation should succeed"
        assert "pytest|coordinator_tests.settings|.test-artifacts/coverage/coordinator/.coverage|" in log, "Dot-prefixed coordinator path should select isolated settings"


def test_coordinator_directory_path_is_inferred(tmp_path):
    """Selecting the coordinator directory itself should select its suite."""
    result, log = _run_runtests(tmp_path, "--pytest", "./src/coordinator_tests")
    assert result.returncode == 0, "Coordinator directory routing should succeed"
    assert "-c pytest-coordinator.ini" in log, "Coordinator directory should use coordinator pytest configuration"


def test_plain_consumer_path_keeps_focused_runner_behavior(tmp_path):
    """A plain consumer path should still run only that path with consumer settings."""
    result, log = _run_runtests(tmp_path, "src/tests/test_async_compatibility.py")
    calls = [line for line in log.splitlines() if line.startswith("pytest|")]
    assert result.returncode == 0, "Plain focused consumer invocation should succeed"
    assert len(calls) == 1, "Plain focused consumer invocation should run one pytest process"
    assert "pytest|tests.settings|.coverage|" in calls[0], "Plain consumer path should use consumer settings"
    assert "src/tests/test_async_compatibility.py" in calls[0], "Plain invocation should pass its focused path"
    assert "-m" not in calls[0], "Plain invocation should retain the existing marker behavior"


def test_focused_playwright_path_without_suite_preserves_coverage_and_settings(tmp_path):
    """Focused browser paths should remain available without server suite selection."""
    result, log = _run_runtests(
        tmp_path,
        "--playwright", "--rebuild-assets", "src/tests/playwright/test_bulk_selection.py::test_bulk_selection_toggle",
        inherited_settings="tests.settings_bootstrap",
        coordinator_sentinel=True,
        combined_sentinel=True,
    )
    calls = [line for line in log.splitlines() if line.startswith("pytest|")]
    run_dir = next(tmp_path.glob("run-*"))
    assert result.returncode == 0, "Focused browser invocation should succeed"
    assert "npm|run build" in log, "Focused browser invocation should build assets when requested"
    assert len(calls) == 1 and "-m playwright" in calls[0], "Focused path should use the browser marker"
    assert "tests.settings_bootstrap" in calls[0], "Focused browser invocation should preserve presentation settings"
    assert "pytest-coordinator.ini" not in calls[0], "Browser path should stay in the consumer suite"
    assert (run_dir / ".test-artifacts/coverage/coordinator/.coverage").read_text() == "preserve coordinator data", "Browser coverage must preserve coordinator data"
    assert (run_dir / ".test-artifacts/coverage/combined/.coverage").read_text() == "preserve combined data", "Browser coverage must preserve aggregate data"


def test_runner_rejects_mixed_suite_paths_before_pytest(tmp_path):
    """One pytest process must not combine tests that require different settings."""
    result, log = _run_runtests(
        tmp_path,
        "--pytest", "src/coordinator_tests/test_suite_isolation.py", "src/tests/test_async_compatibility.py",
    )
    assert result.returncode != 0, "Mixed suite paths should be rejected"
    assert "cannot mix coordinator and PowerCRUD" in result.stdout, "Rejection should explain suite ownership"
    assert "pytest|" not in log, "Mixed paths should be rejected before pytest starts"


def test_minimal_path_selects_minimal_settings_with_or_without_suite(tmp_path):
    """The isolated minimal-settings module must always use its dedicated settings."""
    for arguments in (
        ("--suite", "powercrud", "--pytest", "src/tests/test_minimal_settings_no_async.py"),
        ("--pytest", "./src/tests/test_minimal_settings_no_async.py"),
    ):
        result, log = _run_runtests(tmp_path, *arguments, inherited_settings="tests.settings_bootstrap")
        assert result.returncode == 0, "Minimal-settings path should execute"
        assert "pytest|tests.settings_minimal|.coverage|" in log, "Minimal path must not inherit ordinary settings"


def test_runner_rejects_minimal_and_ordinary_tests_together(tmp_path):
    """Minimal tests must not share one pytest process with ordinary consumers."""
    result, log = _run_runtests(
        tmp_path,
        "--suite", "powercrud", "--pytest", "src/tests/test_minimal_settings_no_async.py", "src/tests/test_async_compatibility.py",
    )
    assert result.returncode != 0, "Mixed minimal and ordinary paths should be rejected"
    assert "minimal-settings tests must run separately" in result.stdout, "Minimal-settings rejection should explain the rule"
    assert "pytest|" not in log, "Mixed minimal selection should stop before pytest"


@pytest.mark.parametrize("mode", [(), ("--pytest",), ("--collect-only",)])
@pytest.mark.parametrize("path", [".", "./src/", "src/coordinator_tests/.."])
def test_ancestor_directories_reject_mixed_suites_before_commands(tmp_path, mode, path):
    """Ancestor paths must not collect both Django configurations in one process."""
    result, log = _run_runtests(tmp_path, *mode, path)
    assert result.returncode != 0, "A directory containing both suites must be rejected"
    assert "--suite all --pytest" in result.stdout, "Rejection should explain the safe aggregate invocation"
    assert not log, "Mixed directory selection must stop before preflight, assets, or pytest"


@pytest.mark.parametrize("suite", ["coordinator", "powercrud"])
def test_explicit_suite_cannot_override_mixed_directory_safeguard(tmp_path, suite):
    """An explicit suite must not make a mixed directory safe for one process."""
    result, log = _run_runtests(tmp_path, "--suite", suite, "--pytest", "src")
    assert result.returncode != 0, "Mixed directory selection must remain invalid with a suite flag"
    assert "--suite all --pytest" in result.stdout, "The diagnostic should offer separate execution"
    assert not log, "An invalid explicit selection must not execute commands"


@pytest.mark.parametrize("mode", [(), ("--pytest",), ("--collect-only",)])
@pytest.mark.parametrize("path", ["src/tests", "./src/tests/../tests/"])
def test_consumer_directory_excludes_minimal_settings_module(tmp_path, mode, path):
    """Focused consumer directories keep minimal tests out of their settings process."""
    result, log = _run_runtests(tmp_path, *mode, path, inherited_settings="tests.settings_bootstrap")
    calls = [line for line in log.splitlines() if line.startswith("pytest|")]
    assert result.returncode == 0, "Focused consumer directory selection should remain supported"
    assert len(calls) == 1, "Focused directory selection should run one ordinary consumer process"
    assert "pytest|tests.settings_bootstrap|" in calls[0], "Focused directories must preserve custom consumer settings"
    assert "--ignore=src/tests/test_minimal_settings_no_async.py" in calls[0], "Directory selection must exclude the minimal module"
    assert calls[0].endswith(" src/tests"), "Pytest must receive the normalized directory so exclusions use the same path"
    assert "./runtests --pytest src/tests/test_minimal_settings_no_async.py" in result.stdout, "The exclusion notice should provide the separate command"
    if mode == ("--collect-only",):
        assert "python|" not in log and "npm|" not in log, "Directory collection must skip preflight and assets"


@pytest.mark.parametrize("path", ["src/tests/../coordinator_tests/", "src/./coordinator_tests/"])
def test_equivalent_coordinator_directories_infer_owned_settings(tmp_path, path):
    """Directory normalization should infer actual ownership before selecting settings."""
    result, log = _run_runtests(tmp_path, path, inherited_settings="tests.settings_bootstrap")
    assert result.returncode == 0, "Equivalent coordinator directory paths should be accepted"
    assert "pytest|coordinator_tests.settings|" in log, "Canonical coordinator paths must force coordinator settings"
    assert "-c pytest-coordinator.ini" in log, "Normalized ownership must select the coordinator configuration"


@pytest.mark.parametrize("mode", [(), ("--pytest",), ("--collect-only",)])
def test_multiple_minimal_nodes_share_their_dedicated_settings(tmp_path, mode):
    """Multiple nodes from the same minimal module require only one compatible process."""
    nodes = (
        "src/tests/test_minimal_settings_no_async.py::test_powercrud_mixin_imports_without_async_stack",
        "./src/tests/../tests/test_minimal_settings_no_async.py::test_builtin_template_pack_resolves_without_powercrud_settings",
    )
    result, log = _run_runtests(tmp_path, *mode, *nodes, inherited_settings="tests.settings_bootstrap")
    calls = [line for line in log.splitlines() if line.startswith("pytest|")]
    assert result.returncode == 0, "Compatible minimal-settings nodes must not be rejected as mixed tests"
    assert len(calls) == 1, "Minimal nodes should execute in a single settings process"
    assert "pytest|tests.settings_minimal|" in calls[0], "All selected minimal nodes must use minimal settings"
    assert "src/tests/test_minimal_settings_no_async.py::test_powercrud_mixin_imports_without_async_stack" in calls[0], "The first node selector must reach pytest unchanged"
    assert "src/tests/test_minimal_settings_no_async.py::test_builtin_template_pack_resolves_without_powercrud_settings" in calls[0], "Only the second node's file path should be normalized"
    assert "--ignore=" not in calls[0], "Explicit minimal nodes must not receive a directory exclusion"


def test_explicit_consumer_suite_accepts_multiple_minimal_nodes(tmp_path):
    """The consumer suite flag must allow several nodes with the same minimal settings."""
    result, log = _run_runtests(
        tmp_path, "--suite", "powercrud", "--pytest",
        "src/tests/test_minimal_settings_no_async.py::test_powercrud_mixin_imports_without_async_stack",
        "src/tests/test_minimal_settings_no_async.py::test_builtin_template_pack_resolves_without_powercrud_settings",
    )
    assert result.returncode == 0, "Explicit PowerCRUD selection should accept compatible minimal nodes"
    assert "pytest|tests.settings_minimal|" in log, "The explicit suite must still select minimal settings"


@pytest.mark.parametrize("mode", [(), ("--pytest",), ("--collect-only",)])
def test_minimal_node_and_ordinary_directory_are_rejected(tmp_path, mode):
    """Explicit minimal selection cannot share a process with an ordinary directory."""
    result, log = _run_runtests(
        tmp_path, *mode, "src/tests/", "src/tests/./test_minimal_settings_no_async.py::test_example",
    )
    assert result.returncode != 0, "Minimal nodes combined with an ordinary directory must be rejected"
    assert "minimal-settings tests must run separately" in result.stdout, "Rejection should identify the settings conflict"
    assert not log, "Incompatible settings selections must stop before command execution"


def test_node_parameter_text_does_not_change_path_ownership(tmp_path):
    """Slashes and parent segments inside a parameter ID are not filesystem paths."""
    node = "src/tests/test_minimal_settings_no_async.py::test_example[../coordinator_tests/..]"
    result, log = _run_runtests(tmp_path, "--pytest", node)
    assert result.returncode == 0, "Parameterized node text must not be normalized as part of the file path"
    assert "pytest|tests.settings_minimal|" in log, "Only the file component should determine settings"
    assert node in log, "Parameterized node text must reach pytest unchanged"


def test_collect_only_skips_preflight_build_and_coverage(tmp_path):
    """Collection must not run database checks, asset builds, or coverage commands."""
    result, log = _run_runtests(tmp_path, "--collect-only", "--suite", "coordinator")
    assert result.returncode == 0, "Coordinator collection should succeed"
    assert "--collect-only" in log, "Collection mode should pass its flag to pytest"
    assert "python|" not in log, "Collection should skip database preflight"
    assert not any(line.startswith("coverage|") for line in log.splitlines()), "Collection should skip coverage commands"
    assert "npm|" not in log, "Collection should skip asset builds"
    run_dir = next(tmp_path.glob("run-*"))
    assert not (run_dir / ".test-artifacts").exists(), "Collection must not create coverage directories"


def test_all_collection_uses_two_settings_processes_without_preflight(tmp_path):
    """All-suite collection should use separate consumer and coordinator processes."""
    result, log = _run_runtests(tmp_path, "--suite", "all", "--collect-only")
    calls = [line for line in log.splitlines() if line.startswith("pytest|")]
    assert result.returncode == 0, "All-suite collection should succeed"
    assert len(calls) == 2, "All-suite collection should invoke pytest once per settings set"
    assert "pytest|tests.settings|.coverage|" in calls[0], "Consumer collection should use consumer settings"
    assert "-c pytest.ini" in calls[0], "Consumer collection should use root config"
    assert "pytest|coordinator_tests.settings|.test-artifacts/coverage/coordinator/.coverage|" in calls[1], "Coordinator collection should use coordinator settings"
    assert "-c pytest-coordinator.ini" in calls[1], "Coordinator collection should use coordinator config"
    assert not any(line.startswith(("python|", "coverage|")) for line in log.splitlines()), "Collection must avoid preflight and coverage commands"


def test_bare_pytest_runs_both_server_suites_then_reports_combined_data(tmp_path):
    """The server-only route must run ordinary, minimal, Bootstrap, and coordinator suites."""
    result, log = _run_runtests(tmp_path, "--pytest")
    pytest_calls = [line for line in log.splitlines() if line.startswith("pytest|")]
    assert result.returncode == 0, "Server-only aggregate route should succeed"
    assert len(pytest_calls) == 4, "Aggregate server run should have four separately configured pytest calls"
    assert "tests.settings_minimal" in pytest_calls[1], "Minimal settings should run separately"
    assert "tests.settings_bootstrap" in pytest_calls[2], "Bootstrap server batch should run separately"
    assert "coordinator_tests.settings|.test-artifacts/coverage/coordinator/.coverage" in pytest_calls[3], "Coordinator suite should run separately"
    assert "coverage|.test-artifacts/coverage/coordinator/.coverage|combine --keep --data-file=.test-artifacts/coverage/combined/.coverage" in log, "Aggregate data should preserve both inputs"
    assert "coverage|.test-artifacts/coverage/combined/.coverage|html" in log, "Aggregate report should explicitly read combined data"


def test_all_suite_runs_two_server_processes_and_combines_coverage(tmp_path):
    """The explicit all-suite option should execute and report both server suites."""
    result, log = _run_runtests(tmp_path, "--suite", "all", "--pytest")
    calls = [line for line in log.splitlines() if line.startswith("pytest|")]
    assert result.returncode == 0, "Explicit all-suite run should succeed"
    assert len(calls) == 4, "Explicit all-suite run should separate core, minimal, Bootstrap, and coordinator processes"
    assert "pytest|tests.settings|.coverage|" in calls[0], "Consumer core should use consumer settings and data"
    assert "tests.settings_minimal" in calls[1], "Minimal tests should use their isolated settings"
    assert "tests.settings_bootstrap" in calls[2], "Bootstrap tests should use presentation settings"
    assert "coordinator_tests.settings|.test-artifacts/coverage/coordinator/.coverage" in calls[3], "Coordinator tests should use separate settings and data"
    assert "coverage|.test-artifacts/coverage/coordinator/.coverage|combine --keep --data-file=.test-artifacts/coverage/combined/.coverage" in log, "Explicit aggregate run should combine raw inputs"
    assert "coverage|.test-artifacts/coverage/combined/.coverage|html" in log, "Explicit aggregate report should read combined data"


def test_default_route_stubs_asset_build_and_runs_both_suites(tmp_path):
    """The full default route should safely reach server and browser stages in isolation."""
    result, log = _run_runtests(tmp_path, coordinator_sentinel=True)
    assert result.returncode == 0, "Stubbed default workflow should succeed"
    assert "npm|run build" in log, "Default workflow should include its existing asset build"
    assert "coordinator_tests.settings" in log, "Default workflow should include coordinator tests"
    assert log.count("--cov-append") >= 3, "Consumer and browser runs should append their coverage"
    assert log.count("combine --keep --data-file=.test-artifacts/coverage/combined/.coverage") == 2, "Coverage should be combined before and after browser appends"
    assert "coverage|.test-artifacts/coverage/combined/.coverage|html" in log, "Final report should use aggregate data"
    run_dir = next(tmp_path.glob("run-*"))
    assert (run_dir / ".test-artifacts/coverage/coordinator/.coverage").exists(), "Browser coverage must leave coordinator raw data intact"


def test_coordinator_rejects_browser_or_asset_options(tmp_path):
    """Coordinator-only execution must not build assets or run browser selections."""
    for arguments in (
        ("--suite", "coordinator", "--pytest", "--rebuild-assets"),
        ("--suite", "coordinator", "--playwright"),
    ):
        result, log = _run_runtests(tmp_path, *arguments)
        assert result.returncode != 0, "Coordinator browser/build combination should be rejected"
        assert "pytest|" not in log and "npm|" not in log, "Rejected coordinator options must have no side effects"


def test_all_suite_rejects_focused_paths(tmp_path):
    """An aggregate run cannot apply one focused path to two unrelated suites."""
    result, log = _run_runtests(tmp_path, "--suite", "all", "--pytest", "src/tests/test_async_compatibility.py")
    assert result.returncode != 0, "All-suite focused paths should be rejected"
    assert "--suite all cannot be combined" in result.stdout, "Rejection should explain the invalid combination"
    assert "pytest|" not in log, "Rejected aggregation should stop before pytest"


def test_focused_suites_keep_distinct_coverage_files(tmp_path):
    """Focused coordinator and consumer runs must select independent data files."""
    coordinator, coordinator_log = _run_runtests(
        tmp_path, "--suite", "coordinator", "--pytest", "src/coordinator_tests/test_suite_isolation.py",
    )
    consumer, consumer_log = _run_runtests(
        tmp_path, "--suite", "powercrud", "--pytest", "src/tests/test_async_compatibility.py",
    )
    assert coordinator.returncode == 0 and consumer.returncode == 0, "Both focused suite routes should succeed"
    assert ".test-artifacts/coverage/coordinator/.coverage" in coordinator_log, "Coordinator run should use its own data file"
    assert ".coverage|" in consumer_log, "Consumer run should preserve its existing data file"
    assert "combine" not in coordinator_log + consumer_log, "Focused runs must not combine stale data"


def test_consumer_coverage_reset_preserves_coordinator_data(tmp_path):
    """Preparing consumer coverage must not erase the coordinator raw data file."""
    result, _ = _run_runtests(
        tmp_path,
        "--suite", "powercrud", "--pytest",
        coordinator_sentinel=True,
        combined_sentinel=True,
    )
    run_dir = next(tmp_path.glob("run-*"))
    assert result.returncode == 0, "Full consumer route should complete with command stubs"
    assert (run_dir / ".test-artifacts/coverage/coordinator/.coverage").read_text() == "preserve coordinator data", "Consumer reset must preserve coordinator coverage"
    assert (run_dir / ".test-artifacts/coverage/combined/.coverage").read_text() == "preserve combined data", "Consumer reset must preserve existing aggregate coverage"


@pytest.mark.parametrize("failure", [7, -signal.SIGTERM])
def test_consumer_failure_preserves_other_artifacts_and_exit_status(tmp_path, failure):
    """Failure or termination must leave other artifacts untouched in their locations."""
    result, _ = _run_runtests(
        tmp_path,
        "--suite", "powercrud", "--pytest",
        pytest_exit=7 if failure > 0 else 0,
        pytest_terminate=failure < 0,
        coordinator_sentinel=True,
        combined_sentinel=True,
    )
    run_dir = next(tmp_path.glob("run-*"))
    assert result.returncode == failure, "Consumer failure or signal status should reach the caller"
    assert (run_dir / ".test-artifacts/coverage/coordinator/.coverage").read_text() == "preserve coordinator data", "Failed consumer run must leave coordinator data untouched"
    assert (run_dir / ".test-artifacts/coverage/combined/.coverage").read_text() == "preserve combined data", "Failed consumer run must leave aggregate data untouched"
    assert not list(run_dir.glob(".preserved-*")), "No coverage backup files should be created"


@pytest.mark.parametrize("missing", [".coverage", ".test-artifacts/coverage/coordinator/.coverage"])
def test_aggregate_requires_both_raw_inputs(tmp_path, missing):
    """Incomplete raw results must fail rather than generate a partial aggregate."""
    result, log = _run_runtests(tmp_path, "--suite", "all", "--pytest", omit_data=missing)
    assert result.returncode != 0, "An aggregate requires both suite files"
    assert f"missing {missing}" in result.stdout, "The error should identify the missing suite file"
    assert not any(line.startswith("coverage|") for line in log.splitlines()), "Incomplete input must stop combination and reporting"


def test_runner_propagates_pytest_failure_status(tmp_path):
    """A pytest failure must remain a failing runtests exit status."""
    result, _ = _run_runtests(
        tmp_path,
        "--suite", "coordinator", "--pytest", "src/coordinator_tests/test_suite_isolation.py", pytest_exit=7,
    )
    assert result.returncode == 7, "runtests should return the pytest failure status unchanged"
