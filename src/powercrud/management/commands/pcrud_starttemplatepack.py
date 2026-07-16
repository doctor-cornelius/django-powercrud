"""Create a separately distributable starter package for a PowerCRUD pack."""

from __future__ import annotations

import shutil
from importlib.resources import files
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from powercrud.template_packs import TemplatePack, resolve_template_pack


class Command(BaseCommand):
    """Create a plain, editable package rather than registering a framework upstream."""

    help = (
        "Create a standalone PowerCRUD template-pack package from a maintained "
        "template source."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "package",
            help="Python package name to create, for example my_powercrud_pack.",
        )
        parser.add_argument(
            "destination",
            type=Path,
            help="New empty directory that will contain the package project.",
        )
        parser.add_argument(
            "--source-template-pack",
            default="daisyui",
            help=(
                "Template source: daisyui (default), bootstrap5, or a "
                "module.path:attribute selector."
            ),
        )
        parser.add_argument(
            "--identity",
            default=None,
            help="Pack identity used in template and static paths (default: package name).",
        )

    def handle(self, *args, **options):
        package_name = options["package"]
        self._validate_package_name(package_name)
        identity = options["identity"] or package_name.rsplit(".", 1)[-1].replace("_", "-")
        self._validate_identity(identity)
        destination = options["destination"]
        if destination.exists() and any(destination.iterdir()):
            raise CommandError(f"Destination {destination} must be new or empty.")

        selector = self._source_selector(options["source_template_pack"])
        try:
            source_pack = resolve_template_pack(selector)
        except Exception as exc:
            raise CommandError(f"Could not load source template pack {selector!r}: {exc}") from exc

        package_dir = destination / "src" / Path(*package_name.split("."))
        template_destination = package_dir / "templates" / "powercrud" / "packs" / identity
        source_templates = Path(
            files(source_pack.template_package).joinpath(
                *Path(source_pack.template_resource_root).parts
            )
        )
        if not source_templates.is_dir():
            raise CommandError(f"Source pack templates were not found at {source_templates}.")

        destination.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copytree(source_templates, template_destination, dirs_exist_ok=True)
            self._write_package_files(package_dir, package_name, identity, source_pack)
            self._write_project_files(destination, package_name, identity)
        except OSError as exc:
            raise CommandError(f"Could not create starter pack: {exc}") from exc

        selector_path = f"{package_name}.template_pack:template_pack"
        self.stdout.write(
            self.style.SUCCESS(
                "Created a standalone PowerCRUD template-pack starter.\n"
                f"Templates copied from: {source_pack.identity}\n"
                f"Package project: {destination}\n\n"
                "Next: replace the copied framework classes, implement only the adapter "
                "hooks your framework needs, then build and test this package.\n"
                "Consumers install it, add its Django app to INSTALLED_APPS, and select:\n"
                "POWERCRUD_SETTINGS = {\n"
                f'    "POWERCRUD_TEMPLATE_PACK": "{selector_path}",\n'
                "}"
            )
        )

    @staticmethod
    def _source_selector(value: str) -> str:
        return {"daisyui": "daisyui", "bootstrap5": "powercrud.contrib.bootstrap5:template_pack"}.get(value, value)

    @staticmethod
    def _validate_package_name(package_name: str) -> None:
        if not package_name or not all(part.isidentifier() for part in package_name.split(".")):
            raise CommandError("package must be a dotted Python package name.")

    @staticmethod
    def _validate_identity(identity: str) -> None:
        if not identity or "/" in identity or "\\" in identity or identity in {".", ".."}:
            raise CommandError("identity must be one safe path segment.")

    def _write_package_files(
        self,
        package_dir: Path,
        package_name: str,
        identity: str,
        source_pack: TemplatePack,
    ) -> None:
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "__init__.py").write_text(
            '"""An independently maintained PowerCRUD template pack."""\n', encoding="utf-8"
        )
        (package_dir / "apps.py").write_text(
            "from django.apps import AppConfig\n\n\n"
            "class TemplatePackConfig(AppConfig):\n"
            f'    name = "{package_name}"\n',
            encoding="utf-8",
        )
        (package_dir / "adapter.py").write_text(
            "from powercrud.template_packs import BaseServerAdapter\n\n\n"
            "class ServerAdapter(BaseServerAdapter):\n"
            "    \"\"\"Add only framework-specific server presentation here.\"\"\"\n\n\n"
            "server_adapter = ServerAdapter()\n",
            encoding="utf-8",
        )
        (package_dir / "template_pack.py").write_text(
            "from powercrud.template_packs import (\n"
            "    BrowserAdapterSpec,\n    PackAssets,\n    PackageResource,\n"
            "    TEMPLATE_PACK_CONTRACT_VERSION,\n    TemplatePack,\n)\n\n"
            "from .adapter import server_adapter\n\n\n"
            "template_pack = TemplatePack(\n"
            f'    identity="{identity}",\n'
            "    contract_version=TEMPLATE_PACK_CONTRACT_VERSION,\n"
            f'    template_namespace="powercrud/packs/{identity}",\n'
            f'    template_package="{package_name}",\n'
            f'    template_resource_root="templates/powercrud/packs/{identity}",\n'
            f'    server_adapter="{package_name}.adapter:server_adapter",\n'
            f"    capabilities=frozenset({sorted(source_pack.capabilities)!r}),\n"
            "    supports_native_forms=True,\n"
            f'    django_app="{package_name}",\n'
            "    assets=PackAssets(\n"
            f'        stylesheets=("powercrud/packs/{identity}/css/powercrud.css",),\n'
            f'        copy_roots=(PackageResource("{package_name}", "static/powercrud/packs/{identity}"),),\n'
            "        browser_adapter=BrowserAdapterSpec(\n"
            "            api_version=1,\n"
            f'            static_path="powercrud/packs/{identity}/js/adapter.js",\n'
            f'            source=PackageResource("{package_name}", "static/powercrud/packs/{identity}/js/adapter.js"),\n'
            "        ),\n"
            "    ),\n"
            ")\n",
            encoding="utf-8",
        )
        static_dir = package_dir / "static" / "powercrud" / "packs" / identity
        (static_dir / "css").mkdir(parents=True, exist_ok=True)
        (static_dir / "js").mkdir(parents=True, exist_ok=True)
        (static_dir / "css" / "powercrud.css").write_text(
            "/* Add this pack's framework CSS or small PowerCRUD adjustments here. */\n",
            encoding="utf-8",
        )
        (static_dir / "js" / "adapter.js").write_text(
            "// This minimal adapter uses PowerCRUD's neutral browser defaults.\n"
            "// Add only hooks needed by this framework; no-op hooks are supplied by core.\n"
            "window.PowerCRUDAdapter = Object.freeze({\n"
            "    apiVersion: 1,\n"
            f"    identity: '{identity}',\n"
            "    create() { return {}; },\n"
            "});\n",
            encoding="utf-8",
        )

    @staticmethod
    def _write_project_files(destination: Path, package_name: str, identity: str) -> None:
        distribution_name = package_name.replace("_", "-").replace(".", "-")
        package_path = "/".join(package_name.split("."))
        destination.joinpath("pyproject.toml").write_text(
            "[build-system]\nrequires = [\"hatchling\"]\nbuild-backend = \"hatchling.build\"\n\n"
            "[project]\n"
            f'name = "{distribution_name}"\nversion = "0.1.0"\n'
            'requires-python = ">=3.11"\n'
            'dependencies = ["django-powercrud"]\n\n'
            "[tool.hatch.build.targets.wheel]\n"
            f'packages = ["src/{package_path}"]\n\n'
            "[tool.hatch.build.targets.sdist]\n"
            f'include = ["src/{package_path}/**", "tests/**", "README.md"]\n',
            encoding="utf-8",
        )
        destination.joinpath("README.md").write_text(
            f"# {distribution_name}\n\n"
            "A PowerCRUD template-pack starter. See PowerCRUD's template-pack authoring guide.\n"
            f"Its template-pack identity is `{identity}`.\n",
            encoding="utf-8",
        )
        tests_dir = destination / "tests"
        tests_dir.mkdir(exist_ok=True)
        tests_dir.joinpath("test_contract.py").write_text(
            "from powercrud.template_pack_testing import assert_template_pack_conforms\n\n\n"
            "def test_template_pack_contract():\n"
            "    assert_template_pack_conforms(\n"
            f'        "{package_name}.template_pack:template_pack"\n'
            "    )\n",
            encoding="utf-8",
        )
