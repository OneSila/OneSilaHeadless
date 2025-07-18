from django.db import migrations, models


def create_missing_rules(apps, schema_editor):
    AmazonProductType = apps.get_model('amazon', 'AmazonProductType')
    AmazonSalesChannel = apps.get_model('amazon', 'AmazonSalesChannel')
    ProductPropertiesRule = apps.get_model('properties', 'ProductPropertiesRule')
    PropertySelectValueTranslation = apps.get_model('properties', 'PropertySelectValueTranslation')

    for rule in ProductPropertiesRule.objects.all().iterator():
        sales_channels = AmazonSalesChannel.objects.filter(multi_tenant_company=rule.multi_tenant_company)

        if not sales_channels.exists():
            continue

        product_type_value = (
            PropertySelectValueTranslation.objects
            .filter(
                propertyselectvalue_id=rule.product_type_id,
                language=rule.multi_tenant_company.language
            )
            .values_list('value', flat=True)
            .first()
        ) or f"ProductType-{rule.product_type_id}"

        for sc in sales_channels.iterator():
            if not AmazonProductType.objects.filter(
                multi_tenant_company=rule.multi_tenant_company,
                local_instance=rule,
                sales_channel=sc,
            ).exists():

                AmazonProductType.objects.create(
                    multi_tenant_company=rule.multi_tenant_company,
                    local_instance=rule,
                    sales_channel=sc,
                    name=product_type_value,
                    imported=False,
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
