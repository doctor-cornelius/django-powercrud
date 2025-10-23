from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sample", "0003_asynctaskrecord_id_alter_asynctaskrecord_task_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="asynctaskrecord",
            name="task_args",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
