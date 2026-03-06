from django import forms

from . import models


class BookForm(forms.ModelForm):
    """Book form with author-scoped genre choices."""

    def __init__(self, *args, author_for_genres=None, **kwargs):
        """Initialise the form and scope genres to the resolved author."""
        super().__init__(*args, **kwargs)
        author_pk = self._resolve_author_for_genres(author_for_genres)
        self._filter_genres(author_pk)
        self._set_genres_optional()

    def _resolve_author_for_genres(self, explicit_author_pk):
        """Resolve author selection from explicit input, bound data, or instance."""
        if explicit_author_pk:
            return explicit_author_pk

        bound_data = getattr(self, "data", None)
        if bound_data:
            prefixed_key = self.add_prefix("author")
            posted_author = bound_data.get(prefixed_key) or bound_data.get("author")
            if posted_author:
                return posted_author

        instance = getattr(self, "instance", None)
        if instance is not None:
            instance_author_pk = getattr(instance, "author_id", None)
            if instance_author_pk:
                return instance_author_pk

        return None

    def _filter_genres(self, author_pk):
        """Restrict genre choices to genres available for the chosen author."""
        genres_field = self.fields.get("genres")
        if not genres_field:
            return

        queryset = models.Genre.objects.all().order_by("name")
        if author_pk:
            author = models.Author.objects.filter(pk=author_pk).first()
            queryset = (
                author.genres.all().order_by("name")
                if author is not None
                else queryset.none()
            )
        genres_field.queryset = queryset

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
