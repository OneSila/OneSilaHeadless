from types import SimpleNamespace

from core.tests import TestCase
from properties.models import Property
from sales_channels.integrations.amazon.factories.sales_channels.full_schema import (
    AmazonProductTypeRuleFactory,
)
from sales_channels.integrations.amazon.models import AmazonSalesChannel, AmazonSalesChannelView
from sales_channels.integrations.amazon.models.properties import AmazonProperty, AmazonProductType


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
