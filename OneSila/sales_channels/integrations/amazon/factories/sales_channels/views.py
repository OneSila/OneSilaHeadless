from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.models import AmazonSalesChannelView


class AmazonSalesChannelViewPullFactory(GetAmazonAPIMixin, PullRemoteInstanceMixin):
    """Pull Amazon marketplaces as sales channel views."""

    remote_model_class = AmazonSalesChannelView
    field_mapping = {
        'remote_id': 'id',
        'url': 'domain_name',
        'name': 'name',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['remote_id']

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        marketplaces = self.get_marketplaces()

        self.remote_instances = [
            {
                'id': mp.marketplace.id,
                'name': f"{mp.store_name} {mp.marketplace.country_code}",
                'domain_name': mp.marketplace.domain_name,
            }
            for mp in marketplaces
            if mp.participation.is_participating
        ]

    def serialize_response(self, response):
        return response