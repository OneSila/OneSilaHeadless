from django.db import migrations, models


def create_missing_rules(apps, schema_editor):
    AmazonProductType = apps.get_model('amazon', 'AmazonProductType')
    AmazonSalesChannel = apps.get_model('amazon', 'AmazonSalesChannel')
    ProductPropertiesRule = apps.get_model('properties', 'ProductPropertiesRule')

    for rule in ProductPropertiesRule.objects.all().iterator():
        for sc in AmazonSalesChannel.objects.filter(multi_tenant_company=rule.multi_tenant_company).iterator():
            AmazonProductType.objects.get_or_create(
                multi_tenant_company=rule.multi_tenant_company,
                local_instance=rule,
                sales_channel=sc,
                defaults={
                    'name': rule.product_type.value,
                    'imported': False,
                }
            )


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0034_alter_listing_offer_required_properties_to_dict'),
        ('properties', '0012_alter_property_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='amazonproducttype',
            name='imported',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(create_missing_rules, migrations.RunPython.noop),
    ]
