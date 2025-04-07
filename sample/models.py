from django.db import models


class Author(models.Model):
    class Meta:
        verbose_name = "The Author Person"

    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)

    @property
    def has_bio(self):
        return bool(self.bio)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    published_date = models.DateField()
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()

        if not self.uneditable_field:
            self.uneditable_field = "This field is uneditable"

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    @property
    def there_are_so_many_pages_this_header_surely_will_wrap(self):
        return self.pages > 10

    def __str__(self):
        return self.title
