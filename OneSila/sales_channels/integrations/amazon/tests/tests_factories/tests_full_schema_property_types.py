import json
from types import SimpleNamespace

from core.tests import TestCase
from properties.models import Property
from sales_channels.integrations.amazon.factories.sales_channels.full_schema import (
    AmazonProductTypeRuleFactory,
)
from sales_channels.integrations.amazon.models import AmazonSalesChannel, AmazonSalesChannelView
from sales_channels.integrations.amazon.models.properties import AmazonProperty, AmazonProductType, AmazonPublicDefinition
from sales_channels.integrations.amazon.models.documents import AmazonDocumentType
from sales_channels.integrations.amazon.models.sales_channels import AmazonRemoteLanguage


class AmazonSchemaPropertyTypeSyncTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        self.view = AmazonSalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.factory = AmazonProductTypeRuleFactory(
            product_type_code="TEST_PRODUCT_TYPE",
            sales_channel=self.sales_channel,
            api=object(),
        )

    def _build_public_definition(self, *, code: str, prop_type: str) -> SimpleNamespace:
        return SimpleNamespace(
            export_definition=[
                {
                    "code": code,
                    "name": code.replace("__", " ").title(),
                    "type": prop_type,
                    "values": [],
                }
            ],
            is_required=False,
        )

    def test_get_or_create_product_type_returns_oldest_when_duplicates_exist(self) -> None:
        first = AmazonProductType.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            product_type_code="DUPLICATE_TYPE",
        )
        AmazonProductType.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            product_type_code="DUPLICATE_TYPE",
        )

        factory = AmazonProductTypeRuleFactory(
            product_type_code="DUPLICATE_TYPE",
            sales_channel=self.sales_channel,
            api=object(),
        )

        self.assertEqual(factory.product_type.id, first.id)

    def test_create_remote_properties_does_not_override_existing_type(self) -> None:
        public_definition = self._build_public_definition(
            code="material__value",
            prop_type=Property.TYPES.MULTISELECT,
        )

        self.factory.create_remote_properties(public_definition, self.view, is_default=True)

        remote_property = AmazonProperty.objects.get(
            sales_channel=self.sales_channel,
            code="material__value",
        )
        self.assertEqual(remote_property.type, Property.TYPES.MULTISELECT)
        self.assertEqual(remote_property.original_type, Property.TYPES.MULTISELECT)

        remote_property.type = Property.TYPES.SELECT
        remote_property.save(update_fields=["type"])

        self.factory.create_remote_properties(public_definition, self.view, is_default=True)

        remote_property.refresh_from_db()
        self.assertEqual(remote_property.type, Property.TYPES.SELECT)
        self.assertEqual(remote_property.original_type, Property.TYPES.MULTISELECT)

    def test_create_remote_properties_backfills_missing_type(self) -> None:
        AmazonProperty.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            code="size__value",
            type=None,
            original_type=None,
        )
        public_definition = self._build_public_definition(
            code="size__value",
            prop_type=Property.TYPES.TEXT,
        )

        self.factory.create_remote_properties(public_definition, self.view, is_default=False)

        remote_property = AmazonProperty.objects.get(
            sales_channel=self.sales_channel,
            code="size__value",
        )
        self.assertEqual(remote_property.original_type, Property.TYPES.TEXT)
        self.assertEqual(remote_property.type, Property.TYPES.TEXT)

    def test_sync_public_definitions_marks_document_field_and_creates_compliance_document_types(self) -> None:
        schema_definition = {
            "type": "array",
            "description": "Compliance documents for GPSR.",
            "items": {
                "type": "object",
                "properties": {
                    "content_type": {
                        "type": "string",
                        "description": "Compliance media content type.",
                        "enum": ["application_guide", "safety_data_sheet"],
                        "enumNames": ["Application Guide", "Safety Data Sheet"],
                    },
                    "source_location": {"type": "string"},
                    "content_language": {"type": "string"},
                    "marketplace_id": {"type": "string"},
                },
            },
        }

        public_definition = self.factory.sync_public_definitions(
            attr_code="compliance_media",
            schema_definition=schema_definition,
            required_properties=set(),
            view=self.view,
            offer_allowed_properties=[],
        )

        public_definition.refresh_from_db()
        self.assertTrue(public_definition.is_document_field)
        self.assertTrue(public_definition.is_internal)
        self.assertEqual(public_definition.document_field_kind, "COMPLIANCE_MEDIA")
        self.assertEqual(
            public_definition.document_allowed_types,
            ["application_guide", "safety_data_sheet"],
        )

        usage_definition = json.loads(public_definition.usage_definition)
        self.assertEqual(
            usage_definition["compliance_media"][0]["content_type"],
            "%document_type%",
        )
        self.assertEqual(
            usage_definition["compliance_media"][0]["source_location"],
            "%document_url%",
        )
        self.assertEqual(
            usage_definition["compliance_media"][0]["content_language"],
            "%document_language%",
        )

        remote_ids = set(
            AmazonDocumentType.objects.filter(sales_channel=self.sales_channel).values_list("remote_id", flat=True)
        )
        self.assertIn("compliance_media__application_guide", remote_ids)
        self.assertIn("compliance_media__safety_data_sheet", remote_ids)
        self.assertTrue(
            AmazonDocumentType.objects.filter(
                sales_channel=self.sales_channel,
                remote_id="compliance_media__application_guide",
                description="Compliance documents for GPSR.",
            ).exists()
        )

    def test_sync_public_definitions_collapses_pf_image_document_types(self) -> None:
        schema_definition = {
            "type": "array",
            "description": "Safety image locator.",
            "items": {
                "type": "object",
                "properties": {
                    "media_location": {"type": "string"},
                    "marketplace_id": {"type": "string"},
                },
            },
        }

        self.factory.sync_public_definitions(
            attr_code="image_locator_ukpf",
            schema_definition=schema_definition,
            required_properties=set(),
            view=self.view,
            offer_allowed_properties=[],
        )
        self.factory.sync_public_definitions(
            attr_code="image_locator_depf",
            schema_definition=schema_definition,
            required_properties=set(),
            view=self.view,
            offer_allowed_properties=[],
        )

        self.assertEqual(
            AmazonDocumentType.objects.filter(
                sales_channel=self.sales_channel,
                remote_id="image_locator_pf",
            ).count(),
            1,
        )
        self.assertTrue(
            AmazonPublicDefinition.objects.filter(
                code="image_locator_ukpf",
                is_document_field=True,
                is_internal=True,
            ).exists()
        )

    def test_sync_document_type_text_updates_only_for_default_or_empty_values(self) -> None:
        schema_definition = {
            "type": "array",
            "description": "Compliance docs EN text",
            "items": {
                "type": "object",
                "properties": {
                    "content_type": {
                        "type": "string",
                        "enum": ["application_guide"],
                        "enumNames": ["Application Guide EN"],
                    },
                    "source_location": {"type": "string"},
                    "content_language": {"type": "string"},
                    "marketplace_id": {"type": "string"},
                },
            },
        }

        document_type = AmazonDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="compliance_media__application_guide",
            name="Old Name",
            description="Old Description",
        )

        self.factory.sync_public_definitions(
            attr_code="compliance_media",
            schema_definition=schema_definition,
            required_properties=set(),
            view=self.view,
            offer_allowed_properties=[],
            is_default=False,
        )
        document_type.refresh_from_db()
        self.assertEqual(document_type.name, "Old Name")
        self.assertEqual(document_type.description, "Old Description")

        self.factory.sync_public_definitions(
            attr_code="compliance_media",
            schema_definition=schema_definition,
            required_properties=set(),
            view=self.view,
            offer_allowed_properties=[],
            is_default=True,
        )
        document_type.refresh_from_db()
        self.assertEqual(document_type.name, "Application Guide En")
        self.assertEqual(document_type.description, "Compliance docs EN text")

    def test_sync_pf_document_type_text_prefers_matching_locale_suffix(self) -> None:
        self.sales_channel.country = "GB"
        self.sales_channel.save(update_fields=["country"])
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_code="en_GB",
        )

        schema_definition = {
            "type": "array",
            "description": "Localized PF safety image",
            "items": {
                "type": "object",
                "properties": {
                    "media_location": {"type": "string"},
                    "marketplace_id": {"type": "string"},
                },
            },
        }

        document_type = AmazonDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="image_locator_pf",
            name="Current Name",
            description="Current Description",
        )

        self.factory.sync_public_definitions(
            attr_code="image_locator_depf",
            schema_definition=schema_definition,
            required_properties=set(),
            view=self.view,
            offer_allowed_properties=[],
            is_default=True,
        )
        document_type.refresh_from_db()
        self.assertEqual(document_type.name, "Current Name")
        self.assertEqual(document_type.description, "Current Description")

        self.factory.sync_public_definitions(
            attr_code="image_locator_ukpf",
            schema_definition=schema_definition,
            required_properties=set(),
            view=self.view,
            offer_allowed_properties=[],
            is_default=True,
        )
        document_type.refresh_from_db()
        self.assertEqual(document_type.name, "Safety Image (PF)")
        self.assertEqual(document_type.description, "Localized PF safety image")
