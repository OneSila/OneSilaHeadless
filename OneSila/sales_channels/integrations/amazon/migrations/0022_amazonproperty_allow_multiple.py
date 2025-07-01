from django.db import migrations


def set_allow_multiple(apps, schema_editor):
    RemoteProperty = apps.get_model('sales_channels', 'RemoteProperty')
    AmazonProperty = apps.get_model('amazon', 'AmazonProperty')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ct = ContentType.objects.get_for_model(AmazonProperty)
    RemoteProperty.objects.filter(polymorphic_ctype_id=ct.id).update(allow_multiple=True)


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0021_amazonproduct_asin'),
        ('sales_channels', '0037_remoteproperty_allow_multiple'),
    ]

    operations = [
        migrations.RunPython(set_allow_multiple, migrations.RunPython.noop),
    ]
