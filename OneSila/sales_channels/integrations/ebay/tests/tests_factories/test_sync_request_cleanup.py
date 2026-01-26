from types import SimpleNamespace
from unittest.mock import patch

from model_bakery import baker

from media.models import MediaProductThrough, Media
from products.models import Product, ProductTranslation
from properties.models import Property, ProductProperty, ProductPropertyTextTranslation
from sales_channels.integrations.ebay.factories.products.content import (
    EbayProductContentUpdateFactory,
)
from sales_channels.integrations.ebay.factories.prices.prices import (
    EbayPriceUpdateFactory,
)
from sales_channels.integrations.ebay.factories.products.products import (
    EbayProductUpdateFactory,
)
from sales_channels.integrations.ebay.factories.products.properties import (
    EbayProductPropertyDeleteFactory,
)
from sales_channels.integrations.ebay.factories.products.images import (
    EbayMediaProductThroughDeleteFactory,
)
from sales_channels.integrations.ebay.models import (
    EbayProduct,
    EbaySalesChannelView,
    EbayProductContent,
    EbayPrice,
    EbayProperty,
    EbayProductProperty,
    EbayMediaThroughProduct,
)
from sales_channels.integrations.ebay.tests.tests_factories.mixins import (
    TestCaseEbayMixin,
)
from sales_channels.models import SalesChannelViewAssign, SyncRequest


class EbaySyncRequestCleanupTests(TestCaseEbayMixin):
    def setUp(self):
        super().setUp()
        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="EBAY_US",
            name="US",
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = baker.make(
            EbayProduct,
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

    @patch("sales_channels.integrations.ebay.factories.products.mixins.GetEbayAPIMixin.get_api")
    def test_content_sync_request_cleaned(self, _get_api):
        ProductTranslation.objects.create(
            product=self.product,
            language="en",
            name="Name",
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_content = EbayProductContent.objects.create(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        sync_request = self._create_sync_request(sync_type=SyncRequest.TYPE_CONTENT)

        factory = EbayProductContentUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            remote_instance=remote_content,
            view=self.view,
            language="en",
        )
        with patch.object(factory, "update_remote", return_value=SimpleNamespace()), patch.object(
            factory, "serialize_response", return_value={}
        ), patch.object(factory, "needs_update", return_value=True):
            factory.run()

        sync_request.refresh_from_db()
        self.assertEqual(sync_request.status, SyncRequest.STATUS_DONE)

    @patch("sales_channels.integrations.ebay.factories.products.mixins.GetEbayAPIMixin.get_api")
    def test_price_sync_request_cleaned(self, _get_api):
        EbayPrice.objects.create(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        sync_request = self._create_sync_request(sync_type=SyncRequest.TYPE_PRICE)

        factory = EbayPriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
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

    @patch("sales_channels.integrations.ebay.factories.products.mixins.GetEbayAPIMixin.get_api")
    def test_product_sync_request_cleaned(self, _get_api):
        sync_request = self._create_sync_request(sync_type=SyncRequest.TYPE_PRODUCT)

        factory = EbayProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
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

    @patch("sales_channels.integrations.ebay.factories.products.mixins.GetEbayAPIMixin.get_api")
    def test_property_sync_request_cleaned_for_local_instance(self, _get_api):
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
        remote_property = EbayProperty.objects.create(
            local_instance=prop,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            marketplace=self.view,
        )
        remote_product_property = EbayProductProperty.objects.create(
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

        factory = EbayProductPropertyDeleteFactory(
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            remote_instance=remote_product_property,
            view=self.view,
            remote_property=remote_property,
        )
        with patch.object(factory, "delete_remote", return_value=SimpleNamespace()), patch.object(
            factory, "serialize_response", return_value={}
        ):
            factory.run()

        sync_request.refresh_from_db()
        other_request.refresh_from_db()
        self.assertEqual(sync_request.status, SyncRequest.STATUS_DONE)
        self.assertEqual(other_request.status, SyncRequest.STATUS_PENDING)

    @patch("sales_channels.integrations.ebay.factories.products.mixins.GetEbayAPIMixin.get_api")
    def test_images_sync_request_cleaned_for_local_instance(self, _get_api):
        media = baker.make(
            Media,
            multi_tenant_company=self.multi_tenant_company,
        )
        through = MediaProductThrough.objects.create(
            product=self.product,
            media=media,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_assoc = EbayMediaThroughProduct.objects.create(
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

        factory = EbayMediaProductThroughDeleteFactory(
            sales_channel=self.sales_channel,
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
