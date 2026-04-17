import json

from asgiref.sync import async_to_sync
from unittest.mock import AsyncMock, patch

from core.tests import TestCase
from llm.mcp.runtime import AccessToken
from properties.mcp.tools.create_property import CreatePropertyMcpTool
from properties.mcp.tools.create_property_select_value import CreatePropertySelectValueMcpTool
from properties.mcp.tools.edit_property import EditPropertyMcpTool
from properties.mcp.tools.edit_property_select_value import EditPropertySelectValueMcpTool
from properties.mcp.tools.get_property import GetPropertyMcpTool
from properties.mcp.tools.get_property_select_value import GetPropertySelectValueMcpTool
from properties.mcp.tools.search_properties import SearchPropertiesMcpTool
from properties.mcp.tools.search_property_select_values import SearchPropertySelectValuesMcpTool
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

    def _get_payload(self, *, result):
        self.assertEqual(len(result.content), 1)
        return json.loads(result.content[0].text)

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

        payload = self._get_payload(result=result)
        self.assertEqual(payload["results"][0]["id"], self.property.id)
        self.assertEqual(payload["results"][0]["name"], "Color")
        self.assertFalse(payload["has_more"])
        self.assertNotIn("translations", payload["results"][0])
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_search_properties_includes_translations_when_requested(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = SearchPropertiesMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            search="Color",
            include_translations=True,
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(
            {item["name"] for item in payload["results"][0]["translations"]},
            {"Color", "Couleur"},
        )
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

        payload = self._get_payload(result=result)
        translation_names = {item["name"] for item in payload["translations"]}
        value_translations = {
            item["value"]
            for item in payload["values"][0]["translations"]
        }

        self.assertEqual(payload["id"], self.property.id)
        self.assertEqual(payload["internal_name"], "color")
        self.assertSetEqual(translation_names, {"Color", "Couleur"})
        self.assertSetEqual(value_translations, {"Red", "Rouge"})
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_search_property_select_values_omits_translations_by_default(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = SearchPropertySelectValuesMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            search="Red",
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(payload["results"][0]["id"], self.property_value.id)
        self.assertNotIn("translations", payload["results"][0])
        self.assertNotIn("usage_count", payload["results"][0])
        self.assertNotIn("full_value_name", payload["results"][0])
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_search_property_select_values_includes_translations_when_requested(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = SearchPropertySelectValuesMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            search="Red",
            include_translations=True,
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(
            {item["value"] for item in payload["results"][0]["translations"]},
            {"Red", "Rouge"},
        )
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_search_property_select_values_includes_usage_count_when_requested(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = SearchPropertySelectValuesMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            search="Red",
            include_usage_count=True,
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertIn("usage_count", payload["results"][0])
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_get_property_select_value_executes_from_async_context(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = GetPropertySelectValueMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            select_value_id=self.property_value.id,
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.assertEqual(payload["id"], self.property_value.id)
        self.assertEqual(payload["property"]["id"], self.property.id)
        self.assertEqual({item["value"] for item in payload["translations"]}, {"Red", "Rouge"})
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_create_property_returns_lean_payload(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = CreatePropertyMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            type=Property.TYPES.TEXT,
            internal_name="material",
            name="Material",
            translations='[{"language":"fr","name":"Materiau"}]',
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        created_property = Property.objects.get(id=payload["property_id"])
        self.assertTrue(payload["created"])
        self.assertEqual(payload["internal_name"], "material")
        self.assertEqual(created_property.name, "Material")
        self.assertEqual(payload["message"], "Saved successfully. Use get_property for details.")
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_edit_property_returns_lean_payload(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = EditPropertyMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            property_id=self.property.id,
            add_to_filters=False,
            translations='[{"language":"fr","name":"Teinte"}]',
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        self.property.refresh_from_db()
        self.assertTrue(payload["updated"])
        self.assertEqual(payload["property_id"], self.property.id)
        self.assertFalse(self.property.add_to_filters)
        self.assertEqual(payload["message"], "Saved successfully. Use get_property for details.")
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_create_property_select_value_returns_lean_payload(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = CreatePropertySelectValueMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            value="Blue",
            property_id=self.property.id,
            translations='[{"language":"fr","value":"Bleu"}]',
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        created_value = PropertySelectValue.objects.get(id=payload["select_value_id"])
        self.assertTrue(payload["created"])
        self.assertEqual(payload["property_id"], self.property.id)
        self.assertEqual(created_value.value, "Blue")
        self.assertEqual(payload["message"], "Saved successfully. Use get_property_select_value for details.")
        ctx.error.assert_not_awaited()

    @patch("llm.mcp.auth.get_access_token")
    def test_edit_property_select_value_returns_lean_payload(self, mock_get_access_token):
        mock_get_access_token.return_value = self._build_access_token(
            company_id=self.multi_tenant_company.id,
        )
        ctx = DummyContext()
        tool = EditPropertySelectValueMcpTool(mcp=DummyMcp())

        result = async_to_sync(tool.execute)(
            select_value_id=self.property_value.id,
            translations='[{"language":"fr","value":"Rouge vif"}]',
            ctx=ctx,
        )

        payload = self._get_payload(result=result)
        updated_translation = PropertySelectValueTranslation.objects.get(
            propertyselectvalue=self.property_value,
            language="fr",
        )
        self.assertTrue(payload["updated"])
        self.assertEqual(payload["select_value_id"], self.property_value.id)
        self.assertEqual(updated_translation.value, "Rouge vif")
        self.assertEqual(payload["message"], "Saved successfully. Use get_property_select_value for details.")
        ctx.error.assert_not_awaited()
