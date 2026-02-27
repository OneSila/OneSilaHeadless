from model_bakery import baker

from core.tests import TestCase
from properties.models import Property
from sales_channels.integrations.amazon.factories.sync.public_definition_toggle import (
    AmazonPublicDefinitionInternalSwitchFactory,
)
from sales_channels.integrations.amazon.models import (
    AmazonProductType,
    AmazonSalesChannel,
    AmazonSalesChannelView,
)
from sales_channels.integrations.amazon.models.properties import (
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonPublicDefinition,
    AmazonProductTypeItem,
)


class AmazonPublicDefinitionInternalSwitchFactoryTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER-1",
        )
        self.view_eu = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="DE",
            api_region_code="EU_DE",
        )
        self.view_na = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="US",
            api_region_code="NA_US",
        )
        self.local_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_becomes_internal_removes_orphan_property_and_values(self):
        product_type = AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type_code="CHAIR",
        )
        remote_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="color",
            type=Property.TYPES.SELECT,
            local_instance=self.local_property,
        )
        AmazonProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_rule=product_type,
            remote_property=remote_property,
        )
        AmazonPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_property=remote_property,
            marketplace=self.view_eu,
            remote_value="RED",
            remote_name="Red",
        )
        definition = AmazonPublicDefinition.objects.create(
            api_region_code="EU_DE",
            product_type_code="CHAIR",
            code="color",
            name="Color",
            is_internal=True,
            export_definition=[
                {
                    "code": "color",
                    "name": "Color",
                    "type": Property.TYPES.SELECT,
                    "values": [{"value": "RED", "name": "Red"}],
                }
            ],
        )

        AmazonPublicDefinitionInternalSwitchFactory(public_definition=definition).run()

        self.assertFalse(
            AmazonProductTypeItem.objects.filter(
                amazon_rule=product_type,
                remote_property__code="color",
            ).exists()
        )
        self.assertFalse(
            AmazonProperty.objects.filter(
                id=remote_property.id,
            ).exists()
        )
        self.assertFalse(
            AmazonPropertySelectValue.objects.filter(
                amazon_property_id=remote_property.id,
            ).exists()
        )

    def test_becomes_internal_keeps_property_when_other_product_type_still_uses_it(self):
        product_type_chair = AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type_code="CHAIR",
        )
        product_type_table = AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type_code="TABLE",
        )
        remote_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="color",
            type=Property.TYPES.SELECT,
            local_instance=self.local_property,
        )
        AmazonProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_rule=product_type_chair,
            remote_property=remote_property,
        )
        other_item = AmazonProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_rule=product_type_table,
            remote_property=remote_property,
        )
        definition = AmazonPublicDefinition.objects.create(
            api_region_code="EU_DE",
            product_type_code="CHAIR",
            code="color",
            name="Color",
            is_internal=True,
            export_definition=[
                {
                    "code": "color",
                    "name": "Color",
                    "type": Property.TYPES.SELECT,
                    "values": [],
                }
            ],
        )

        AmazonPublicDefinitionInternalSwitchFactory(public_definition=definition).run()

        self.assertFalse(
            AmazonProductTypeItem.objects.filter(
                amazon_rule=product_type_chair,
                remote_property=remote_property,
            ).exists()
        )
        self.assertTrue(
            AmazonProductTypeItem.objects.filter(
                id=other_item.id,
            ).exists()
        )
        self.assertTrue(
            AmazonProperty.objects.filter(
                id=remote_property.id,
            ).exists()
        )

    def test_becomes_non_internal_reimports_only_matching_region_views(self):
        product_type = AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type_code="DESK",
        )
        definition = AmazonPublicDefinition.objects.create(
            api_region_code="EU_DE",
            product_type_code="DESK",
            code="material",
            name="Material",
            is_internal=False,
            raw_schema={
                "type": "array",
                "items": {
                    "properties": {
                        "value": {
                            "title": "Material",
                            "type": "string",
                            "enum": ["WOOD"],
                            "enumNames": ["Wood"],
                        }
                    }
                },
            },
            export_definition=None,
            usage_definition="",
        )

        AmazonPublicDefinitionInternalSwitchFactory(public_definition=definition).run()

        definition.refresh_from_db()
        self.assertTrue(definition.export_definition)
        self.assertTrue(definition.usage_definition)

        remote_property = AmazonProperty.objects.get(
            sales_channel=self.sales_channel,
            code="material",
        )
        self.assertTrue(
            AmazonProductTypeItem.objects.filter(
                amazon_rule=product_type,
                remote_property=remote_property,
            ).exists()
        )
        self.assertTrue(
            AmazonPropertySelectValue.objects.filter(
                amazon_property=remote_property,
                marketplace=self.view_eu,
                remote_value="WOOD",
            ).exists()
        )
        self.assertFalse(
            AmazonPropertySelectValue.objects.filter(
                amazon_property=remote_property,
                marketplace=self.view_na,
            ).exists()
        )
