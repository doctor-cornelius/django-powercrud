from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone


class Command(BaseCommand):
    help = "Clears all session data from the database"

    def add_arguments(self, parser):
        parser.add_argument(
            '--expired-only',
            action='store_true',
            help='Only clear expired sessions',
        )

    def handle(self, *args, **options):
        if options['expired_only']:
            deleted_count, _ = Session.objects.filter(
                expire_date__lt=timezone.now()
            ).delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} expired sessions')
            )
        else:
            deleted_count, _ = Session.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} sessions')
            )