#!/usr/bin/env python3
"""Build-independent clean-install validation for selectable template packs."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import types
from importlib.resources import files
from pathlib import Path, PurePosixPath


SELECTORS = (
    "daisyui",
    "powercrud.contrib.bootstrap5:template_pack",
)
PROBE_REQUIREMENTS = (
    "Django>=5.2,<7",
    "django-crispy-forms>=2.5,<3",
    "crispy-tailwind>=1.0.3,<2",
    "crispy-bootstrap5>=2026.3,<2027",
)
BOOTSTRAP_RUNTIME_FILES = (
    "contrib/bootstrap5/static/powercrud/contrib/bootstrap5/css/bootstrap5.css",
    "contrib/bootstrap5/static/powercrud/contrib/bootstrap5/js/bootstrap5.js",
    "contrib/bootstrap5/static/powercrud/contrib/bootstrap5/js/runtime/bootstrap5-action-selection-adapter.js",
    "contrib/bootstrap5/static/powercrud/contrib/bootstrap5/js/runtime/bootstrap5-composition.js",
    "contrib/bootstrap5/static/powercrud/contrib/bootstrap5/js/runtime/bootstrap5-floating-panel-adapter.js",
    "contrib/bootstrap5/static/powercrud/contrib/bootstrap5/js/runtime/bootstrap5-inline-presentation-adapter.js",
    "contrib/bootstrap5/static/powercrud/contrib/bootstrap5/js/runtime/bootstrap5-modal-adapter.js",
    "contrib/bootstrap5/static/powercrud/contrib/bootstrap5/js/runtime/bootstrap5-searchable-select-adapter.js",
    "contrib/bootstrap5/static/powercrud/contrib/bootstrap5/js/runtime/bootstrap5-tooltip-adapter.js",
)


def _run(command: list[str]) -> None:
    """Run one required subprocess without inheriting the source checkout as a package."""
    subprocess.run(command, check=True)


def _is_within(path: Path, parent: Path) -> bool:
    """Return whether one resolved path is inside another resolved path."""
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _probe_installed_artifact(source_root: Path) -> None:
    """Validate all distributed declarations from the active isolated environment."""
    from crispy_forms.helper import FormHelper
    from django import forms
    from django.conf import settings
    from django.template.loader import render_to_string

    probe_urlconf = types.ModuleType("powercrud_artifact_probe_urls")
    probe_urlconf.urlpatterns = []
    sys.modules[probe_urlconf.__name__] = probe_urlconf

    if not settings.configured:
        settings.configure(
            SECRET_KEY="template-pack-artifact-probe",
            INSTALLED_APPS=(
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "django.contrib.staticfiles",
                "crispy_forms",
                "crispy_tailwind",
                "crispy_bootstrap5",
                "powercrud",
                "powercrud.contrib.bootstrap5",
            ),
            TEMPLATES=(
                {
                    "BACKEND": "django.template.backends.django.DjangoTemplates",
                    "APP_DIRS": True,
                },
            ),
            ROOT_URLCONF=probe_urlconf.__name__,
            STATIC_URL="/static/",
            CRISPY_ALLOWED_TEMPLATE_PACKS=("tailwind", "bootstrap5"),
            CRISPY_TEMPLATE_PACK="tailwind",
        )

    import django

    django.setup()

    import powercrud
    from powercrud.template_pack_validation import validate_template_pack
    from powercrud.template_packs import resolve_template_pack

    package_path = Path(powercrud.__file__).resolve()
    if _is_within(package_path, source_root):
        raise SystemExit(
            "Installed-resource probe imported powercrud from the source checkout: "
            f"{package_path}"
        )

    package_root = files("powercrud")
    for relative_path in BOOTSTRAP_RUNTIME_FILES:
        resource = package_root.joinpath(*PurePosixPath(relative_path).parts)
        if not resource.is_file():
            raise SystemExit(
                "Installed-resource probe could not find the Bootstrap runtime file: "
                f"{relative_path}"
            )

    class RequiredNameForm(forms.Form):
        """Expose native and crispy validation output from the installed package."""

        name = forms.CharField(label="Display name")

    for selector in SELECTORS:
        template_pack = resolve_template_pack(selector)
        validate_template_pack(template_pack)
        form = RequiredNameForm(data={"name": ""})
        form.helper = FormHelper()
        form.helper.form_tag = False
        form.helper.disable_csrf = True
        if form.is_valid():
            raise SystemExit(
                f"Installed-resource probe expected a bound validation error for {selector}"
            )
        settings.CRISPY_TEMPLATE_PACK = next(
            iter(template_pack.crispy_template_packs), settings.CRISPY_TEMPLATE_PACK
        )
        for use_crispy, renderer_name in ((False, "native"), (True, "crispy")):
            rendered = render_to_string(
                f"{template_pack.template_namespace}/partial/form_fields.html",
                {
                    "form": form,
                    "use_crispy": use_crispy,
                    "framework_template_path": template_pack.template_namespace,
                },
            )
            if not all(
                expected in rendered
                for expected in ('name="name"', "Display name", "This field is required")
            ):
                raise SystemExit(
                    f"Installed-resource probe could not render {renderer_name} form output "
                    f"for {selector}"
                )
            if "<form" in rendered:
                raise SystemExit(
                    f"Installed-resource probe found a nested form in {renderer_name} output "
                    f"for {selector}"
                )
        print(
            f"validated {template_pack.identity} from {package_path.parent} "
            f"using selector {selector}"
        )


def _parse_arguments() -> argparse.Namespace:
    """Parse either an installed probe request or one or more artifact requests."""
    parser = argparse.ArgumentParser(
        description="Validate selectable PowerCRUD packs from isolated installed artifacts."
    )
    parser.add_argument(
        "artifacts",
        metavar="ARTIFACT",
        nargs="*",
        type=Path,
        help="Wheel and/or sdist files to install into separate temporary environments.",
    )
    parser.add_argument(
        "--probe-installed",
        action="store_true",
        help="Run the installed-package probe in the current interpreter.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path.cwd(),
        help="Source checkout that the installed probe must not import from.",
    )
    arguments = parser.parse_args()
    if arguments.probe_installed == bool(arguments.artifacts):
        parser.error("provide artifacts or --probe-installed, but not both")
    return arguments


def main() -> None:
    """Install each artifact in a fresh environment, then prove its resources work."""
    arguments = _parse_arguments()
    source_root = arguments.source_root.resolve()
    if arguments.probe_installed:
        _probe_installed_artifact(source_root)
        return

    for artifact in arguments.artifacts:
        artifact = artifact.resolve()
        if not artifact.is_file():
            raise SystemExit(f"Artifact does not exist: {artifact}")
        with tempfile.TemporaryDirectory(prefix="powercrud-template-pack-") as directory:
            environment = Path(directory) / "venv"
            interpreter = environment / "bin" / "python"
            _run(["uv", "venv", "--clear", str(environment)])
            _run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--python",
                    str(interpreter),
                    *PROBE_REQUIREMENTS,
                    str(artifact),
                ]
            )
            _run(
                [
                    str(interpreter),
                    "-I",
                    str(Path(__file__).resolve()),
                    "--probe-installed",
                    "--source-root",
                    str(source_root),
                ]
            )
            print(f"installed-resource gate passed for {artifact.name}")


if __name__ == "__main__":
    main()
