from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models import ProtectedError
from sample.models import Author, Book


class Command(BaseCommand):
    help = "Deletes sample data (books and/or authors)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete all books and authors',
        )
        parser.add_argument(
            '--books',
            action='store_true',
            help='Delete only books',
        )
        parser.add_argument(
            '--authors',
            action='store_true',
            help='Delete only authors (will also delete related books)',
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "This command can only be run in development mode (DEBUG=True)"
            )

        if not any([options['all'], options['books'], options['authors']]):
            self.stdout.write(
                self.style.WARNING('Please specify what to delete: --all, --books, or --authors')
            )
            return

        if options['all'] or options['books']:
            book_count, _ = Book.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {book_count} books')
            )

        if options['all'] or options['authors']:
            try:
                author_count, _ = Author.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully deleted {author_count} authors')
                )
            except ProtectedError:
                self.stdout.write(
                    self.style.ERROR('Could not delete authors due to protected references. Try deleting books first.')
                )
