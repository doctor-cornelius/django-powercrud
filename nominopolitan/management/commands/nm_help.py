from django.core.management.base import BaseCommand
import os
import sys
from pathlib import Path
import importlib.resources

class Command(BaseCommand):
    help = "Displays the Nominopolitan README.md documentation in a paginated format"

    def add_arguments(self, parser):
        parser.add_argument(
            '--lines',
            type=int,
            default=20,
            help='Number of lines to display per page (default: 20)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Display entire content without pagination',
        )

    def handle(self, *args, **options):
        try:
            # First try to get README from package resources
            try:
                import nominopolitan
                with importlib.resources.files(nominopolitan).joinpath('README.md').open('r', encoding='utf-8') as f:
                    content = f.readlines()
            except (ImportError, FileNotFoundError):
                # Fallback to local development path
                package_dir = Path(__file__).resolve().parent.parent.parent.parent
                readme_path = package_dir / 'README.md'
                
                if not readme_path.exists():
                    self.stdout.write(
                        self.style.ERROR('README.md not found in the package directory')
                    )
                    return

                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.readlines()

            if options['all']:
                # Display entire content at once
                for line in content:
                    self.stdout.write(line.rstrip())
                return

            lines_per_page = options['lines']
            total_lines = len(content)
            current_line = 0

            while current_line < total_lines:
                # Display a page of content
                for i in range(current_line, min(current_line + lines_per_page, total_lines)):
                    self.stdout.write(content[i].rstrip())

                current_line += lines_per_page

                # If we're not at the end, prompt for next page
                if current_line < total_lines:
                    self.stdout.write('\n' + '-' * 80)
                    self.stdout.write(
                        self.style.WARNING(
                            f'Showing lines {current_line - lines_per_page + 1}-{min(current_line, total_lines)} '
                            f'of {total_lines}. Press Enter for next page, q to quit: '
                        )
                    )
                    
                    if input().lower() == 'q':
                        break

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading README.md: {str(e)}')
            )
