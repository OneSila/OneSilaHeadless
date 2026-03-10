from unittest.mock import patch

from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.models import MiraklSalesChannel
from sales_channels.integrations.shopify.models import ShopifySalesChannel
from sales_channels.signals import refresh_website_pull_models


class MiraklMetadataReceiverTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )

    @patch("sales_channels.integrations.mirakl.factories.sales_channels.MiraklRemoteCurrencyPullFactory")
    @patch("sales_channels.integrations.mirakl.factories.sales_channels.MiraklRemoteLanguagePullFactory")
    @patch("sales_channels.integrations.mirakl.factories.sales_channels.MiraklSalesChannelViewPullFactory")
    def test_refresh_signal_runs_three_metadata_factories(
        self,
        view_factory_cls,
        language_factory_cls,
        currency_factory_cls,
    ):
        refresh_website_pull_models.send(
            sender=self.sales_channel.__class__,
            instance=self.sales_channel,
        )

        view_factory_cls.assert_called_once_with(sales_channel=self.sales_channel)
        language_factory_cls.assert_called_once_with(sales_channel=self.sales_channel)
        currency_factory_cls.assert_called_once_with(sales_channel=self.sales_channel)
        view_factory_cls.return_value.run.assert_called_once_with()
        language_factory_cls.return_value.run.assert_called_once_with()
        currency_factory_cls.return_value.run.assert_called_once_with()

    @patch("sales_channels.integrations.mirakl.factories.sales_channels.MiraklRemoteCurrencyPullFactory")
    @patch("sales_channels.integrations.mirakl.factories.sales_channels.MiraklRemoteLanguagePullFactory")
    @patch("sales_channels.integrations.mirakl.factories.sales_channels.MiraklSalesChannelViewPullFactory")
    def test_non_mirakl_channel_is_ignored(
        self,
        view_factory_cls,
        language_factory_cls,
        currency_factory_cls,
    ):
        shopify_channel = baker.make(
            ShopifySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://shop.example.com",
        )

        refresh_website_pull_models.send(
            sender=shopify_channel.__class__,
            instance=shopify_channel,
        )

        view_factory_cls.assert_not_called()
        language_factory_cls.assert_not_called()
        currency_factory_cls.assert_not_called()

