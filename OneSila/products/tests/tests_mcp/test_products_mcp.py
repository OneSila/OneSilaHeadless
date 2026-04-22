import json
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from asgiref.sync import async_to_sync
from jsonschema import validate as jsonschema_validate

from core.tests import TransactionTestCase
from eancodes.models import EanCode
from llm.models import BrandCustomPrompt
from llm.mcp.runtime import AccessToken
from products.mcp.output_types import UPSERT_PRODUCTS_OUTPUT_SCHEMA
from products.mcp.resources import build_product_inspector_error_codes_payload
from media.models import Media, MediaProductThrough
from products.mcp.tools.create_product import CreateProductsMcpTool
from products.mcp.tools.get_company_details import GetCompanyDetailsMcpTool
from products.mcp.tools.get_product import GetProductMcpTool
from products.mcp.tools.search_sales_channels import SearchSalesChannelsMcpTool
from products.mcp.tools.search_products import SearchProductsMcpTool
from products.mcp.tools.upsert_product import UpsertProductsMcpTool
from products.models import Product, ProductTranslation, ProductTranslationBulletPoint
from products_inspector.constants import (
    HAS_IMAGES_ERROR,
)
from products_inspector.models import Inspector, InspectorBlock
from properties.models import (
    Property,
    ProductPropertiesRule,
    ProductPropertiesRuleItem,
    ProductProperty,
    PropertySelectValue,
    PropertySelectValueTranslation,
    PropertyTranslation,
)
from sales_channels.models import SalesChannel, SalesChannelView, SalesChannelViewAssign
from sales_prices.models import SalesPrice
from taxes.models import VatRate
from currencies.models import Currency, PublicCurrency


class DummyMcp:
    def tool(self, **kwargs):
        def decorator(func):
            return func

        return decorator


class DummyContext:
    def __init__(self):
        self.info = AsyncMock()
        self.warning = AsyncMock()
        self.error = AsyncMock()


class ProductMcpToolAsyncTestCase(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.get_authenticated_company_patcher = patch(
            "llm.mcp.mcp_tool.get_authenticated_company",
            return_value=self.multi_tenant_company,
        )
        self.get_authenticated_company_patcher.start()
        self.addCleanup(self.get_authenticated_company_patcher.stop)
        self.get_authenticated_user_patcher = patch(
            "llm.mcp.mcp_tool.get_authenticated_user_from_auth",
            return_value=self.user,
        )
        self.get_authenticated_user_patcher.start()
        self.addCleanup(self.get_authenticated_user_patcher.stop)
        self.sales_channel_connect_patcher = patch.object(SalesChannel, "connect", return_value=None)
        self.sales_channel_connect_patcher.start()
        self.addCleanup(self.sales_channel_connect_patcher.stop)
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.languages = ["en", "fr"]
        self.multi_tenant_company.save(update_fields=["language", "languages"])

        self.vat_rate = VatRate.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Standard",
            rate=21,
        )
        PublicCurrency.objects.get_or_create(
            iso_code="GBP",
            defaults={"name": "Pound Sterling", "symbol": "£"},
        )
        self.secondary_currency = Currency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            iso_code="EUR",
            name="Euro",
            symbol="€",
            inherits_from=self.currency,
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="BOOK-001",
            type=Product.SIMPLE,
            active=True,
            allow_backorder=False,
            vat_rate=self.vat_rate,
        )
        ProductTranslation.objects.create(
            product=self.product,
            language="en",
            name="Book Page",
            subtitle="Main subtitle",
            short_description="Short copy",
            description="Longer default description",
            multi_tenant_company=self.multi_tenant_company,
        )
        french_translation = ProductTranslation.objects.create(
            product=self.product,
            language="fr",
            name="Page du livre",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.sales_channel = SalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://amazon-nice-prints.example.com",
            active=True,
        )
        ProductTranslation.objects.create(
            product=self.product,
            language="en",
            name="Book Page Amazon",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=french_translation,
            text="Point de vente",
            sort_order=1,
            multi_tenant_company=self.multi_tenant_company,
        )
        inspector, _ = Inspector.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
        )
        inspector.has_missing_information = True
        inspector.has_missing_optional_information = False
        inspector.save(update_fields=["has_missing_information", "has_missing_optional_information"])

        image_block, _ = InspectorBlock.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            inspector=inspector,
            error_code=HAS_IMAGES_ERROR,
            defaults={
                "successfully_checked": False,
                "fixing_message": "Upload a main product image.",
            },
        )
        image_block.successfully_checked = False
        image_block.fixing_message = "Upload a main product image."
        image_block.save(update_fields=["successfully_checked", "fixing_message"])

        self.property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
            internal_name="book_format",
        )
        PropertyTranslation.objects.create(
            property=self.property,
            language="en",
            name="Book Format",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.select_value = PropertySelectValue.objects.create(
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.select_value,
            language="en",
            value="Hardcover",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.other_select_value = PropertySelectValue.objects.create(
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.other_select_value,
            language="en",
            value="Paperback",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.property,
            value_select=self.select_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.product_type_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
            defaults={
                "type": Property.TYPES.SELECT,
                "internal_name": "product_type",
            },
        )
        PropertyTranslation.objects.get_or_create(
            property=self.product_type_property,
            multi_tenant_company=self.multi_tenant_company,
            language="en",
            defaults={
                "name": "Product Type",
                "multi_tenant_company": self.multi_tenant_company,
            },
        )
        self.product_type_select_value = PropertySelectValue.objects.create(
            property=self.product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.product_type_select_value,
            language="en",
            value="Book",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.product_type_select_value,
            language="fr",
            value="Livre",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.product_type_property,
            value_select=self.product_type_select_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product_rule, _ = ProductPropertiesRule.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_select_value,
            sales_channel=None,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.product_rule,
            property=self.property,
            type=ProductPropertiesRuleItem.REQUIRED,
        )
        self.optional_property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
            internal_name="subtitle_hint",
        )
        PropertyTranslation.objects.create(
            property=self.optional_property,
            language="en",
            name="Subtitle Hint",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.brand_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="brand",
            defaults={
                "type": Property.TYPES.SELECT,
                "is_public_information": True,
                "non_deletable": True,
            },
        )
        PropertyTranslation.objects.get_or_create(
            property=self.brand_property,
            language="en",
            multi_tenant_company=self.multi_tenant_company,
            defaults={
                "name": "Brand",
                "multi_tenant_company": self.multi_tenant_company,
            },
        )
        self.brand_value = PropertySelectValue.objects.create(
            property=self.brand_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.brand_value,
            language="en",
            value="Acme",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.brand_value,
            language="fr",
            value="Acme",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.brand_property,
            value_select=self.brand_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        BrandCustomPrompt.objects.create(
            brand_value=self.brand_value,
            language=None,
            prompt="Use a crisp premium tone.",
            multi_tenant_company=self.multi_tenant_company,
        )
        BrandCustomPrompt.objects.create(
            brand_value=self.brand_value,
            language="fr",
            prompt="Utilisez un ton premium concis.",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.product_rule,
            property=self.optional_property,
            type=ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR,
        )

        self.image = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.IMAGE,
            title="Front image",
        )
        MediaProductThrough.objects.create(
            product=self.product,
            media=self.image,
            is_main_image=True,
            sort_order=1,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )

        SalesPrice.objects.create(
            product=self.product,
            currency=self.currency,
            rrp=Decimal("15.00"),
            price=Decimal("12.50"),
            multi_tenant_company=self.multi_tenant_company,
        )

        # Keep the async MCP fixtures deterministic. Several setup actions above
        # trigger inspector refresh signals that would otherwise clear the
        # "missing images" state these tests expect to serialize and filter by.
        inspector = self.product.inspector
        inspector.has_missing_information = True
        inspector.has_missing_optional_information = False
        inspector.save(update_fields=["has_missing_information", "has_missing_optional_information"])
        image_block = inspector.blocks.get(error_code=HAS_IMAGES_ERROR)
        image_block.successfully_checked = False
        image_block.fixing_message = "Upload a main product image."
        image_block.save(update_fields=["successfully_checked", "fixing_message"])

    def _build_access_token(self, *, company_id: int) -> AccessToken:
        self.assertEqual(company_id, self.multi_tenant_company.id)
        return AccessToken(
            token="test-token",
            client_id=f"user:{self.user.id}",
            scopes=[],
        )

    def _get_payload(self, *, result):
        if result.structured_content is not None:
            return result.structured_content
        self.assertEqual(len(result.content), 1)
        return json.loads(result.content[0].text)

    @patch("llm.mcp.auth.get_access_token")
    def test_search_products_executes_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = SearchProductsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            search="Book",
            property_id=self.property.id,
            select_value_id=self.select_value.id,
            has_images=True,
            has_missing_required_information=True,
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(len(payload["results"]), 1)
        summary = payload["results"][0]
        self.assertEqual(summary["id"], self.product.id)
        self.assertEqual(summary["sku"], "BOOK-001")
        self.assertTrue(summary["has_images"])
        self.assertTrue(summary["has_missing_required_information"])
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_search_products_supports_assignment_and_inspector_error_filters(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        view = SalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="Main website",
            url="https://amazon-nice-prints.example.com/en",
        )
        other_view = SalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="Outlet",
            url="https://amazon-nice-prints.example.com/outlet",
        )
        SalesChannelViewAssign.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            sales_channel_view=view,
            multi_tenant_company=self.multi_tenant_company,
        )
        other_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="BOOK-002",
            type=Product.SIMPLE,
            active=True,
            vat_rate=self.vat_rate,
        )
        ProductTranslation.objects.create(
            product=other_product,
            language="en",
            name="Book Poster",
            multi_tenant_company=self.multi_tenant_company,
        )
        other_inspector, _ = Inspector.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product=other_product,
        )
        InspectorBlock.objects.update_or_create(
            multi_tenant_company=self.multi_tenant_company,
            inspector=other_inspector,
            error_code=HAS_IMAGES_ERROR,
            defaults={
                "successfully_checked": False,
            },
        )
        SalesChannelViewAssign.objects.create(
            product=other_product,
            sales_channel=self.sales_channel,
            sales_channel_view=other_view,
            multi_tenant_company=self.multi_tenant_company,
        )

        ctx = DummyContext()
        tool = SearchProductsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            assigned_to_sales_channel_view_id=view.id,
            inspector_not_successfully_code_error=HAS_IMAGES_ERROR,
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual([item["id"] for item in payload["results"]], [self.product.id])
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_search_products_supports_exclude_property_select_value_and_assignment_filters(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        main_view = SalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="Main website",
            url="https://amazon-nice-prints.example.com/en",
        )
        other_view = SalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="Outlet",
            url="https://amazon-nice-prints.example.com/outlet",
        )
        SalesChannelViewAssign.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            sales_channel_view=main_view,
            multi_tenant_company=self.multi_tenant_company,
        )
        matching_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="BOOK-003",
            type=Product.SIMPLE,
            active=True,
            vat_rate=self.vat_rate,
        )
        ProductTranslation.objects.create(
            product=matching_product,
            language="en",
            name="Notebook",
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesChannelViewAssign.objects.create(
            product=matching_product,
            sales_channel=self.sales_channel,
            sales_channel_view=other_view,
            multi_tenant_company=self.multi_tenant_company,
        )

        ctx = DummyContext()
        tool = SearchProductsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            exclude_property_id=self.property.id,
            exclude_select_value_id=self.select_value.id,
            not_assigned_to_sales_channel_view_id=main_view.id,
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual([item["id"] for item in payload["results"]], [matching_product.id])
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_get_company_details_returns_guidance_without_requested_sections(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = GetCompanyDetailsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(ctx=ctx)

        payload = self._get_payload(result=result)
        self.assertIn("message", payload)
        self.assertNotIn("languages", payload)
        self.assertNotIn("product_types", payload)
        self.assertNotIn("vat_rates", payload)
        self.assertNotIn("currencies", payload)
        self.assertNotIn("brand_voices", payload)
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_get_company_details_returns_only_requested_sections(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = GetCompanyDetailsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            show_languages=True,
            show_product_types_translations=True,
            show_product_types_usage_counts=True,
            show_vat_rates=True,
            show_currencies=True,
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertNotIn("message", payload)
        self.assertEqual(payload["languages"]["default_language_code"], "en")
        self.assertEqual(
            {item["code"] for item in payload["languages"]["enabled_languages"]},
            {"en", "fr"},
        )
        self.assertEqual(payload["product_types"]["property"]["id"], self.product_type_property.id)
        self.assertEqual(payload["product_types"]["count"], 1)
        self.assertEqual(payload["product_types"]["results"][0]["id"], self.product_type_select_value.id)
        self.assertEqual(payload["product_types"]["results"][0]["value"], "Book")
        self.assertEqual(payload["product_types"]["results"][0]["usage_count"], 1)
        self.assertEqual(
            {item["value"] for item in payload["product_types"]["results"][0]["translations"]},
            {"Book", "Livre"},
        )
        self.assertEqual(payload["vat_rates"]["count"], 1)
        self.assertEqual(payload["vat_rates"]["results"][0]["id"], self.vat_rate.id)
        self.assertEqual(payload["currencies"]["count"], 2)
        self.assertEqual(payload["currencies"]["default_currency_code"], self.currency.iso_code)
        currencies_by_iso = {
            item["iso_code"]: item
            for item in payload["currencies"]["results"]
        }
        self.assertTrue(currencies_by_iso[self.currency.iso_code]["is_default"])
        self.assertEqual(
            currencies_by_iso[self.secondary_currency.iso_code]["inherits_from_iso_code"],
            self.currency.iso_code,
        )
        self.assertNotIn("brand_voices", payload)
        ctx.error.assert_not_awaited()

    def test_product_inspector_error_codes_resource_payload_marks_supported_and_deprecated_codes(self):
        payload = build_product_inspector_error_codes_payload()

        self.assertIn("codes", payload)
        by_code = {item["code"]: item for item in payload["codes"]}
        self.assertEqual(by_code[HAS_IMAGES_ERROR]["key"], "HAS_IMAGES_ERROR")
        self.assertIn("label", by_code[HAS_IMAGES_ERROR])

    @patch("llm.mcp.auth.get_access_token")
    def test_get_product_returns_sparse_base_by_default(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = GetProductMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            sku="BOOK-001",
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(payload["sku"], "BOOK-001")
        self.assertIsNone(payload["ean_code"])
        self.assertEqual(payload["vat_rate"], 21)
        self.assertIn("/products/product/", payload["onesila_url"])
        self.assertNotIn("inspector", payload)
        self.assertNotIn("property_requirements", payload)
        self.assertNotIn("translations", payload)
        self.assertNotIn("images", payload)
        self.assertNotIn("properties", payload)
        self.assertNotIn("prices", payload)
        self.assertNotIn("vat_rate_data", payload)
        self.assertNotIn("website_views_assign", payload)
        self.assertNotIn("brand_voice", payload)
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_get_product_returns_requested_sections(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = GetProductMcpTool(mcp=DummyMcp())
        website_view = SalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="Main website",
            url="https://amazon-nice-prints.example.com",
        )
        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code="1234567890123",
        )
        website_view_assign = SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=website_view,
            link="https://amazon-nice-prints.example.com/products/book-page",
        )
        image_block = self.product.inspector.blocks.get(error_code=HAS_IMAGES_ERROR)
        image_block.successfully_checked = False
        image_block.fixing_message = "Upload a main product image."
        image_block.save(update_fields=["successfully_checked", "fixing_message"])

        result = async_to_sync(tool.execute)(
            sku="BOOK-001",
            show_inspector=True,
            show_website_views_assign=True,
            show_property_requirements=True,
            show_translations=True,
            show_vat_rate_data=True,
            show_images=True,
            show_properties=True,
            show_prices=True,
            show_brand_voice=True,
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(payload["inspector"]["status_label"], "red")
        self.assertEqual(payload["ean_code"], "1234567890123")
        self.assertEqual(len(payload["inspector"]["issues"]), 1)
        self.assertEqual(payload["inspector"]["issues"][0]["code"], 101)
        self.assertEqual(
            payload["inspector"]["issues"][0]["title"],
            "Products Missing Images",
        )
        self.assertEqual(
            payload["inspector"]["issues"][0]["fixing_message"],
            "Upload a main product image.",
        )
        self.assertEqual(len(payload["translations"]), 3)
        translation_names = {item["name"] for item in payload["translations"]}
        self.assertSetEqual(translation_names, {"Book Page", "Page du livre", "Book Page Amazon"})
        french_translation = next(
            item for item in payload["translations"]
            if item["language"] == "fr"
        )
        self.assertEqual(french_translation["bullet_points"], ["Point de vente"])
        amazon_translation = next(
            item for item in payload["translations"]
            if item["name"] == "Book Page Amazon"
        )
        self.assertEqual(
            amazon_translation["sales_channel"],
            {
                "id": self.sales_channel.id,
                "hostname": self.sales_channel.hostname,
                "active": True,
                "type": "magento",
                "subtype": None,
            },
        )
        self.assertEqual(
            payload["website_views_assign"],
            [
                {
                    "id": website_view_assign.id,
                    "view_name": "Main website",
                    "remote_url": "https://amazon-nice-prints.example.com/products/book-page",
                }
            ],
        )
        properties_by_internal_name = {
            item["property"]["internal_name"]: item
            for item in payload["properties"]
        }
        self.assertEqual(
            properties_by_internal_name["book_format"]["values"][0]["id"],
            self.select_value.id,
        )
        self.assertEqual(
            payload["property_requirements"]["product_type"],
            {
                "id": self.product_type_select_value.id,
                "select_value": "Book",
            },
        )
        requirements_by_property_id = {
            item["property_id"]: item
            for item in payload["property_requirements"]["requirements"].values()
        }
        self.assertEqual(
            requirements_by_property_id[self.property.id]["requirement_type"],
            ProductPropertiesRuleItem.REQUIRED,
        )
        self.assertTrue(
            requirements_by_property_id[self.property.id]["effectively_required"]
        )
        self.assertTrue(
            requirements_by_property_id[self.property.id]["has_value"]
        )
        self.assertEqual(
            requirements_by_property_id[self.property.id]["current_value_summary"],
            "Hardcover",
        )
        self.assertEqual(
            requirements_by_property_id[self.optional_property.id]["requirement_type"],
            ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR,
        )
        self.assertTrue(
            requirements_by_property_id[self.optional_property.id]["effectively_required"]
        )
        self.assertFalse(
            requirements_by_property_id[self.optional_property.id]["has_value"]
        )
        self.assertEqual(payload["vat_rate_data"]["id"], self.vat_rate.id)
        self.assertEqual(payload["prices"][0]["currency"], self.currency.iso_code)
        self.assertEqual(len(payload["images"]), 1)
        self.assertEqual(
            payload["images"][0]["sales_channel"],
            {
                "id": self.sales_channel.id,
                "hostname": self.sales_channel.hostname,
                "active": True,
                "type": "magento",
                "subtype": None,
            },
        )
        self.assertEqual(payload["brand_voice"]["brand_value_id"], self.brand_value.id)
        self.assertEqual(payload["brand_voice"]["brand_value"], "Acme")
        self.assertEqual(payload["brand_voice"]["default_prompt"], "Use a crisp premium tone.")
        self.assertEqual(
            payload["brand_voice"]["language_prompts"],
            [
                {
                    "language": "fr",
                    "prompt": "Utilisez un ton premium concis.",
                }
            ],
        )
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_search_sales_channels_filters_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        view = SalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="Main website",
            url="https://amazon-nice-prints.example.com/en",
        )
        ctx = DummyContext()
        tool = SearchSalesChannelsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            search="amazon",
            active=True,
            type="magento",
            limit=10,
            offset=0,
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(payload["total_count"], 1)
        self.assertFalse(payload["has_more"])
        self.assertEqual(payload["results"][0]["hostname"], self.sales_channel.hostname)
        self.assertEqual(payload["results"][0]["type"], "magento")
        self.assertTrue(payload["results"][0]["active"])
        self.assertEqual(
            payload["results"][0]["views"],
            [
                {
                    "id": view.id,
                    "name": "Main website",
                    "is_default": None,
                }
            ],
        )
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_search_sales_channels_lists_all_without_filters(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        view = SalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="Main website",
            url="https://amazon-nice-prints.example.com/en",
        )
        ctx = DummyContext()
        tool = SearchSalesChannelsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            limit=10,
            offset=0,
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(payload["total_count"], 1)
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["id"], self.sales_channel.id)
        self.assertEqual(
            payload["results"][0]["views"],
            [
                {
                    "id": view.id,
                    "name": "Main website",
                    "is_default": None,
                }
            ],
        )
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_executes_core_updates_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = UpsertProductsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            products={
                "sku": "BOOK-001",
                "active": False,
                "ean_code": "999888777",
                "translations": (
                    '[{"language": "fr", "short_description": "Résumé court mis à jour", '
                    '"bullet_points": ["Premier point", "Deuxième point"]}]'
                ),
                "prices": (
                    f'[{{"currency": "{self.currency.iso_code}", "price": "13.50", "rrp": "16.00"}}]'
                ),
                "properties": (
                    f'[{{"property_id": {self.property.id}, "value": {self.other_select_value.id}, '
                    f'"value_is_id": true}}]'
                ),
            },
            ctx=ctx,
        )

        self.product.refresh_from_db()
        translation = ProductTranslation.objects.get(
            product=self.product,
            language="fr",
            sales_channel=None,
        )
        bullet_points = list(
            translation.bullet_points.order_by("sort_order", "id").values_list("text", flat=True)
        )
        sales_price = SalesPrice.objects.get(
            product=self.product,
            currency=self.currency,
        )
        ean_code = EanCode.objects.get(product=self.product)
        product_property = ProductProperty.objects.get(
            product=self.product,
            property=self.property,
        )
        payload = self._get_payload(result=result)
        self.assertFalse(self.product.active)
        self.assertEqual(payload["requested_count"], 1)
        self.assertEqual(payload["processed_count"], 1)
        self.assertEqual(payload["updated_count"], 1)
        result_item = payload["results"][0]
        self.assertFalse(result_item["active"])
        self.assertEqual(translation.name, "Page du livre")
        self.assertEqual(translation.short_description, "Résumé court mis à jour")
        self.assertEqual(bullet_points, ["Premier point", "Deuxième point"])
        self.assertEqual(sales_price.price, Decimal("13.50"))
        self.assertEqual(sales_price.rrp, Decimal("16.00"))
        self.assertEqual(ean_code.ean_code, "999888777")
        self.assertEqual(product_property.value_select_id, self.other_select_value.id)
        self.assertEqual(result_item["product_id"], self.product.id)
        self.assertEqual(result_item["sku"], "BOOK-001")
        self.assertEqual(
            result_item["applied_updates"],
            {
                "active": False,
                "ean_code": True,
                "translations": 1,
                "prices": 1,
                "properties": 1,
            },
        )
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_updates_vat_rate_by_rate(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        reduced_vat_rate = VatRate.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Reduced",
            rate=9,
        )
        ctx = DummyContext()
        tool = UpsertProductsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            products={
                "sku": "BOOK-001",
                "vat_rate": reduced_vat_rate.rate,
            },
            ctx=ctx,
        )

        self.product.refresh_from_db()
        payload = self._get_payload(result=result)
        self.assertEqual(self.product.vat_rate_id, reduced_vat_rate.id)
        self.assertEqual(
            payload["results"][0]["applied_updates"],
            {
                "vat_rate": True,
            },
        )
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_updates_vat_rate_by_id(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        reduced_vat_rate = VatRate.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Reduced",
            rate=9,
        )
        ctx = DummyContext()
        tool = UpsertProductsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            products={
                "sku": "BOOK-001",
                "vat_rate_id": reduced_vat_rate.id,
            },
            ctx=ctx,
        )

        self.product.refresh_from_db()
        payload = self._get_payload(result=result)
        self.assertEqual(self.product.vat_rate_id, reduced_vat_rate.id)
        self.assertEqual(
            payload["results"][0]["applied_updates"],
            {
                "vat_rate": True,
            },
        )
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_rejects_when_no_sections_are_provided(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = UpsertProductsMcpTool(mcp=DummyMcp())

        with self.assertRaisesMessage(
            Exception,
            "Each product update must include at least one section: vat_rate_id, vat_rate, active, ean_code, translations, prices, properties, images, or sales_channel_view_ids.",
        ):
            async_to_sync(tool.execute)(
                products={"sku": "BOOK-001"},
                ctx=ctx,
            )

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_assigns_missing_website_views_only(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        existing_view = SalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="Existing website",
            url="https://amazon-nice-prints.example.com/existing",
        )
        new_view = SalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="French website",
            url="https://amazon-nice-prints.example.com/fr",
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=existing_view,
        )
        ctx = DummyContext()
        tool = UpsertProductsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            products={
                "sku": "BOOK-001",
                "sales_channel_view_ids": json.dumps([existing_view.id, new_view.id]),
            },
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        result_item = payload["results"][0]
        self.assertEqual(
            SalesChannelViewAssign.objects.filter(
                product=self.product,
                sales_channel_view__in=[existing_view, new_view],
            ).count(),
            2,
        )
        self.assertEqual(
            result_item["applied_updates"]["website_views_assignments"],
            1,
        )
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_rejects_inherited_currency(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        inherited_currency = self.secondary_currency
        ctx = DummyContext()
        tool = UpsertProductsMcpTool(mcp=DummyMcp())

        with self.assertRaisesMessage(
            Exception,
            "Currency 'EUR' inherits its price from 'GBP' and cannot be edited directly. Update the base currency price instead.",
        ):
            async_to_sync(tool.execute)(
                products={
                    "sku": "BOOK-001",
                    "prices": f'[{{"currency": "{inherited_currency.iso_code}", "price": "10.00"}}]',
                },
                ctx=ctx,
            )

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_rejects_unconfigured_currency(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = UpsertProductsMcpTool(mcp=DummyMcp())

        with self.assertRaisesMessage(
            Exception,
            "Currency 'ZZZ' is not configured for this account.",
        ):
            async_to_sync(tool.execute)(
                products={
                    "sku": "BOOK-001",
                    "prices": '[{"currency": "ZZZ", "price": "10.00"}]',
                },
                ctx=ctx,
            )

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_parses_false_string_for_boolean_properties(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        boolean_property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.BOOLEAN,
            internal_name="is_collectible",
        )
        PropertyTranslation.objects.create(
            property=boolean_property,
            language="en",
            name="Is Collectible",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.product,
            property=boolean_property,
            value_boolean=True,
            multi_tenant_company=self.multi_tenant_company,
        )

        ctx = DummyContext()
        tool = UpsertProductsMcpTool(mcp=DummyMcp())

        async_to_sync(tool.execute)(
            products={
                "sku": "BOOK-001",
                "properties": f'[{{"property_id": {boolean_property.id}, "value": "false"}}]',
            },
            ctx=ctx,
        )

        product_property = ProductProperty.objects.get(
            product=self.product,
            property=boolean_property,
        )
        self.assertFalse(product_property.value_boolean)
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_accepts_multiselect_ids_as_comma_separated_string(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        multiselect_property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.MULTISELECT,
            internal_name="reading_modes",
        )
        PropertyTranslation.objects.create(
            property=multiselect_property,
            language="en",
            name="Reading Modes",
            multi_tenant_company=self.multi_tenant_company,
        )
        ebook_value = PropertySelectValue.objects.create(
            property=multiselect_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        audio_value = PropertySelectValue.objects.create(
            property=multiselect_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=ebook_value,
            language="en",
            value="Ebook",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=audio_value,
            language="en",
            value="Audio",
            multi_tenant_company=self.multi_tenant_company,
        )

        ctx = DummyContext()
        tool = UpsertProductsMcpTool(mcp=DummyMcp())

        async_to_sync(tool.execute)(
            products={
                "sku": "BOOK-001",
                "properties": (
                    f'[{{"property_id": {multiselect_property.id}, "value": "{ebook_value.id}, {audio_value.id}", '
                    f'"value_is_id": "true"}}]'
                ),
            },
            ctx=ctx,
        )

        product_property = ProductProperty.objects.get(
            product=self.product,
            property=multiselect_property,
        )
        assigned_ids = list(product_property.value_multi_select.order_by("id").values_list("id", flat=True))

        self.assertEqual(assigned_ids, [ebook_value.id, audio_value.id])
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_schema_accepts_float_values(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        float_property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.FLOAT,
            internal_name="weight_kg",
        )
        PropertyTranslation.objects.create(
            property=float_property,
            language="en",
            name="Weight Kg",
            multi_tenant_company=self.multi_tenant_company,
        )

        ctx = DummyContext()
        tool = UpsertProductsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            products={
                "sku": "BOOK-001",
                "properties": f'[{{"property_id": {float_property.id}, "value": "10.0"}}]',
            },
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        jsonschema_validate(
            instance=payload,
            schema=UPSERT_PRODUCTS_OUTPUT_SCHEMA,
        )
        ctx.error.assert_not_awaited()

    @patch("products.mcp.update_helpers.run_product_import_update")
    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_adds_images_executes_from_async_context(self, mock_get_access_token, mock_run_product_import_update):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        mock_run_product_import_update.return_value = SimpleNamespace(
            images_associations_instances=SimpleNamespace(count=lambda: 1),
        )
        ctx = DummyContext()
        tool = UpsertProductsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            products={
                "sku": "BOOK-001",
                "images": '[{"image_url": "https://example.com/book.jpg", "title": "Alt cover"}]',
            },
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(payload["results"][0]["applied_updates"]["images"], 1)
        mock_run_product_import_update.assert_called_once()
        ctx.error.assert_not_awaited()

    @patch("products.mcp.update_helpers.run_product_import_update")
    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_accepts_image_content_without_image_url(self, mock_get_access_token, mock_run_product_import_update):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        mock_run_product_import_update.return_value = SimpleNamespace(
            images_associations_instances=SimpleNamespace(count=lambda: 1),
        )
        ctx = DummyContext()
        tool = UpsertProductsMcpTool(mcp=DummyMcp())

        async_to_sync(tool.execute)(
            products={
                "sku": "BOOK-001",
                "images": '[{"image_content": "aW1nMQ==", "title": "Chat upload"}]',
            },
            ctx=ctx,
        )

        _, kwargs = mock_run_product_import_update.call_args
        self.assertEqual(
            kwargs["product_data"]["images"],
            [{"image_content": "aW1nMQ==", "title": "Chat upload"}],
        )
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_create_product_executes_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = CreateProductsMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            products={
                "type": Product.SIMPLE,
                "name": "Created Book",
                "product_type_id": self.product_type_select_value.id,
                "vat_rate_id": self.vat_rate.id,
                "active": True,
                "ean_code": "555666777",
                "translations": '[{"language": "fr", "name": "Livre cree"}]',
                "prices": f'[{{"currency": "{self.currency.iso_code}", "price": "19.95", "rrp": "24.95"}}]',
                "properties": (
                    f'[{{"property_id": {self.property.id}, "value": {self.select_value.id}, '
                    f'"value_is_id": true}}]'
                ),
            },
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(payload["requested_count"], 1)
        self.assertEqual(payload["processed_count"], 1)
        self.assertEqual(payload["created_count"], 1)
        result_item = payload["results"][0]
        created_product = Product.objects.get(id=result_item["product_id"])
        self.assertEqual(created_product.type, Product.SIMPLE)
        self.assertTrue(result_item["created"])
        self.assertTrue(result_item["sku_was_generated"])
        self.assertTrue(created_product.sku)
        self.assertEqual(result_item["name"], "Created Book")
        self.assertTrue(created_product.active)

        product_type_assignment = ProductProperty.objects.get(
            product=created_product,
            property=self.product_type_property,
        )
        self.assertEqual(product_type_assignment.value_select_id, self.product_type_select_value.id)

        product_property = ProductProperty.objects.get(
            product=created_product,
            property=self.property,
        )
        self.assertEqual(product_property.value_select_id, self.select_value.id)

        created_price = SalesPrice.objects.get(
            product=created_product,
            currency=self.currency,
        )
        self.assertEqual(created_price.price, Decimal("19.95"))
        self.assertEqual(created_price.rrp, Decimal("24.95"))
        created_translation = ProductTranslation.objects.get(
            product=created_product,
            language="fr",
            sales_channel=None,
        )
        self.assertEqual(created_translation.name, "Livre cree")
        created_ean = EanCode.objects.get(product=created_product)
        self.assertEqual(created_ean.ean_code, "555666777")
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_products_rejects_more_than_ten_products(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = UpsertProductsMcpTool(mcp=DummyMcp())

        with self.assertRaisesMessage(
            Exception,
            "products supports up to 10 items per call; received 11.",
        ):
            async_to_sync(tool.execute)(
                products=[{"sku": "BOOK-001", "active": False} for _ in range(11)],
                ctx=ctx,
            )
