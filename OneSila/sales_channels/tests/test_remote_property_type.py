from django.test import TransactionTestCase
from model_bakery import baker
from strawberry.relay import to_base64

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from properties.models import Property, PropertyTranslation
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.integrations.amazon.models.properties import AmazonProperty
from sales_channels.integrations.amazon.schema.types.types import AmazonPropertyType
from sales_channels.integrations.ebay.models import EbaySalesChannel, EbaySalesChannelView
from sales_channels.integrations.ebay.models.properties import EbayProperty
from sales_channels.integrations.ebay.schema.types.types import EbayPropertyType
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.magento2.models.properties import MagentoProperty
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.integrations.shein.models.properties import SheinProperty
from sales_channels.integrations.shein.schema.types.types import SheinPropertyType
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel, WoocommerceGlobalAttribute
from sales_channels.models.properties import RemoteProperty
from sales_channels.schema.types.types import RemotePropertyType


class RemotePropertyTypeResolverTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.amazon_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="amazon",
        )
        self.ebay_channel = baker.make(
            EbaySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="ebay",
        )
        self.shein_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein",
        )
        self.magento_channel = baker.make(
            MagentoSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://magento.example.com",
        )
        self.woocommerce_channel = baker.make(
            WoocommerceSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://woo.example.com",
        )

        self.local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        baker.make(
            PropertyTranslation,
            property=self.local_property,
            name="Local Name",
        )

    def test_remote_property_fields(self):
        shein_property = baker.make(
            SheinProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.shein_channel,
            name="Shein Name",
            name_en="Shein EN",
            allows_unmapped_values=True,
        )
        ebay_marketplace = baker.make(
            EbaySalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.ebay_channel,
        )
        ebay_property = baker.make(
            EbayProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.ebay_channel,
            marketplace=ebay_marketplace,
            localized_name="Ebay Name",
            translated_name="Ebay Translated",
            allows_unmapped_values=False,
        )
        amazon_property = baker.make(
            AmazonProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.amazon_channel,
            code="color",
            name="Amazon Name",
            allows_unmapped_values=True,
        )
        magento_property = baker.make(
            MagentoProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.magento_channel,
            local_instance=self.local_property,
            attribute_code="attr_code",
        )
        woo_property = baker.make(
            WoocommerceGlobalAttribute,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.woocommerce_channel,
            local_instance=self.local_property,
        )
        base_property = baker.make(
            RemoteProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.magento_channel,
        )

        self.assertEqual(
            RemotePropertyType.remote_name(shein_property, None),
            "Shein Name",
        )
        self.assertEqual(
            RemotePropertyType.translated_remote_name(shein_property, None),
            "Shein EN",
        )
        self.assertIsNone(RemotePropertyType.marketplace(shein_property, None))
        self.assertTrue(RemotePropertyType.allows_unmapped_values(shein_property, None))
        self.assertEqual(
            RemotePropertyType.proxy_id(shein_property, None),
            to_base64(SheinPropertyType, shein_property.pk),
        )

        self.assertEqual(
            RemotePropertyType.remote_name(ebay_property, None),
            "Ebay Name",
        )
        self.assertEqual(
            RemotePropertyType.translated_remote_name(ebay_property, None),
            "Ebay Translated",
        )
        self.assertEqual(
            RemotePropertyType.marketplace(ebay_property, None),
            ebay_marketplace,
        )
        self.assertFalse(RemotePropertyType.allows_unmapped_values(ebay_property, None))
        self.assertEqual(
            RemotePropertyType.proxy_id(ebay_property, None),
            to_base64(EbayPropertyType, ebay_property.pk),
        )

        self.assertEqual(
            RemotePropertyType.remote_name(amazon_property, None),
            "Amazon Name",
        )
        self.assertEqual(
            RemotePropertyType.translated_remote_name(amazon_property, None),
            "Amazon Name",
        )
        self.assertIsNone(RemotePropertyType.marketplace(amazon_property, None))
        self.assertTrue(RemotePropertyType.allows_unmapped_values(amazon_property, None))
        self.assertEqual(
            RemotePropertyType.proxy_id(amazon_property, None),
            to_base64(AmazonPropertyType, amazon_property.pk),
        )

        self.assertEqual(
            RemotePropertyType.remote_name(magento_property, None),
            "Local Name",
        )
        self.assertEqual(
            RemotePropertyType.translated_remote_name(magento_property, None),
            "Local Name",
        )
        self.assertIsNone(RemotePropertyType.marketplace(magento_property, None))
        self.assertTrue(RemotePropertyType.allows_unmapped_values(magento_property, None))
        self.assertEqual(
            RemotePropertyType.proxy_id(magento_property, None),
            to_base64(RemotePropertyType, magento_property.pk),
        )

        self.assertEqual(
            RemotePropertyType.remote_name(woo_property, None),
            "Local Name",
        )
        self.assertEqual(
            RemotePropertyType.translated_remote_name(woo_property, None),
            "Local Name",
        )
        self.assertIsNone(RemotePropertyType.marketplace(woo_property, None))
        self.assertTrue(RemotePropertyType.allows_unmapped_values(woo_property, None))
        self.assertEqual(
            RemotePropertyType.proxy_id(woo_property, None),
            to_base64(RemotePropertyType, woo_property.pk),
        )

        self.assertEqual(
            RemotePropertyType.remote_name(base_property, None),
            "Unknown",
        )
        self.assertIsNone(RemotePropertyType.translated_remote_name(base_property, None))
        self.assertIsNone(RemotePropertyType.marketplace(base_property, None))
        self.assertTrue(RemotePropertyType.allows_unmapped_values(base_property, None))
        self.assertEqual(
            RemotePropertyType.proxy_id(base_property, None),
            to_base64(RemotePropertyType, base_property.pk),
        )
