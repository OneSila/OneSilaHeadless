from magento.models import Product
from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoPrice, MagentoCurrency


class MagentoPriceUpdateFactory(GetMagentoAPIMixin, RemotePriceUpdateFactory):
    remote_model_class = MagentoPrice

    def update_remote(self):
        self.magento_product: Product = self.api.products.by_sku(self.remote_product.remote_sku)

        for remote_currency in MagentoCurrency.objects.filter(sales_channel=self.sales_channel,
                                                              local_instance__iso_code__in=self.to_update_currencies):
            iso = remote_currency.local_instance.iso_code
            current_price = self.price_data.get(iso)
            store_view_codes = remote_currency.store_view_codes

            if current_price is None or len(store_view_codes) == 0:
                continue  # just skip if something went weird

            full_price = current_price.get("price")
            discounted_price = current_price.get("discount_price")

            # for some reason we need to use a store view scope to update all the store view in the website
            scope = store_view_codes[0]

            self.magento_product.price = full_price
            self.magento_product.special_price = discounted_price
            self.magento_product.save(scope=scope)

            # if remote_currency.is_default:
            #     self.magento_product.refresh(scope=None)
            #     self.magento_product.price = full_price
            #     self.magento_product.special_price = discounted_price
            #     self.magento_product.save(scope='all')

    def serialize_response(self, response):
        return {}