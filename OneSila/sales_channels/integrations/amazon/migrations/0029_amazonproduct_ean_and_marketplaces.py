from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0028_rename_amazonvat_amazontaxcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='amazonproduct',
            name='created_marketplaces',
            field=models.JSONField(default=list, blank=True, help_text='List of Amazon marketplace IDs where the product was created.'),
        ),
        migrations.AddField(
            model_name='amazonproduct',
            name='ean_code',
            field=models.CharField(max_length=14, null=True, blank=True, help_text='EAN code used when the product was first created.'),
        ),
    ]
