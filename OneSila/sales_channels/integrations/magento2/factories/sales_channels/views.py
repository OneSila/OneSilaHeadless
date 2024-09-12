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
        'name': 'name',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['remote_id', 'code']
    api_package_name = 'store'
    api_method_name = 'views'
    api_method_is_property = True
    allow_create = True
    allow_update = True
    allow_delete = True
    is_model_response = True

    def allow_process(self, remote_data):
        return int(remote_data.id) != 0 and remote_data.is_active


    def serialize_response(self, response):
        """
        Converts the API response into a list of instances.
        Assumes the response is already a list of models when `is_model_response` is True.
        """
        return response