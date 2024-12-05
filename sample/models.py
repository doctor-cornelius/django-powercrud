from django.db import models


class Author(models.Model):
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
    pages = models.IntegerField()
    description = models.TextField(blank=True)
    uneditable_field = models.CharField(max_length=200, blank=True, null=True, editable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()

        if not self.uneditable_field:
            self.uneditable_field = "This field is uneditable"

    def save(self):
        self.clean()
        super().save()
        return self

    @property
    def many_pages(self):
        return self.pages > 10

    def __str__(self):
        return self.title
