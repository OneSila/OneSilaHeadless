from unittest.mock import patch

from model_bakery import baker

from core.tests import TestCase
from properties.models import Property, PropertySelectValue
from sales_channels.integrations.mirakl.models import (
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklSalesChannel,
)
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


class MiraklPropertySelectValueReceiverTests(TestCase):
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
        self.local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        self.local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=self.local_property,
        )
        self.remote_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="color",
            type=Property.TYPES.SELECT,
            local_instance=self.local_property,
        )

    @patch("sales_channels.integrations.mirakl.factories.sync.MiraklPropertySelectValueSiblingMappingFactory")
    def test_post_create_runs_propagation_for_mapped_select_value(self, sync_factory_cls):
        remote_value = baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            code="purple",
            value="Purple",
            local_instance=self.local_value,
        )

        sync_factory_cls.assert_called_once_with(remote_select_value=remote_value)
        sync_factory_cls.return_value.run.assert_called_once_with()

    @patch("sales_channels.integrations.mirakl.factories.sync.MiraklPropertySelectValueSiblingMappingFactory")
    def test_post_update_runs_propagation_only_when_local_mapping_changes(self, sync_factory_cls):
        remote_value = baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            code="purple",
            value="Purple",
            local_instance=None,
        )
        sync_factory_cls.reset_mock()

        remote_value.local_instance = self.local_value
        remote_value.save(update_fields=["local_instance"])

        sync_factory_cls.assert_called_once_with(remote_select_value=remote_value)
        sync_factory_cls.return_value.run.assert_called_once_with()

    @patch("sales_channels.integrations.mirakl.factories.sync.MiraklPropertySelectValueSiblingMappingFactory")
    def test_post_update_ignores_non_mapping_updates(self, sync_factory_cls):
        remote_value = baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            code="purple",
            value="Purple",
            local_instance=None,
        )
        sync_factory_cls.reset_mock()

        remote_value.value = "Purple Updated"
        remote_value.save(update_fields=["value"])

        sync_factory_cls.assert_not_called()
