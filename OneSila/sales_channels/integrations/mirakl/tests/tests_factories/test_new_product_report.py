from unittest.mock import patch

from django.core.files.base import ContentFile
from model_bakery import baker

from core.tests import TestCase
from integrations.models import IntegrationLog
from products.models import ConfigurableVariation
from sales_channels.exceptions import MiraklNewProductReportLookupError
from sales_channels.integrations.mirakl.factories.feeds import MiraklNewProductReportSyncFactory
from sales_channels.integrations.mirakl.models import (
    MiraklEanCode,
    MiraklProduct,
    MiraklProperty,
    MiraklProductType,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelFeedItem,
    MiraklSalesChannelView,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklNewProductReportSyncFactoryTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="DEFAULT",
            name="Default",
        )
        self.product_type = baker.make(
            MiraklProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="ean",
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_EAN,
        )
        self.remote_product = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_sku="",
            remote_id="",
            syncing_current_percentage=40,
        )
        self.feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            product_type=self.product_type,
            type=MiraklSalesChannelFeed.TYPE_COMBINED,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_PARTIAL,
            remote_id="3001",
        )
        baker.make(
            MiraklSalesChannelFeedItem,
            multi_tenant_company=self.multi_tenant_company,
            feed=self.feed,
            remote_product=self.remote_product,
            sales_channel_view=self.view,
            payload_data=[
                {
                    "product_id": "LOCAL-SKU-1",
                    "ean": "5056863153495",
                    "product_title": "Dog Ballerina Costume",
                }
            ],
        )

    def test_mirakl_sales_channel_exposes_new_report_lookup_error_as_user_exception(self):
        self.assertIn(MiraklNewProductReportLookupError, self.sales_channel._meta.user_exceptions)

    @patch.object(MiraklNewProductReportSyncFactory, "mirakl_get")
    def test_run_parses_csv_and_syncs_remote_identifiers_from_p31(self, mirakl_get_mock):
        self.feed.new_product_report_file.save(
            "mirakl-added-products.csv",
            ContentFile(
                "\n".join(
                    [
                        '"product_category","product_id","ean","errors"',
                        '"toys-dress_up_and_role_play","LOCAL-SKU-1","5056863153495","1001|Brand is required"',
                    ]
                )
            ),
            save=True,
        )
        mirakl_get_mock.return_value = {
            "products": [
                {
                    "category_code": "5110114",
                    "category_label": "Coffee Machines",
                    "product_id": "5056863153495",
                    "product_id_type": "EAN",
                    "product_sku": "MKP100000000037254",
                    "product_title": "Dog Ballerina Costume",
                }
            ]
        }

        synced_count = MiraklNewProductReportSyncFactory(feed=self.feed).run()

        self.assertEqual(synced_count, 1)
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.remote_sku, "MKP100000000037254")
        self.assertEqual(self.remote_product.remote_id, "5056863153495")
        self.assertEqual(self.remote_product.product_id_type, "EAN")
        self.assertEqual(self.remote_product.product_reference, "5056863153495")
        self.assertEqual(self.remote_product.title, "Dog Ballerina Costume")
        self.assertEqual(self.remote_product.syncing_current_percentage, 100)
        self.assertEqual(
            self.remote_product.raw_data["new_product_report"]["ean"],
            "5056863153495",
        )
        self.assertEqual(
            self.remote_product.raw_data["new_product_report_lookup"]["product_sku"],
            "MKP100000000037254",
        )
        self.assertTrue(
            MiraklEanCode.objects.filter(
                remote_product=self.remote_product,
                ean_code="5056863153495",
            ).exists()
        )
        mirakl_get_mock.assert_called_once_with(
            path="/api/products",
            params={"product_references": "EAN|5056863153495"},
        )
        self.assertTrue(
            IntegrationLog.objects.filter(
                remote_product=self.remote_product,
                identifier=MiraklNewProductReportSyncFactory.LOG_FIX_IDENTIFIER,
                status=IntegrationLog.STATUS_SUCCESS,
            ).exists()
        )

    @patch.object(MiraklNewProductReportSyncFactory, "mirakl_get")
    def test_run_syncs_configurable_added_product_to_variation_mirror(self, mirakl_get_mock):
        parent_product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="CONFIGURABLE",
            sku="PARENT-1",
        )
        child_product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
            sku="CHILD-1",
        )
        baker.make(
            ConfigurableVariation,
            multi_tenant_company=self.multi_tenant_company,
            parent=parent_product,
            variation=child_product,
        )
        self.remote_product.local_instance = parent_product
        self.remote_product.remote_sku = ""
        self.remote_product.save(update_fields=["local_instance", "remote_sku"])
        child_remote = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_product,
            remote_parent_product=self.remote_product,
            is_variation=True,
            remote_sku="",
            remote_id="",
        )
        self.feed.items.all().delete()
        baker.make(
            MiraklSalesChannelFeedItem,
            multi_tenant_company=self.multi_tenant_company,
            feed=self.feed,
            remote_product=self.remote_product,
            sales_channel_view=self.view,
            payload_data=[
                {
                    "sku": "CHILD-1",
                    "product_id": "CHILD-1",
                    "ean": "5056863153495",
                    "product_title": "Dog Ballerina Costume",
                }
            ],
        )
        self.feed.new_product_report_file.save(
            "mirakl-added-products.csv",
            ContentFile(
                "\n".join(
                    [
                        '"product_category","product_id","ean","errors"',
                        '"toys-dress_up_and_role_play","CHILD-1","5056863153495",""',
                    ]
                )
            ),
            save=True,
        )
        mirakl_get_mock.return_value = {
            "products": [
                {
                    "category_code": "5110114",
                    "category_label": "Coffee Machines",
                    "product_id": "5056863153495",
                    "product_id_type": "EAN",
                    "product_sku": "MKP100000000037254",
                    "product_title": "Dog Ballerina Costume",
                }
            ]
        }

        synced_count = MiraklNewProductReportSyncFactory(feed=self.feed).run()

        self.assertEqual(synced_count, 1)
        self.remote_product.refresh_from_db()
        child_remote.refresh_from_db()
        self.assertEqual(self.remote_product.remote_sku, "")
        self.assertEqual(child_remote.remote_sku, "MKP100000000037254")
        self.assertEqual(child_remote.remote_id, "5056863153495")
        self.assertTrue(
            MiraklEanCode.objects.filter(
                remote_product=child_remote,
                ean_code="5056863153495",
            ).exists()
        )

    @patch.object(MiraklNewProductReportSyncFactory, "mirakl_get")
    def test_run_matches_variation_rows_with_namespaced_offer_keys(self, mirakl_get_mock):
        parent_product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="CONFIGURABLE",
            sku="PARENT-1",
        )
        child_product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
            sku="CHILD-1",
        )
        baker.make(
            ConfigurableVariation,
            multi_tenant_company=self.multi_tenant_company,
            parent=parent_product,
            variation=child_product,
        )
        self.remote_product.local_instance = parent_product
        self.remote_product.remote_sku = ""
        self.remote_product.save(update_fields=["local_instance", "remote_sku"])
        child_remote = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_product,
            remote_parent_product=self.remote_product,
            is_variation=True,
            remote_sku="",
            remote_id="",
        )
        self.feed.items.all().delete()
        baker.make(
            MiraklSalesChannelFeedItem,
            multi_tenant_company=self.multi_tenant_company,
            feed=self.feed,
            remote_product=self.remote_product,
            sales_channel_view=self.view,
            payload_data=[
                {
                    "offer__sku": "CHILD-1",
                    "offer__product-id": "CHILD-1",
                    "ean": "5056863153495",
                }
            ],
        )
        self.feed.new_product_report_file.save(
            "mirakl-added-products.csv",
            ContentFile(
                "\n".join(
                    [
                        '"product_category","product_id","ean","errors"',
                        '"toys-dress_up_and_role_play","CHILD-1","5056863153495",""',
                    ]
                )
            ),
            save=True,
        )
        mirakl_get_mock.return_value = {
            "products": [
                {
                    "category_code": "5110114",
                    "category_label": "Coffee Machines",
                    "product_id": "5056863153495",
                    "product_id_type": "EAN",
                    "product_sku": "MKP100000000037254",
                    "product_title": "Dog Ballerina Costume",
                }
            ]
        }

        synced_count = MiraklNewProductReportSyncFactory(feed=self.feed).run()

        self.assertEqual(synced_count, 1)
        child_remote.refresh_from_db()
        self.assertEqual(child_remote.remote_sku, "MKP100000000037254")
        self.assertEqual(child_remote.remote_id, "5056863153495")

    @patch.object(MiraklNewProductReportSyncFactory, "mirakl_get")
    def test_run_raises_when_p31_cannot_resolve_added_product(self, mirakl_get_mock):
        self.feed.new_product_report_file.save(
            "mirakl-added-products.csv",
            ContentFile(
                "\n".join(
                    [
                        '"product_category","product_id","ean"',
                        '"toys-dress_up_and_role_play","LOCAL-SKU-1","5056863153495"',
                    ]
                )
            ),
            save=True,
        )
        mirakl_get_mock.return_value = {"products": []}

        with self.assertRaises(MiraklNewProductReportLookupError) as ctx:
            MiraklNewProductReportSyncFactory(feed=self.feed).run()

        self.assertIn("P31 did not return a product", str(ctx.exception))
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.remote_sku, "")
        self.assertFalse(
            MiraklEanCode.objects.filter(
                remote_product=self.remote_product,
                ean_code="5056863153495",
            ).exists()
        )
        self.assertTrue(
            IntegrationLog.objects.filter(
                remote_product=self.remote_product,
                identifier=MiraklNewProductReportSyncFactory.LOG_IDENTIFIER,
                status=IntegrationLog.STATUS_FAILED,
                user_error=True,
            ).exists()
        )
