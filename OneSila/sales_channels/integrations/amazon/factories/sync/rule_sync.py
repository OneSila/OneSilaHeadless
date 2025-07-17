from django.db.models import Max

from properties.models import ProductPropertiesRuleItem
from sales_channels.integrations.amazon.models import (
    AmazonProductTypeItem,
    AmazonProperty,
)


class AmazonPropertyRuleItemSyncFactory:
    """Create or update ProductPropertiesRuleItem when mapping Amazon properties."""

    def __init__(self, amazon_property: AmazonProperty):
        self.amazon_property = amazon_property

    def run(self):
        if not self.amazon_property.local_instance:
            return

        items = AmazonProductTypeItem.objects.filter(
            remote_property=self.amazon_property,
            amazon_rule__local_instance__isnull=False,
        )

        for item in items:
            rule = item.amazon_rule.local_instance
            max_sort = rule.items.aggregate(max_sort=Max("sort_order")).get(
                "max_sort"
            ) or 0
            rule_item, created = ProductPropertiesRuleItem.objects.get_or_create(
                multi_tenant_company=rule.multi_tenant_company,
                rule=rule,
                property=self.amazon_property.local_instance,
                defaults={
                    "type": item.remote_type or ProductPropertiesRuleItem.OPTIONAL,
                    "sort_order": max_sort + 1,
                },
            )

            if not created:
                new_type = item.remote_type or ProductPropertiesRuleItem.OPTIONAL
                if rule_item.type != new_type:
                    if not (
                        new_type == ProductPropertiesRuleItem.OPTIONAL
                        and rule_item.type
                        != ProductPropertiesRuleItem.OPTIONAL
                    ):
                        rule_item.type = new_type
                        rule_item.save(update_fields=["type"])


class AmazonProductTypeAsinSyncFactory:
    """Ensure merchant_suggested_asin is required when a product type is mapped."""

    def __init__(self, amazon_product_type):
        self.amazon_product_type = amazon_product_type

    def run(self):
        if not self.amazon_product_type.local_instance:
            return

        asin_property = AmazonProperty.objects.filter(
            sales_channel=self.amazon_product_type.sales_channel,
            code="merchant_suggested_asin",
        ).first()

        if not asin_property or not asin_property.local_instance:
            return

        item, created = AmazonProductTypeItem.objects.get_or_create(
            multi_tenant_company=self.amazon_product_type.multi_tenant_company,
            sales_channel=self.amazon_product_type.sales_channel,
            amazon_rule=self.amazon_product_type,
            remote_property=asin_property,
            defaults={"remote_type": ProductPropertiesRuleItem.REQUIRED},
        )

        if created or item.remote_type != ProductPropertiesRuleItem.REQUIRED:
            item.remote_type = ProductPropertiesRuleItem.REQUIRED
            item.save()

        rule = self.amazon_product_type.local_instance
        max_sort = rule.items.aggregate(max_sort=Max("sort_order")).get("max_sort") or 0
        rule_item, created_local = ProductPropertiesRuleItem.objects.get_or_create(
            multi_tenant_company=rule.multi_tenant_company,
            rule=rule,
            property=asin_property.local_instance,
            defaults={
                "type": ProductPropertiesRuleItem.REQUIRED,
                "sort_order": max_sort + 1,
            },
        )

        if not created_local and rule_item.type != ProductPropertiesRuleItem.REQUIRED:
            rule_item.type = ProductPropertiesRuleItem.REQUIRED
            rule_item.save(update_fields=["type"])
