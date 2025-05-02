import json
from sales_channels.factories.products.content import RemoteProductContentUpdateFactory
from sales_channels.integrations.shopify.contsnts import DEFAULT_METAFIELD_NAMESPACE
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models.products import ShopifyProductContent

class ShopifyProductContentUpdateFactory(GetShopifyApiMixin, RemoteProductContentUpdateFactory):
    remote_model_class = ShopifyProductContent

    def customize_payload(self):
        """
        Build the dict of fields to update on the Shopify product itself.
        We update: title (name), body_html (description), handle (url_key).
        """
        self.payload = {
            'title': self.local_instance.name,
            'body_html': self.local_instance.description,
            'handle': self.local_instance.url_key
        }
        return self.payload

    def update_remote(self):
        """
        Activates the session, fetches the Product by its remote_id, updates
        the core fields, then optionally writes a short_description metafield.
        """

        product = self.api.Product.find(self.remote_product.remote_id)

        if not product:
            raise ValueError(f"No Shopify Product found with id {self.remote_product.remote_id}")

        # Update core fields
        for field, val in self.payload.items():
            setattr(product, field, val)

        product.save()

        # Short description as a JSON-string metafield?
        key = getattr(self.sales_channel, 'short_description_metafield_key', None)
        short_desc = getattr(self.local_instance, 'short_description', None)
        if key and short_desc:
            mf = self.api.Metafield({
                'namespace':   DEFAULT_METAFIELD_NAMESPACE,
                'key':         key,
                'value':       json.dumps({'short_description': short_desc}),
                'type':        'json_string'
            })
            product.add_metafield(mf)

        return product

    def serialize_response(self, response):
        return response.to_dict()
