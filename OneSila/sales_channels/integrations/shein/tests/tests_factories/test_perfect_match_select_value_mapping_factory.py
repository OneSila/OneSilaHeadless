from core.tests import TestCase
from model_bakery import baker

from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation
from sales_channels.integrations.shein.factories.auto_import import (
    SheinPerfectMatchSelectValueMappingFactory,
)
from sales_channels.integrations.shein.models import (
    SheinProperty,
    SheinPropertySelectValue,
    SheinRemoteLanguage,
    SheinSalesChannel,
)


class SheinPerfectMatchSelectValueMappingFactoryTest(TestCase):
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

        self.property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_property = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.property,
            remote_id="color",
            name="Color",
            name_en="Color",
            type=Property.TYPES.SELECT,
        )

    def test_run_maps_by_value_perfect_match(self):
        local_value = baker.make(
            PropertySelectValue,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=local_value,
            language="en",
            value="Red",
        )
        remote_select_value = SheinPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            remote_id="red",
            value="Red",
            value_en="",
        )

        SheinPerfectMatchSelectValueMappingFactory(sales_channel=self.sales_channel).run()

        remote_select_value.refresh_from_db()
        self.assertEqual(remote_select_value.local_instance, local_value)

    def test_run_maps_by_value_en_perfect_match(self):
        local_value = baker.make(
            PropertySelectValue,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=local_value,
            language="en",
            value="Vermilion",
        )
        remote_select_value = SheinPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            remote_id="vermilion",
            value="",
            value_en="Vermilion",
        )

        SheinPerfectMatchSelectValueMappingFactory(sales_channel=self.sales_channel).run()

        remote_select_value.refresh_from_db()
        self.assertEqual(remote_select_value.local_instance, local_value)

    def test_run_does_not_map_when_value_matches_other_property(self):
        other_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        other_local_value = baker.make(
            PropertySelectValue,
            property=other_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=other_local_value,
            language="en",
            value="Red",
        )
        remote_select_value = SheinPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            remote_id="red",
            value="Red",
            value_en="",
        )

        SheinPerfectMatchSelectValueMappingFactory(sales_channel=self.sales_channel).run()

        remote_select_value.refresh_from_db()
        self.assertIsNone(remote_select_value.local_instance)
