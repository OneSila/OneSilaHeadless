from types import SimpleNamespace
from unittest.mock import patch

from model_bakery import baker

from core.tests import TransactionTestCase
from media.models import MediaProductThrough, Media
from products.models import Product, ProductTranslation
from properties.models import Property, ProductProperty, ProductPropertyTextTranslation
from sales_channels.integrations.amazon.factories.products.content import (
    AmazonProductContentUpdateFactory,
)
from sales_channels.integrations.amazon.factories.prices.prices import (
    AmazonPriceUpdateFactory,
)
from sales_channels.integrations.amazon.factories.products.products import (
    AmazonProductUpdateFactory,
)
from sales_channels.integrations.amazon.factories.properties.properties import (
    AmazonProductPropertyDeleteFactory,
)
from sales_channels.integrations.amazon.factories.products.images import (
    AmazonMediaProductThroughDeleteFactory,
)
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonProduct,
    AmazonProductContent,
    AmazonPrice,
    AmazonProperty,
    AmazonProductProperty,
    AmazonImageProductAssociation,
)
from sales_channels.models import SalesChannelViewAssign, SyncRequest


class AmazonSyncRequestCleanupTests(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self._connect_patcher = patch.object(
            AmazonSalesChannel,
            "connect",
            return_value=None,
        )
        self._connect_patcher.start()
        self.addCleanup(self._connect_patcher.stop)

        self.sales_channel = AmazonSalesChannel.objects.create(
            hostname="amazon.example.com",
            active=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.view = AmazonSalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            name="US",
            remote_id="US",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = baker.make(
            AmazonProduct,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            multi_tenant_company=self.multi_tenant_company,
        )
        if not self.remote_product.product_owner:
            self.remote_product.product_owner = True
            self.remote_product.save(update_fields=["product_owner"])
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

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client")
    def test_content_sync_request_cleaned(self, _get_client):
        ProductTranslation.objects.create(
            product=self.product,
            language="en",
            name="Name",
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_content = AmazonProductContent()
        remote_content.remote_product = self.remote_product
        remote_content.sales_channel = self.sales_channel
        remote_content.multi_tenant_company = self.multi_tenant_company
        remote_content.save()
        sync_request = self._create_sync_request(sync_type=SyncRequest.TYPE_CONTENT)

        factory = AmazonProductContentUpdateFactory(
            self.sales_channel,
            self.product,
            remote_product=self.remote_product,
            view=self.view,
            remote_instance=remote_content,
            language="en",
        )
        with patch.object(factory, "update_remote", return_value=SimpleNamespace()), patch.object(
            factory, "serialize_response", return_value={}
        ), patch.object(factory, "needs_update", return_value=True):
            factory.run()

        sync_request.refresh_from_db()
        self.assertEqual(sync_request.status, SyncRequest.STATUS_DONE)

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client")
    def test_price_sync_request_cleaned(self, _get_client):
        AmazonPrice.objects.create(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        sync_request = self._create_sync_request(sync_type=SyncRequest.TYPE_PRICE)

        factory = AmazonPriceUpdateFactory(
            self.sales_channel,
            self.product,
            remote_product=self.remote_product,
            view=self.view,
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

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client")
    def test_product_sync_request_cleaned(self, _get_client):
        sync_request = self._create_sync_request(sync_type=SyncRequest.TYPE_PRODUCT)

        factory = AmazonProductUpdateFactory(
            self.sales_channel,
            self.product,
            remote_instance=self.remote_product,
            view=self.view,
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

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client")
    def test_property_sync_request_cleaned_for_local_instance(self, _get_client):
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
        remote_property = AmazonProperty.objects.create(
            local_instance=prop,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_product_property = AmazonProductProperty.objects.create(
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

        factory = AmazonProductPropertyDeleteFactory(
            self.sales_channel,
            product_property,
            remote_product=self.remote_product,
            view=self.view,
            remote_property=remote_property,
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

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client")
    def test_images_sync_request_cleaned_for_local_instance(self, _get_client):
        media = baker.make(
            Media,
            multi_tenant_company=self.multi_tenant_company,
        )
        through = MediaProductThrough.objects.create(
            product=self.product,
            media=media,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_assoc = AmazonImageProductAssociation.objects.create(
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

        factory = AmazonMediaProductThroughDeleteFactory(
            self.sales_channel,
            remote_product=self.remote_product,
            local_instance=through,
            remote_instance=remote_assoc,
            view=self.view,
        )
        with patch.object(factory, "delete_remote", return_value=SimpleNamespace()), patch.object(
            factory, "serialize_response", return_value={}
        ):
            factory.run()

        sync_request.refresh_from_db()
        other_request.refresh_from_db()
        self.assertEqual(sync_request.status, SyncRequest.STATUS_DONE)
        self.assertEqual(other_request.status, SyncRequest.STATUS_PENDING)
