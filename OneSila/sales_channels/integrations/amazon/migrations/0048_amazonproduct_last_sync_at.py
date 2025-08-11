from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0047_amazonimageproductassociation_imported_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='amazonproduct',
            name='last_sync_at',
            field=models.DateTimeField(blank=True, null=True, help_text='Timestamp of the last sync with Amazon.'),
        ),
    ]
