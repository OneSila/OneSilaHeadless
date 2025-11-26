from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0023_merchant_suggested_asin'),
    ]

    operations = [
        migrations.AddField(
            model_name='amazonproducttype',
            name='variation_themes',
            field=models.JSONField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='amazonpublicdefinition',
            name='allowed_in_configurator',
            field=models.BooleanField(default=False),
        ),
    ]
