from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ebay', '0003_alter_ebaysaleschannel_access_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='ebaysaleschannelview',
            name='is_default',
            field=models.BooleanField(default=False, help_text='Marks the default marketplace for this eBay store.'),
        ),
        migrations.AddField(
            model_name='ebaycurrency',
            name='sales_channel_view',
            field=models.ForeignKey(blank=True, help_text='The marketplace associated with this remote currency.', null=True, on_delete=models.CASCADE, related_name='remote_currencies', to='ebay.ebaysaleschannelview'),
        ),
        migrations.AddField(
            model_name='ebayremotelanguage',
            name='sales_channel_view',
            field=models.ForeignKey(blank=True, help_text='The marketplace associated with this remote language.', null=True, on_delete=models.CASCADE, related_name='remote_languages', to='ebay.ebaysaleschannelview'),
        ),
    ]
