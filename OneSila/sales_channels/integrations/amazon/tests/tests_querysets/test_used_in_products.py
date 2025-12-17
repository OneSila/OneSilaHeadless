from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from properties.models import (
    Property,
    PropertySelectValue,
    ProductProperty,
)
from sales_channels.integrations.amazon.models import (
    AmazonProduct,
    AmazonProductProperty,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonSalesChannel,
    AmazonSalesChannelView,
)


class AmazonRemotePropertyUsedInProductsQuerySetTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = baker.make(
            AmazonProduct,
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
            AmazonProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
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
            AmazonProductProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            remote_property=None,
        )

        qs_used = AmazonProperty.objects.filter(id=self.remote_property.id).used_in_products(True)
        self.assertEqual(list(qs_used), [self.remote_property])

        qs_unused = AmazonProperty.objects.filter(id=self.remote_property.id).used_in_products(False)
        self.assertEqual(list(qs_unused), [])

    def test_used_in_products_via_remote_property(self):
        product_property = baker.make(
            ProductProperty,
            product=self.product,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        baker.make(
            AmazonProductProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            remote_property=self.remote_property,
        )

        qs_used = AmazonProperty.objects.filter(id=self.remote_property.id).used_in_products(True)
        self.assertEqual(list(qs_used), [self.remote_property])


class AmazonRemoteSelectValueUsedInProductsQuerySetTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.marketplace = baker.make(
            AmazonSalesChannelView,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = baker.make(
            AmazonProduct,
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
            AmazonProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.property,
        )

    def test_used_in_products_via_local_select_value(self):
        local_value = baker.make(
            PropertySelectValue,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonPropertySelectValue.objects.bulk_create(
            [
                AmazonPropertySelectValue(
                    amazon_property=self.remote_property,
                    marketplace=self.marketplace,
                    sales_channel=self.sales_channel,
                    multi_tenant_company=self.multi_tenant_company,
                    local_instance=local_value,
                    remote_value="VAL",
                )
            ]
        )
        remote_value = AmazonPropertySelectValue.objects.get(
            sales_channel=self.sales_channel,
            marketplace=self.marketplace,
            remote_value="VAL",
        )
        product_property = baker.make(
            ProductProperty,
            product=self.product,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
            value_select=local_value,
        )
        baker.make(
            AmazonProductProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            remote_property=self.remote_property,
        )

        qs_used = AmazonPropertySelectValue.objects.filter(id=remote_value.id).used_in_products(True)
        self.assertEqual(list(qs_used), [remote_value])

    def test_used_in_products_via_remote_select_value_field(self):
        AmazonPropertySelectValue.objects.bulk_create(
            [
                AmazonPropertySelectValue(
                    amazon_property=self.remote_property,
                    marketplace=self.marketplace,
                    sales_channel=self.sales_channel,
                    multi_tenant_company=self.multi_tenant_company,
                    local_instance=None,
                    remote_value="REMOTE_ONLY",
                )
            ]
        )
        remote_value = AmazonPropertySelectValue.objects.get(
            sales_channel=self.sales_channel,
            marketplace=self.marketplace,
            remote_value="REMOTE_ONLY",
        )
        product_property = baker.make(
            ProductProperty,
            product=self.product,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        baker.make(
            AmazonProductProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            remote_property=self.remote_property,
        )

        qs_used = AmazonPropertySelectValue.objects.filter(id=remote_value.id).used_in_products(True)
        self.assertEqual(list(qs_used), [remote_value])
