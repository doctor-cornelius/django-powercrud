from django import forms
from . import models

class BookForm(forms.ModelForm):
    class Meta:
        model = models.Book
        fields = [
            "title",
            "author",
            "published_date",
            "isbn",
            "pages",
            "description",
        ]
        widgets = {
            "published_date": forms.DateInput(attrs={"type": "date"}),
        }


class AuthorForm(forms.ModelForm):
    class Meta:
        model = models.Author
        fields = [
            "name",
            "bio",
            "birth_date",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }
