from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoSalesChannelView
import logging

logger = logging.getLogger(__name__)


class MagentoSalesChannelViewPullFactory(GetMagentoAPIMixin, PullRemoteInstanceMixin):
    remote_model_class = MagentoSalesChannelView
    field_mapping = {
        'remote_id': 'id',
        'code': 'code',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['remote_id', 'code']
    api_package_name = 'store'
    api_method_name = 'websites'
    api_method_is_property = True
    allow_create = True
    allow_update = True
    allow_delete = True
    is_model_response = True

    def allow_process(self, remote_data):
        return int(remote_data.id) != 0

    def process_remote_instance(self, remote_data, remote_instance_mirror, created):

        if created:
            remote_instance_mirror.name = remote_data.name
            remote_instance_mirror.save()

    def serialize_response(self, response):
        """
        Converts the API response into a list of instances.
        Assumes the response is already a list of models when `is_model_response` is True.
        """
        return response
