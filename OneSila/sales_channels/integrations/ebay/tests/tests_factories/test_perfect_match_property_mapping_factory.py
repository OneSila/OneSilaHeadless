from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from properties.models import Property, PropertyTranslation
from sales_channels.integrations.ebay.factories.auto_import import (
    EbayPerfectMatchPropertyMappingFactory,
)
from sales_channels.integrations.ebay.models import (
    EbayProperty,
    EbayRemoteLanguage,
    EbaySalesChannel,
    EbaySalesChannelView,
)


class EbayPerfectMatchPropertyMappingFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.multi_tenant_company.language = "en-us"
        self.multi_tenant_company.save(update_fields=["language"])

        self._translate_task_patcher = patch(
            "sales_channels.integrations.ebay.receivers.ebay_translate_property_task",
            return_value=None,
        )
        self._translate_task_patcher.start()
        self.addCleanup(self._translate_task_patcher.stop)

        self.sales_channel = EbaySalesChannel.objects.create(
            hostname="test.ebay",
            environment=EbaySalesChannel.PRODUCTION,
            active=True,
            multi_tenant_company=self.multi_tenant_company,
            refresh_token="test-refresh-token",
        )
        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            remote_id="EBAY_GB",
            is_default=True,
        )
        EbayRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            local_instance="en-us",
            remote_code="en_US",
        )

    def test_run_maps_by_localized_name_perfect_match(self):
        matching_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=matching_property,
            language="en-us",
            name="Color",
        )

        other_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=other_property,
            language="en-us",
            name="Material",
        )

        matching_remote = EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            remote_id="Color",
            localized_name="Color",
            type=Property.TYPES.SELECT,
        )
        mismatched_remote = EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            remote_id="Size",
            localized_name="Size",
            type=Property.TYPES.SELECT,
        )

        EbayPerfectMatchPropertyMappingFactory(sales_channel=self.sales_channel).run()

        matching_remote.refresh_from_db()
        mismatched_remote.refresh_from_db()
        self.assertEqual(matching_remote.local_instance, matching_property)
        self.assertIsNone(mismatched_remote.local_instance)
