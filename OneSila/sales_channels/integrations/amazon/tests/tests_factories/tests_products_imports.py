from unittest.mock import patch

from core.tests import TestCase
from imports_exports.models import Import
from imports_exports.factories.products import ImportProductInstance
from model_bakery import baker
from properties.models import (
    ProductProperty,
    ProductPropertiesRule,
    Property,
    PropertySelectValue,
    PropertySelectValueTranslation,
)
from sales_channels.integrations.amazon.factories.imports.products_imports import (
    AmazonProductsImportProcessor,
    AmazonProductItemFactory,
)
from imports_exports.factories.mixins import UpdateOnlyInstanceNotFound
from sales_channels.integrations.amazon.models import (
    AmazonProduct,
    AmazonProductType,
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonImportData,
    AmazonGtinExemption,
    AmazonProductBrowseNode,
)


class AmazonProductsImportProcessorNameTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER"
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="GB",
        )
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_name_from_attributes(self):
        product_data = {
            "sku": "SKU123",
            "attributes": {"item_name": [{"value": "Attr name"}]},
            "summaries": [{
                "item_name": "Summary name",
                "asin": "ASIN",
                "marketplace_id": "GB",
                "status": ["BUYABLE"],
                "product_type": "TYPE",
            }],
        }
        with patch.object(AmazonProductsImportProcessor, "get_api", return_value=None), \
                patch.object(AmazonProductsImportProcessor, "_parse_images", return_value=[]), \
                patch.object(AmazonProductsImportProcessor, "_parse_prices", return_value=([], [])), \
                patch.object(AmazonProductsImportProcessor, "_parse_attributes", return_value=([], {})), \
                patch.object(AmazonProductsImportProcessor, "_fetch_catalog_attributes", return_value=None):
            processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
            structured, _, _ = processor.get__product_data(product_data, False)
        self.assertEqual(structured["name"], "Attr name")

    def test_name_fallback_to_summary(self):
        product_data = {
            "sku": "SKU123",
            "attributes": {},
            "summaries": [{
                "item_name": "Summary name",
                "asin": "ASIN",
                "marketplace_id": "GB",
                "status": ["BUYABLE"],
                "product_type": "TYPE",
            }],
        }
        with patch.object(AmazonProductsImportProcessor, "get_api", return_value=None), \
                patch.object(AmazonProductsImportProcessor, "_parse_images", return_value=[]), \
                patch.object(AmazonProductsImportProcessor, "_parse_prices", return_value=([], [])), \
                patch.object(AmazonProductsImportProcessor, "_parse_attributes", return_value=([], {})), \
                patch.object(AmazonProductsImportProcessor, "_fetch_catalog_attributes", return_value=None):
            processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
            structured, _, _ = processor.get__product_data(product_data, False)
        self.assertEqual(structured["name"], "Summary name")


class AmazonProductsImportProcessorPriceTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="GB",
        )
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_missing_currency_raises_error(self):
        product_data = {
            "offers": [
                {"offer_type": "B2C", "price": {"amount": "10", "currency_code": "USD"}}
            ]
        }
        processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
        with self.assertRaises(ValueError):
            processor._parse_prices(product_data)

    def test_currency_object_in_salespricelist_data(self):
        product_data = {
            "offers": [
                {"offer_type": "B2C", "price": {"amount": "10", "currency_code": "GBP"}}
            ]
        }
        processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
        _, items = processor._parse_prices(product_data)
        self.assertEqual(
            items[0]["salespricelist_data"]["currency_object"], self.currency
        )


class AmazonProductsImportProcessorImagesTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_fallback_to_summary_main_image(self):
        product_data = {
            "attributes": {},
            "summaries": [
                {"main_image": {"link": "https://example.com/image.jpg"}}
            ],
        }
        with patch.object(AmazonProductsImportProcessor, "get_api", return_value=None):
            processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
            images = processor._parse_images(product_data)
        self.assertEqual(
            images,
            [
                {
                    "image_url": "https://example.com/image.jpg",
                    "sort_order": 0,
                    "is_main_image": True,
                }
            ],
        )

    def test_no_fallback_when_attributes_present(self):
        product_data = {
            "attributes": {
                "main_product_image_locator": [
                    {"media_location": "https://example.com/attr.jpg"}
                ]
            },
            "summaries": [
                {"main_image": {"link": "https://example.com/summary.jpg"}}
            ],
        }
        with patch.object(AmazonProductsImportProcessor, "get_api", return_value=None):
            processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
            images = processor._parse_images(product_data)
        self.assertEqual(
            images,
            [
                {
                    "image_url": "https://example.com/attr.jpg",
                    "sort_order": 0,
                    "is_main_image": True,
                }
            ],
        )

    def test_image_order_with_gaps(self):
        product_data = {
            "attributes": {
                "main_product_image_locator": [
                    {"media_location": "https://example.com/main.jpg"}
                ],
                "other_product_image_locator_1": [
                    {"media_location": "https://example.com/1.jpg"}
                ],
                "other_product_image_locator_3": [
                    {"media_location": "https://example.com/3.jpg"}
                ],
            }
        }
        with patch.object(AmazonProductsImportProcessor, "get_api", return_value=None):
            processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
            images = processor._parse_images(product_data)
        self.assertEqual(
            images,
            [
                {
                    "image_url": "https://example.com/main.jpg",
                    "sort_order": 0,
                    "is_main_image": True,
                },
                {
                    "image_url": "https://example.com/1.jpg",
                    "sort_order": 1,
                    "is_main_image": False,
                },
                {
                    "image_url": "https://example.com/3.jpg",
                    "sort_order": 2,
                    "is_main_image": False,
                },
            ],
        )


class AmazonProductsImportProcessorRulePreserveTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="GB",
        )
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

        # create product type and rule
        self.product_type_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
            type=Property.TYPES.SELECT,
        )
        self.product_type_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
            value="Default",
        )
        self.rule, _ = ProductPropertiesRule.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_value,
        )

        self.product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.product_type_property,
            value_select=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type_code="DEFAULT_CODE",
            local_instance=self.rule,
        )
        self.remote_product = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_sku="SKU123",
            local_instance=self.product,
            is_variation=False,
        )

    def test_rule_kept_when_product_type_mismatch(self):
        product_data = {
            "sku": "SKU123",
            "attributes": {"item_name": [{"value": "Name"}]},
            "summaries": [
                {
                    "item_name": "Name",
                    "asin": "ASIN1",
                    "marketplace_id": "GB",
                    "status": ["BUYABLE"],
                    "product_type": "OTHER_CODE",
                }
            ],
        }

        structured = {"name": "Name", "sku": "SKU123", "__asin": "ASIN1", "type": "SIMPLE"}

        with patch.object(AmazonProductsImportProcessor, "get__product_data", return_value=(structured, None, self.view)), \
                patch("sales_channels.integrations.amazon.factories.imports.products_imports.ImportProductInstance") as MockImportProductInstance, \
                patch.object(AmazonProductsImportProcessor, "update_remote_product"), \
                patch.object(AmazonProductsImportProcessor, "handle_ean_code"), \
                patch.object(AmazonProductsImportProcessor, "handle_attributes"), \
                patch.object(AmazonProductsImportProcessor, "handle_translations"), \
                patch.object(AmazonProductsImportProcessor, "handle_prices"), \
                patch.object(AmazonProductsImportProcessor, "handle_images"), \
                patch.object(AmazonProductsImportProcessor, "handle_variations"), \
                patch.object(AmazonProductsImportProcessor, "handle_sales_channels_views"), \
                patch.object(AmazonProductsImportProcessor, "_add_broken_record") as mock_broken, \
                patch("sales_channels.integrations.amazon.factories.imports.products_imports.FetchRemoteIssuesFactory") as MockIssuesFactory:

            from types import SimpleNamespace

            mock_instance = SimpleNamespace(
                process=lambda: None,
                prepare_mirror_model_class=lambda *args, **kwargs: None,
                remote_instance=self.remote_product,
                data={},
                instance=self.remote_product.local_instance,
            )
            MockImportProductInstance.return_value = mock_instance
            MockIssuesFactory.return_value.run.return_value = None

            processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
            processor.process_product_item(product_data)

            called_rule = MockImportProductInstance.call_args.kwargs["rule"]
            self.assertEqual(called_rule, self.rule)
            self.assertTrue(mock_broken.called)


class AmazonProductsImportProcessorImportDataTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="GB",
        )
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
        )

    def test_import_data_saved(self):
        product_data = {
            "sku": "SKU123",
            "attributes": {"item_name": [{"value": "Name"}]},
            "summaries": [
                {
                    "item_name": "Name",
                    "asin": "ASIN1",
                    "marketplace_id": "GB",
                    "status": ["BUYABLE"],
                    "product_type": "TYPE",
                }
            ],
        }

        structured = {"name": "Name", "sku": "SKU123", "__asin": "ASIN1", "type": "SIMPLE"}

        with patch.object(AmazonProductsImportProcessor, "get__product_data", return_value=(structured, None, self.view)), \
                patch("sales_channels.integrations.amazon.factories.imports.products_imports.ImportProductInstance") as MockImportProductInstance, \
                patch.object(AmazonProductsImportProcessor, "update_remote_product"), \
                patch.object(AmazonProductsImportProcessor, "handle_ean_code"), \
                patch.object(AmazonProductsImportProcessor, "handle_attributes"), \
                patch.object(AmazonProductsImportProcessor, "handle_translations"), \
                patch.object(AmazonProductsImportProcessor, "handle_prices"), \
                patch.object(AmazonProductsImportProcessor, "handle_images"), \
                patch.object(AmazonProductsImportProcessor, "handle_variations"), \
                patch.object(AmazonProductsImportProcessor, "handle_sales_channels_views"), \
                patch("sales_channels.integrations.amazon.factories.imports.products_imports.FetchRemoteIssuesFactory") as MockIssuesFactory:

            from types import SimpleNamespace

            mock_instance = SimpleNamespace(
                process=lambda: None,
                prepare_mirror_model_class=lambda *args, **kwargs: None,
                instance=self.product,
                remote_instance=None,
                data={},
            )
            MockImportProductInstance.return_value = mock_instance
            MockIssuesFactory.return_value.run.return_value = None

            processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
            processor.process_product_item(product_data)

        saved = AmazonImportData.objects.get()
        self.assertEqual(saved.sales_channel, self.sales_channel)
        self.assertEqual(saved.product, self.product)
        self.assertEqual(saved.view, self.view)
        self.assertEqual(saved.data["sku"], "SKU123")


class AmazonProductsImportProcessorBrowseNodeGtinTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="GB",
        )
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_extracts_browse_node_and_gtin_exemption(self):
        product_data = {
            "sku": "SKU123",
            "attributes": {
                "item_name": [{"value": "Name"}],
                "recommended_browse_nodes": [{"value": "BN1"}],
                "supplier_declared_has_product_identifier_exemption": [{"value": True}],
            },
            "summaries": [
                {
                    "item_name": "Name",
                    "asin": "ASIN1",
                    "marketplace_id": "GB",
                    "status": ["BUYABLE"],
                    "product_type": "TYPE",
                }
            ],
        }
        with patch.object(AmazonProductsImportProcessor, "get_api", return_value=None), \
                patch.object(AmazonProductsImportProcessor, "_parse_images", return_value=[]), \
                patch.object(AmazonProductsImportProcessor, "_parse_prices", return_value=([], [])), \
                patch.object(AmazonProductsImportProcessor, "_parse_attributes", return_value=([], {})), \
                patch.object(AmazonProductsImportProcessor, "_fetch_catalog_attributes", return_value=None):
            processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
            structured, _, _ = processor.get__product_data(product_data, False)

        self.assertTrue(structured["__gtin_exemption"])
        self.assertEqual(structured["__recommended_browse_node_id"], "BN1")

    def test_handlers_persist_models(self):
        product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
        )
        data = {
            "name": "Name",
            "sku": "SKU123",
            "type": "SIMPLE",
            "__gtin_exemption": True,
            "__recommended_browse_node_id": "BN1",
        }
        import_instance = ImportProductInstance(
            data,
            import_process=self.import_process,
            instance=product,
            sales_channel=self.sales_channel,
        )
        processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)

        processor.handle_gtin_exemption(import_instance, self.view)
        processor.handle_product_browse_node(import_instance, self.view)

        self.assertTrue(
            AmazonGtinExemption.objects.filter(
                product=product, view=self.view, value=True
            ).exists()
        )
        self.assertTrue(
            AmazonProductBrowseNode.objects.filter(
                product=product,
                sales_channel=self.sales_channel,
                view=self.view,
                recommended_browse_node_id="BN1",
            ).exists()
        )


class AmazonProductsImportProcessorUpdateOnlyTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="GB",
        )
        self.import_process = Import.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_non_configurable_product_update_only(self):
        product_data = {
            "sku": "SKU123",
            "attributes": {"name": [{"value": "Name"}]},
            "summaries": [{"product_type": "TYPE"}],
        }
        structured = {
            "name": "Name",
            "sku": "SKU123",
            "__asin": "ASIN1",
            "type": "SIMPLE",
        }

        with patch.object(
            AmazonProductsImportProcessor,
            "get__product_data",
            return_value=(structured, None, self.view),
        ), patch.object(
            AmazonProductsImportProcessor,
            "update_remote_product",
        ), patch.object(
            AmazonProductsImportProcessor,
            "handle_ean_code",
        ), patch.object(
            AmazonProductsImportProcessor,
            "handle_attributes",
        ), patch.object(
            AmazonProductsImportProcessor,
            "handle_translations",
        ), patch.object(
            AmazonProductsImportProcessor,
            "handle_prices",
        ), patch.object(
            AmazonProductsImportProcessor,
            "handle_images",
        ), patch.object(
            AmazonProductsImportProcessor,
            "handle_sales_channels_views",
        ), patch.object(
            AmazonProductsImportProcessor,
            "handle_gtin_exemption",
        ), patch.object(
            AmazonProductsImportProcessor,
            "handle_product_browse_node",
        ), patch(
            "sales_channels.integrations.amazon.factories.imports.products_imports.FetchRemoteIssuesFactory"
        ) as MockIssuesFactory, patch(
            "sales_channels.integrations.amazon.factories.imports.products_imports.ImportProductInstance"
        ) as MockImportProductInstance, patch(
            "sales_channels.integrations.amazon.factories.imports.products_imports.get_is_product_variation",
            return_value=(False, None),
        ):
            from types import SimpleNamespace

            mock_instance = SimpleNamespace(
                process=lambda: None,
                prepare_mirror_model_class=lambda *args, **kwargs: None,
                update_only=False,
                remote_instance=None,
                instance=None,
            )
            MockImportProductInstance.return_value = mock_instance
            MockIssuesFactory.return_value.run.return_value = None

            processor = AmazonProductsImportProcessor(
                self.import_process, self.sales_channel
            )
            processor.process_product_item(product_data)

            self.assertTrue(MockImportProductInstance.return_value.update_only)


class AmazonProductItemFactoryRunTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.product_data = {"sku": "SKU123"}

    def test_broken_record_when_update_only_product_missing(self):
        factory = AmazonProductItemFactory(
            self.product_data,
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

        with patch("imports_exports.helpers.append_broken_record"), patch.object(
            AmazonProductItemFactory,
            "process_product_item",
            side_effect=UpdateOnlyInstanceNotFound("missing"),
        ):
            factory.run()

        self.assertEqual(len(factory.broken_records), 1)
        self.assertEqual(
            factory.broken_records[0]["code"],
            factory.ERROR_UPDATE_ONLY_NOT_FOUND,
        )
