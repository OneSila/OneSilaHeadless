import json
from unittest.mock import Mock, patch

from django.db import connection
from model_bakery import baker

from core.tests import TestCase
from products.product_types import SIMPLE
from sales_channels.factories.cpt.product_feed import SalesChannelGptProductFeedFactory
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.models import RemoteProduct, SalesChannel


class SalesChannelGptProductFeedFactoryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_column(SalesChannel, "gpt_feed_json", "TEXT DEFAULT '[]'")
        cls._ensure_column(SalesChannel, "gpt_feed_file", "TEXT")
        cls._ensure_column(RemoteProduct, "required_feed_sync", "INTEGER DEFAULT 0 NOT NULL")

    @staticmethod
    def _ensure_column(model, field_name: str, sql_definition: str) -> None:
        field = model._meta.get_field(field_name)
        table = model._meta.db_table
        with connection.cursor() as cursor:
            column_names = {
                column.name for column in connection.introspection.get_table_description(cursor, table)
            }
        if field.column in column_names:
            return
        with connection.cursor() as cursor:
            cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN {field.column} {sql_definition}"
            )

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
            "sales_channels.factories.cpt.product_feed.ProductFeedPayloadFactory",
            return_value=factory_mock,
        ) as factory_cls:
            SalesChannelGptProductFeedFactory(sync_all=False).work()

        factory_cls.assert_called_once()
        remote_product.refresh_from_db()
        self.assertFalse(remote_product.required_feed_sync)

        self.channel.refresh_from_db()
        self.assertEqual(self.channel.gpt_feed_json, [payload])
        self.assertIsNotNone(self.channel.gpt_feed_file)
        self.channel.gpt_feed_file.open("r")
        try:
            data = json.load(self.channel.gpt_feed_file)
        finally:
            self.channel.gpt_feed_file.close()
        self.assertEqual(data, [payload])

    def test_incremental_removes_stale_entries(self):
        remote_product = self._build_remote_product(sku="SKU-2")
        self.channel.gpt_feed_json = [{"id": "SKU-2", "title": "Old"}]
        self.channel.save(update_fields=["gpt_feed_json"])
        factory_mock = Mock()
        factory_mock.build.return_value = []

        with patch(
            "sales_channels.factories.cpt.product_feed.ProductFeedPayloadFactory",
            return_value=factory_mock,
        ):
            SalesChannelGptProductFeedFactory(sync_all=False).work()

        remote_product.refresh_from_db()
        self.assertFalse(remote_product.required_feed_sync)
        self.channel.refresh_from_db()
        self.assertEqual(self.channel.gpt_feed_json, [])

    def test_sync_all_refreshes_even_without_flags(self):
        remote_product = self._build_remote_product(sku="SKU-3")
        RemoteProduct.objects.filter(pk=remote_product.pk).update(required_feed_sync=False)
        remote_product.refresh_from_db()
        self.channel.gpt_feed_json = [{"id": "OTHER", "title": "Other"}]
        self.channel.save(update_fields=["gpt_feed_json"])
        payload = {"id": "SKU-3", "title": "Fresh"}
        factory_mock = Mock()
        factory_mock.build.return_value = [payload]

        with patch(
            "sales_channels.factories.cpt.product_feed.ProductFeedPayloadFactory",
            return_value=factory_mock,
        ):
            SalesChannelGptProductFeedFactory(sync_all=True).work()

        remote_product.refresh_from_db()
        self.assertFalse(remote_product.required_feed_sync)
        self.channel.refresh_from_db()
        self.assertEqual(self.channel.gpt_feed_json, [payload])
