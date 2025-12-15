from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation
from sales_channels.integrations.ebay.factories.auto_import import (
    EbayPerfectMatchSelectValueMappingFactory,
)
from sales_channels.integrations.ebay.models import (
    EbayProperty,
    EbayPropertySelectValue,
    EbayRemoteLanguage,
    EbaySalesChannel,
    EbaySalesChannelView,
)


class EbayPerfectMatchSelectValueMappingFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.multi_tenant_company.language = "de"
        self.multi_tenant_company.save(update_fields=["language"])

        self._translate_task_patcher = patch(
            "sales_channels.integrations.ebay.receivers.ebay_translate_select_value_task",
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

        self.property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_property = EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=self.property,
            remote_id="Color",
            localized_name="Color",
        )

    def test_run_maps_by_localized_value_perfect_match(self):
        local_value = baker.make(
            PropertySelectValue,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=local_value,
            language="en-us",
            value="Red",
        )
        remote_select_value = EbayPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            ebay_property=self.remote_property,
            marketplace=self.view,
            localized_value="Red",
        )

        EbayPerfectMatchSelectValueMappingFactory(sales_channel=self.sales_channel).run()

        remote_select_value.refresh_from_db()
        self.assertEqual(remote_select_value.local_instance, local_value)

    def test_run_maps_by_translated_value_perfect_match(self):
        local_value = baker.make(
            PropertySelectValue,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=local_value,
            language="en-us",
            value="Vermilion",
        )
        remote_select_value = EbayPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            ebay_property=self.remote_property,
            marketplace=self.view,
            localized_value="vermilion",
            translated_value="Vermilion",
        )

        EbayPerfectMatchSelectValueMappingFactory(sales_channel=self.sales_channel).run()

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
            language="en-us",
            value="Red",
        )
        remote_select_value = EbayPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            ebay_property=self.remote_property,
            marketplace=self.view,
            localized_value="Red",
        )

        EbayPerfectMatchSelectValueMappingFactory(sales_channel=self.sales_channel).run()

        remote_select_value.refresh_from_db()
        self.assertIsNone(remote_select_value.local_instance)
