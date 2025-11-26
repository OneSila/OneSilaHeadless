from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('imports_exports', '0012_importreport'),
    ]

    operations = [
        migrations.AddField(
            model_name='import',
            name='total_records',
            field=models.PositiveIntegerField(default=0, help_text='Total number of items that this import will process.'),
        ),
        migrations.AddField(
            model_name='import',
            name='processed_records',
            field=models.PositiveIntegerField(default=0, help_text='How many items have been processed so far in async imports.'),
        ),
    ]
