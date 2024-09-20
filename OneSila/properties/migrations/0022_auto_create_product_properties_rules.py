from django.db import migrations


def create_rules_for_product_types(apps, schema_editor):
    PropertySelectValue = apps.get_model('properties', 'PropertySelectValue')
    ProductPropertiesRule = apps.get_model('properties', 'ProductPropertiesRule')

    product_types = PropertySelectValue.objects.filter(property__is_product_type=True)
    for product_type in product_types:

        if not ProductPropertiesRule.objects.filter(product_type=product_type).exists():
            rule = ProductPropertiesRule.objects.create(
                product_type=product_type,
                multi_tenant_company=product_type.multi_tenant_company
            )

class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0021_productpropertiesrule_created_by_multi_tenant_user_and_more'),
    ]

    operations = [
        migrations.RunPython(create_rules_for_product_types, migrations.RunPython.noop),
    ]
