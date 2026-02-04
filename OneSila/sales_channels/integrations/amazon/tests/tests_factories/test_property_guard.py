from core.tests import TestCase
from properties.models import (
    Property,
    ProductPropertiesRule,
    ProductPropertiesRuleItem,
    PropertySelectValue,
    PropertySelectValueTranslation,
    ProductProperty,
)
from products.models import Product
from sales_channels.factories.task_queue import TaskTarget
from sales_channels.integrations.amazon.factories.task_queue import AmazonProductPropertyAddTask
from sales_channels.integrations.amazon.models import (
    AmazonProduct,
    AmazonProductType,
    AmazonProductTypeItem,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonSalesChannel,
    AmazonSalesChannelView,
)
from sales_channels.integrations.amazon.tests.helpers import DisableWooCommerceSignalsMixin


class AmazonProductPropertyGuardTests(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://amazon.example.com",
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            api_region_code="us",
            remote_id="AMZ",
            name="Amazon",
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="AMZ-GUARD",
        )
        self.remote_product = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )

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

    def _task(self, *, product_property):
        return AmazonProductPropertyAddTask(
            task_func=lambda *args, **kwargs: None,
            product=self.product,
            product_property=product_property,
            number_of_remote_requests=0,
        )

    def _target(self, *, view=True):
        return TaskTarget(
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            sales_channel_view=self.view if view else None,
        )

    def _attach_amazon_rule(self):
        return AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.rule,
            product_type_code="TYPE_A",
        )

    def test_amazon_guard_blocks_when_view_missing(self):
        property_obj = Property.objects.create(
            type=Property.TYPES.TEXT,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=property_obj,
            type=ProductPropertiesRuleItem.REQUIRED,
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
        )

        task = self._task(product_property=product_property)
        result = task.guard(target=self._target(view=False))
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "amazon_view_missing")

    def test_amazon_guard_blocks_when_property_not_mapped(self):
        property_obj = Property.objects.create(
            type=Property.TYPES.TEXT,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=property_obj,
            type=ProductPropertiesRuleItem.REQUIRED,
        )
        AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.rule,
            product_type_code="TYPE_A",
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
        )

        task = self._task(product_property=product_property)
        result = task.guard(target=self._target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "amazon_property_not_mapped")

    def test_amazon_guard_blocks_when_amazon_rule_missing(self):
        property_obj = Property.objects.create(
            type=Property.TYPES.TEXT,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=property_obj,
            type=ProductPropertiesRuleItem.REQUIRED,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=property_obj,
            code="prop",
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
        )

        task = self._task(product_property=product_property)
        result = task.guard(target=self._target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "amazon_product_type_missing")

    def test_amazon_guard_blocks_when_property_not_in_type(self):
        property_obj = Property.objects.create(
            type=Property.TYPES.TEXT,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=property_obj,
            type=ProductPropertiesRuleItem.REQUIRED,
        )
        amazon_rule = self._attach_amazon_rule()
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=property_obj,
            code="prop",
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
        )

        task = self._task(product_property=product_property)
        result = task.guard(target=self._target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "amazon_property_not_in_type")

    def test_amazon_guard_blocks_when_select_value_unmapped(self):
        property_obj = Property.objects.create(
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=property_obj,
            type=ProductPropertiesRuleItem.REQUIRED,
        )
        amazon_rule = self._attach_amazon_rule()
        amazon_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=property_obj,
            code="prop",
        )
        AmazonProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_rule=amazon_rule,
            remote_property=amazon_property,
        )
        select_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=property_obj,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=select_value,
            language="en",
            value="Blue",
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
            value_select=select_value,
        )

        task = self._task(product_property=product_property)
        result = task.guard(target=self._target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "amazon_select_value_unmapped")

    def test_amazon_guard_allows_when_select_value_mapped(self):
        property_obj = Property.objects.create(
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=property_obj,
            type=ProductPropertiesRuleItem.REQUIRED,
        )
        amazon_rule = self._attach_amazon_rule()
        amazon_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=property_obj,
            code="prop",
        )
        AmazonProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_rule=amazon_rule,
            remote_property=amazon_property,
        )
        select_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=property_obj,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=select_value,
            language="en",
            value="Blue",
        )
        AmazonPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_property=amazon_property,
            marketplace=self.view,
            remote_value="Blue",
            local_instance=select_value,
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
            value_select=select_value,
        )

        task = self._task(product_property=product_property)
        result = task.guard(target=self._target())
        self.assertTrue(result.allowed)
