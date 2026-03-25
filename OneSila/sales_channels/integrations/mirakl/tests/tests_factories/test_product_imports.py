from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

from currencies.models import PublicCurrency
from core.tests import TestCase
from model_bakery import baker
from media.models import MediaProductThrough
from products.models import ConfigurableVariation, Product
from properties.models import (
    Property,
    PropertySelectValue,
    PropertySelectValueTranslation,
    PropertyTranslation,
)
from sales_prices.models import SalesPrice
from sales_channels.integrations.mirakl.factories.imports.products.client import MiraklProductsImportClient
from sales_channels.integrations.mirakl.factories.imports.products import MiraklProductsImportProcessor
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklPrice,
    MiraklProduct,
    MiraklProductCategory,
    MiraklProductContent,
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklSalesChannel,
    MiraklSalesChannelImport,
    MiraklSalesChannelView,
)
from sales_channels.models import SalesChannelViewAssign
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklProductsImportProcessorTests(DisableMiraklConnectionMixin, TestCase):
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
            skip_broken_records=True,
        )
        self.view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="INIT",
            name="INIT",
        )
        self.category = baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="toys-dress_up_and_role_play",
            name="Dress Up & Role Play",
            is_leaf=True,
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
            PropertyTranslation.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                property=self.brand_property,
                language=self.multi_tenant_company.language,
                name="Brand",
            )
        self.brand_option = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=self.brand_property,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.brand_option,
            language=self.multi_tenant_company.language,
            value="I Love Fancy Dress",
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
            code="ILFD",
            value="I Love Fancy Dress",
            local_instance=self.brand_option,
        )
        PublicCurrency.objects.get_or_create(
            iso_code="GBP",
            defaults={"name": "Pound Sterling", "symbol": "GBP"},
        )

    def _build_offer(
        self,
        *,
        shop_sku: str,
        product_sku: str,
        title: str = "U.S Army Jumpsuit Costume",
        reference: str = "5055988633820",
    ) -> dict:
        return {
            "active": True,
            "all_prices": [
                {
                    "price": 15.99,
                    "unit_origin_price": 15.99,
                    "unit_discount_price": None,
                    "channel_code": None,
                    "volume_prices": [
                        {
                            "price": 15.99,
                            "quantity_threshold": 1,
                            "unit_origin_price": 15.99,
                            "unit_discount_price": None,
                        }
                    ],
                }
            ],
            "allow_quote_requests": False,
            "applicable_pricing": {
                "price": 15.99,
                "unit_origin_price": 15.99,
                "unit_discount_price": None,
                "channel_code": None,
                "volume_prices": [
                    {
                        "price": 15.99,
                        "quantity_threshold": 1,
                        "unit_origin_price": 15.99,
                        "unit_discount_price": None,
                    }
                ],
            },
            "category_code": "toys-dress_up_and_role_play",
            "category_label": "Dress Up & Role Play",
            "channels": ["INIT"],
            "currency_iso_code": "GBP",
            "description": None,
            "fulfillment": {"center": {"code": "DEFAULT"}},
            "internal_description": "Back office copy",
            "leadtime_to_ship": 3,
            "logistic_class": {"code": "INIT", "label": "Default logistic family"},
            "min_shipping_price": 0.0,
            "min_shipping_price_additional": 0.0,
            "min_shipping_type": "ukstandard",
            "min_shipping_zone": "GB",
            "msrp": 21.99,
            "offer_additional_fields": [],
            "offer_id": 18117596,
            "price": 15.99,
            "price_additional_info": None,
            "product_brand": "I Love Fancy Dress",
            "product_description": "Mirakl imported description",
            "product_references": [{"reference": reference, "reference_type": "EAN"}],
            "product_sku": product_sku,
            "product_title": title,
            "quantity": 30,
            "shipping_deadline": "2026-03-20T23:59:59.999Z",
            "shop_sku": shop_sku,
            "state_code": "11",
            "total_price": 15.99,
            "warehouses": None,
        }

    def _build_p11_product(
        self,
        *,
        reference: str,
        product_sku: str,
        title: str = "U.S Army Jumpsuit Costume",
        description: str = "P11 product description",
        brand: str = "I Love Fancy Dress",
    ) -> dict:
        return {
            "category_code": "toys-dress_up_and_role_play",
            "category_label": "Dress Up & Role Play",
            "product_brand": brand,
            "product_description": description,
            "product_media": {
                "media_url": "https://cdn.example.com/mirakl-image.jpg",
                "type": "LARGE",
            },
            "product_references": [{"reference": reference, "reference_type": "EAN"}],
            "product_sku": product_sku,
            "product_title": title,
            "offers": [],
            "total_count": 1,
        }

    def _build_p31_product(self, *, reference: str, product_sku: str) -> dict:
        return {
            "category_code": "toys-dress_up_and_role_play",
            "category_label": "Dress Up & Role Play",
            "product_id": "P31-123",
            "product_id_type": "EAN",
            "product_sku": product_sku,
            "product_title": "U.S Army Jumpsuit Costume",
            "product_references": [{"reference": reference, "reference_type": "EAN"}],
        }

    @patch("sales_channels.integrations.mirakl.factories.imports.products.processor.time.sleep")
    @patch(
        "imports_exports.factories.media.ImportImageInstance.download_image_from_url"
    )
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_offers_page"
    )
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_products_by_references"
    )
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_products_offers_by_references"
    )
    def test_run_imports_of21_offer_prices_and_p31_remote_id(
        self,
        get_products_offers_by_references_mock,
        get_products_by_references_mock,
        get_offers_page_mock,
        download_image_from_url_mock,
        _sleep_mock,
    ):
        offer = self._build_offer(shop_sku="ILFD7157XL", product_sku="M5055988633820")
        offer["product_description"] = ""
        get_offers_page_mock.return_value = {
            "offers": [offer],
            "total_count": 1,
        }
        get_products_offers_by_references_mock.return_value = [
            self._build_p11_product(
                reference="5055988633820",
                product_sku="M5055988633820",
                description="P11 enriched description",
            )
        ]
        get_products_by_references_mock.return_value = [
            self._build_p31_product(
                reference="5055988633820",
                product_sku="M5055988633820",
            )
        ]
        download_image_from_url_mock.return_value = None

        MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        ).run()

        remote_product = MiraklProduct.objects.get(
            sales_channel=self.sales_channel,
            remote_sku="M5055988633820",
        )
        local_price = SalesPrice.objects.get(
            product=remote_product.local_instance,
            currency__iso_code="GBP",
        )
        content = MiraklProductContent.objects.get(remote_product=remote_product)
        remote_price = MiraklPrice.objects.get(remote_product=remote_product)

        self.assertEqual(remote_product.remote_id, "P31-123")
        self.assertEqual(remote_product.local_instance.sku, "ILFD7157XL")
        self.assertEqual(local_price.price, Decimal("15.99"))
        self.assertEqual(local_price.rrp, Decimal("21.99"))
        self.assertEqual(
            content.content_data[self.multi_tenant_company.language]["short_description"],
            "Back office copy",
        )
        self.assertEqual(
            content.content_data[self.multi_tenant_company.language]["description"],
            "P11 enriched description",
        )
        self.assertEqual(remote_price.price_data["GBP"]["discount_price"], 15.99)
        self.assertEqual(remote_price.price_data["GBP"]["price"], 21.99)
        get_products_offers_by_references_mock.assert_called_once_with(
            product_references=[("EAN", "5055988633820")],
        )
        get_products_by_references_mock.assert_called_once_with(
            product_references=[("EAN", "5055988633820")],
        )
        self.assertTrue(
            SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                sales_channel_view=self.view,
                remote_product=remote_product,
                product=remote_product.local_instance,
            ).exists()
        )

    @patch("sales_channels.integrations.mirakl.factories.imports.products.processor.time.sleep")
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_products_by_references"
    )
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_offers_page"
    )
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_products_offers_by_references"
    )
    def test_p31_not_found_does_not_mark_import_broken(
        self,
        get_products_offers_by_references_mock,
        get_offers_page_mock,
        get_products_by_references_mock,
        _sleep_mock,
    ):
        get_offers_page_mock.return_value = {
            "offers": [self._build_offer(shop_sku="ILFD4538XXL", product_sku="M5060347859551")],
            "total_count": 1,
        }
        get_products_offers_by_references_mock.return_value = []
        get_products_by_references_mock.return_value = []

        MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        ).run()

        self.import_process.refresh_from_db()
        self.assertEqual(self.import_process.status, MiraklSalesChannelImport.STATUS_SUCCESS)
        self.assertEqual(self.import_process.broken_records, [])


class MiraklProductsImportClientTests(DisableMiraklConnectionMixin, TestCase):
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

    def test_get_products_by_references_batches_requests_by_100(self):
        client = MiraklProductsImportClient(sales_channel=self.sales_channel)
        product_references = [("EAN", f"code-{index}") for index in range(205)]

        with patch.object(client, "mirakl_get", return_value={"products": []}) as mirakl_get_mock:
            client.get_products_by_references(product_references=product_references)

        self.assertEqual(mirakl_get_mock.call_count, 3)
        first_batch = mirakl_get_mock.call_args_list[0].kwargs["params"]["product_references"].split(",")
        second_batch = mirakl_get_mock.call_args_list[1].kwargs["params"]["product_references"].split(",")
        third_batch = mirakl_get_mock.call_args_list[2].kwargs["params"]["product_references"].split(",")

        self.assertEqual(len(first_batch), 100)
        self.assertEqual(len(second_batch), 100)
        self.assertEqual(len(third_batch), 5)
