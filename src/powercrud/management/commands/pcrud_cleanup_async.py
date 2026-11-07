import json
from django.core.exceptions import ImproperlyConfigured
from django.core.management import CommandError
from django.core.management.base import BaseCommand

from powercrud.async_manager import AsyncConfigurationError, AsyncManager


class Command(BaseCommand):
    help = "Cleanup stale PowerCRUD async artifacts (conflicts, progress, dashboard records)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output cleanup summary as JSON instead of human-readable text.",
        )

    def handle(self, *args, **options):
        try:
            manager = AsyncManager()
        except (AsyncConfigurationError, ImproperlyConfigured) as exc:
            raise CommandError(f"Async cleanup is unavailable: {exc}") from exc
        summary = manager.cleanup_completed_tasks()

        if options.get("json"):
            self.stdout.write(json.dumps(summary, indent=2, sort_keys=True))
            return

        cleaned = summary.get("cleaned", {})
        skipped = summary.get("skipped", {})

        self.stdout.write(self.style.MIGRATE_HEADING("PowerCRUD Async Cleanup Summary"))
        self.stdout.write(f"Active tasks inspected: {summary.get('active_tasks', 0)}")
        self.stdout.write("")

        if not cleaned:
            self.stdout.write(self.style.SUCCESS("No stale tasks were found."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Cleaned {len(cleaned)} task(s):"))
            for task_name, details in cleaned.items():
                reason = details.get("reason", "unknown")
                conflicts = details.get("conflict_lock_keys", 0)
                progress = details.get("progress_entries", 0)
                dashboard = details.get("dashboard_records", 0)
                self.stdout.write(
                    f"  - {task_name} ({reason}) "
                    f"[locks={conflicts}, progress={progress}, dashboard={dashboard}]"
                )

        if skipped:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(f"Skipped {len(skipped)} active task(s):")
            )
            for task_name, reason in skipped.items():
                self.stdout.write(f"  - {task_name}: {reason}")
