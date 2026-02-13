from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

import random
from faker import Faker

from sample.models import Author, Book


class Command(BaseCommand):
    help = "Creates sample data for testing (authors and books)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--authors",
            type=int,
            default=25,
            help="Number of authors to create (default: 25)",
        )
        parser.add_argument(
            "--books",
            type=int,
            default=50,
            help="Number of books to create (default: 50)",
        )
        parser.add_argument(
            "--books-per-author",
            type=int,
            default=10,
            help="Average number of books per author (default: 10). If specified, overrides --authors.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "This command can only be run in development mode (DEBUG=True)"
            )

        fake = Faker()
        num_books = options["books"]
        books_per_author = options["books_per_author"]
        num_authors_arg = options["authors"]

        if books_per_author:
            # Calculate authors based on books per author, ensuring at least 1 author
            num_authors = max(1, num_books // books_per_author)
            if num_authors_arg != 25:  # Only warn if user explicitly set --authors
                self.stdout.write(
                    self.style.WARNING(
                        f"Warning: --books-per-author ({books_per_author}) is specified. "
                        f"Calculating {num_authors} authors based on {num_books} books. "
                        f"The --authors argument ({num_authors_arg}) will be ignored."
                    )
                )
        else:
            num_authors = num_authors_arg

        self.stdout.write("Creating authors...")
        authors = []
        for _ in range(num_authors):
            name = fake.name()
            author = Author.objects.create(
                name=name,
                bio=fake.paragraph(nb_sentences=random.randint(2, 4)),
                birth_date=fake.date_of_birth(minimum_age=30, maximum_age=80),
            )
            authors.append(author)

        self.stdout.write(self.style.SUCCESS(f"Created {len(authors)} authors"))

        self.stdout.write("Creating books...")
        for i in range(num_books):
            title = fake.sentence(nb_words=random.randint(3, 7))

            # Generate ISBN using Faker
            isbn = fake.isbn13()

            # Random date within last 30 years
            pub_date = timezone.now().date() - timedelta(days=random.randint(0, 10950))

            Book.objects.create(
                title=title,
                author=random.choice(authors),
                published_date=pub_date,
                isbn=isbn,
                pages=random.randint(100, 1000),
                description=fake.paragraph(nb_sentences=random.randint(3, 5)),
            )

            if (i + 1) % 10 == 0:
                self.stdout.write(f"Created {i + 1} books...")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully created {num_books} books and {num_authors} authors"
            )
        )
