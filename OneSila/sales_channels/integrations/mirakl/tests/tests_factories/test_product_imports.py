from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

from currencies.models import PublicCurrency
from core.tests import TestCase
from model_bakery import baker
from products.models import ConfigurableVariation, Product
from properties.models import Property, PropertySelectValue
from sales_prices.models import SalesPrice
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
        self.brand_option = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=self.brand_property,
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

    def _build_offer(self, *, shop_sku: str, product_sku: str, title: str = "U.S Army Jumpsuit Costume") -> dict:
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
            "product_references": [{"reference": "5055988633820", "reference_type": "EAN"}],
            "product_sku": product_sku,
            "product_title": title,
            "quantity": 30,
            "shipping_deadline": "2026-03-20T23:59:59.999Z",
            "shop_sku": shop_sku,
            "state_code": "11",
            "total_price": 15.99,
            "warehouses": None,
        }

    @patch("sales_channels.integrations.mirakl.factories.imports.products.processor.time.sleep")
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_product_by_reference"
    )
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_offers_page"
    )
    def test_run_imports_of21_offer_prices_and_p31_remote_id(
        self,
        get_offers_page_mock,
        get_product_by_reference_mock,
        _sleep_mock,
    ):
        offer = self._build_offer(shop_sku="ILFD7157XL", product_sku="M5055988633820")
        get_offers_page_mock.return_value = {
            "offers": [offer],
            "total_count": 1,
        }
        get_product_by_reference_mock.return_value = {
            "product_id": "P31-123",
            "product_references": [{"reference": "5055988633820", "reference_type": "EAN"}],
        }

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
        self.assertEqual(remote_price.price_data["GBP"]["discount_price"], 15.99)
        self.assertEqual(remote_price.price_data["GBP"]["price"], 21.99)
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
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_product_by_reference"
    )
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_offers_page"
    )
    def test_run_groups_same_of21_signature_into_synthetic_configurable_and_sleeps_between_pages(
        self,
        get_offers_page_mock,
        get_product_by_reference_mock,
        sleep_mock,
    ):
        first_offer = self._build_offer(shop_sku="ILFD7157XL", product_sku="M5055988633820")
        second_offer = self._build_offer(shop_sku="ILFD7157L", product_sku="M5055988633813")
        get_offers_page_mock.side_effect = [
            {"offers": [first_offer], "total_count": 2},
            {"offers": [second_offer], "total_count": 2},
        ]
        get_product_by_reference_mock.return_value = None

        MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        ).run()

        parent_remote = MiraklProduct.objects.get(
            sales_channel=self.sales_channel,
            raw_data__synthetic_configurable=True,
        )
        child_remotes = list(
            MiraklProduct.objects.filter(
                sales_channel=self.sales_channel,
                remote_parent_product=parent_remote,
            )
            .select_related("local_instance")
            .order_by("local_instance__sku")
        )

        self.import_process.refresh_from_db()
        self.assertEqual(self.import_process.total_records, 2)
        self.assertEqual(self.import_process.processed_records, 2)
        sleep_mock.assert_called_once_with(5)
        self.assertEqual(parent_remote.local_instance.type, Product.CONFIGURABLE)
        self.assertEqual(len(child_remotes), 2)
        self.assertTrue(all(child_remote.is_variation for child_remote in child_remotes))
        self.assertTrue(
            ConfigurableVariation.objects.filter(
                parent=parent_remote.local_instance,
                variation=child_remotes[0].local_instance,
            ).exists()
        )
        self.assertTrue(
            SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product=parent_remote.local_instance,
                remote_product=parent_remote,
            ).exists()
        )
        self.assertFalse(
            SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product__sku__in=["ILFD7157XL", "ILFD7157L"],
            ).exists()
        )

    @patch("sales_channels.integrations.mirakl.factories.imports.products.processor.time.sleep")
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_product_by_reference"
    )
    @patch(
        "sales_channels.integrations.mirakl.factories.imports.products.client.MiraklProductsImportClient.get_offers_page"
    )
    def test_p31_not_found_does_not_mark_import_broken(
        self,
        get_offers_page_mock,
        get_product_by_reference_mock,
        _sleep_mock,
    ):
        get_offers_page_mock.return_value = {
            "offers": [self._build_offer(shop_sku="ILFD4538XXL", product_sku="M5060347859551")],
            "total_count": 1,
        }
        get_product_by_reference_mock.return_value = None

        MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        ).run()

        self.import_process.refresh_from_db()
        self.assertEqual(self.import_process.status, MiraklSalesChannelImport.STATUS_SUCCESS)
        self.assertEqual(self.import_process.broken_records, [])
