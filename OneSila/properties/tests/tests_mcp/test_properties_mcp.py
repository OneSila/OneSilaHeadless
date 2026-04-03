from asgiref.sync import async_to_sync
from unittest.mock import AsyncMock, patch

from core.tests import TestCase
from llm.mcp.runtime import AccessToken
from properties.mcp.tools.get_property import GetPropertyMcpTool
from properties.mcp.tools.search_properties import SearchPropertiesMcpTool
from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation, PropertyTranslation


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


class PropertyMcpToolAsyncTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.languages = ["en", "fr"]
        self.multi_tenant_company.save(update_fields=["language", "languages"])

        self.property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
            internal_name="color",
            has_image=True,
        )
        PropertyTranslation.objects.create(
            property=self.property,
            language="en",
            name="Color",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            property=self.property,
            language="fr",
            name="Couleur",
            multi_tenant_company=self.multi_tenant_company,
        )

        self.property_value = PropertySelectValue.objects.create(
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.property_value,
            language="en",
            value="Red",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.property_value,
            language="fr",
            value="Rouge",
            multi_tenant_company=self.multi_tenant_company,
        )

    def _build_access_token(self, *, company_id: int) -> AccessToken:
        return AccessToken(
            token="test-token",
            client_id=f"company:{company_id}",
            scopes=[],
        )

    @patch("llm.mcp.auth.get_access_token")
    def test_search_properties_executes_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = SearchPropertiesMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            search="Color",
            ctx=ctx,
        )

        self.assertEqual(result.structured_content["results"][0]["id"], self.property.id)
        self.assertEqual(result.structured_content["results"][0]["name"], "Color")
        self.assertFalse(result.structured_content["has_more"])
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_get_property_executes_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = GetPropertyMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            property_id=self.property.id,
            ctx=ctx,
        )

        translation_names = {item["name"] for item in result.structured_content["translations"]}
        value_translations = {
            item["value"]
            for item in result.structured_content["values"][0]["translations"]
        }

        self.assertEqual(result.structured_content["id"], self.property.id)
        self.assertEqual(result.structured_content["internal_name"], "color")
        self.assertSetEqual(translation_names, {"Color", "Couleur"})
        self.assertSetEqual(value_translations, {"Red", "Rouge"})
        ctx.error.assert_not_awaited()
