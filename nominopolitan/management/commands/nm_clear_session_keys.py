from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone


class Command(BaseCommand):
    help = "Clears all nominopolitan session data from the database"

    def add_arguments(self, parser):
        parser.add_argument(
            '--expired-only',
            action='store_true',
            help='Only clear expired nominopolitan sessions',
        )

    def handle(self, *args, **options):
        # Get all sessions
        sessions = Session.objects.all()
        if options['expired_only']:
            sessions = sessions.filter(expire_date__lt=timezone.now())

        deleted_count = 0
        for session in sessions:
            session_data = session.get_decoded()
            # Create a list of keys to delete
            keys_to_delete = [
                key for key in session_data.keys()
                if key.startswith('nominopolitan')
            ]
            
            if keys_to_delete:
                # If all keys in session are nominopolitan keys, delete entire session
                if len(keys_to_delete) == len(session_data):
                    session.delete()
                    deleted_count += 1
                else:
                    # Otherwise just delete nominopolitan keys
                    for key in keys_to_delete:
                        del session_data[key]
                        deleted_count += 1
                    session.session_data = session_data
                    session.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {deleted_count} nominopolitan session{"s" if deleted_count != 1 else ""}'
            )
        )
