from django.db import migrations
from django.db.models import Max

def add_merchant_asin(apps, schema_editor):
    AmazonSalesChannel = apps.get_model('amazon', 'AmazonSalesChannel')
    AmazonProperty = apps.get_model('amazon', 'AmazonProperty')
    AmazonProductType = apps.get_model('amazon', 'AmazonProductType')
    AmazonProductTypeItem = apps.get_model('amazon', 'AmazonProductTypeItem')
    Property = apps.get_model('properties', 'Property')
    PropertyTranslation = apps.get_model('properties', 'PropertyTranslation')
    ProductPropertiesRuleItem = apps.get_model('properties', 'ProductPropertiesRuleItem')

    for sc in AmazonSalesChannel.objects.all().iterator():
        remote_prop, _ = AmazonProperty.objects.get_or_create(
            allow_multiple=True,
            sales_channel=sc,
            multi_tenant_company=sc.multi_tenant_company,
            code='merchant_suggested_asin',
            defaults={'type': 'TEXT'},
        )

        if not remote_prop.local_instance:
            local_prop, _ = Property.objects.get_or_create(
                internal_name='amazon_asin',
                multi_tenant_company=sc.multi_tenant_company,
                defaults={'type': 'TEXT', 'non_deletable': True},
            )
            PropertyTranslation.objects.get_or_create(
                property=local_prop,
                language=sc.multi_tenant_company.language,
                multi_tenant_company=sc.multi_tenant_company,
                defaults={'name': 'Amazon Asin'},
            )
            if not local_prop.non_deletable:
                local_prop.non_deletable = True
                local_prop.save(update_fields=['non_deletable'])
            remote_prop.local_instance = local_prop
            remote_prop.save()
        else:
            local_prop = remote_prop.local_instance

        for pt in AmazonProductType.objects.filter(sales_channel=sc):
            item, created = AmazonProductTypeItem.objects.get_or_create(
                multi_tenant_company=sc.multi_tenant_company,
                sales_channel=sc,
                amazon_rule=pt,
                remote_property=remote_prop,
                defaults={'remote_type': 'REQUIRED'},
            )
            if created or item.remote_type != 'REQUIRED':
                item.remote_type = 'REQUIRED'
                item.save()

            if pt.local_instance:
                rule = pt.local_instance
                sort_order = 0
                rule_item, created_local = ProductPropertiesRuleItem.objects.get_or_create(
                    multi_tenant_company=rule.multi_tenant_company,
                    rule=rule,
                    property=local_prop,
                    defaults={'type': 'REQUIRED', 'sort_order': sort_order + 1},
                )
                if not created_local and rule_item.type != 'REQUIRED':
                    rule_item.type = 'REQUIRED'
                    rule_item.save(update_fields=['type'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0022_amazonproperty_allow_multiple'),
        ('properties', '0012_alter_property_options_and_more'),
    ]

    operations = [
        migrations.RunPython(add_merchant_asin, noop),
    ]
