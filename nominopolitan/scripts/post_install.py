import subprocess
from pathlib import Path

def run():
    """
    Post-installation script that runs after package is installed.
    """
    try:
        # Try to import Django settings
        from django.conf import settings
        safelist_location = getattr(settings, 'NM_TAILWIND_SAFELIST_JSON_LOC', None)
        
        if safelist_location:
            # Settings exist, try to run the command
            subprocess.run([
                "python", "-m", "django",
                "nm_extract_tailwind_classes",
                "--pretty"
            ])
            print("\n✨ Nominopolitan: Tailwind safelist generated successfully")
        else:
            _print_help_message()
    except (ImportError, Exception):
        _print_help_message()

def _print_help_message():
    print("\n📦 Nominopolitan post-install:")
    print("To generate Tailwind safelist, either:")
    print("1. Add NM_TAILWIND_SAFELIST_JSON_LOC to your Django settings:")
    print("   NM_TAILWIND_SAFELIST_JSON_LOC = 'config'  # Creates BASE_DIR/config/nominopolitan_tailwind_safelist.json")
    print("   NM_TAILWIND_SAFELIST_JSON_LOC = 'config/safelist.json'  # Uses exact filename")
    print("\n2. Or run the command manually with an output location:")
    print("   python manage.py nm_extract_tailwind_classes --output ./config")
    print("   python manage.py nm_extract_tailwind_classes --output ./config/safelist.json")

def main():
    run()

if __name__ == "__main__":
    main()
