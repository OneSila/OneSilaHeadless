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
from sales_channels.integrations.magento2.factories.task_queue import MagentoProductPropertyAddTask
from sales_channels.integrations.magento2.models import MagentoProduct, MagentoSalesChannel
from sales_channels.tests.helpers import DisableMagentoAndWooConnectionsMixin


class MagentoPropertyGuardTests(DisableMagentoAndWooConnectionsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = MagentoSalesChannel.objects.create(
            hostname="https://magento.example.com",
            host_api_username="api-user",
            host_api_key="api-key",
            authentication_method=MagentoSalesChannel.AUTH_METHOD_CHOICES[0][0],
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="PROP-GUARD",
        )
        self.remote_product = MagentoProduct.objects.create(
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

    def _get_target(self):
        return TaskTarget(
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )

    def _build_task(self, *, product_property):
        return MagentoProductPropertyAddTask(
            task_func=lambda *args, **kwargs: None,
            product=self.product,
            product_property=product_property,
            number_of_remote_requests=0,
        )

    def test_guard_blocks_when_property_missing(self):
        task_runner = self._build_task(product_property=None)
        result = task_runner.guard(target=self._get_target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "product_property_missing")

    def test_guard_blocks_internal_property(self):
        property_obj = Property.objects.create(
            type=Property.TYPES.TEXT,
            is_public_information=False,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
        )
        task_runner = self._build_task(product_property=product_property)
        result = task_runner.guard(target=self._get_target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "property_internal")

    def test_guard_blocks_property_not_in_rule(self):
        rule = ProductPropertiesRule.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_value,
            sales_channel=self.sales_channel,
        )
        property_obj = Property.objects.create(
            type=Property.TYPES.TEXT,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
        )
        task_runner = self._build_task(product_property=product_property)
        result = task_runner.guard(target=self._get_target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "property_not_used_in_rule")

    def test_guard_allows_when_property_in_rule(self):
        rule = ProductPropertiesRule.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_value,
            sales_channel=self.sales_channel,
        )
        property_obj = Property.objects.create(
            type=Property.TYPES.TEXT,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertiesRuleItem.objects.create(
            rule=rule,
            property=property_obj,
            type=ProductPropertiesRuleItem.REQUIRED,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
        )
        task_runner = self._build_task(product_property=product_property)
        result = task_runner.guard(target=self._get_target())
        self.assertTrue(result.allowed)
