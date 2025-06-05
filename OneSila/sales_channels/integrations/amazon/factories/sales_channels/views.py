from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.models import AmazonSalesChannelView


class AmazonSalesChannelViewPullFactory(GetAmazonAPIMixin, PullRemoteInstanceMixin):
    """Pull Amazon marketplaces as sales channel views."""

    remote_model_class = AmazonSalesChannelView
    field_mapping = {
        'remote_id': 'id',
        'url': 'domain_name',
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
                'id': mp['marketplace']['id'],
                'name': mp['marketplace']['name'],
                'country_code': mp['marketplace']['country_code'],
                'domain_name': mp['marketplace']['domain_name'],
            }
            for mp in marketplaces
            if mp.get('participation', {}).get('is_participating')
        ]

    def serialize_response(self, response):
        return response

    def process_remote_instance(self, remote_data, remote_instance_mirror, created):
        name = f"{remote_data['name']} ({remote_data['country_code']})"
        if remote_instance_mirror.name != name:
            remote_instance_mirror.name = name
            remote_instance_mirror.save(update_fields=['name'])
