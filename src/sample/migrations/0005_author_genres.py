from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sample", "0004_asynctaskrecord_task_args"),
    ]

    operations = [
        migrations.AddField(
            model_name="author",
            name="genres",
            field=models.ManyToManyField(
                blank=True, related_name="authors", to="sample.genre"
            ),
        ),
    ]
