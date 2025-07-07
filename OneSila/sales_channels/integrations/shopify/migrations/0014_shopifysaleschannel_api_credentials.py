from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('shopify', '0013_remove_shopifysaleschannel_is_external_install'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopifysaleschannel',
            name='api_key',
            field=models.CharField(blank=True, help_text='API key of the Shopify custom app associated with this store.', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='shopifysaleschannel',
            name='api_secret',
            field=models.CharField(blank=True, help_text='API secret of the Shopify custom app associated with this store.', max_length=255, null=True),
        ),
    ]
