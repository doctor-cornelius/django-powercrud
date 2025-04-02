import os
import re
import json
from pathlib import Path
from django.core.management.base import BaseCommand

# Define regex pattern to extract class names
CLASS_REGEX = re.compile(r'class=["\']([^"\']+)["\']')
DEFAULT_FILENAME = "nominopolitan_tailwind_safelist.json"

class Command(BaseCommand):
    help = "Extracts Tailwind CSS class names from templates and Python files."

    def add_arguments(self, parser):
        parser.add_argument(
            '--pretty',
            action='store_true',
            help='Print the output in a pretty, formatted way'
        )
        parser.add_argument(
            '--package-dir',
            action='store_true',
            help='Save the file in the package directory instead of current working directory'
        )
        parser.add_argument(
            '--output',
            type=str,
            help=f'Specify output path (relative to current directory or absolute). If a directory is specified, {DEFAULT_FILENAME} will be created inside it'
        )

    def handle(self, *args, **kwargs):
        base_dir = Path(__file__).resolve().parent.parent.parent
        templates_dir = base_dir / "templates"
        package_dir = base_dir

        extracted_classes = set()

        # Scan HTML templates
        for html_file in templates_dir.rglob("*.html"):
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()
                for match in CLASS_REGEX.findall(content):
                    extracted_classes.update(match.split())

        # Scan Python files for class names inside strings
        for py_file in package_dir.rglob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                for match in CLASS_REGEX.findall(content):
                    extracted_classes.update(match.split())

        # Convert to a sorted list
        class_list = sorted(extracted_classes)

        # Determine output location
        if kwargs['output']:
            output_path = Path(kwargs['output']).expanduser().resolve()
            # If output_path is a directory, append the default filename
            if output_path.is_dir():
                output_file = output_path / DEFAULT_FILENAME
            else:
                output_file = output_path
        elif kwargs['package_dir']:
            output_file = base_dir / DEFAULT_FILENAME
        else:
            output_file = Path.cwd() / DEFAULT_FILENAME

        # Create directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save to a JSON file in compressed format
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(class_list, f, separators=(',', ':'))

        # Print output based on format preference
        if kwargs['pretty']:
            formatted_json = json.dumps(class_list, indent=2)
            self.stdout.write(formatted_json)
        else:
            compressed_json = json.dumps(class_list, separators=(',', ':'))
            self.stdout.write(compressed_json)

        self.stdout.write(self.style.SUCCESS(f"\nExtracted {len(class_list)} classes to {output_file}"))
