import os
import re
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# Define regex patterns to extract class names
CLASS_REGEX = re.compile(r'class=["\']([^"\']+)["\']')
JSON_ARRAY_REGEX = re.compile(r'\[(.*?)\]', re.DOTALL)

DEFAULT_FILENAME = 'nominopolitan_tailwind_safelist.json'
def extract_classes_from_json(content):
    """Extract classes from JSON content"""
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return set(data)
    except json.JSONDecodeError:
        pass
    return set()

def extract_classes_from_txt(content):
    """Extract classes from text content, assuming one class per line"""
    return set(line.strip() for line in content.splitlines() if line.strip())

def get_help_message():
    return (
        "Output location not specified. Either:\n"
        "1. Set NM_TAILWIND_SAFELIST_JSON_LOC in your Django settings (relative to BASE_DIR), or\n"
        "2. Use --output to specify the output location\n\n"
        "Examples:\n"
        "  Settings:\n"
        "    NM_TAILWIND_SAFELIST_JSON_LOC = 'config'  # Creates BASE_DIR/config/nominopolitan_tailwind_safelist.json\n"
        "    NM_TAILWIND_SAFELIST_JSON_LOC = 'config/safelist.json'  # Uses exact filename\n"
        "  Command line:\n"
        "    --output ./config  # Creates ./config/nominopolitan_tailwind_safelist.json\n"
        "    --output ./config/safelist.json  # Uses exact filename"
    )

class Command(BaseCommand):
    help = "Extracts Tailwind CSS class names from templates, Python files, JSON files, and text files."

    def add_arguments(self, parser):
        parser.add_argument(
            '--pretty',
            action='store_true',
            help='Save and print the output in a pretty, formatted way'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Specify output path (directory or file path)'
        )

    def handle(self, *args, **kwargs):
        # Determine output location
        output_path = None
        if kwargs['output']:
            # For --output, treat path as relative to current directory
            path = Path(kwargs['output']).expanduser()
            # If path is a directory or doesn't have an extension, treat as directory
            if path.is_dir() or not path.suffix:
                output_path = path / DEFAULT_FILENAME
            else:
                output_path = path
        elif hasattr(settings, 'NM_TAILWIND_SAFELIST_JSON_LOC') and settings.NM_TAILWIND_SAFELIST_JSON_LOC:
            try:
                # For settings value, treat path as relative to BASE_DIR
                base_dir = Path(settings.BASE_DIR)
                path = Path(settings.NM_TAILWIND_SAFELIST_JSON_LOC)
                
                # Combine with BASE_DIR if it's not absolute
                if not path.is_absolute():
                    path = base_dir / path

                # If path is a directory or doesn't have an extension, treat as directory
                if path.is_dir() or not path.suffix:
                    output_path = path / DEFAULT_FILENAME
                else:
                    output_path = path
            except Exception as e:
                raise CommandError(f"Invalid NM_TAILWIND_SAFELIST_JSON_LOC setting: {str(e)}\n\n{get_help_message()}")
        else:
            raise CommandError(get_help_message())

        # Resolve the final path
        output_path = output_path.resolve()

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

        # Scan JSON files
        for json_file in package_dir.rglob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                content = f.read()
                extracted_classes.update(extract_classes_from_json(content))

        # Scan TXT files
        for txt_file in package_dir.rglob("*.txt"):
            with open(txt_file, "r", encoding="utf-8") as f:
                content = f.read()
                extracted_classes.update(extract_classes_from_txt(content))

        # Convert to a sorted list
        class_list = sorted(extracted_classes)

        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save to a JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            if kwargs['pretty']:
                json.dump(class_list, f, indent=2)
                f.write('\n')  # Add newline at end of file
            else:
                json.dump(class_list, f, separators=(',', ':'))

        # Print output
        if kwargs['pretty']:
            formatted_json = json.dumps(class_list, indent=2)
            self.stdout.write(formatted_json)
        else:
            compressed_json = json.dumps(class_list, separators=(',', ':'))
            self.stdout.write(compressed_json)

        self.stdout.write(self.style.SUCCESS(f"\nExtracted {len(class_list)} classes to {output_path}"))
