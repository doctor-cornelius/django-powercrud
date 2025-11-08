from django import forms
from crispy_forms.helper import FormHelper

from . import models

class BookForm(forms.ModelForm):
    def __init__(self, *args, author_for_genres=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._filter_genres(author_for_genres)

    def _filter_genres(self, author_pk):
        genres_field = self.fields.get("genres")
        if not genres_field:
            return

        queryset = models.Genre.objects.all()
        if author_pk:
            author = models.Author.objects.filter(pk=author_pk).first()
            if author and author.name:
                prefix = author.name[:1]
                filtered = queryset.filter(name__istartswith=prefix)
                if filtered.exists():
                    queryset = filtered
        genres_field.queryset = queryset

    class Meta:
        model = models.Book
        fields = [
            "title",
            "author",
            "genres",
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
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.helper = FormHelper()
    #     self.helper.form_tag = False
    #     self.helper.disable_csrf = True

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
