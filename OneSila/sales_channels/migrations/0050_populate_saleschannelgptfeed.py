from django.db import migrations


def _create_missing_gpt_feeds(*, apps, schema_editor):
    SalesChannel = apps.get_model('sales_channels', 'SalesChannel')
    SalesChannelGptFeed = apps.get_model('sales_channels', 'SalesChannelGptFeed')

    missing_channels = SalesChannel.objects.all()

    feeds_to_create = [
        SalesChannelGptFeed(
            sales_channel=sales_channel,
            multi_tenant_company=sales_channel.multi_tenant_company,
        )
        for sales_channel in missing_channels
    ]

    if feeds_to_create:
        SalesChannelGptFeed.objects.bulk_create(feeds_to_create, batch_size=500)


def create_missing_gpt_feeds(apps, schema_editor):
    _create_missing_gpt_feeds(apps=apps, schema_editor=schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ('sales_channels', '0049_remoteproduct_required_feed_sync_saleschannelgptfeed'),
    ]

    operations = [
        migrations.RunPython(create_missing_gpt_feeds, reverse_code=migrations.RunPython.noop),
    ]
