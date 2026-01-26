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
from sales_channels.tests.helpers import DisableMagentoAndWooConnectionsMixin


class RemotePropertyTypeResolverTest(
    DisableMagentoAndWooConnectionsMixin,
    TransactionTestCaseMixin,
    TransactionTestCase,
):
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

        query = """
            query {
              remoteProperties {
                edges {
                  node {
                    remoteName
                    translatedRemoteName
                    marketplace { id }
                    allowsUnmappedValues
                    proxyId
                  }
                }
              }
            }
        """
        resp = self.strawberry_test_client(query=query)
        self.assertTrue(resp.errors is None)

        results = {
            item["node"]["proxyId"]: item["node"]
            for item in resp.data["remoteProperties"]["edges"]
        }

        self.assertEqual(
            results[to_base64(SheinPropertyType, shein_property.pk)]["remoteName"],
            "Shein Name",
        )
        self.assertEqual(
            results[to_base64(SheinPropertyType, shein_property.pk)]["translatedRemoteName"],
            "Shein EN",
        )
        self.assertIsNone(
            results[to_base64(SheinPropertyType, shein_property.pk)]["marketplace"],
        )
        self.assertTrue(
            results[to_base64(SheinPropertyType, shein_property.pk)]["allowsUnmappedValues"],
        )
        self.assertEqual(
            results[to_base64(SheinPropertyType, shein_property.pk)]["proxyId"],
            to_base64(SheinPropertyType, shein_property.pk),
        )

        self.assertEqual(
            results[to_base64(EbayPropertyType, ebay_property.pk)]["remoteName"],
            "Ebay Name",
        )
        self.assertEqual(
            results[to_base64(EbayPropertyType, ebay_property.pk)]["translatedRemoteName"],
            "Ebay Translated",
        )
        self.assertEqual(
            results[to_base64(EbayPropertyType, ebay_property.pk)]["marketplace"]["id"],
            to_base64("SalesChannelViewType", ebay_marketplace.pk),
        )
        self.assertFalse(
            results[to_base64(EbayPropertyType, ebay_property.pk)]["allowsUnmappedValues"],
        )
        self.assertEqual(
            results[to_base64(EbayPropertyType, ebay_property.pk)]["proxyId"],
            to_base64(EbayPropertyType, ebay_property.pk),
        )

        self.assertEqual(
            results[to_base64(AmazonPropertyType, amazon_property.pk)]["remoteName"],
            "Amazon Name",
        )
        self.assertEqual(
            results[to_base64(AmazonPropertyType, amazon_property.pk)]["translatedRemoteName"],
            "Amazon Name",
        )
        self.assertIsNone(
            results[to_base64(AmazonPropertyType, amazon_property.pk)]["marketplace"],
        )
        self.assertTrue(
            results[to_base64(AmazonPropertyType, amazon_property.pk)]["allowsUnmappedValues"],
        )
        self.assertEqual(
            results[to_base64(AmazonPropertyType, amazon_property.pk)]["proxyId"],
            to_base64(AmazonPropertyType, amazon_property.pk),
        )

        self.assertEqual(
            results[to_base64(RemotePropertyType, magento_property.pk)]["remoteName"],
            "Local Name",
        )
        self.assertEqual(
            results[to_base64(RemotePropertyType, magento_property.pk)]["translatedRemoteName"],
            "Local Name",
        )
        self.assertIsNone(
            results[to_base64(RemotePropertyType, magento_property.pk)]["marketplace"],
        )
        self.assertTrue(
            results[to_base64(RemotePropertyType, magento_property.pk)]["allowsUnmappedValues"],
        )
        self.assertEqual(
            results[to_base64(RemotePropertyType, magento_property.pk)]["proxyId"],
            to_base64(RemotePropertyType, magento_property.pk),
        )

        self.assertEqual(
            results[to_base64(RemotePropertyType, woo_property.pk)]["remoteName"],
            "Local Name",
        )
        self.assertEqual(
            results[to_base64(RemotePropertyType, woo_property.pk)]["translatedRemoteName"],
            "Local Name",
        )
        self.assertIsNone(
            results[to_base64(RemotePropertyType, woo_property.pk)]["marketplace"],
        )
        self.assertTrue(
            results[to_base64(RemotePropertyType, woo_property.pk)]["allowsUnmappedValues"],
        )
        self.assertEqual(
            results[to_base64(RemotePropertyType, woo_property.pk)]["proxyId"],
            to_base64(RemotePropertyType, woo_property.pk),
        )

        self.assertEqual(
            results[to_base64(RemotePropertyType, base_property.pk)]["remoteName"],
            "Unknown",
        )
        self.assertIsNone(
            results[to_base64(RemotePropertyType, base_property.pk)]["translatedRemoteName"],
        )
        self.assertIsNone(
            results[to_base64(RemotePropertyType, base_property.pk)]["marketplace"],
        )
        self.assertTrue(
            results[to_base64(RemotePropertyType, base_property.pk)]["allowsUnmappedValues"],
        )
        self.assertEqual(
            results[to_base64(RemotePropertyType, base_property.pk)]["proxyId"],
            to_base64(RemotePropertyType, base_property.pk),
        )
