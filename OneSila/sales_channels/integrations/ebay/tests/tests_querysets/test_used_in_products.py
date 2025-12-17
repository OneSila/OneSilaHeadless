from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from properties.models import Property, PropertySelectValue, ProductProperty
from sales_channels.integrations.ebay.models import (
    EbayProduct,
    EbayProductProperty,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannel,
    EbaySalesChannelView,
)


class EbayRemotePropertyUsedInProductsQuerySetTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = EbaySalesChannel.objects.create(
            hostname="ebay-test",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.marketplace = EbaySalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = baker.make(
            EbayProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        self.property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        self.remote_property = baker.make(
            EbayProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.marketplace,
            local_instance=self.property,
        )

    def test_used_in_products_via_local_instance_property(self):
        product_property = baker.make(
            ProductProperty,
            product=self.product,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        baker.make(
            EbayProductProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            remote_property=None,
        )

        qs_used = EbayProperty.objects.filter(id=self.remote_property.id).used_in_products(True)
        self.assertEqual(list(qs_used), [self.remote_property])


class EbayRemoteSelectValueUsedInProductsQuerySetTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = EbaySalesChannel.objects.create(
            hostname="ebay-test",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.marketplace = EbaySalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = baker.make(
            EbayProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        self.property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        self.remote_property = baker.make(
            EbayProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.marketplace,
            local_instance=self.property,
        )

    def test_used_in_products_via_local_select_value(self):
        local_value = baker.make(
            PropertySelectValue,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        EbayPropertySelectValue.objects.bulk_create(
            [
                EbayPropertySelectValue(
                    ebay_property=self.remote_property,
                    marketplace=self.marketplace,
                    sales_channel=self.sales_channel,
                    multi_tenant_company=self.multi_tenant_company,
                    local_instance=local_value,
                    localized_value="V",
                )
            ]
        )
        remote_value = EbayPropertySelectValue.objects.get(
            sales_channel=self.sales_channel,
            marketplace=self.marketplace,
            localized_value="V",
        )
        product_property = baker.make(
            ProductProperty,
            product=self.product,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
            value_select=local_value,
        )
        baker.make(
            EbayProductProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            remote_property=self.remote_property,
        )

        qs_used = EbayPropertySelectValue.objects.filter(id=remote_value.id).used_in_products(True)
        self.assertEqual(list(qs_used), [remote_value])
