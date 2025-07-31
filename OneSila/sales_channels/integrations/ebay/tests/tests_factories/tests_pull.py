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
        self.assertTrue(factory.remote_model_class.objects.filter(sales_channel=self.sales_channel).exists())

    def test_pull_view(self):
        factory = EbaySalesChannelViewPullFactory(sales_channel=self.sales_channel)
        factory.run()
        self.assertTrue(factory.remote_model_class.objects.filter(sales_channel=self.sales_channel).exists())

    def test_pull_language(self):
        factory = EbayRemoteLanguagePullFactory(sales_channel=self.sales_channel)
        factory.run()
        self.assertTrue(factory.remote_model_class.objects.filter(sales_channel=self.sales_channel).exists())
