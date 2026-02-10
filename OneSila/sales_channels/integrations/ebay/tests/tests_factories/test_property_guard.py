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
from sales_channels.integrations.ebay.factories.task_queue import EbayProductPropertyAddTask
from sales_channels.integrations.ebay.models import (
    EbayProduct,
    EbayCategory,
    EbayProductType,
    EbayProductTypeItem,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannel,
    EbaySalesChannelView, EbayProductCategory,
)


class EbayProductPropertyGuardTests(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = EbaySalesChannel.objects.create(
            hostname="https://ebay.example.com",
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="EBAY_US",
            name="US",
        )
        tree_id = getattr(self.view, "default_category_tree_id", None) or "0"
        self.category = EbayCategory.objects.create(
            marketplace_default_tree_id=tree_id,
            remote_id="123",
            name="Category",
            full_name="Category",
            has_children=False,
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="EBAY-GUARD",
        )
        self.remote_product = EbayProduct.objects.create(
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
        return EbayProductPropertyAddTask(
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

    def _attach_ebay_type(self):
        return EbayProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=self.rule,
            remote_id="123",
        )

    def test_ebay_guard_blocks_when_property_not_mapped(self):
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
        self._attach_ebay_type()
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
        )

        task = self._task(product_property=product_property)
        result = task.guard(target=self._target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "ebay_property_not_mapped")

    def test_ebay_guard_blocks_when_property_not_in_type(self):
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
        self._attach_ebay_type()
        EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=property_obj,
            remote_id="PROP",
        )
        EbayProductCategory.objects.create(
            product=self.product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            view=self.view,
            remote_id="123",
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=property_obj,
        )

        task = self._task(product_property=product_property)
        result = task.guard(target=self._target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "ebay_aspect_not_allowed_in_category")

    def test_ebay_guard_blocks_when_category_missing(self):
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
        EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
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
        self.assertEqual(result.reason, "ebay_category_missing")

    def test_ebay_guard_allows_when_select_value_mapped(self):
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
        ebay_type = self._attach_ebay_type()
        ebay_property = EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=property_obj,
            remote_id="PROP",
        )
        EbayProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=ebay_type,
            ebay_property=ebay_property,
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
        EbayPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            ebay_property=ebay_property,
            marketplace=self.view,
            local_instance=select_value,
            localized_value="Blue",
        )
        EbayProductCategory.objects.create(
            product=self.product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            view=self.view,
            remote_id="123",
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
