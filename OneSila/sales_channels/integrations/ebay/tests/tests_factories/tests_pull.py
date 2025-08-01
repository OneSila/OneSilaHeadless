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
        factory = EbaySalesChannelViewPullFactory(sales_channel=self.sales_channel)
        factory.run()
        self.assertTrue(factory.remote_model_class.objects.filter(sales_channel=self.sales_channel).exists())

    def test_pull_language(self):
        factory = EbayRemoteLanguagePullFactory(sales_channel=self.sales_channel)
        factory.run()
        languages = factory.remote_model_class.objects.filter(sales_channel=self.sales_channel)
        self.assertTrue(languages.exists())
        from sales_channels.integrations.ebay.factories.sales_channels.languages import _map_local_language
        for lang in languages:
            self.assertEqual(lang.local_instance, _map_local_language(lang.remote_code))
