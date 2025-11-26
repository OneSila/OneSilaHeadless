from core.tests import TestCase
from model_bakery import baker
from properties.models import Property, PropertySelectValue, ProductProperty
from products.models import Product
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonProduct,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProductProperty,
)
from sales_channels.integrations.amazon.factories.auto_import import AmazonAutoImportSelectValueFactory
from ..helpers import DisableWooCommerceSignalsMixin


class AmazonAutoImportSelectValueFactoryTest(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="VIEW",
        )
        self.property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.property,
            code="color",
            type=Property.TYPES.SELECT,
            allows_unmapped_values=True,
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        self.remote_select_value = AmazonPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_property=self.remote_property,
            marketplace=self.view,
            remote_value="red",
            remote_name="Red",
        )
        self.remote_product_property = AmazonProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            remote_property=self.remote_property,
            remote_value="red",
            remote_select_value=self.remote_select_value,
        )

    def test_run_maps_and_creates_product_property(self):
        local_value = baker.make(
            PropertySelectValue,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_select_value.local_instance = local_value
        self.remote_select_value.save()

        fac = AmazonAutoImportSelectValueFactory(self.remote_select_value)
        fac.run()

        pp = ProductProperty.objects.get(product=self.product, property=self.property)
        self.assertEqual(pp.value_select, local_value)
        self.remote_product_property.refresh_from_db()
        self.assertEqual(self.remote_product_property.local_instance, pp)
