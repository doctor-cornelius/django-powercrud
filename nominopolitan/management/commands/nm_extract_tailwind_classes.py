import os
import re
import json
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

DEFAULT_FILENAME = 'nominopolitan_tailwind_safelist.json'

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
    help = "Copies the compiled Tailwind CSS file to the specified location for use in safelist."

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Specify output path (directory or file path)'
        )
        parser.add_argument(
            '--legacy',
            action='store_true',
            help='Use legacy method of extracting classes from templates and files'
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

        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Find the package directory
        base_dir = Path(__file__).resolve().parent.parent.parent
        assets_dir = base_dir / "assets" / "django_assets"
        
        if not assets_dir.exists():
            raise CommandError(f"Assets directory not found at {assets_dir}")
        
        # Find the first CSS file in the assets directory
        css_files = list(assets_dir.glob("*.css"))
        if not css_files:
            raise CommandError(f"No CSS files found in {assets_dir}")
        
        css_file = css_files[0]
        self.stdout.write(f"Using compiled CSS file: {css_file}")
        
        # Copy the CSS file to the output location
        shutil.copy2(css_file, output_path)
        
        self.stdout.write(self.style.SUCCESS(f"\nCopied CSS file to {output_path}"))
