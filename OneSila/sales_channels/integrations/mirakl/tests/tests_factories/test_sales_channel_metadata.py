from unittest.mock import patch

from django.test import override_settings
from currencies.models import Currency
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.factories.sales_channels import (
    MiraklRemoteCurrencyPullFactory,
    MiraklRemoteLanguagePullFactory,
    MiraklSalesChannelViewPullFactory,
    ValidateMiraklCredentialsFactory,
)
from sales_channels.integrations.mirakl.models import (
    MiraklRemoteCurrency,
    MiraklRemoteLanguage,
    MiraklSalesChannel,
    MiraklSalesChannelView,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklSalesChannelMetadataFactoriesTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )

    @patch.object(ValidateMiraklCredentialsFactory, "get_platform_configuration")
    @patch.object(ValidateMiraklCredentialsFactory, "validate_credentials")
    def test_validate_credentials_stores_account_payload(
        self,
        validate_credentials_mock,
        get_platform_configuration_mock,
    ):
        validate_credentials_mock.return_value = {
            "shop_id": 123,
            "shop_name": "Demo Shop",
            "currency_iso_code": "EUR",
        }
        get_platform_configuration_mock.return_value = {
            "features": {
                "catalog": {
                    "product_import_only_on_leaf": True,
                    "list_of_multiple_values_separator": "|",
                    "product_data_validation_by_channel": True,
                },
                "offer_prices_decimals": "2",
                "operator_csv_delimiter": "SEMICOLON",
            },
        }

        ValidateMiraklCredentialsFactory(sales_channel=self.sales_channel).run()
        self.sales_channel.refresh_from_db()

        self.assertEqual(self.sales_channel.raw_data["shop_name"], "Demo Shop")
        self.assertTrue(self.sales_channel.product_import_only_on_leaf)
        self.assertEqual(self.sales_channel.list_of_multiple_values_separator, "|")
        self.assertEqual(self.sales_channel.offer_prices_decimals, 2)
        self.assertEqual(
            self.sales_channel.operator_csv_delimiter,
            MiraklSalesChannel.CSV_DELIMITER_SEMICOLON,
        )
        self.assertTrue(self.sales_channel.product_data_validation_by_channel)
        validate_credentials_mock.assert_called_once_with()
        get_platform_configuration_mock.assert_called_once_with()

    @override_settings(TESTING=False)
    @patch.object(ValidateMiraklCredentialsFactory, "apply_platform_configuration")
    @patch.object(ValidateMiraklCredentialsFactory, "get_platform_configuration")
    @patch.object(ValidateMiraklCredentialsFactory, "validate_credentials")
    def test_sales_channel_connect_validates_dirty_credentials(
        self,
        validate_credentials_mock,
        get_platform_configuration_mock,
        apply_platform_configuration_mock,
    ):
        validate_credentials_mock.return_value = {
            "shop_id": 123,
            "shop_name": "Updated Shop",
        }
        get_platform_configuration_mock.return_value = {"features": {}}

        self.sales_channel.api_key = "updated-secret-token"
        self.sales_channel.save()
        self.sales_channel.refresh_from_db()

        validate_credentials_mock.assert_called_once_with()
        get_platform_configuration_mock.assert_called_once_with()
        apply_platform_configuration_mock.assert_called_once()
        self.assertEqual(self.sales_channel.raw_data["shop_name"], "Updated Shop")

    @patch.object(MiraklSalesChannelViewPullFactory, "mirakl_get")
    def test_view_pull_creates_views(self, mirakl_get_mock):
        mirakl_get_mock.return_value = {
            "channels": [
                {"code": "FR", "label": "France", "description": "French storefront"},
                {"code": "DE", "label": "Germany", "description": "German storefront"},
            ],
        }

        MiraklSalesChannelViewPullFactory(sales_channel=self.sales_channel).run()

        self.assertEqual(
            MiraklSalesChannelView.objects.filter(sales_channel=self.sales_channel).count(),
            2,
        )
        view = MiraklSalesChannelView.objects.get(sales_channel=self.sales_channel, remote_id="FR")
        self.assertEqual(view.name, "France")
        self.assertEqual(view.description, "French storefront")

    @patch.object(MiraklRemoteLanguagePullFactory, "mirakl_get")
    def test_language_pull_maps_local_language(self, mirakl_get_mock):
        mirakl_get_mock.return_value = {
            "locales": [
                {"code": "fr_FR", "label": "French", "platform_default": True},
                {"code": "de", "label": "German"},
            ],
        }

        MiraklRemoteLanguagePullFactory(sales_channel=self.sales_channel).run()

        french = MiraklRemoteLanguage.objects.get(
            sales_channel=self.sales_channel,
            remote_code="fr_FR",
        )
        german = MiraklRemoteLanguage.objects.get(
            sales_channel=self.sales_channel,
            remote_code="de",
        )
        self.assertEqual(french.local_instance, "fr")
        self.assertEqual(german.local_instance, "de")
        self.assertTrue(french.is_default)
        self.assertFalse(german.is_default)

    @patch.object(MiraklRemoteCurrencyPullFactory, "mirakl_get")
    def test_currency_pull_marks_default_and_maps_local_currency(self, mirakl_get_mock):
        Currency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            iso_code="EUR",
            name="Euro",
            symbol="EUR",
            is_default_currency=False,
        )
        mirakl_get_mock.return_value = {
            "currencies": [
                {"code": "EUR", "label": "Euro", "platform_default": True},
                {"code": "USD", "label": "US Dollar"},
            ],
        }

        MiraklRemoteCurrencyPullFactory(sales_channel=self.sales_channel).run()

        eur = MiraklRemoteCurrency.objects.get(
            sales_channel=self.sales_channel,
            remote_code="EUR",
        )
        usd = MiraklRemoteCurrency.objects.get(
            sales_channel=self.sales_channel,
            remote_code="USD",
        )
        self.assertTrue(eur.is_default)
        self.assertEqual(eur.local_instance.iso_code, "EUR")
        self.assertFalse(usd.is_default)
