from django.db import migrations

def forwards_func(apps, schema_editor):
    Integration = apps.get_model('integrations', 'Integration')
    MagentoSalesChannel = apps.get_model('magento2', 'MagentoSalesChannel')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    new_ct = ContentType.objects.get_for_model(MagentoSalesChannel)
    for integration in Integration.objects.all():
        integration.polymorphic_ctype = new_ct
        integration.save()

class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0001_initial'),
        ('sales_channels', '0032_remove_saleschannel_id_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
    ]
