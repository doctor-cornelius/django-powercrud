import os
import re
import json
from pathlib import Path
from django.core.management.base import BaseCommand

# Define regex pattern to extract class names
CLASS_REGEX = re.compile(r'class=["\']([^"\']+)["\']')

class Command(BaseCommand):
    help = "Extracts Tailwind CSS class names from templates and Python files."

    def add_arguments(self, parser):
        parser.add_argument(
            '--pretty',
            action='store_true',
            help='Print the output in a pretty, formatted way'
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

        # Save to a JSON file in compressed format
        output_file = base_dir / "tailwind_safelist.json"
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
