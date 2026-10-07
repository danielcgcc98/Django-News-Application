from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="newsletter",
            old_name="content",
            new_name="description",
        ),
    ]
