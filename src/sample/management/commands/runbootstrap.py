"""Run the bundled sample app with its Bootstrap 5 settings overlay."""

from __future__ import annotations

import os
import sys
from argparse import ArgumentTypeError
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


MISSING_PORT_MESSAGE = (
    "A port is required. Run the command using this syntax: "
    "./manage.py runbootstrap --port 8003"
)


def parse_port(value: str) -> int:
    """Return a valid TCP port parsed from a command-line value."""
    try:
        port = int(value)
    except ValueError as exc:
        raise ArgumentTypeError("Port must be an integer between 1 and 65535.") from exc

    if not 1 <= port <= 65535:
        raise ArgumentTypeError("Port must be an integer between 1 and 65535.")
    return port


class Command(BaseCommand):
    """Start Django's development server using the Bootstrap sample settings."""

    help = "Run the bundled sample app using the Bootstrap 5 presentation."
    missing_args_message = MISSING_PORT_MESSAGE
    requires_system_checks: list[str] = []

    def add_arguments(self, parser) -> None:
        """Require the port that the Bootstrap development server should use."""
        parser.add_argument(
            "--port",
            required=True,
            type=parse_port,
            help="Port to bind the Bootstrap sample server to, for example 8003.",
        )

    def handle(self, *args, **options) -> None:
        """Replace this process with runserver using the Bootstrap settings overlay."""
        manage_py = Path(settings.BASE_DIR) / "manage.py"
        command = [
            sys.executable,
            str(manage_py),
            "runserver",
            "--settings=config.settings_bootstrap",
            f"0.0.0.0:{options['port']}",
        ]
        os.execv(sys.executable, command)
