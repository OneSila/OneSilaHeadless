from unittest.mock import PropertyMock, patch

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.admin import (
    MiraklPropertyAdmin,
    MiraklSalesChannelFeedAdmin,
    set_mirakl_properties_as_bullet_point,
    set_mirakl_properties_as_unit,
)
from sales_channels.integrations.mirakl.models import MiraklProperty, MiraklSalesChannel, MiraklSalesChannelFeed
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

    def test_set_ready_to_render_action_updates_selected_feeds(self):
        ready_feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            status=MiraklSalesChannelFeed.STATUS_READY_TO_RENDER,
        )
        pending_feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            status=MiraklSalesChannelFeed.STATUS_PENDING,
        )
        queryset = MiraklSalesChannelFeed.objects.filter(id__in=[ready_feed.id, pending_feed.id]).order_by("id")

        with patch.object(self.model_admin, "message_user") as message_user_mock:
            self.model_admin.set_ready_to_render(request=None, queryset=queryset)

        ready_feed.refresh_from_db()
        pending_feed.refresh_from_db()
        self.assertEqual(ready_feed.status, MiraklSalesChannelFeed.STATUS_READY_TO_RENDER)
        self.assertEqual(pending_feed.status, MiraklSalesChannelFeed.STATUS_READY_TO_RENDER)
        message_user_mock.assert_called_once_with(
            None,
            "Marked 1 Mirakl feeds as ready to render.",
        )


class MiraklPropertyAdminTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.model_admin = MiraklPropertyAdmin(MiraklProperty, AdminSite())

    def test_search_results_match_role_type_from_raw_data(self):
        matching_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="product_identifier",
            raw_data={
                "roles": [
                    {"type": "UNIQUE_IDENTIFIER"},
                    {"type": "TITLE"},
                ],
            },
        )
        baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="product_title",
            raw_data={
                "roles": [
                    {"type": "TITLE"},
                ],
            },
        )

        queryset, use_distinct = self.model_admin.get_search_results(
            request=None,
            queryset=MiraklProperty.objects.all(),
            search_term="UNIQUE_IDENTIFIER",
        )

        self.assertTrue(use_distinct)
        self.assertEqual(list(queryset), [matching_property])

    def test_set_as_unit_action_updates_selected_properties(self):
        first_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            representation_type=MiraklProperty.REPRESENTATION_PROPERTY,
        )
        second_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            representation_type=MiraklProperty.REPRESENTATION_IMAGE,
        )
        queryset = MiraklProperty.objects.filter(id__in=[first_property.id, second_property.id]).order_by("id")

        with patch.object(self.model_admin, "message_user") as message_user_mock:
            set_mirakl_properties_as_unit(self.model_admin, request=None, queryset=queryset)

        first_property.refresh_from_db()
        second_property.refresh_from_db()
        self.assertEqual(first_property.representation_type, MiraklProperty.REPRESENTATION_UNIT)
        self.assertEqual(second_property.representation_type, MiraklProperty.REPRESENTATION_UNIT)
        message_user_mock.assert_called_once_with(
            None,
            "Set 2 Mirakl properties to unit.",
        )

    def test_set_as_bullet_point_action_updates_selected_properties(self):
        remote_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            representation_type=MiraklProperty.REPRESENTATION_PROPERTY,
        )

        with patch.object(self.model_admin, "message_user") as message_user_mock:
            set_mirakl_properties_as_bullet_point(
                self.model_admin,
                request=None,
                queryset=MiraklProperty.objects.filter(id=remote_property.id),
            )

        remote_property.refresh_from_db()
        self.assertEqual(
            remote_property.representation_type,
            MiraklProperty.REPRESENTATION_PRODUCT_BULLET_POINT,
        )
        message_user_mock.assert_called_once_with(
            None,
            "Set 1 Mirakl properties to bullet point.",
        )
