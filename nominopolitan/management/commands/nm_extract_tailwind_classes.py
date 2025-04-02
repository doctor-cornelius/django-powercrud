import os
import re
import json
from pathlib import Path
from django.core.management.base import BaseCommand

# Define regex pattern to extract class names
CLASS_REGEX = re.compile(r'class=["\']([^"\']+)["\']')

class Command(BaseCommand):
    help = "Extracts Tailwind CSS class names from templates and Python files."

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

        # Save to a JSON file
        output_file = base_dir / "tailwind_safelist.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(class_list, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Extracted {len(class_list)} classes to {output_file}"))
