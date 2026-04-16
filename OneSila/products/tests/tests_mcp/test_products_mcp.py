import json
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from asgiref.sync import async_to_sync
from jsonschema import validate as jsonschema_validate

from core.tests import TransactionTestCase
from llm.mcp.runtime import AccessToken
from products.mcp.output_types import PRODUCT_BATCH_MUTATION_OUTPUT_SCHEMA
from products.mcp.resources import build_product_inspector_error_codes_payload
from media.models import Media, MediaProductThrough
from products.mcp.tools.activate_product import ActivateProductMcpTool
from products.mcp.tools.add_product_images import AddProductImagesMcpTool
from products.mcp.tools.create_product import CreateProductMcpTool
from products.mcp.tools.deactivate_product import DeactivateProductMcpTool
from products.mcp.tools.get_product import GetProductMcpTool
from products.mcp.tools.get_product_types import GetProductTypesMcpTool
from products.mcp.tools.get_vat_rates import GetVatRatesMcpTool
from products.mcp.tools.search_sales_channels import SearchSalesChannelsMcpTool
from products.mcp.tools.search_products import SearchProductsMcpTool
from products.mcp.tools.update_product_content import UpdateProductContentMcpTool
from products.mcp.tools.upsert_product_price import UpsertProductPriceMcpTool
from products.mcp.tools.upsert_product_property_values import UpsertProductPropertyValuesMcpTool
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
        return AccessToken(
            token="test-token",
            client_id=f"company:{company_id}",
            scopes=[],
        )

    def _get_payload(self, *, result):
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

    def test_product_inspector_error_codes_resource_payload_marks_supported_and_deprecated_codes(self):
        payload = build_product_inspector_error_codes_payload()

        self.assertIn("codes", payload)
        by_code = {item["code"]: item for item in payload["codes"]}
        self.assertEqual(by_code[HAS_IMAGES_ERROR]["key"], "HAS_IMAGES_ERROR")
        self.assertIn("label", by_code[HAS_IMAGES_ERROR])

    @patch("llm.mcp.auth.get_access_token")
    def test_get_product_executes_from_async_context(self, mock_get_access_token):
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
        self.assertEqual(payload["vat_rate"], 21)
        self.assertEqual(payload["global_id"], self.product.global_id)
        self.assertEqual(payload["onesila_path"], f"/products/product/{self.product.global_id}")
        self.assertIn(payload["onesila_path"], payload["onesila_url"])
        self.assertEqual(payload["inspector"]["status_label"], "red")
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
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_search_sales_channels_filters_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
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
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_search_sales_channels_lists_all_without_filters(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
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
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_get_product_types_executes_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = GetProductTypesMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(payload["property"]["id"], self.product_type_property.id)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["results"][0]["id"], self.product_type_select_value.id)
        self.assertEqual(payload["results"][0]["value"], "Book")
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_get_vat_rates_executes_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = GetVatRatesMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["results"][0]["id"], self.vat_rate.id)
        self.assertEqual(payload["results"][0]["rate"], 21)
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_deactivate_product_executes_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = DeactivateProductMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            sku="BOOK-001",
            ctx=ctx,
        )

        self.product.refresh_from_db()
        payload = self._get_payload(result=result)
        self.assertFalse(self.product.active)
        self.assertFalse(payload["active"])
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_activate_product_executes_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        self.product.active = False
        self.product.save(update_fields=["active"])
        ctx = DummyContext()
        tool = ActivateProductMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            sku="BOOK-001",
            ctx=ctx,
        )

        self.product.refresh_from_db()
        payload = self._get_payload(result=result)
        self.assertTrue(self.product.active)
        self.assertTrue(payload["active"])
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_price_executes_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = UpsertProductPriceMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            sku="BOOK-001",
            currency=self.currency.iso_code,
            price="13.50",
            rrp="16.00",
            ctx=ctx,
        )

        sales_price = SalesPrice.objects.get(
            product=self.product,
            currency=self.currency,
        )
        payload = self._get_payload(result=result)
        self.assertEqual(sales_price.price, Decimal("13.50"))
        self.assertEqual(sales_price.rrp, Decimal("16.00"))
        self.assertEqual(payload["product_id"], self.product.id)
        self.assertEqual(payload["sku"], "BOOK-001")
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_price_rejects_inherited_currency(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        inherited_currency = Currency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            iso_code="EUR",
            name="Euro",
            symbol="€",
            inherits_from=self.currency,
        )
        ctx = DummyContext()
        tool = UpsertProductPriceMcpTool(mcp=DummyMcp())

        with self.assertRaisesMessage(
            Exception,
            "Currency 'EUR' inherits its price from 'GBP' and cannot be edited directly. Update the base currency price instead.",
        ):
            async_to_sync(tool.execute)(
                sku="BOOK-001",
                currency=inherited_currency.iso_code,
                price="10.00",
                ctx=ctx,
            )

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_price_rejects_unconfigured_currency(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = UpsertProductPriceMcpTool(mcp=DummyMcp())

        with self.assertRaisesMessage(
            Exception,
            "Currency 'ZZZ' is not configured for this account.",
        ):
            async_to_sync(tool.execute)(
                sku="BOOK-001",
                currency="ZZZ",
                price="10.00",
                ctx=ctx,
            )

    @patch("llm.mcp.auth.get_access_token")
    def test_update_product_content_executes_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = UpdateProductContentMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            sku="BOOK-001",
            language="fr",
            short_description="Résumé court mis à jour",
            bullet_points='["Premier point", "Deuxième point"]',
            ctx=ctx,
        )

        translation = ProductTranslation.objects.get(
            product=self.product,
            language="fr",
            sales_channel=None,
        )
        bullet_points = list(
            translation.bullet_points.order_by("sort_order", "id").values_list("text", flat=True)
        )
        payload = self._get_payload(result=result)
        self.assertEqual(translation.name, "Page du livre")
        self.assertEqual(translation.short_description, "Résumé court mis à jour")
        self.assertEqual(bullet_points, ["Premier point", "Deuxième point"])
        self.assertEqual(payload["product_id"], self.product.id)
        self.assertEqual(payload["sku"], "BOOK-001")
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_property_values_executes_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = UpsertProductPropertyValuesMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            sku="BOOK-001",
            updates=(
                f'[{{"property_id": {self.property.id}, "value": {self.other_select_value.id}, '
                f'"value_is_id": true}}]'
            ),
            ctx=ctx,
        )

        product_property = ProductProperty.objects.get(
            product=self.product,
            property=self.property,
        )
        payload = self._get_payload(result=result)
        self.assertEqual(product_property.value_select_id, self.other_select_value.id)
        self.assertEqual(payload["updated_count"], 1)
        self.assertEqual(payload["product_id"], self.product.id)
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_property_values_parses_false_string_for_boolean_properties(self, mock_get_access_token):
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
        tool = UpsertProductPropertyValuesMcpTool(mcp=DummyMcp())

        async_to_sync(tool.execute)(
            sku="BOOK-001",
            updates=f'[{{"property_id": {boolean_property.id}, "value": "false"}}]',
            ctx=ctx,
        )

        product_property = ProductProperty.objects.get(
            product=self.product,
            property=boolean_property,
        )
        self.assertFalse(product_property.value_boolean)
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_upsert_product_property_values_accepts_multiselect_ids_as_comma_separated_string(self, mock_get_access_token):
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
        tool = UpsertProductPropertyValuesMcpTool(mcp=DummyMcp())

        async_to_sync(tool.execute)(
            sku="BOOK-001",
            updates=(
                f'[{{"property_id": {multiselect_property.id}, "value": "{ebook_value.id}, {audio_value.id}", '
                f'"value_is_id": "true"}}]'
            ),
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
    def test_upsert_product_property_values_schema_accepts_float_values(self, mock_get_access_token):
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
        tool = UpsertProductPropertyValuesMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            sku="BOOK-001",
            updates=f'[{{"property_id": {float_property.id}, "value": "10.0"}}]',
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        jsonschema_validate(
            instance=payload,
            schema=PRODUCT_BATCH_MUTATION_OUTPUT_SCHEMA,
        )
        ctx.error.assert_not_awaited()

    @patch("products.mcp.tools.add_product_images.run_product_import_update")
    @patch("llm.mcp.auth.get_access_token")
    def test_add_product_images_executes_from_async_context(self, mock_get_access_token, mock_run_product_import_update):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        mock_run_product_import_update.return_value = SimpleNamespace(
            images_associations_instances=SimpleNamespace(count=lambda: 1),
        )
        ctx = DummyContext()
        tool = AddProductImagesMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            sku="BOOK-001",
            images='[{"image_url": "https://example.com/book.jpg", "title": "Alt cover"}]',
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(payload["updated_count"], 1)
        mock_run_product_import_update.assert_called_once()
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_create_product_executes_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = CreateProductMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            type=Product.SIMPLE,
            name="Created Book",
            product_type_id=self.product_type_select_value.id,
            price="19.95",
            rrp="24.95",
            vat_rate_id=self.vat_rate.id,
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        created_product = Product.objects.get(id=payload["product_id"])
        self.assertEqual(created_product.type, Product.SIMPLE)
        self.assertTrue(payload["created"])
        self.assertTrue(payload["sku_was_generated"])
        self.assertTrue(created_product.sku)
        self.assertEqual(payload["name"], "Created Book")

        product_type_assignment = ProductProperty.objects.get(
            product=created_product,
            property=self.product_type_property,
        )
        self.assertEqual(product_type_assignment.value_select_id, self.product_type_select_value.id)

        created_price = SalesPrice.objects.get(
            product=created_product,
            currency=self.currency,
        )
        self.assertEqual(created_price.price, Decimal("19.95"))
        self.assertEqual(created_price.rrp, Decimal("24.95"))
        ctx.error.assert_not_awaited()
