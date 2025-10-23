from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from sample.models import AsyncTaskRecord


class Command(BaseCommand):
    help = "Remove async task records older than the provided age (default 7 days)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Age in days after which completed tasks are removed.",
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options["days"])
        qs = AsyncTaskRecord.objects.filter(updated_at__lt=cutoff)
        deleted, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} async task records older than {options['days']} days."))
