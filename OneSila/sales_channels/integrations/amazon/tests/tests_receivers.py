from unittest.mock import patch

from model_bakery import baker
from core.tests import TestCase
from properties.models import Property, PropertySelectValue
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonProduct,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProductType,
    AmazonRemoteLanguage,
)
from products.models import Product
from sales_channels.signals import manual_sync_remote_product, update_remote_product
from sales_channels.integrations.amazon.tasks import resync_amazon_product_db_task
from .helpers import DisableWooCommerceSignalsMixin


class AmazonProductTypeReceiversTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )

    @patch("sales_channels.integrations.amazon.receivers.create_amazon_product_type_rule_task")
    def test_factory_run_triggered_on_imported_change(self, task_func):
        pt = AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type_code="CHAIR",
            imported=False,
        )

        pt.imported = True
        pt.save()

        task_func.assert_called_once_with(
            product_type_code=pt.product_type_code,
            sales_channel_id=pt.sales_channel_id,
        )


class AmazonManualSyncReceiverTest(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="VIEW",
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )

    # @patch("sales_channels.integrations.amazon.receivers.run_single_amazon_product_task_flow")
    # def test_manual_sync_queues_task(self, flow_mock):
    #     manual_sync_remote_product.send(
    #         sender=AmazonProduct,
    #         instance=self.remote_product,
    #         view=self.view,
    #         force_validation_only=True,
    #     )
    #
    #     flow_mock.assert_called_once()
    #     _, kwargs = flow_mock.call_args
    #     self.assertEqual(kwargs["task_func"], resync_amazon_product_db_task)
    #     self.assertTrue(kwargs["force_validation_only"])
    #     self.assertEqual(kwargs["view"], self.view)


class AmazonPropertyReceiversTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.marketplace = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="VIEW",
        )
        self.local_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.local_select_value = baker.make(
            PropertySelectValue,
            property=self.local_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.local_property,
            code="color",
            type=Property.TYPES.SELECT,
        )
        self.remote_select_value = AmazonPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_property=self.remote_property,
            marketplace=self.marketplace,
            remote_value="red",
            remote_name="Red",
            local_instance=self.local_select_value,
        )

    def test_unmap_select_values_when_property_unmapped(self):
        self.assertIsNotNone(self.remote_select_value.local_instance)

        self.remote_property.local_instance = None
        self.remote_property.save()

        self.remote_select_value.refresh_from_db()
        self.assertIsNone(self.remote_select_value.local_instance)

    def test_unmap_select_values_when_property_remapped(self):
        self.assertIsNotNone(self.remote_select_value.local_instance)

        new_local_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_property.local_instance = new_local_property
        self.remote_property.save()

        self.remote_select_value.refresh_from_db()
        self.assertIsNone(self.remote_select_value.local_instance)


class AmazonSelectValueTranslationReceiverTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.marketplace = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="VIEW",
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
        )

    @patch("sales_channels.integrations.amazon.receivers.AmazonSelectValueTranslationLLM.translate", return_value="Red")
    def test_translate_when_language_diff(self, translate_mock):
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.marketplace,
            remote_code="de_DE",
            local_instance="de",
        )

        val = AmazonPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_property=self.remote_property,
            marketplace=self.marketplace,
            remote_value="rot",
            remote_name="Rot",
        )

        translate_mock.assert_called_once()
        val.refresh_from_db()
        self.assertEqual(val.translated_remote_name, "Red")

    @patch("sales_channels.integrations.amazon.receivers.AmazonSelectValueTranslationLLM.translate")
    def test_no_translation_when_language_same(self, translate_mock):
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.marketplace,
            remote_code="en_US",
            local_instance="en",
        )

        val = AmazonPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_property=self.remote_property,
            marketplace=self.marketplace,
            remote_value="red",
            remote_name="Red",
        )

        translate_mock.assert_not_called()
        val.refresh_from_db()
        self.assertEqual(val.translated_remote_name, "Red")

    @patch("sales_channels.integrations.amazon.receivers.AmazonSelectValueTranslationLLM.translate")
    def test_ignored_code_skips_translation(self, translate_mock):
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.marketplace,
            remote_code="de_DE",
            local_instance="de",
        )

        self.remote_property.code = "country_of_origin"
        self.remote_property.save()

        val = AmazonPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_property=self.remote_property,
            marketplace=self.marketplace,
            remote_value="DE",
            remote_name="Deutschland",
        )

        translate_mock.assert_not_called()
        val.refresh_from_db()
        self.assertEqual(val.translated_remote_name, "Deutschland")