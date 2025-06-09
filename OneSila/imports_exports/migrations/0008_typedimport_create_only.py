from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('imports_exports', '0007_typedimport_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='typedimport',
            name='create_only',
            field=models.BooleanField(default=False, help_text='If True, existing objects fetched during the import will not be updated.'),
        ),
    ]
