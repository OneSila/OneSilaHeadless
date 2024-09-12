from currencies.models import Currency
from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models.sales_channels import MagentoRemoteLanguage, MagentoSalesChannelView
from sales_channels.integrations.magento2.models.taxes import MagentoCurrency
from sales_channels.models import RemoteLog


class MagentoRemoteLanguagePullFactory(GetMagentoAPIMixin, PullRemoteInstanceMixin):
    remote_model_class = MagentoRemoteLanguage
    field_mapping = {
        'remote_id': 'id',
        'remote_code': 'locale',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['remote_id', 'locale']
    api_package_name = 'store'
    api_method_name = 'configs'
    api_method_is_property = True
    allow_create = True
    allow_update = True
    allow_delete = True
    is_model_response = True

    def allow_process(self, remote_data):
        return int(remote_data.id) != 0

    def serialize_response(self, response):
        """
        Assumes the response is already a list of models when `is_model_response` is True.
        """
        return response

    def update_get_or_create_lookup(self, lookup, remote_data):

        sales_channel_view = MagentoSalesChannelView.objects.filter(
            code=remote_data.code,
            sales_channel=self.sales_channel
        ).first()

        lookup['sales_channel_view'] = sales_channel_view
        return lookup

    def get_or_create_remote_currency(self, remote_data, sales_channel_view):
        """
        Handles the retrieval or creation of the Magento remote currency based on the remote data.

        :param remote_data: Data from the remote system containing currency information.
        :param sales_channel_view: The sales channel view associated with the remote currency.
        """
        # Extract the base currency code
        base_currency_code = remote_data.base_currency_code

        if base_currency_code:
            local_currency = Currency.objects.filter(
                iso_code=base_currency_code,
                multi_tenant_company=self.sales_channel.multi_tenant_company
            ).first()

            # Create or get the remote currency mirror, setting local_instance if available
            magento_currency, created = MagentoCurrency.objects.get_or_create(
                local_instance=local_currency,
                sales_channel=self.sales_channel,
                sales_channel_view=sales_channel_view,
                remote_code=base_currency_code,
                multi_tenant_company=self.sales_channel.multi_tenant_company
            )

            if created:
                identifier = self.get_identifier()
                self.log_action_for_instance(
                    magento_currency,
                    RemoteLog.ACTION_CREATE,
                    remote_data,
                    {'base_currency_code': base_currency_code},
                    identifier
                )

    def process_remote_instance(self, remote_data, remote_instance_mirror):
        """
        Process each instance and set additional fields or relationships as needed.
        """
        sales_channel_view = remote_instance_mirror.sales_channel_view
        if not sales_channel_view.url:

            sales_channel_view.url = remote_data.base_url
            sales_channel_view.save()

        self.get_or_create_remote_currency(remote_data, sales_channel_view)
