from unittest.mock import patch

from .mixins import TestCaseEbayMixin
from sales_channels.integrations.ebay.factories.sales_channels import (
    EbayRemoteCurrencyPullFactory,
    EbayRemoteLanguagePullFactory,
    EbaySalesChannelViewPullFactory,
)


class TestEbayPullFactories(TestCaseEbayMixin):
    def test_pull_currency(self):
        factory = EbayRemoteCurrencyPullFactory(sales_channel=self.sales_channel)
        factory.run()
        currencies = factory.remote_model_class.objects.filter(sales_channel=self.sales_channel)
        self.assertTrue(currencies.exists())
        codes = {c.remote_code for c in currencies}
        self.assertEqual(len(codes), currencies.count())

    def test_pull_view(self):
        fulfillment = [{'label': 'Fulfillment', 'value': 'f1'}]
        payment = [{'label': 'Payment', 'value': 'p1'}]
        return_policies = [{'label': 'Return', 'value': 'r1'}]
        locations = [{'label': '123 High Street, London', 'value': 'loc1'}]

        with patch.object(EbaySalesChannelViewPullFactory, 'get_subscription_marketplace_ids', return_value=['EBAY_GB']), \
                patch.object(EbaySalesChannelViewPullFactory, '_get_fulfillment_policy_choices', return_value=fulfillment), \
                patch.object(EbaySalesChannelViewPullFactory, '_get_payment_policy_choices', return_value=payment), \
                patch.object(EbaySalesChannelViewPullFactory, '_get_return_policy_choices', return_value=return_policies), \
                patch.object(EbaySalesChannelViewPullFactory, '_get_merchant_location_choices', return_value=locations), \
                patch.object(EbaySalesChannelViewPullFactory, '_get_default_category_tree_id', return_value='3'), \
                patch.object(EbaySalesChannelViewPullFactory, 'get_default_marketplace_id', return_value='EBAY_GB'):
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

    def test_pull_language(self):
        factory = EbayRemoteLanguagePullFactory(sales_channel=self.sales_channel)
        factory.run()
        languages = factory.remote_model_class.objects.filter(sales_channel=self.sales_channel)
        self.assertTrue(languages.exists())
        from sales_channels.integrations.ebay.factories.sales_channels.languages import _map_local_language
        for lang in languages:
            self.assertEqual(lang.local_instance, _map_local_language(lang.remote_code))
