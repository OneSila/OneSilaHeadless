from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.models import (
    EbayRemoteLanguage,
    EbaySalesChannelView,
)


class EbayRemoteLanguagePullFactory(GetEbayAPIMixin, PullRemoteInstanceMixin):
    """Pull default languages for each eBay marketplace."""

    remote_model_class = EbayRemoteLanguage
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
        self.remote_instances = []
        marketplaces = self.get_marketplace_ids()
        reference = self.marketplace_reference()

        for marketplace_id in marketplaces:
            info = reference.get(marketplace_id)
            if not info:
                continue
            languages = info[1]
            for code, data in languages.items():
                url = data[0] if isinstance(data, (list, tuple)) and data else ""
                self.remote_instances.append({
                    "code": code,
                    "view_remote_id": marketplace_id,
                    "url": url,
                })

    def update_get_or_create_lookup(self, lookup, remote_data):
        view = EbaySalesChannelView.objects.filter(
            remote_id=remote_data['view_remote_id'],
            sales_channel=self.sales_channel,
        ).first()
        lookup['sales_channel_view'] = view
        return lookup

    def create_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        remote_instance_mirror.remote_code = remote_data['code']
        remote_instance_mirror.sales_channel = self.sales_channel
        remote_instance_mirror.multi_tenant_company = self.sales_channel.multi_tenant_company
        remote_instance_mirror.sales_channel_view = EbaySalesChannelView.objects.filter(
            remote_id=remote_data['view_remote_id'],
            sales_channel=self.sales_channel,
        ).first()
        remote_instance_mirror.save()
