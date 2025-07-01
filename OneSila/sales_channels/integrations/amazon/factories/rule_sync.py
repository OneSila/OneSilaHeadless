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
