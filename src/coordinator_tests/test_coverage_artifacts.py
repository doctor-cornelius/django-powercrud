"""Check real pytest-cov output and combination in an isolated temporary directory."""

import configparser
import os
import shlex
import subprocess
import sys
from pathlib import Path

from coverage import CoverageData


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_real_pytest_cov_artifacts_are_independent_and_combine_without_loss(tmp_path):
    """Use the real coordinator config/plugin to protect output creation and isolation."""
    pytest_config = tmp_path / "pytest.ini"
    pytest_config.write_text("[pytest]\n")
    probe = tmp_path / "test_probe.py"
    context_path = REPOSITORY_ROOT / "src/powercrud/_coordinator/context.py"
    probe.write_text(
        "import runpy\n"
        "def test_context_probe():\n"
        f"    context = runpy.run_path({str(context_path)!r})\n"
        "    assert context['get_current_task']() is None, 'Fresh context should be empty'\n"
    )
    environment = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("COVERAGE_", "COV_CORE_"))
        and key not in ("PYTEST_ADDOPTS", "DJANGO_SETTINGS_MODULE")
    }
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    environment["PYTHONPATH"] = str(REPOSITORY_ROOT / "src")

    def run(*arguments):
        """Execute actual tools without inheriting the outer suite's coverage session."""
        result = subprocess.run(
            [sys.executable, *arguments], cwd=tmp_path, env=environment,
            text=True, capture_output=True, timeout=30, check=False,
        )
        assert result.returncode == 0, f"Tool failed: {arguments}\n{result.stdout}\n{result.stderr}"

    def read(path):
        """Read measured file/line data using the public API."""
        data = CoverageData(basename=str(path))
        data.read()
        return {name: set(data.lines(name) or []) for name in data.measured_files()}

    common = ("-m", "pytest", "-c", str(pytest_config), "-p", "pytest_cov.plugin", "--cov-report=", str(probe))
    coordinator_options = ("--cov", f"--cov-config={REPOSITORY_ROOT / '.coveragerc-coordinator'}")
    parser = configparser.ConfigParser()
    parser.read(REPOSITORY_ROOT / "pytest.ini")
    consumer_options = shlex.split(parser["pytest"]["addopts"])
    coordinator = tmp_path / ".test-artifacts/coverage/coordinator/.coverage"
    combined = tmp_path / ".test-artifacts/coverage/combined/.coverage"
    consumer = tmp_path / ".coverage"

    run(*common, *coordinator_options)
    assert coordinator.is_file(), "The actual coordinator config must emit its selected data file"
    assert str(context_path) in read(coordinator), "The artifact must contain measured coordinator code"
    assert not consumer.exists(), "Coordinator output must not overwrite the consumer location"
    combined.parent.mkdir(parents=True)
    seed = CoverageData(basename=str(combined))
    seed.add_lines({str(tmp_path / "obsolete.py"): {1}})
    seed.write()
    coordinator_before, combined_before = coordinator.read_bytes(), combined.read_bytes()

    run(*common, *consumer_options)
    assert consumer.is_file(), "Real consumer pytest-cov must create its raw data"
    assert coordinator.read_bytes() == coordinator_before, "Consumer execution must preserve coordinator bytes"
    assert combined.read_bytes() == combined_before, "Consumer execution must preserve aggregate bytes"
    consumer_before = consumer.read_bytes()
    run(*common, *coordinator_options)
    assert consumer.read_bytes() == consumer_before, "Coordinator execution must preserve consumer bytes"
    assert combined.read_bytes() == combined_before, "Coordinator execution must preserve aggregate bytes"

    coordinator_before = coordinator.read_bytes()
    expected = read(consumer)
    for name, lines in read(coordinator).items():
        expected.setdefault(name, set()).update(lines)
    run("-m", "coverage", "combine", "--keep", f"--data-file={combined}", str(consumer), str(coordinator))
    assert read(combined) == expected, "Combination must replace stale data with the exact input union"
    assert consumer.read_bytes() == consumer_before, "Combination must retain consumer data unchanged"
    assert coordinator.read_bytes() == coordinator_before, "Combination must retain coordinator data unchanged"
