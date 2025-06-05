from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.models import (
    AmazonRemoteLanguage,
    AmazonSalesChannelView,
)


class AmazonRemoteLanguagePullFactory(GetAmazonAPIMixin, PullRemoteInstanceMixin):
    """Pull default languages for each Amazon marketplace."""

    remote_model_class = AmazonRemoteLanguage
    field_mapping = {
        'remote_code': 'code',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['remote_code', 'sales_channel_view']

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        marketplaces = self.get_marketplaces()
        self.remote_instances = [
            {
                'code': mp['marketplace']['default_language_code'],
                'view_remote_id': mp['marketplace']['id'],
            }
            for mp in marketplaces
            if mp.get('participation', {}).get('is_participating')
        ]

    def update_get_or_create_lookup(self, lookup, remote_data):
        view = AmazonSalesChannelView.objects.filter(
            remote_id=remote_data['view_remote_id'],
            sales_channel=self.sales_channel,
        ).first()
        lookup['sales_channel_view'] = view
        return lookup

    def create_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        remote_instance_mirror.remote_code = remote_data['code']
        remote_instance_mirror.sales_channel = self.sales_channel
        remote_instance_mirror.multi_tenant_company = self.sales_channel.multi_tenant_company
        remote_instance_mirror.sales_channel_view = AmazonSalesChannelView.objects.filter(
            remote_id=remote_data['view_remote_id'],
            sales_channel=self.sales_channel,
        ).first()
        remote_instance_mirror.save()
