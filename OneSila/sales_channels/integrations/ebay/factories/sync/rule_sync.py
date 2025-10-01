"""Factories for synchronizing local rule items based on eBay mappings."""

from django.db.models import Max

from properties.models import ProductPropertiesRuleItem
from sales_channels.integrations.ebay.models import EbayProductTypeItem, EbayProperty


class EbayPropertyRuleItemSyncFactory:
    """Ensure ProductPropertiesRuleItems exist for mapped eBay properties."""

    def __init__(self, ebay_property: EbayProperty):
        self.ebay_property = ebay_property

    def run(self) -> None:
        if not self.ebay_property.local_instance:
            return

        items = EbayProductTypeItem.objects.filter(
            ebay_property=self.ebay_property,
            product_type__local_instance__isnull=False,
        )

        for item in items:
            rule = item.product_type.local_instance
            max_sort = (
                rule.items.aggregate(max_sort=Max("sort_order")).get("max_sort")
                or 0
            )

            rule_item, created = ProductPropertiesRuleItem.objects.get_or_create(
                multi_tenant_company=rule.multi_tenant_company,
                rule=rule,
                property=self.ebay_property.local_instance,
                defaults={
                    "type": item.remote_type or ProductPropertiesRuleItem.OPTIONAL,
                    "sort_order": max_sort + 1,
                },
            )

            if created:
                continue

            new_type = item.remote_type or ProductPropertiesRuleItem.OPTIONAL
            if rule_item.type == new_type:
                continue

            if (
                new_type == ProductPropertiesRuleItem.OPTIONAL
                and rule_item.type != ProductPropertiesRuleItem.OPTIONAL
            ):
                continue

            rule_item.type = new_type
            rule_item.save(update_fields=["type"])
