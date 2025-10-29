import json
from unittest.mock import Mock, patch

from django.db import connection
from model_bakery import baker

from core.tests import TransactionTestCase
from products.product_types import SIMPLE
from sales_channels.factories.gpt.product_feed import SalesChannelGptProductFeedFactory
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.models import RemoteProduct, SalesChannel, SalesChannelGptFeed


class SalesChannelGptProductFeedFactoryTests(TransactionTestCase):

    def setUp(self):
        super().setUp()
        self.connect_patcher = patch(
            "sales_channels.models.sales_channels.SalesChannel.connect",
            autospec=True,
            return_value=None,
        )
        self.connect_patcher.start()
        self.addCleanup(self.connect_patcher.stop)
        self.channel: SalesChannel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://channel.example.com",
            gpt_enable=True,
            gpt_seller_name="Acme",
            gpt_return_policy="https://example.com/returns",
            gpt_return_window=30,
            gpt_seller_privacy_policy="https://example.com/privacy",
            gpt_seller_tos="https://example.com/tos",
            gpt_seller_url="https://example.com/seller",
        )
        self.view = baker.make(
            "sales_channels.SalesChannelView",
            sales_channel=self.channel,
            multi_tenant_company=self.multi_tenant_company,
            url="https://channel.example.com",
        )

    def _build_remote_product(self, *, sku: str, required_feed_sync: bool = True):
        product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            sku=sku,
            type=SIMPLE,
        )
        remote_product = baker.make(
            "sales_channels.RemoteProduct",
            sales_channel=self.channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=product,
            remote_sku=f"REMOTE-{sku}",
        )
        baker.make(
            "sales_channels.SalesChannelViewAssign",
            product=product,
            sales_channel=self.channel,
            sales_channel_view=self.view,
            remote_product=remote_product,
            multi_tenant_company=self.multi_tenant_company,
        )
        if required_feed_sync is False:
            RemoteProduct.objects.filter(pk=remote_product.pk).update(required_feed_sync=False)
            remote_product.refresh_from_db()
        return remote_product

    def test_incremental_updates_feed_and_file(self):
        remote_product = self._build_remote_product(sku="SKU-1")
        payload = {"id": "SKU-1", "title": "Updated"}
        factory_mock = Mock()
        factory_mock.build.return_value = [payload]

        with patch(
            "sales_channels.factories.gpt.product_feed.ProductFeedPayloadFactory",
            return_value=factory_mock,
        ) as factory_cls:
            SalesChannelGptProductFeedFactory(sync_all=False).run()

        factory_cls.assert_called_once()
        remote_product.refresh_from_db()
        self.assertFalse(remote_product.required_feed_sync)

        feed = SalesChannelGptFeed.objects.get(sales_channel=self.channel)
        self.assertEqual(feed.items, [payload])
        self.assertIsNotNone(feed.file)
        feed.file.open("r")
        try:
            data = json.load(feed.file)
        finally:
            feed.file.close()
        self.assertEqual(data, [payload])
        self.assertIsNotNone(feed.last_synced_at)

    def test_incremental_removes_stale_entries(self):
        remote_product = self._build_remote_product(sku="SKU-2")
        feed = self.channel.ensure_gpt_feed()
        feed.items = [{"id": "SKU-2", "title": "Old"}]
        feed.save(update_fields=["items"])
        factory_mock = Mock()
        factory_mock.build.return_value = []

        with patch(
            "sales_channels.factories.gpt.product_feed.ProductFeedPayloadFactory",
            return_value=factory_mock,
        ):
            SalesChannelGptProductFeedFactory(sync_all=False).run()

        remote_product.refresh_from_db()
        self.assertFalse(remote_product.required_feed_sync)
        feed.refresh_from_db()
        self.assertEqual(feed.items, [])

    def test_sync_all_refreshes_even_without_flags(self):
        remote_product = self._build_remote_product(sku="SKU-3")
        RemoteProduct.objects.filter(pk=remote_product.pk).update(required_feed_sync=False)
        remote_product.refresh_from_db()
        feed = self.channel.ensure_gpt_feed()
        feed.items = [{"id": "OTHER", "title": "Other"}]
        feed.save(update_fields=["items"])
        payload = {"id": "SKU-3", "title": "Fresh"}
        factory_mock = Mock()
        factory_mock.build.return_value = [payload]

        with patch(
            "sales_channels.factories.gpt.product_feed.ProductFeedPayloadFactory",
            return_value=factory_mock,
        ):
            SalesChannelGptProductFeedFactory(sync_all=True).run()

        remote_product.refresh_from_db()
        self.assertFalse(remote_product.required_feed_sync)
        feed.refresh_from_db()
        self.assertEqual(feed.items, [payload])

    def test_deleted_sku_removes_entry(self):
        self._build_remote_product(sku="SKU-DEL")
        feed = self.channel.ensure_gpt_feed()
        feed.items = [
            {"id": "SKU-DEL", "title": "Remove"},
            {"id": "KEEP", "title": "Keep"},
        ]
        feed.save(update_fields=["items"])

        SalesChannelGptProductFeedFactory(
            sync_all=False,
            sales_channel_id=self.channel.id,
            deleted_sku="SKU-DEL",
        ).run()

        feed.refresh_from_db()
        self.assertEqual(feed.items, [{"id": "KEEP", "title": "Keep"}])
        self.assertIsNotNone(feed.last_synced_at)
