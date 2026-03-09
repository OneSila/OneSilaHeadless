from unittest.mock import MagicMock, patch

from .mixins import TestCaseEbayMixin
from sales_channels.integrations.ebay.factories.sales_channels import (
    EbayRemoteCurrencyPullFactory,
    EbayRemoteLanguagePullFactory,
    EbaySalesChannelViewPullFactory,
    EbayStoreCategoryPullFactory,
)
from sales_channels.integrations.ebay.models import EbayStoreCategory


class TestEbayPullFactories(TestCaseEbayMixin):
    @patch("sales_channels.integrations.ebay.factories.mixins.GetEbayAPIMixin.get_api", return_value=MagicMock())
    def test_pull_currency(self, _mock_get_api):
        currency_reference = {
            "EBAY_GB": ("United Kingdom", {"en_GB": ["https://www.ebay.co.uk"]}),
            "EBAY_DE": ("Germany", {"de_DE": ["https://www.ebay.de"]}),
        }
        marketplace_ids = list(currency_reference.keys())
        currency_lookup = {
            "EBAY_GB": {"default_currency": {"code": "GBP"}},
            "EBAY_DE": {"default_currency": {"code": "EUR"}},
        }

        with patch.object(EbayRemoteCurrencyPullFactory, "get_marketplace_ids", return_value=marketplace_ids), \
                patch.object(EbayRemoteCurrencyPullFactory, "marketplace_reference", return_value=currency_reference), \
                patch.object(
                    EbayRemoteCurrencyPullFactory,
                    "get_marketplace_currencies",
                    side_effect=lambda marketplace_id: currency_lookup[marketplace_id],
                ):
            factory = EbayRemoteCurrencyPullFactory(sales_channel=self.sales_channel)
            factory.run()
        currencies = factory.remote_model_class.objects.filter(sales_channel=self.sales_channel)
        self.assertTrue(currencies.exists())
        codes = {c.remote_code for c in currencies}
        self.assertEqual(len(codes), currencies.count())

    @patch("sales_channels.integrations.ebay.factories.mixins.GetEbayAPIMixin.get_api", return_value=MagicMock())
    def test_pull_view(self, _mock_get_api):
        fulfillment = [{'label': 'Fulfillment', 'value': 'f1'}]
        payment = [{'label': 'Payment', 'value': 'p1'}]
        return_policies = [{'label': 'Return', 'value': 'r1'}]
        locations = [{'label': '123 High Street, London', 'value': 'loc1'}]
        marketplace_reference = {
            'EBAY_GB': ('United Kingdom', {'en_GB': ['https://www.ebay.co.uk']}),
        }

        with patch.object(EbaySalesChannelViewPullFactory, 'get_subscription_marketplace_ids', return_value=['EBAY_GB']), \
                patch.object(EbaySalesChannelViewPullFactory, '_get_fulfillment_policy_choices', return_value=fulfillment), \
                patch.object(EbaySalesChannelViewPullFactory, '_get_payment_policy_choices', return_value=payment), \
                patch.object(EbaySalesChannelViewPullFactory, '_get_return_policy_choices', return_value=return_policies), \
                patch.object(EbaySalesChannelViewPullFactory, '_get_merchant_location_choices', return_value=locations), \
                patch.object(EbaySalesChannelViewPullFactory, '_get_default_category_tree_id', return_value='3'), \
                patch.object(EbaySalesChannelViewPullFactory, 'get_default_marketplace_id', return_value='EBAY_GB'), \
                patch.object(EbaySalesChannelViewPullFactory, 'marketplace_reference', return_value=marketplace_reference), \
                patch.object(EbaySalesChannelViewPullFactory, 'get_marketplace_ids', return_value=['EBAY_GB']):
            factory = EbaySalesChannelViewPullFactory(sales_channel=self.sales_channel)
            factory.run()

        queryset = factory.remote_model_class.objects.filter(sales_channel=self.sales_channel)
        self.assertTrue(queryset.exists())
        view = queryset.get()
        self.assertEqual(view.fulfillment_policy_choices, fulfillment)
        self.assertEqual(view.payment_policy_choices, payment)
        self.assertEqual(view.return_policy_choices, return_policies)
        self.assertEqual(view.merchant_location_choices, locations)
        self.assertEqual(view.default_category_tree_id, '3')

    @patch("sales_channels.integrations.ebay.factories.mixins.GetEbayAPIMixin.get_api", return_value=MagicMock())
    def test_pull_language(self, _mock_get_api):
        marketplace_reference = {
            'EBAY_GB': ('United Kingdom', {'en_GB': ['https://www.ebay.co.uk'], 'en_US': ['https://www.ebay.com']}),
        }

        with patch.object(EbayRemoteLanguagePullFactory, 'get_marketplace_ids', return_value=['EBAY_GB']), \
                patch.object(EbayRemoteLanguagePullFactory, 'marketplace_reference', return_value=marketplace_reference):
            factory = EbayRemoteLanguagePullFactory(sales_channel=self.sales_channel)
            factory.run()
        languages = factory.remote_model_class.objects.filter(sales_channel=self.sales_channel)
        self.assertTrue(languages.exists())
        from sales_channels.integrations.ebay.factories.sales_channels.languages import _map_local_language
        for lang in languages:
            self.assertEqual(lang.local_instance, _map_local_language(lang.remote_code))

    @patch("sales_channels.integrations.ebay.factories.mixins.GetEbayAPIMixin.get_api", return_value=MagicMock())
    def test_pull_store_categories_creates_hierarchy(self, _mock_get_api):
        payload = {
            "storeCategories": [
                {
                    "categoryId": "10",
                    "categoryName": "Fashion",
                    "order": 0,
                    "level": 1,
                    "childrenCategories": [
                        {
                            "categoryId": "11",
                            "categoryName": "Men",
                            "order": 0,
                            "level": 2,
                        }
                    ],
                },
                {
                    "categoryId": "20",
                    "categoryName": "Other",
                    "order": 1,
                    "level": 1,
                },
            ]
        }

        with patch.object(EbayStoreCategoryPullFactory, "get_store_categories", return_value=payload):
            factory = EbayStoreCategoryPullFactory(sales_channel=self.sales_channel)
            factory.run()

        categories = EbayStoreCategory.objects.filter(sales_channel=self.sales_channel)
        self.assertEqual(categories.count(), 3)

        fashion = categories.get(remote_id="10")
        men = categories.get(remote_id="11")
        other = categories.get(remote_id="20")

        self.assertEqual(men.parent_id, fashion.id)
        self.assertEqual(men.full_path, "/Fashion/Men")
        self.assertTrue(men.is_leaf)
        self.assertIsNone(other.parent)
        self.assertEqual(other.full_path, "/Other")

    @patch("sales_channels.integrations.ebay.factories.mixins.GetEbayAPIMixin.get_api", return_value=MagicMock())
    def test_pull_store_categories_updates_and_deletes(self, _mock_get_api):
        first_payload = {
            "storeCategories": [
                {
                    "categoryId": "10",
                    "categoryName": "Fashion",
                    "order": 0,
                    "level": 1,
                    "childrenCategories": [
                        {
                            "categoryId": "11",
                            "categoryName": "Men",
                            "order": 0,
                            "level": 2,
                        }
                    ],
                },
                {
                    "categoryId": "99",
                    "categoryName": "Legacy",
                    "order": 1,
                    "level": 1,
                },
            ]
        }
        second_payload = {
            "storeCategories": [
                {
                    "categoryId": "10",
                    "categoryName": "Fashion",
                    "order": 0,
                    "level": 1,
                    "childrenCategories": [
                        {
                            "categoryId": "11",
                            "categoryName": "Menswear",
                            "order": 2,
                            "level": 2,
                            "childrenCategories": [
                                {
                                    "categoryId": "12",
                                    "categoryName": "Shirts",
                                    "order": 0,
                                    "level": 3,
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        with patch.object(EbayStoreCategoryPullFactory, "get_store_categories", return_value=first_payload):
            factory = EbayStoreCategoryPullFactory(sales_channel=self.sales_channel)
            factory.run()

        existing = EbayStoreCategory.objects.get(sales_channel=self.sales_channel, remote_id="11")
        existing_pk = existing.pk

        with patch.object(EbayStoreCategoryPullFactory, "get_store_categories", return_value=second_payload):
            factory = EbayStoreCategoryPullFactory(sales_channel=self.sales_channel)
            factory.run()

        self.assertFalse(
            EbayStoreCategory.objects.filter(sales_channel=self.sales_channel, remote_id="99").exists()
        )

        updated = EbayStoreCategory.objects.get(sales_channel=self.sales_channel, remote_id="11")
        self.assertEqual(updated.pk, existing_pk)
        self.assertEqual(updated.name, "Menswear")
        self.assertFalse(updated.is_leaf)
        self.assertEqual(updated.full_path, "/Fashion/Menswear")

        shirts = EbayStoreCategory.objects.get(sales_channel=self.sales_channel, remote_id="12")
        self.assertEqual(shirts.parent_id, updated.id)
        self.assertTrue(shirts.is_leaf)
        self.assertEqual(shirts.full_path, "/Fashion/Menswear/Shirts")
