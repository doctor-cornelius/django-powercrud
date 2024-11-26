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
            "submission_date": forms.DateInput(attrs={"type": "date"}),
        }
