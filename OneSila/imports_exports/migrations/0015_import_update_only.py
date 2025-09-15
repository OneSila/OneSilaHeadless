from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imports_exports', '0014_alter_mappedimport_json_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='import',
            name='update_only',
            field=models.BooleanField(default=False, help_text='If True, the import will only update existing objects and fail if they do not exist.'),
        ),
    ]
