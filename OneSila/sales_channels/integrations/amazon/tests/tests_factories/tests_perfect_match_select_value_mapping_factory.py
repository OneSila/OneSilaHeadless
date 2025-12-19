from core.tests import TestCase
from model_bakery import baker
from unittest.mock import patch

from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation
from sales_channels.integrations.amazon.factories.auto_import import (
    AmazonPerfectMatchSelectValueMappingFactory,
)
from sales_channels.integrations.amazon.models import (
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonRemoteLanguage,
    AmazonSalesChannel,
    AmazonSalesChannelView,
)

from ..helpers import DisableWooCommerceSignalsMixin


class AmazonPerfectMatchSelectValueMappingFactoryTest(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.multi_tenant_company.language = "de"
        self.multi_tenant_company.save(update_fields=["language"])

        self._translate_task_patcher = patch(
            "sales_channels.integrations.amazon.receivers.amazon_translate_select_value_task",
            return_value=None,
        )
        self._translate_task_patcher.start()
        self.addCleanup(self._translate_task_patcher.stop)

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
        self.remote_language = AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            local_instance="en",
            remote_code="en_US",
            remote_id="LANG",
        )
        self.property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.property,
            code="color",
            type=Property.TYPES.SELECT,
            allows_unmapped_values=True,
        )

    def test_run_maps_by_remote_name_perfect_match(self):
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
        remote_select_value = AmazonPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_property=self.remote_property,
            marketplace=self.view,
            remote_value="red",
            remote_name="Red",
        )

        AmazonPerfectMatchSelectValueMappingFactory(sales_channel=self.sales_channel).run()

        remote_select_value.refresh_from_db()
        self.assertEqual(remote_select_value.local_instance, local_value)

    def test_run_maps_by_translated_remote_name_when_remote_name_missing(self):
        local_value = baker.make(
            PropertySelectValue,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=local_value,
            language="de",
            value="Zinnoberrot",
        )
        remote_select_value = AmazonPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_property=self.remote_property,
            marketplace=self.view,
            remote_value="vermilion",
            remote_name=None,
            translated_remote_name="Zinnoberrot",
        )

        AmazonPerfectMatchSelectValueMappingFactory(sales_channel=self.sales_channel).run()

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
        remote_select_value = AmazonPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_property=self.remote_property,
            marketplace=self.view,
            remote_value="red",
            remote_name="Red",
        )

        AmazonPerfectMatchSelectValueMappingFactory(sales_channel=self.sales_channel).run()

        remote_select_value.refresh_from_db()
        self.assertIsNone(remote_select_value.local_instance)

    def test_run_maps_by_translated_remote_name_in_company_language_even_when_marketplace_language_differs(self):
        spanish_view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="VIEW_ES",
            is_default=False,
        )
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=spanish_view,
            local_instance="es",
            remote_code="es_ES",
            remote_id="LANG_ES",
        )

        local_value = baker.make(
            PropertySelectValue,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=local_value,
            language="de",
            value="Rot",
        )
        remote_select_value = AmazonPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_property=self.remote_property,
            marketplace=spanish_view,
            remote_value="roja",
            remote_name="Roja",
            translated_remote_name="Rot",
        )

        AmazonPerfectMatchSelectValueMappingFactory(sales_channel=self.sales_channel).run()

        remote_select_value.refresh_from_db()
        self.assertEqual(remote_select_value.local_instance, local_value)
