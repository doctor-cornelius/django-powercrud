from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import random

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

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "This command can only be run in development mode (DEBUG=True)"
            )

        num_authors = options["authors"]
        num_books = options["books"]

        # Author names generation
        first_names = ["James", "Maria", "Robert", "Lisa", "Michael", "Sarah", "David", 
                      "Jennifer", "John", "Patricia", "Richard", "Elizabeth", "Joseph",
                      "Margaret", "Charles", "Susan", "Daniel", "Nancy", "Paul", "Betty",
                      "Mark", "Dorothy", "Donald", "Sandra", "Steven", "Emily", "Thomas",
                      "Jessica", "William", "Karen"]
        
        last_names = ["Smith", "Garcia", "Johnson", "Brown", "Davis", "Wilson", "Martinez",
                     "Taylor", "Anderson", "Thomas", "White", "Hall", "Lee", "Clark",
                     "Wright", "Lopez", "Hill", "Green", "Adams", "King", "Baker",
                     "Scott", "Nelson", "Carter", "Mitchell", "Young", "Walker",
                     "Allen", "King", "Wright"]

        self.stdout.write("Creating authors...")
        authors = []
        for _ in range(num_authors):
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            author = Author.objects.create(
                name=name,
                bio=f"Distinguished author known for {random.choice(['fiction', 'non-fiction', 'poetry', 'drama'])} works.",
                birth_date=datetime(
                    random.randint(1940, 1990),
                    random.randint(1, 12),
                    random.randint(1, 28)
                ).date()
            )
            authors.append(author)
        
        self.stdout.write(self.style.SUCCESS(f"Created {len(authors)} authors"))

        # Book title components
        titles_prefix = ["The", "A", "My", "Our", "Their"]
        titles_main = ["Journey", "Story", "Adventure", "Mystery", "Secret", 
                      "Legend", "Tale", "Chronicles", "Path", "Quest",
                      "Voyage", "Saga", "Epic", "Legacy", "Prophecy"]
        titles_suffix = ["of Time", "in Space", "of Love", "of Magic", "of Life",
                        "of Dreams", "of Hope", "of Destiny", "of the Ages",
                        "of Tomorrow", "of the Past", "of the Future", "of Glory",
                        "of Wonder", "of Mystery"]

        self.stdout.write("Creating books...")
        for i in range(num_books):
            title = f"{random.choice(titles_prefix)} {random.choice(titles_main)} {random.choice(titles_suffix)}"
            
            # Generate ISBN (simplified version)
            isbn = ''.join([str(random.randint(0, 9)) for _ in range(13)])
            
            # Random date within last 30 years
            pub_date = timezone.now().date() - timedelta(days=random.randint(0, 10950))
            
            Book.objects.create(
                title=title,
                author=random.choice(authors),
                published_date=pub_date,
                isbn=isbn,
                pages=random.randint(100, 1000),
                description=f"A compelling {random.choice(['story', 'narrative', 'account', 'tale'])} "
                           f"about {random.choice(['love', 'adventure', 'mystery', 'life', 'destiny'])}."
            )
            
            if (i + 1) % 10 == 0:
                self.stdout.write(f"Created {i + 1} books...")

        self.stdout.write(self.style.SUCCESS(
            f"\nSuccessfully created {num_books} books and {num_authors} authors"
        ))
