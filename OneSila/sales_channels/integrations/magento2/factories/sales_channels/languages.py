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
        'store_view_code': 'code'
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

    def preflight_check(self):
        """
        Load website mapping (id → code) before processing.
        """
        active = self.sales_channel.active
        if not active:
            return active

        self.website_map = {
            int(website.id): website.code
            for website in self.api.store.websites
        }

        return active

    def allow_process(self, remote_data):
        return int(remote_data.id) != 0

    def serialize_response(self, response):
        """
        Assumes the response is already a list of models when `is_model_response` is True.
        """
        return response

    def update_get_or_create_lookup(self, lookup, remote_data):

        sales_channel_view = MagentoSalesChannelView.objects.filter(
            remote_id=remote_data.website_id,
            sales_channel=self.sales_channel
        ).first()

        lookup['sales_channel_view'] = sales_channel_view
        return lookup

    def get_or_create_remote_currency(self, remote_data):
        """
        Retrieves or creates a MagentoCurrency scoped at website level.
        """
        website_code = self.website_map.get(int(remote_data.website_id))
        base_currency_code = remote_data.base_currency_code

        if not website_code or not base_currency_code:
            return

        local_currency = Currency.objects.filter(
            iso_code=base_currency_code,
            multi_tenant_company=self.sales_channel.multi_tenant_company
        ).first()

        magento_currency, created = MagentoCurrency.objects.get_or_create(
            website_code=website_code,
            remote_id=remote_data.website_id,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company
        )

        update_fields = []

        if magento_currency.remote_code != base_currency_code:
            magento_currency.remote_code = base_currency_code
            update_fields.append('remote_code')

        if not magento_currency.local_instance and local_currency:
            magento_currency.local_instance = local_currency
            update_fields.append('local_instance')

        if update_fields:
            magento_currency.save(update_fields=update_fields)

        # Optional: log creation / update
        identifier, _ = self.get_identifiers()
        if created:
            self.log_action_for_instance(
                magento_currency,
                RemoteLog.ACTION_CREATE,
                remote_data,
                {'base_currency_code': base_currency_code},
                identifier
            )
        elif update_fields:
            self.log_action_for_instance(
                magento_currency,
                RemoteLog.ACTION_UPDATE,
                remote_data,
                {'updated_fields': update_fields},
                identifier
            )

    def process_remote_instance(self, remote_data, remote_instance_mirror, created):
        """
        Process each instance and set additional fields or relationships as needed.
        """
        sales_channel_view = remote_instance_mirror.sales_channel_view
        if not sales_channel_view.url:

            sales_channel_view.url = remote_data.base_url
            sales_channel_view.save()

        self.get_or_create_remote_currency(remote_data)
