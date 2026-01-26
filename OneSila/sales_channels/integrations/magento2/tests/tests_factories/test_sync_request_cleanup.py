from types import SimpleNamespace
from unittest.mock import patch

from django.utils import timezone
from model_bakery import baker

from core.tests import TransactionTestCase
from media.models import MediaProductThrough, Media
from products.models import Product, ProductTranslation
from properties.models import Property, ProductProperty, ProductPropertyTextTranslation
from sales_channels.integrations.magento2.factories.products.content import (
    MagentoProductContentUpdateFactory,
)
from sales_channels.integrations.magento2.factories.prices.prices import (
    MagentoPriceUpdateFactory,
)
from sales_channels.integrations.magento2.factories.products.products import (
    MagentoProductUpdateFactory,
)
from sales_channels.integrations.magento2.factories.properties.properties import (
    MagentoProductPropertyDeleteFactory,
)
from sales_channels.integrations.magento2.factories.products.images import (
    MagentoMediaProductThroughDeleteFactory,
)
from sales_channels.integrations.magento2.models import (
    MagentoProduct,
    MagentoProductContent,
    MagentoPrice,
    MagentoProperty,
    MagentoProductProperty,
    MagentoImageProductAssociation,
    MagentoSalesChannelView,
)
from sales_channels.integrations.magento2.tests.mixins import (
    MagentoSalesChannelTestMixin,
)
from sales_channels import signals as sc_signals
from sales_channels.models import SalesChannelViewAssign, SyncRequest


class MagentoSyncRequestCleanupTests(MagentoSalesChannelTestMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self._api_patcher = patch(
            "sales_channels.integrations.magento2.factories.mixins.GetMagentoAPIMixin.get_api",
            return_value=SimpleNamespace(),
        )
        self._api_patcher.start()
        self.addCleanup(self._api_patcher.stop)

        signal_names = [
            "create_remote_product",
            "delete_remote_product",
            "update_remote_product",
            "sync_remote_product",
            "manual_sync_remote_product",
            "create_remote_product_property",
            "update_remote_product_property",
            "delete_remote_product_property",
            "update_remote_price",
            "update_remote_product_content",
            "update_remote_product_eancode",
            "add_remote_product_variation",
            "remove_remote_product_variation",
            "create_remote_image_association",
            "update_remote_image_association",
            "delete_remote_image_association",
            "delete_remote_image",
            "sales_view_assign_updated",
        ]
        self._signal_patchers = [
            patch.object(getattr(sc_signals, name), "send", return_value=[])
            for name in signal_names
        ]
        for patcher in self._signal_patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

        self.view = MagentoSalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            name="Default",
            remote_id=1,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = baker.make(
            MagentoProduct,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesChannelViewAssign.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _create_sync_request(self, *, sync_type, task_kwargs=None):
        return SyncRequest.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            sync_type=sync_type,
            status=SyncRequest.STATUS_PENDING,
            task_func_path="dummy.task",
            task_kwargs=task_kwargs or {},
            number_of_remote_requests=0,
        )

    def test_content_sync_request_cleaned(self):
        ProductTranslation.objects.create(
            product=self.product,
            language="en",
            name="Name",
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_content = MagentoProductContent.objects.create(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        sync_request = self._create_sync_request(sync_type=SyncRequest.TYPE_CONTENT)

        factory = MagentoProductContentUpdateFactory(
            self.sales_channel,
            self.product,
            remote_product=self.remote_product,
            remote_instance=remote_content,
            language="en",
        )
        with patch.object(factory, "update_remote", return_value=SimpleNamespace()), patch.object(
            factory, "serialize_response", return_value={}
        ), patch.object(factory, "needs_update", return_value=True):
            factory.run()

        sync_request.refresh_from_db()
        self.assertEqual(sync_request.status, SyncRequest.STATUS_DONE)

    def test_price_sync_request_cleaned(self):
        MagentoPrice.objects.create(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        sync_request = self._create_sync_request(sync_type=SyncRequest.TYPE_PRICE)

        factory = MagentoPriceUpdateFactory(
            self.sales_channel,
            self.product,
            remote_product=self.remote_product,
        )
        with patch.object(factory, "set_to_update_currencies") as set_currencies, patch.object(
            factory, "update_remote", return_value=SimpleNamespace()
        ):
            factory.price_data = {"USD": {"price": 10, "discount_price": None}}
            factory.to_update_currencies = ["USD"]
            set_currencies.side_effect = lambda: None
            factory.run()

        sync_request.refresh_from_db()
        self.assertEqual(sync_request.status, SyncRequest.STATUS_DONE)

    def test_product_sync_request_cleaned(self):
        sync_request = self._create_sync_request(sync_type=SyncRequest.TYPE_PRODUCT)

        factory = MagentoProductUpdateFactory(
            self.sales_channel,
            self.product,
            remote_instance=self.remote_product,
        )
        patch_methods = [
            "set_type",
            "initialize_remote_product",
            "check_status",
            "validate",
            "sanity_check",
            "precalculate_progress_step_increment",
            "set_rule",
            "build_payload",
            "customize_payload",
            "pre_action_process",
            "update_progress",
            "perform_remote_action",
            "set_discount",
            "post_action_process",
            "assign_saleschannels",
            "final_process",
            "log_action",
        ]
        patches = [patch.object(factory, name, return_value=None) for name in patch_methods]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        factory.initialize_remote_product.side_effect = lambda: setattr(factory, "remote_instance", self.remote_product)
        with patch.object(factory, "preflight_check", return_value=True):
            factory.run()

        sync_request.refresh_from_db()
        self.assertEqual(sync_request.status, SyncRequest.STATUS_DONE)

    def test_property_sync_request_cleaned_for_local_instance(self):
        prop = Property.objects.create(
            type=Property.TYPES.TEXT,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=self.product,
            property=prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertyTextTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_property=product_property,
            language="en",
            value_text="value",
        )
        remote_property = MagentoProperty.objects.create(
            local_instance=prop,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_product_property = MagentoProductProperty.objects.create(
            local_instance=product_property,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            remote_property=remote_property,
            multi_tenant_company=self.multi_tenant_company,
        )

        sync_request = self._create_sync_request(
            sync_type=SyncRequest.TYPE_PROPERTY,
            task_kwargs={"local_instance_id": product_property.id},
        )
        other_request = self._create_sync_request(
            sync_type=SyncRequest.TYPE_PROPERTY,
            task_kwargs={"local_instance_id": product_property.id + 1},
        )

        factory = MagentoProductPropertyDeleteFactory(
            self.sales_channel,
            product_property,
            remote_product=self.remote_product,
            remote_instance=remote_product_property,
        )
        with patch.object(factory, "delete_remote", return_value=SimpleNamespace()), patch.object(
            factory, "serialize_response", return_value={}
        ):
            factory.run()

        sync_request.refresh_from_db()
        other_request.refresh_from_db()
        self.assertEqual(sync_request.status, SyncRequest.STATUS_DONE)
        self.assertEqual(other_request.status, SyncRequest.STATUS_PENDING)

    def test_images_sync_request_cleaned_for_local_instance(self):
        media = baker.make(
            Media,
            multi_tenant_company=self.multi_tenant_company,
        )
        through = MediaProductThrough.objects.create(
            product=self.product,
            media=media,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_assoc = MagentoImageProductAssociation.objects.create(
            local_instance=through,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            multi_tenant_company=self.multi_tenant_company,
        )

        sync_request = self._create_sync_request(
            sync_type=SyncRequest.TYPE_IMAGES,
            task_kwargs={"local_instance_id": through.id},
        )
        other_request = self._create_sync_request(
            sync_type=SyncRequest.TYPE_IMAGES,
            task_kwargs={"local_instance_id": through.id + 1},
        )

        factory = MagentoMediaProductThroughDeleteFactory(
            self.sales_channel,
            remote_product=self.remote_product,
            local_instance=through,
            remote_instance=remote_assoc,
        )
        with patch.object(factory, "delete_remote", return_value=SimpleNamespace()), patch.object(
            factory, "serialize_response", return_value={}
        ):
            factory.run()

        sync_request.refresh_from_db()
        other_request.refresh_from_db()
        self.assertEqual(sync_request.status, SyncRequest.STATUS_DONE)
        self.assertEqual(other_request.status, SyncRequest.STATUS_PENDING)
