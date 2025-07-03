from django.db import models

from django.core.exceptions import ValidationError

class Author(models.Model):
    class Meta:
        verbose_name = "The Author Person"

    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    an_integer_with_long_heading_text = models.IntegerField(default=0)

    @property
    def has_bio(self):
        return bool(self.bio)

    @property
    def property_birth_date(self):
        return self.birth_date

    def __str__(self):
        return self.name


class Profile(models.Model):
    """Just for testing logic for OneToOneFields"""
    author = models.OneToOneField(
        Author, on_delete=models.CASCADE, related_name="profile"
    )
    nickname = models.CharField(max_length=100)
    favorite_genre = models.ForeignKey(
        "Genre", on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.nickname} ({self.author.name})"


class Genre(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    numeric_string = models.CharField(max_length=4, blank=True)

    def clean(self):
        if self.numeric_string and not self.numeric_string.isnumeric():
            raise ValidationError("Numeric string must be numeric")

    def __str__(self):
        return self.name


class Book(models.Model):

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['title', 'author'], name='unique_title_author')
        ]

    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    genres = models.ManyToManyField(Genre, related_name="books")
    published_date = models.DateField()
    bestseller = models.BooleanField(
        default=False,
        help_text="Is this book a bestseller?",
        )
    isbn = models.CharField(max_length=13, unique=True)
    isbn_empty = models.GeneratedField(
        expression=(
            models.Case(
                models.When(isbn='', then=True),
                models.When(isbn__isnull=True, then=True),
                default=False,
                output_field=models.BooleanField(),
            )
        ),
        output_field=models.BooleanField(),
        db_persist=True
    )
    pages = models.IntegerField()
    description = models.TextField(blank=True)
    uneditable_field = models.CharField(max_length=200, blank=True, null=True, editable=False)

    @property
    def there_are_so_many_pages_this_header_surely_will_wrap(self):
        return self.pages > 10

    @property
    def a_really_long_property_header_for_title(self):
        return self.title
    a_really_long_property_header_for_title.fget.short_description = "Really Long Title"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()

        if not self.uneditable_field:
            self.uneditable_field = "This field is uneditable"

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title
