from django.db.models import Max

from properties.models import ProductPropertiesRuleItem, Property
from sales_channels.integrations.shein.models import (
    SheinProductTypeItem,
    SheinProperty,
)


class SheinPropertyRuleItemSyncFactory:
    """Ensure ProductPropertiesRuleItems reflect Shein requirement metadata."""

    def __init__(self, *, shein_property: SheinProperty) -> None:
        self.shein_property = shein_property

    def run(self) -> None:
        if not self.shein_property.local_instance:
            return

        items = SheinProductTypeItem.objects.filter(
            property=self.shein_property,
            product_type__local_instance__isnull=False,
        )

        for item in items:
            rule = item.product_type.local_instance
            new_type = self._resolve_rule_item_type(
                item=item,
                local_property=self.shein_property.local_instance,
            )
            if not new_type:
                continue

            max_sort = (
                rule.items.aggregate(max_sort=Max("sort_order")).get("max_sort") or 0
            )
            rule_item, created = ProductPropertiesRuleItem.objects.get_or_create(
                multi_tenant_company=rule.multi_tenant_company,
                rule=rule,
                property=self.shein_property.local_instance,
                defaults={
                    "type": new_type,
                    "sort_order": max_sort + 1,
                },
            )

            if created or rule_item.type == new_type:
                continue

            if self._is_optional_downgrade(current=rule_item.type, new=new_type):
                continue

            rule_item.type = new_type
            rule_item.save(update_fields=["type"])

    def _resolve_rule_item_type(
        self,
        *,
        item: SheinProductTypeItem,
        local_property: Property,
    ) -> str | None:
        if item.requirement == SheinProductTypeItem.Requirement.NOT_FILLABLE:
            return None

        if item.attribute_type == SheinProductTypeItem.AttributeType.SALES:
            if local_property.type == Property.TYPES.SELECT:
                if item.requirement == SheinProductTypeItem.Requirement.REQUIRED:
                    return ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR
                return ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR
            if item.requirement == SheinProductTypeItem.Requirement.REQUIRED:
                return ProductPropertiesRuleItem.REQUIRED

        if item.requirement == SheinProductTypeItem.Requirement.REQUIRED:
            return ProductPropertiesRuleItem.REQUIRED
        return ProductPropertiesRuleItem.OPTIONAL

    def _is_optional_downgrade(self, *, current: str, new: str) -> bool:
        optional_types = {
            ProductPropertiesRuleItem.OPTIONAL,
            ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR,
        }
        return new in optional_types and current not in optional_types
