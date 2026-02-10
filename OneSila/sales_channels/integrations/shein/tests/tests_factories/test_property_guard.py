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
from sales_channels.integrations.amazon.tests.helpers import DisableWooCommerceSignalsMixin
from sales_channels.integrations.shein.factories.task_queue import SheinProductPropertyAddTask
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinProduct,
    SheinProductType,
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
    SheinSalesChannel,
    SheinProductCategory,
)


class SheinProductPropertyGuardTests(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            hostname="https://shein.example.com",
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="SHEIN-GUARD",
        )
        self.remote_product = SheinProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        self.category = SheinCategory.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="CAT-1",
            name="Category",
            is_leaf=True,
            product_type_remote_id="TYPE_A",
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
        return SheinProductPropertyAddTask(
            task_func=lambda *args, **kwargs: None,
            product=self.product,
            product_property=product_property,
            number_of_remote_requests=0,
        )

    def _target(self):
        return TaskTarget(
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )

    def _attach_shein_type(self):
        return SheinProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.rule,
            remote_id="TYPE_A",
        )

    def test_guard_blocks_when_property_not_mapped(self):
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
        self._attach_shein_type()
        SheinProductCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel=self.sales_channel,
            remote_id="CAT-1",
            product_type_remote_id="TYPE_A",
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
        )

        task = self._task(product_property=product_property)
        result = task.guard(target=self._target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "shein_property_not_mapped")

    def test_guard_blocks_when_property_not_in_type(self):
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
        self._attach_shein_type()
        SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=property_obj,
            remote_id="PROP",
        )
        SheinProductCategory.objects.create(
            product=self.product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CAT-1",
            product_type_remote_id="TYPE_A",
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
        )

        task = self._task(product_property=product_property)
        result = task.guard(target=self._target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "shein_attribute_not_allowed_in_category")

    def test_guard_blocks_when_category_missing(self):
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
        SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=property_obj,
            remote_id="PROP",
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
        )

        task = self._task(product_property=product_property)
        result = task.guard(target=self._target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "shein_category_missing")

    def test_guard_allows_when_select_value_mapped(self):
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
        shein_type = self._attach_shein_type()
        shein_property = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=property_obj,
            remote_id="PROP",
        )
        SheinProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=shein_type,
            property=shein_property,
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
        SheinPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=shein_property,
            local_instance=select_value,
            remote_id="BLUE",
        )
        SheinProductCategory.objects.create(
            product=self.product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CAT-1",
            product_type_remote_id="TYPE_A",
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
