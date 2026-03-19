from core.tests import TestCase
from model_bakery import baker

from properties.models import (
    Property,
    PropertySelectValue,
    PropertySelectValueTranslation,
    PropertyTranslation,
)
from sales_channels.integrations.mirakl.factories.auto_import import (
    MiraklPerfectMatchPropertyMappingFactory,
    MiraklPerfectMatchSelectValueMappingFactory,
)
from sales_channels.integrations.mirakl.models import (
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklRemoteLanguage,
    MiraklSalesChannel,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklPerfectMatchFactoriesTest(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.save(update_fields=["language"])

        self.sales_channel = MiraklSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret",
        )
        MiraklRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance="en",
            remote_code="en_GB",
            label="English - GB",
            is_default=True,
        )

    def test_perfect_match_property_maps_from_name(self):
        local_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
            language="en",
            name="Colour Group",
        )

        remote_property = MiraklProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="colour_group",
            name="Colour Group",
            type=Property.TYPES.SELECT,
            label_translations=[{"locale": "en", "value": "Colour Group"}],
        )

        MiraklPerfectMatchPropertyMappingFactory(sales_channel=self.sales_channel).run()

        remote_property.refresh_from_db()
        self.assertEqual(remote_property.local_instance, local_property)

    def test_perfect_match_select_value_maps_from_value(self):
        local_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        local_value = baker.make(
            PropertySelectValue,
            property=local_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=local_value,
            language="en",
            value="Blue",
        )

        remote_property = MiraklProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="colour_group",
            name="Colour Group",
            type=Property.TYPES.SELECT,
            local_instance=local_property,
        )
        remote_value = MiraklPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=remote_property,
            code="blue",
            value="Blue",
            label_translations=[{"locale": "en", "value": "Blue"}],
            value_label_translations=[{"locale": "en", "value": "Blue"}],
        )

        MiraklPerfectMatchSelectValueMappingFactory(sales_channel=self.sales_channel).run()

        remote_value.refresh_from_db()
        self.assertEqual(remote_value.local_instance, local_value)
