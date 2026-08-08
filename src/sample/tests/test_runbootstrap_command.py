"""Tests for the sample app's Bootstrap development-server command."""

from pathlib import Path
import sys

import pytest
from django.conf import settings
from django.core.management import call_command

from sample.management.commands import runbootstrap


def test_runbootstrap_requires_an_explicit_port(capsys):
    """Calling runbootstrap without --port should show the exact usage example."""
    command = runbootstrap.Command()

    with pytest.raises(SystemExit) as exc_info:
        command.run_from_argv(["./manage.py", "runbootstrap"])

    error_output = capsys.readouterr().err
    assert exc_info.value.code == 2, "A missing --port option should be a CLI error."
    assert runbootstrap.MISSING_PORT_MESSAGE in error_output, (
        "The missing-port error should explain how to launch the command."
    )


def test_runbootstrap_reexecutes_runserver_with_bootstrap_settings(monkeypatch):
    """The command should start runserver with Bootstrap settings on the chosen port."""
    exec_call = {}

    def capture_exec(executable, arguments):
        """Capture the process replacement without starting a development server."""
        exec_call["executable"] = executable
        exec_call["arguments"] = arguments

    monkeypatch.setattr(runbootstrap.os, "execv", capture_exec)

    call_command("runbootstrap", port=8003)

    assert exec_call["executable"] == sys.executable, (
        "The replacement process should use the active Python interpreter."
    )
    assert exec_call["arguments"] == [
        sys.executable,
        str(Path(settings.BASE_DIR) / "manage.py"),
        "runserver",
        "--settings=config.settings_bootstrap",
        "0.0.0.0:8003",
    ], "The replacement command should select Bootstrap settings and bind the requested port."


@pytest.mark.parametrize("port", ["0", "65536", "not-a-port"])
def test_runbootstrap_rejects_invalid_ports(port, capsys):
    """The command should reject values outside the valid TCP port range."""
    command = runbootstrap.Command()

    with pytest.raises(SystemExit) as exc_info:
        command.run_from_argv(["./manage.py", "runbootstrap", "--port", port])

    error_output = capsys.readouterr().err
    assert exc_info.value.code == 2, "An invalid --port value should be a CLI error."
    assert "Port must be an integer between 1 and 65535." in error_output, (
        "The invalid-port error should explain the accepted range."
    )
