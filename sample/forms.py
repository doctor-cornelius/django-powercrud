from django import forms
from . import models

class BookForm(forms.ModelForm):
    class Meta:
        model = models.Book
        fields = [
            "title",
            "author",
            "published_date",
            "bestseller",
            "isbn",
            "pages",
            "description",
        ]
        widgets = {
            "published_date": forms.DateInput(attrs={"type": "date"}),
        }
        # template_name = 'sample/book_form.html'  # Removed as it's not used


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
