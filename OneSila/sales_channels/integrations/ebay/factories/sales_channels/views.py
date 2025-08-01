from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.models import EbaySalesChannelView


class EbaySalesChannelViewPullFactory(GetEbayAPIMixin, PullRemoteInstanceMixin):
    """Pull eBay marketplaces as sales channel views."""

    remote_model_class = EbaySalesChannelView
    field_mapping = {
        'remote_id': 'marketplace_id',
        'name': 'name',
        'url': 'url',
        'is_default': 'is_default',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['remote_id']

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        self.remote_instances = []
        marketplaces = self.get_marketplace_ids()
        try:
            default_marketplace = self.get_default_marketplace_id()
        except:
            # for this api sometimes we get
            # There was a problem with an eBay internal system or process. Contact eBay developer support for assistance
            # and this can manually be set so we can ignore it for now
            default_marketplace = None

        reference = self.marketplace_reference()

        for marketplace_id in marketplaces:
            info = reference.get(marketplace_id)

            if not info:
                continue

            name = info[0]
            languages = info[1]
            url = next(iter(languages.values()))[0] if languages else ""
            self.remote_instances.append({
                "marketplace_id": marketplace_id,
                "name": name,
                "url": url,
                "is_default": marketplace_id == default_marketplace,
            })

    def serialize_response(self, response):
        return response
