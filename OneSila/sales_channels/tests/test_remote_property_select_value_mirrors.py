from django.test import TransactionTestCase
from model_bakery import baker
from strawberry.relay import to_base64

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation
from sales_channels.integrations.amazon.models import AmazonSalesChannel, AmazonSalesChannelView
from sales_channels.integrations.amazon.models.properties import AmazonProperty, AmazonPropertySelectValue
from sales_channels.integrations.amazon.schema.types.types import AmazonPropertySelectValueType
from sales_channels.integrations.ebay.models import EbaySalesChannel, EbaySalesChannelView
from sales_channels.integrations.ebay.models.properties import EbayProperty, EbayPropertySelectValue
from sales_channels.integrations.ebay.schema.types.types import EbayPropertySelectValueType
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.magento2.models.properties import MagentoProperty, MagentoPropertySelectValue
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.integrations.shein.models.properties import SheinProperty, SheinPropertySelectValue
from sales_channels.integrations.shein.schema.types.types import SheinPropertySelectValueType
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel, WoocommerceGlobalAttribute, WoocommerceGlobalAttributeValue
from sales_channels.schema.types.types import RemotePropertySelectValueType
from sales_channels.tests.helpers import DisableMagentoAndWooConnectionsMixin


class RemotePropertySelectValueMirrorsQueryTest(
    DisableMagentoAndWooConnectionsMixin,
    TransactionTestCaseMixin,
    TransactionTestCase,
):
    def setUp(self):
        super().setUp()
        self.local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        self.local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=self.local_property,
        )
        baker.make(
            PropertySelectValueTranslation,
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.local_value,
            language=self.multi_tenant_company.language,
            value="Local Value",
        )

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

    def test_remote_property_select_value_mirrors(self):
        shein_property = baker.make(
            SheinProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.shein_channel,
        )
        shein_value = baker.make(
            SheinPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.shein_channel,
            remote_property=shein_property,
            local_instance=self.local_value,
            value="Shein Value",
            value_en="Shein Translated",
        )

        amazon_property = baker.make(
            AmazonProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.amazon_channel,
            code="color",
            name="Color",
        )
        amazon_marketplace = baker.make(
            AmazonSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.amazon_channel,
        )
        amazon_value = baker.make(
            AmazonPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.amazon_channel,
            amazon_property=amazon_property,
            marketplace=amazon_marketplace,
            local_instance=self.local_value,
            remote_value="red",
            remote_name="Red",
            translated_remote_name="Rot",
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
            localized_name="Color",
            translated_name="Farbe",
        )
        ebay_value = baker.make(
            EbayPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.ebay_channel,
            ebay_property=ebay_property,
            marketplace=ebay_marketplace,
            local_instance=self.local_value,
            localized_value="Blue",
            translated_value="Blau",
        )

        magento_property = baker.make(
            MagentoProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.magento_channel,
            local_instance=self.local_property,
            attribute_code="attr_code",
        )
        magento_value = baker.make(
            MagentoPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.magento_channel,
            remote_property=magento_property,
            local_instance=self.local_value,
        )

        woo_property = baker.make(
            WoocommerceGlobalAttribute,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.woocommerce_channel,
            local_instance=self.local_property,
        )
        woo_value = baker.make(
            WoocommerceGlobalAttributeValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.woocommerce_channel,
            remote_property=woo_property,
            local_instance=self.local_value,
        )

        query = """
            query($value: String!) {
              remotePropertySelectValueMirrors(propertySelectValue: $value) {
                value
                translatedValue
                marketplace { id }
                proxyId
                remoteProperty { proxyId }
              }
            }
        """
        resp = self.strawberry_test_client(
            query=query,
            variables={"value": self.to_global_id(self.local_value)},
        )
        self.assertTrue(resp.errors is None)

        results = {item["proxyId"]: item for item in resp.data["remotePropertySelectValueMirrors"]}
        self.assertEqual(len(results), 5)

        self.assertEqual(
            results[to_base64(SheinPropertySelectValueType, shein_value.pk)]["value"],
            "Shein Value",
        )
        self.assertEqual(
            results[to_base64(SheinPropertySelectValueType, shein_value.pk)]["translatedValue"],
            "Shein Translated",
        )
        self.assertIsNone(
            results[to_base64(SheinPropertySelectValueType, shein_value.pk)]["marketplace"],
        )

        self.assertEqual(
            results[to_base64(AmazonPropertySelectValueType, amazon_value.pk)]["value"],
            "Red",
        )
        self.assertEqual(
            results[to_base64(AmazonPropertySelectValueType, amazon_value.pk)]["translatedValue"],
            "Rot",
        )
        self.assertEqual(
            results[to_base64(AmazonPropertySelectValueType, amazon_value.pk)]["marketplace"]["id"],
            to_base64("SalesChannelViewType", amazon_marketplace.pk),
        )

        self.assertEqual(
            results[to_base64(EbayPropertySelectValueType, ebay_value.pk)]["value"],
            "Blue",
        )
        self.assertEqual(
            results[to_base64(EbayPropertySelectValueType, ebay_value.pk)]["translatedValue"],
            "Blau",
        )
        self.assertEqual(
            results[to_base64(EbayPropertySelectValueType, ebay_value.pk)]["marketplace"]["id"],
            to_base64("SalesChannelViewType", ebay_marketplace.pk),
        )

        self.assertEqual(
            results[to_base64(RemotePropertySelectValueType, magento_value.pk)]["value"],
            "Local Value",
        )
        self.assertEqual(
            results[to_base64(RemotePropertySelectValueType, magento_value.pk)]["translatedValue"],
            "Local Value",
        )
        self.assertIsNone(
            results[to_base64(RemotePropertySelectValueType, magento_value.pk)]["marketplace"],
        )

        self.assertEqual(
            results[to_base64(RemotePropertySelectValueType, woo_value.pk)]["value"],
            "Local Value",
        )
        self.assertEqual(
            results[to_base64(RemotePropertySelectValueType, woo_value.pk)]["translatedValue"],
            "Local Value",
        )
        self.assertIsNone(
            results[to_base64(RemotePropertySelectValueType, woo_value.pk)]["marketplace"],
        )
