from pathlib import Path
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Generates paths for Tailwind CSS configuration"

    def handle(self, *args, **options):
        template_dir = Path(__file__).resolve().parent.parent.parent / "templates"
        paths = [
            str(template_dir / "**/*.html"),
            str(Path(__file__).resolve().parent.parent.parent / "**/*.py"),
        ]
        
        self.stdout.write("Add these paths to your tailwind.config.js content array:\n")
        for path in paths:
            self.stdout.write(f"    '{path}',")

if __name__ == "__main__":
    cmd = Command()
    cmd.handle()
