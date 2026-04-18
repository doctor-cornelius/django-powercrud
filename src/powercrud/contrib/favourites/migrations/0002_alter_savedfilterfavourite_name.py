"""Limit saved favourite names to a compact maximum length."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Reduce the saved favourite name field to the supported UI length."""

    dependencies = [
        ("favourites", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="savedfilterfavourite",
            name="name",
            field=models.CharField(max_length=30),
        ),
    ]
