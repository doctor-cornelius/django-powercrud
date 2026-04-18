"""Limit saved favourite names to a compact maximum length."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Reduce the saved favourite name field to the supported UI length."""

    dependencies = [
        ("favourites", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="savedfilterfavourite",
            name="uniq_powercrud_favourite_user_view_name",
        ),
        migrations.AlterField(
            model_name="savedfilterfavourite",
            name="name",
            field=models.CharField(max_length=30),
        ),
        migrations.AddConstraint(
            model_name="savedfilterfavourite",
            constraint=models.UniqueConstraint(
                fields=("user", "view_key", "name"),
                name="uniq_powercrud_favourite_user_view_name",
            ),
        ),
    ]
