from unittest.mock import PropertyMock, patch

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.admin import MiraklSalesChannelFeedAdmin
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelFeed
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklSalesChannelFeedAdminTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        self.model_admin = MiraklSalesChannelFeedAdmin(MiraklSalesChannelFeed, AdminSite())

    def test_mirakl_sales_channel_feed_is_registered_in_admin(self):
        self.assertIn(MiraklSalesChannelFeed, admin.site._registry)

    def test_file_link_returns_dash_without_file_url(self):
        with patch.object(
            MiraklSalesChannelFeed,
            "file_url",
            new_callable=PropertyMock,
            return_value=None,
        ):
            self.assertEqual(self.model_admin.file_link(self.feed), "-")

    def test_file_link_returns_anchor_with_file_url(self):
        with patch.object(
            MiraklSalesChannelFeed,
            "file_url",
            new_callable=PropertyMock,
            return_value="https://example.com/feed.csv",
        ):
            file_link = self.model_admin.file_link(self.feed)

        self.assertIn('href="https://example.com/feed.csv"', file_link)
        self.assertIn("Open feed file", file_link)
