import json
from unittest.mock import PropertyMock, patch

from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from properties.models import ProductProperty, Property, PropertySelectValue
from sales_channels.exceptions import RemotePropertyValueNotMapped
from sales_channels.integrations.shein.factories.properties.properties import (
    SheinProductPropertyCreateFactory,
)
from sales_channels.integrations.shein.models import (
    SheinProductProperty,
    SheinProductType,
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
    SheinSalesChannel,
)
from sales_channels.models.products import RemoteProduct


class SheinProductPropertyFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.has_errors_patcher = patch(
            "integrations.models.IntegrationObjectMixin.has_errors",
            new_callable=PropertyMock,
            return_value=False,
        )
        self.has_errors_patcher.start()
        self.addCleanup(self.has_errors_patcher.stop)

        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="sc-1",
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = RemoteProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="SKU-1",
        )
        self._product_type_counter = 0

    def _build_product_type_item(self, *, shein_property: SheinProperty, allows_custom: bool = False):
        self._product_type_counter += 1
        product_type = SheinProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id=f"pt-{self._product_type_counter}",
        )
        return SheinProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=product_type,
            property=shein_property,
            attribute_type=SheinProductTypeItem.AttributeType.SALES,
            allows_unmapped_values=allows_custom,
        )

    def test_builds_sales_attribute_payload_with_mapped_value(self):
        local_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        select_value = baker.make(
            PropertySelectValue,
            property=local_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        baker.make(
            "properties.PropertySelectValueTranslation",
            propertyselectvalue=select_value,
            value="Blue",
            language="en",
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=self.product,
            property=local_property,
            value_select=select_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        shein_property = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="2147484187",
            local_instance=local_property,
            allows_unmapped_values=False,
        )
        SheinPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=shein_property,
            remote_id="2147488294",
            local_instance=select_value,
        )
        product_type_item = self._build_product_type_item(shein_property=shein_property)

        factory = SheinProductPropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            product_type_item=product_type_item,
            get_value_only=True,
            skip_checks=True,
            language="en",
        )
        factory.run()

        remote_instance = SheinProductProperty.objects.get(
            local_instance=product_property,
            remote_product=self.remote_product,
        )
        payload = json.loads(remote_instance.remote_value)

        self.assertEqual(payload["attribute_id"], 2147484187)
        self.assertEqual(payload["attribute_value_id"], 2147488294)
        self.assertEqual(payload["attribute_type"], SheinProductTypeItem.AttributeType.SALES)
        self.assertEqual(payload["language"], "en")

    def test_allows_custom_sales_attribute_value_when_permitted(self):
        local_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        select_value = baker.make(
            PropertySelectValue,
            property=local_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        baker.make(
            "properties.PropertySelectValueTranslation",
            propertyselectvalue=select_value,
            value="Custom shade",
            language="en",
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=self.product,
            property=local_property,
            value_select=select_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        shein_property = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="2147489999",
            local_instance=local_property,
            allows_unmapped_values=True,
        )
        product_type_item = self._build_product_type_item(
            shein_property=shein_property,
            allows_custom=True,
        )

        factory = SheinProductPropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            product_type_item=product_type_item,
            get_value_only=True,
            skip_checks=True,
            language="en",
        )
        factory.run()

        remote_instance = SheinProductProperty.objects.get(
            local_instance=product_property,
            remote_product=self.remote_product,
        )
        payload = json.loads(remote_instance.remote_value)

        self.assertEqual(payload["attribute_id"], 2147489999)
        self.assertEqual(payload["custom_attribute_value"], "Custom shade")
        self.assertEqual(payload["attribute_type"], SheinProductTypeItem.AttributeType.SALES)
        self.assertNotIn("attribute_value_id", payload)

    def test_builds_manual_numeric_attribute(self):
        numeric_property = baker.make(
            Property,
            type=Property.TYPES.INT,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=self.product,
            property=numeric_property,
            value_int=5,
            multi_tenant_company=self.multi_tenant_company,
        )
        shein_property = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="300",
            local_instance=numeric_property,
            allows_unmapped_values=True,
        )
        product_type_item = self._build_product_type_item(shein_property=shein_property)
        factory = SheinProductPropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            product_type_item=product_type_item,
            get_value_only=True,
            skip_checks=True,
        )
        factory.run()

        remote_instance = SheinProductProperty.objects.get(
            local_instance=product_property,
            remote_product=self.remote_product,
        )
        payload = json.loads(remote_instance.remote_value)

        self.assertEqual(payload["attribute_extra_value"], 5)
        self.assertEqual(payload["attribute_id"], 300)
        self.assertNotIn("attribute_value_id", payload)

    def test_raises_when_value_unmapped_and_custom_disallowed(self):
        local_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        select_value = baker.make(
            PropertySelectValue,
            property=local_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        baker.make(
            "properties.PropertySelectValueTranslation",
            propertyselectvalue=select_value,
            value="Unmapped",
            language="en",
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=self.product,
            property=local_property,
            value_select=select_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        shein_property = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="500",
            local_instance=local_property,
            allows_unmapped_values=False,
        )
        product_type_item = self._build_product_type_item(shein_property=shein_property)

        factory = SheinProductPropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            product_type_item=product_type_item,
            get_value_only=True,
            skip_checks=True,
        )

        with self.assertRaises(RemotePropertyValueNotMapped):
            factory.run()
