from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from properties.models import ProductProperty, Property
from sales_channels.integrations.shein.models import SheinProperty, SheinPropertySelectValue, SheinSalesChannel
from sales_channels.models.products import RemoteProduct
from sales_channels.models.properties import RemoteProductProperty


class SheinUsedInProductsQuerySetTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = baker.make(
            RemoteProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        self.property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )

        self.remote_property = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.property,
            remote_id="ATTR",
            name="Attr",
        )

        self.remote_value = SheinPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            remote_id="VAL",
            value="Val",
        )

    def test_shein_property_used_in_products(self):
        product_property = baker.make(
            ProductProperty,
            product=self.product,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        RemoteProductProperty.objects.bulk_create(
            [
                RemoteProductProperty(
                    multi_tenant_company=self.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=product_property,
                    remote_product=self.remote_product,
                    remote_property=self.remote_property,
                )
            ]
        )

        qs_used = SheinProperty.objects.filter(id=self.remote_property.id).used_in_products(True)
        self.assertEqual(list(qs_used), [self.remote_property])

        qs_unused = SheinProperty.objects.filter(id=self.remote_property.id).used_in_products(False)
        self.assertEqual(list(qs_unused), [])

    def test_shein_select_value_used_in_products(self):
        product_property = baker.make(
            ProductProperty,
            product=self.product,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        RemoteProductProperty.objects.bulk_create(
            [
                RemoteProductProperty(
                    multi_tenant_company=self.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=product_property,
                    remote_product=self.remote_product,
                    remote_property=self.remote_property,
                )
            ]
        )

        qs_used = SheinPropertySelectValue.objects.filter(id=self.remote_value.id).used_in_products(True)
        self.assertEqual(list(qs_used), [self.remote_value])
