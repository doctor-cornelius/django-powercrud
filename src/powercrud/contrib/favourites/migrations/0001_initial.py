"""Initial migration for the optional PowerCRUD favourites contrib app."""

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Create the saved favourite persistence table."""

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SavedFilterFavourite",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("view_key", models.CharField(max_length=255)),
                ("name", models.CharField(max_length=120)),
                ("state", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="powercrud_saved_filter_favourites",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("name", "pk"),
            },
        ),
        migrations.AddConstraint(
            model_name="savedfilterfavourite",
            constraint=models.UniqueConstraint(
                fields=("user", "view_key", "name"),
                name="uniq_powercrud_favourite_user_view_name",
            ),
        ),
    ]
