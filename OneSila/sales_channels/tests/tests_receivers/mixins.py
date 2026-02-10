from properties.models import (
    ProductPropertiesRule,
    ProductPropertiesRuleItem,
    Property,
    ProductProperty,
    PropertySelectValue,
    PropertySelectValueTranslation,
)
from sales_channels.models import SyncRequest


class AddTaskSyncRequestTestMixin:
    def _init_product_rule(self):
        self.product_type_property = Property.objects.get(
            type=Property.TYPES.SELECT,
            is_product_type=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product_type_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.product_type_value,
            language="en",
            value="Type A",
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=self.product_type_property,
            value_select=self.product_type_value,
        )
        self.rule = ProductPropertiesRule.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_value,
            sales_channel=self.sales_channel,
        )

    def _add_rule_item(self, *, property_obj):
        return ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=property_obj,
            type=ProductPropertiesRuleItem.REQUIRED,
        )

    def _mark_sync_requests_done(self):
        SyncRequest.objects.update(status=SyncRequest.STATUS_DONE)
