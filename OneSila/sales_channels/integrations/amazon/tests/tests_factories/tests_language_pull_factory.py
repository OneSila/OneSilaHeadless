from core.tests import TestCase
from sales_channels.integrations.amazon.factories.sales_channels.languages import AmazonRemoteLanguagePullFactory
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonRemoteLanguage,
)


class AmazonRemoteLanguagePullFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.view = AmazonSalesChannelView.objects.create(
            sales_channel=self.channel,
            remote_id="VIEW1",
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_no_default_local_language_mapping(self):
        factory = AmazonRemoteLanguagePullFactory(sales_channel=self.channel)
        factory.remote_instances = [{"code": "fr", "view_remote_id": "VIEW1"}]
        factory.process_remote_instances()

        remote_language = AmazonRemoteLanguage.objects.get(
            sales_channel=self.channel,
            remote_code="fr",
        )
        self.assertIsNone(remote_language.local_instance)
