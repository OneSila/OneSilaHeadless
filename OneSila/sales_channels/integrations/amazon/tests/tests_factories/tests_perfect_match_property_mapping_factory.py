from core.tests import TestCase
from model_bakery import baker

from properties.models import Property, PropertyTranslation
from sales_channels.integrations.amazon.factories.auto_import import (
    AmazonPerfectMatchPropertyMappingFactory,
)
from sales_channels.integrations.amazon.models import (
    AmazonProperty,
    AmazonRemoteLanguage,
    AmazonSalesChannel,
    AmazonSalesChannelView,
)

from ..helpers import DisableWooCommerceSignalsMixin


class AmazonPerfectMatchPropertyMappingFactoryTest(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.save(update_fields=["language"])

        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="VIEW",
            is_default=True,
        )
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            local_instance="en",
            remote_code="en_US",
            remote_id="LANG",
        )

    def test_run_maps_property_when_name_and_type_match(self):
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

        matching_remote = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="color",
            name="Color",
            type=Property.TYPES.SELECT,
        )
        mismatched_remote = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="material",
            name="Material",
            type=Property.TYPES.SELECT,
        )

        AmazonPerfectMatchPropertyMappingFactory(sales_channel=self.sales_channel).run()

        matching_remote.refresh_from_db()
        mismatched_remote.refresh_from_db()
        self.assertEqual(matching_remote.local_instance, matching_property)
        self.assertIsNone(mismatched_remote.local_instance)
