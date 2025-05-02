from sales_channels.factories.products.eancodes import RemoteEanCodeUpdateFactory
from sales_channels.integrations.shopify.constants import DEFAULT_METAFIELD_NAMESPACE
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models import ShopifyEanCode


class ShopifyEanCodeUpdateFactory(GetShopifyApiMixin, RemoteEanCodeUpdateFactory):
    remote_model_class = ShopifyEanCode

    def needs_update(self):
        self.ean_code_value = self.get_ean_code_value()
        return self.ean_code_value != (self.remote_instance.remote_value or '')

    def update_remote(self):
        # Assumes set_api() has already been called by the base
        product = self.api.Product.find(self.remote_product.remote_id)
        if not product:
            raise ValueError(f"No Shopify product found with id {self.remote_product.remote_id}")

        key = self.sales_channel.ean_metafield_key
        mf_payload = {
            'namespace': DEFAULT_METAFIELD_NAMESPACE,
            'key':       key,
            'value':     str(self.ean_code_value),
            'type':      'single_line_text_field',
        }

        mf = self.api.Metafield(mf_payload)
        product.add_metafield(mf)
        # product.save()

        return mf

    def post_update_process(self):
        self.remote_instance.ean_code = self.ean_code_value

    def serialize_response(self, response):
        return response.to_dict()