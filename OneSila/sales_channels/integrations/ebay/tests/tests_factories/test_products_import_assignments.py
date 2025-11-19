"""Tests for assigning offers during the eBay product import."""

from __future__ import annotations

from core.tests import TestCase
from imports_exports.models import Import
from model_bakery import baker

from sales_channels.integrations.ebay.factories.imports.products_imports import (
    EbayProductsImportProcessor,
)
from sales_channels.integrations.ebay.models import (
    EbayInternalProperty,
    EbayInternalPropertyOption,
    EbayProduct,
    EbayProductOffer,
    EbayRemoteLanguage,
    EbaySalesChannel,
    EbaySalesChannelView,
)
from properties.models import Property, PropertySelectValue
from sales_channels.models.sales_channels import SalesChannelViewAssign
from django.utils import timezone


class DummyImportInstance:
    def __init__(self, *, remote_instance, instance) -> None:
        self.remote_instance = remote_instance
        self.instance = instance
        self.data: dict[str, str] = {}


class EbayProductsImportProcessorAssignmentsTest(TestCase):
    """Verify sales channel view assignments create offer records."""

    def setUp(self) -> None:
        super().setUp()
        self.import_process = baker.make(Import, multi_tenant_company=self.multi_tenant_company)
        self.sales_channel = baker.make(
            EbaySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            refresh_token_expiration=timezone.now() + timezone.timedelta(days=1),
            hostname="assign-test.ebay.local",
            refresh_token='123',
        )
        self.processor = EbayProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        self.view = baker.make(
            EbaySalesChannelView,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="EBAY_TEST",
        )
        self.local_product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            sku="LISTING-SKU",
        )
        self.remote_product = baker.make(
            EbayProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.local_product,
        )
        self.import_instance = DummyImportInstance(
            remote_instance=self.remote_product,
            instance=self.local_product,
        )

    def test_creates_offer_records_with_listing_details(self) -> None:
        offer_payload = {
            "offer_id": "OFFER-123",
            "listing": {
                "listing_id": "LIST-789",
                "listing_status": "ACTIVE",
            },
        }

        self.processor.handle_sales_channels_views(
            import_instance=self.import_instance,
            structured_data={"__marketplace_id": self.view.remote_id},
            view=self.view,
            offer_data=offer_payload,
        )

        assign = SalesChannelViewAssign.objects.get(
            product=self.local_product,
            sales_channel_view=self.view,
        )
        self.assertEqual(assign.remote_product_id, self.remote_product.id)
        self.assertEqual(assign.remote_id, "OFFER-123")

        offer = EbayProductOffer.objects.get(
            remote_product=self.remote_product,
            sales_channel_view=self.view,
        )
        self.assertEqual(offer.remote_id, "OFFER-123")
        self.assertEqual(offer.listing_id, "LIST-789")
        self.assertEqual(offer.listing_status, "ACTIVE")
        self.assertEqual(offer.sales_channel_id, self.sales_channel.id)
        self.assertEqual(offer.multi_tenant_company_id, self.multi_tenant_company.id)


class EbayProductsImportProcessorTranslationsTest(TestCase):
    """Validate translation parsing edge cases for eBay product imports."""

    def setUp(self) -> None:
        super().setUp()
        self.import_process = baker.make(Import, multi_tenant_company=self.multi_tenant_company)
        self.sales_channel = baker.make(
            EbaySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="translations.ebay.local",
            refresh_token_expiration=timezone.now() + timezone.timedelta(days=1),
            refresh_token="dummy-refresh-token",
        )
        self.view = baker.make(
            EbaySalesChannelView,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="EBAY_TRANSLATIONS",
        )
        baker.make(
            EbayRemoteLanguage,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            multi_tenant_company=self.multi_tenant_company,
            remote_code="en-us",
            local_instance="en",
        )
        self.processor = EbayProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

    def test_parse_translations_uses_child_locale_when_missing_on_parent(self) -> None:
        parent_payload = {
            "product": {
                "title": "Parent Listing",
                "description": "Parent-specific description",
            }
        }
        child_payload = {"locale": "en_US"}

        translations, language = self.processor._parse_translations(
            product_data=parent_payload,
            child_product_data=child_payload,
        )

        self.assertEqual(language, "en")
        self.assertEqual(translations[0]["name"], "Parent Listing")
        self.assertEqual(translations[0]["description"], "Parent-specific description")

    def test_parse_translations_prefers_offer_listing_description_for_simple_items(self) -> None:
        product_payload = {
            "locale": "en_US",
            "product": {
                "title": "Simple SKU",
                "description": "Base description",
            },
        }
        offer_payload = {"listing_description": "Offer listing description"}

        translations, _ = self.processor._parse_translations(
            product_data=product_payload,
            offer_data=offer_payload,
        )

        self.assertEqual(translations[0]["description"], "Offer listing description")

    def test_parse_translations_ignores_offer_listing_description_for_configurable_parent(self) -> None:
        parent_payload = {
            "product": {
                "title": "Configurable Parent",
                "description": "Parent description",
            }
        }
        child_payload = {"locale": "en_US"}
        offer_payload = {"listing_description": "Child offer description"}

        translations, _ = self.processor._parse_translations(
            product_data=parent_payload,
            offer_data=offer_payload,
            child_product_data=child_payload,
        )

        self.assertEqual(translations[0]["description"], "Parent description")


class EbayProductsImportProcessorParentSkuTest(TestCase):
    """Ensure variation payloads expose configurable parent metadata."""

    def setUp(self) -> None:
        super().setUp()
        self.import_process = baker.make(Import, multi_tenant_company=self.multi_tenant_company)
        self.sales_channel = baker.make(
            EbaySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            refresh_token_expiration=timezone.now() + timezone.timedelta(days=1),
            refresh_token='123',
            hostname="parent-sku.ebay.local",
        )
        self.view = baker.make(
            EbaySalesChannelView,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="EBAY_PARENT",
        )
        baker.make(
            EbayRemoteLanguage,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            multi_tenant_company=self.multi_tenant_company,
            remote_code="en-us",
            local_instance="en",
        )
        self.processor = EbayProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

    def test_structured_variation_payload_includes_parent_skus(self) -> None:
        product_payload = {
            "sku": "VAR-100",
            "product": {"title": "Variation", "description": "Child description"},
            "locale": "en_US",
        }
        offer_payload = {
            "marketplace_id": self.view.remote_id,
            "listing": {"listing_status": "ACTIVE"},
        }

        structured, _, _ = self.processor.get__product_data(
            product_data=product_payload,
            offer_data=offer_payload,
            is_variation=True,
            is_configurable=False,
            product_instance=None,
            child_product_data=None,
            parent_skus={"CFG-100"},
        )

        self.assertIn("configurable_parent_skus", structured)
        self.assertEqual(set(structured["configurable_parent_skus"]), {"CFG-100"})


class EbayProductsImportProcessorAttributesTest(TestCase):
    """Ensure internal property options map to local select values."""

    def setUp(self) -> None:
        super().setUp()
        self.import_process = baker.make(Import, multi_tenant_company=self.multi_tenant_company)
        self.sales_channel = baker.make(
            EbaySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            refresh_token_expiration=timezone.now() + timezone.timedelta(days=1),
            hostname="attributes.ebay.local",
            refresh_token='123',
        )
        self.view = baker.make(
            EbaySalesChannelView,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="EBAY_ATTR",
        )
        baker.make(
            EbayRemoteLanguage,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            multi_tenant_company=self.multi_tenant_company,
            remote_code="en-us",
            local_instance="en",
        )
        self.processor = EbayProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

    def test_internal_property_option_uses_local_value_id(self) -> None:
        local_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        local_select_value = baker.make(
            PropertySelectValue,
            property=local_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        internal_property = baker.make(
            EbayInternalProperty,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            code="brand",
            type=Property.TYPES.SELECT,
            local_instance=local_property,
        )
        baker.make(
            EbayInternalPropertyOption,
            internal_property=internal_property,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            value="Premium",
            label="Premium",
            local_instance=local_select_value,
        )

        attributes, _ = self.processor._parse_attributes(
            product_data={"product": {"brand": "Premium"}},
        )

        matched = next(attr for attr in attributes if attr["property"] == local_property)
        self.assertEqual(matched["value"], local_select_value.id)
        self.assertTrue(matched.get("value_is_id"))
