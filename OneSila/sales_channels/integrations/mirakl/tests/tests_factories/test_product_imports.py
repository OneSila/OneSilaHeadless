from __future__ import annotations

from unittest.mock import patch

from currencies.models import PublicCurrency
from core.tests import TestCase
from model_bakery import baker
from properties.models import Property, PropertySelectValue
from sales_channels.integrations.mirakl.factories.imports.products.client import MiraklProductsImportClient
from sales_channels.integrations.mirakl.factories.imports.products import MiraklProductsImportProcessor
from sales_channels.integrations.mirakl.models import (
    MiraklPrice,
    MiraklProduct,
    MiraklProductContent,
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklSalesChannel,
    MiraklSalesChannelImport,
    MiraklSalesChannelView,
)
from sales_channels.models import SalesChannelViewAssign


class MiraklProductsImportProcessorTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
            active=True,
        )
        self.import_process = baker.make(
            MiraklSalesChannelImport,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelImport.TYPE_PRODUCTS,
            update_only=False,
        )
        self.view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="B2B",
            name="B2B",
        )
        self.color_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        self.brand_property = Property.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="brand",
        ).first()
        if self.brand_property is None:
            self.brand_property = baker.make(
                Property,
                multi_tenant_company=self.multi_tenant_company,
                internal_name="brand",
                type=Property.TYPES.SELECT,
            )
        self.color_option = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=self.color_property,
        )
        self.brand_option = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=self.brand_property,
            value="Acme",
        )
        self.remote_color = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="color",
            type=Property.TYPES.SELECT,
            local_instance=self.color_property,
        )
        baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=self.remote_color,
            code="RED",
            value="Red",
            local_instance=self.color_option,
        )
        self.remote_brand = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="brand",
            type=Property.TYPES.SELECT,
            local_instance=self.brand_property,
        )
        baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=self.remote_brand,
            code="ACME",
            value="Acme",
            local_instance=self.brand_option,
        )
        PublicCurrency.objects.get_or_create(
            iso_code="EUR",
            defaults={"name": "Euro", "symbol": "EUR"},
        )

    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.start_full_offer_export"
    )
    @patch("sales_channels.integrations.mirakl.factories.imports.products.processor.time.sleep")
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_offer_export_status"
    )
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.download_json_chunk"
    )
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_products_offers"
    )
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_products_by_references"
    )
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_account_info"
    )
    def test_run_imports_products_and_mirrors(
        self,
        get_account_info_mock,
        get_products_by_references_mock,
        get_products_offers_mock,
        download_chunk_mock,
        get_status_mock,
        sleep_mock,
        start_export_mock,
    ):
        get_account_info_mock.return_value = {"offers_count": 25}
        start_export_mock.return_value = {"tracking_id": "track-1"}
        get_status_mock.return_value = {
            "status": "COMPLETED",
            "urls": ["https://mirakl.example.com/export.json"],
        }
        download_chunk_mock.return_value = [
            {
                "offer-id": "offer-1",
                "product-sku": "MKP-1",
                "shop-sku": "SHOP-1",
                "active": True,
                "deleted": False,
                "channels": ["B2B"],
                "currency-iso-code": "EUR",
                "origin-price": "25.00",
                "discount-price": "19.99",
                "color": "Red",
            }
        ]
        get_products_offers_mock.return_value = [
            {
                "product_sku": "MKP-1",
                "product_title": "Mirakl Product",
                "product_description": "Imported from Mirakl",
                "category_code": "chairs",
                "product_references": [
                    {"reference_type": "EAN", "reference": "1234567890123"},
                ],
                "offers": [
                    {
                        "offer_id": "offer-1",
                        "shop_sku": "SHOP-1",
                    }
                ],
            }
        ]
        get_products_by_references_mock.return_value = [
            {
                "product_sku": "MKP-1",
                "product_brand": "Acme",
                "product_references": [
                    {"reference_type": "EAN", "reference": "1234567890123"},
                ],
            }
        ]

        processor = MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor.run()

        remote_product = MiraklProduct.objects.get(sales_channel=self.sales_channel, remote_sku="MKP-1")
        self.assertEqual(remote_product.local_instance.name, "Mirakl Product")
        self.assertTrue(
            remote_product.local_instance.productproperty_set.filter(
                property=self.color_property,
                value_select=self.color_option,
            ).exists()
        )
        self.assertTrue(
            remote_product.local_instance.productproperty_set.filter(
                property=self.brand_property,
                value_select=self.brand_option,
            ).exists()
        )
        content = MiraklProductContent.objects.get(remote_product=remote_product)
        self.assertEqual(content.content_data[self.multi_tenant_company.language]["description"], "Imported from Mirakl")
        price = MiraklPrice.objects.get(remote_product=remote_product)
        self.assertEqual(price.price_data["EUR"]["discount_price"], 19.99)
        self.assertTrue(
            SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                sales_channel_view=self.view,
                remote_product=remote_product,
            ).exists()
        )
        self.import_process.refresh_from_db()
        self.assertEqual(self.import_process.status, MiraklSalesChannelImport.STATUS_SUCCESS)
        self.assertEqual(self.import_process.total_records, 1)

    @patch("sales_channels.integrations.mirakl.factories.mixins.GetMiraklAPIMixin.mirakl_get")
    def test_account_info_request_reads_offers_count_source(self, mirakl_get_mock):
        mirakl_get_mock.return_value = {"offers_count": 123}

        client = MiraklProductsImportClient(sales_channel=self.sales_channel)
        payload = client.get_account_info()

        self.assertEqual(payload["offers_count"], 123)
        mirakl_get_mock.assert_called_once_with(path="/api/account")

    @patch("sales_channels.integrations.mirakl.factories.mixins.GetMiraklAPIMixin.mirakl_post")
    def test_offer_export_request_matches_expected_payload(self, mirakl_post_mock):
        mirakl_post_mock.return_value = {"tracking_id": "track-1"}

        client = MiraklProductsImportClient(sales_channel=self.sales_channel)
        client.start_full_offer_export()

        mirakl_post_mock.assert_called_once()
        payload = mirakl_post_mock.call_args.kwargs["payload"]
        self.assertEqual(payload["export_type"], "application/json")
        self.assertTrue(payload["include_inactive_offers"])
        self.assertEqual(payload["items_per_chunk"], 10000)
        self.assertEqual(payload["models"], ["MARKETPLACE"])
        self.assertNotIn("last_request_date", payload)
        self.assertIn("channels", payload["include_fields"])
        self.assertIn("offer-id", payload["include_fields"])
        self.assertIn("state-code", payload["include_fields"])
