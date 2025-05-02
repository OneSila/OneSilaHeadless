from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models.products import ShopifyProduct
from sales_channels.integrations.shopify.models import ShopifyPrice


class ShopifyPriceUpdateFactory(GetShopifyApiMixin, RemotePriceUpdateFactory):
    """
    Updates the price (and compare_at_price) for a single-variant Shopify product via the REST API.
    """
    remote_model_class = ShopifyPrice

    def update_remote(self):
        """
        Fetch the variant by SKU, update its price and compare_at_price, then save.
        """

        variants = self.api.Variant.find(sku=self.remote_product.remote_sku)
        if not variants:
            raise ValueError(f"No variant found with SKU {self.remote_product.remote_sku}")

        variant = variants[0]

        currency_code = self.to_update_currencies[0]
        price_info = self.price_data.get(currency_code, {})

        if price_info.get('price') is not None:
            variant.price = price_info['price']

        if price_info.get('discount_price') is not None:
            variant.compare_at_price = price_info['discount_price']

        saved_variant = variant.save()
        return saved_variant

    def serialize_response(self, response):
        return {'variant_id': getattr(response, 'id', None)}