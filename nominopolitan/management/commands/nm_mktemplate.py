import shutil
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import TemplateDoesNotExist, get_template
from django.template.engine import Engine
from django.apps import apps
from django.conf import settings


class Command(BaseCommand):
    help = "Bootstrap CRUD templates, either individual templates or the complete framework structure."

    template_prefix = f"nominopolitan/{getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'bootstrap5')}"

    def add_arguments(self, parser):
        # Main argument group
        parser.add_argument(
            "target",
            type=str,
            help="The target app name, or app.Model for templates",
        )

        # Mutually exclusive group for template selection
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--all",
            action="store_true",
            help="Copy all templates (if app.Model specified: all CRUD templates for model, otherwise: entire template structure)",
        )
        group.add_argument(
            "-l",
            "--list",
            action="store_const",
            const="list",
            dest="role",
            help="List template",
        )
        group.add_argument(
            "-d",
            "--detail",
            action="store_const",
            const="detail",
            dest="role",
            help="Detail template",
        )
        group.add_argument(
            "-c",
            "--create",
            action="store_const",
            const="form",
            dest="role",
            help="Create template",
        )
        group.add_argument(
            "-u",
            "--update",
            action="store_const",
            const="form",
            dest="role",
            help="Update template",
        )
        group.add_argument(
            "-f",
            "--form",
            action="store_const",
            const="form",
            dest="role",
            help="Form template",
        )
        group.add_argument(
            "--delete",
            action="store_const",
            const="delete",
            dest="role",
            help="Delete template",
        )

        # Optional model name for single template operations
        parser.add_argument(
            "model",
            nargs="?",
            type=str,
            help="The ModelName to bootstrap a template for (required except with --all).",
        )

    def handle(self, *args, **options):
        try:
            # Try to split as app.Model
            app_name, model_name = options["target"].split(".")
            is_model_specific = True
        except ValueError:
            # If no dot, treat as app name only
            app_name = options["target"]
            model_name = None
            is_model_specific = False

        try:
            app_config = apps.get_app_config(app_name)
        except LookupError:
            raise CommandError(f"App '{app_name}' not found. Is it in INSTALLED_APPS?")

        # Determine target directory
        target_dir = Path(app_config.path) / "templates"
        app_template_dir = target_dir / app_name

        if options["all"]:
            if is_model_specific:
                self._copy_all_model_templates(model_name, target_dir, app_template_dir)
            else:
                self._copy_template_structure(target_dir, app_template_dir)
        else:
            if not is_model_specific:
                raise CommandError("Model must be specified for single template operations (e.g., 'sample.Book')")
            options["model"] = model_name
            self._copy_single_template(options, target_dir, app_template_dir)

    def _copy_template_structure(self, target_dir, app_template_dir):
        """Copy the entire template structure to the target app."""
        # Find the source template directory in the nominopolitan package
        try:
            # Get the nominopolitan package directory
            nominopolitan_dir = Path(__file__).resolve().parent.parent.parent
            source_dir = nominopolitan_dir / "templates" / self.template_prefix

            if not source_dir.exists():
                raise CommandError(
                    f"Could not find template directory: {source_dir}\n"
                    f"Make sure nominopolitan is installed correctly and templates are available."
                )

            # Create target directories if they don't exist
            target_dir.mkdir(exist_ok=True)
            app_template_dir.mkdir(exist_ok=True)

            # Copy the entire template structure
            framework_dir = Path(self.template_prefix).name  # gets 'bootstrap5' from 'nominopolitan/bootstrap5'
            target_framework_dir = app_template_dir / framework_dir
            
            if target_framework_dir.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Target directory {target_framework_dir} already exists. Files will be overwritten."
                    )
                )

            shutil.copytree(source_dir, target_framework_dir, dirs_exist_ok=True)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully copied template structure:\n"
                    f"From: {source_dir}\n"
                    f"To: {target_framework_dir}"
                )
            )

        except Exception as e:
            raise CommandError(f"Failed to copy template structure: {str(e)}")

    def _copy_single_template(self, options, target_dir, app_template_dir):
        """Copy a single template file."""
        model = options["model"]
        role = options["role"]

        if role == "list":
            suffix = "_list.html"
        elif role == "detail":
            suffix = "_detail.html"
        elif role == "form":
            suffix = "_form.html"
        elif role == "delete":
            suffix = "_confirm_delete.html"

        template_name = f"{model.lower()}{suffix}"
        source_template_name = f"{self.template_prefix}/object{suffix}"

        try:
            # Get the nominopolitan package directory
            nominopolitan_dir = Path(__file__).resolve().parent.parent.parent
            source_path = nominopolitan_dir / "templates" / f"{self.template_prefix}/object{suffix}"

            if not source_path.exists():
                raise CommandError(f"Template not found: {source_path}")

            # Create target directories if they don't exist
            target_dir.mkdir(exist_ok=True)
            app_template_dir.mkdir(exist_ok=True)

            # Copy the template
            target_path = app_template_dir / template_name
            shutil.copy2(source_path, target_path)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully copied template:\n"
                    f"From: {source_path}\n"
                    f"To: {target_path}"
                )
            )
        except Exception as e:
            raise CommandError(f"Failed to copy template: {str(e)}")

    def _copy_all_model_templates(self, model_name, target_dir, app_template_dir):
        """Copy all CRUD templates for a specific model."""
        templates = {
            "list": "_list.html",
            "detail": "_detail.html",
            "form": "_form.html",
            "delete": "_confirm_delete.html"
        }

        # Create target directories if they don't exist
        target_dir.mkdir(exist_ok=True)
        app_template_dir.mkdir(exist_ok=True)

        for template_type, suffix in templates.items():
            try:
                # Get the nominopolitan package directory
                nominopolitan_dir = Path(__file__).resolve().parent.parent.parent
                source_path = nominopolitan_dir / "templates" / f"{self.template_prefix}/object{suffix}"

                if not source_path.exists():
                    self.stdout.write(
                        self.style.WARNING(f"Template not found: {source_path}")
                    )
                    continue

                template_name = f"{model_name.lower()}{suffix}"
                target_path = app_template_dir / template_name
                
                shutil.copy2(source_path, target_path)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully copied {template_type} template:\n"
                        f"From: {source_path}\n"
                        f"To: {target_path}"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Failed to copy {template_type} template: {str(e)}")
                )
