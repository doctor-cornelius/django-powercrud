from django import forms

from . import models


class BookForm(forms.ModelForm):
    """Book form tweaks for the sample book editor."""

    def __init__(self, *args, **kwargs):
        """Initialise the form and keep genres optional for the sample demo."""
        super().__init__(*args, **kwargs)
        self._set_genres_optional()

    def _set_genres_optional(self):
        """Allow books to be saved when no author-specific genres are available."""
        genres_field = self.fields.get("genres")
        if not genres_field:
            return

        genres_field.required = False
        genres_field.widget.attrs.pop("required", None)

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
