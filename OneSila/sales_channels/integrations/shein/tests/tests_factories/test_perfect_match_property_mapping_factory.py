from core.tests import TestCase
from model_bakery import baker

from properties.models import Property, PropertyTranslation
from sales_channels.integrations.shein.factories.auto_import import (
    SheinPerfectMatchPropertyMappingFactory,
)
from sales_channels.integrations.shein.models import (
    SheinProperty,
    SheinRemoteLanguage,
    SheinSalesChannel,
)


class SheinPerfectMatchPropertyMappingFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            hostname="shein-test",
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SHEIN",
        )
        SheinRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance="en",
            remote_code="en_US",
            remote_id="LANG",
        )

    def test_run_maps_property_with_matching_name_and_type(self):
        matching_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=matching_property,
            language="en",
            name="Color",
        )

        mismatched_property = baker.make(
            Property,
            type=Property.TYPES.TEXT,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=mismatched_property,
            language="en",
            name="Material",
        )

        matching_remote = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="color",
            name="Color",
            name_en="",
            type=Property.TYPES.SELECT,
        )
        mismatched_remote = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="material",
            name="Material",
            name_en="",
            type=Property.TYPES.SELECT,
        )

        SheinPerfectMatchPropertyMappingFactory(sales_channel=self.sales_channel).run()

        matching_remote.refresh_from_db()
        mismatched_remote.refresh_from_db()
        self.assertEqual(matching_remote.local_instance, matching_property)
        self.assertIsNone(mismatched_remote.local_instance)
