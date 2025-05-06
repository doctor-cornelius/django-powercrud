from django import forms
from crispy_forms.helper import FormHelper

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

# class BookForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_tag = False
#         self.helper.disable_csrf = True

#     class Meta:
#         model = models.Book
#         fields = [
#             "title",
#             "author",
#             "published_date",
#             "bestseller",
#             "isbn",
#             "pages",
#             "description",
#         ]
#         widgets = {
#             "published_date": forms.DateInput(attrs={"type": "date"}),
#         }

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
