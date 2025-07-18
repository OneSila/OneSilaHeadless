from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.models import AmazonPrice, AmazonCurrency


class AmazonPriceUpdateFactory(GetAmazonAPIMixin, RemotePriceUpdateFactory):
    """Update product prices for a specific Amazon marketplace."""

    remote_model_class = AmazonPrice

    def __init__(self, sales_channel, local_instance, remote_product, view, api=None, currency=None, skip_checks=False):
        self.view = view
        super().__init__(
            sales_channel=sales_channel,
            local_instance=local_instance,
            remote_product=remote_product,
            api=api,
            currency=currency,
            skip_checks=skip_checks,
        )

    def get_local_product(self):
        return self.local_instance

    def update_remote(self):
        responses = []

        currencies = AmazonCurrency.objects.filter(
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            local_instance__iso_code__in=self.to_update_currencies,
        )

        for remote_currency in currencies:
            iso = remote_currency.local_instance.iso_code
            price_info = self.price_data.get(iso, {})
            if not price_info:
                continue

            sale_price = price_info.get("discount_price")
            list_price = sale_price if sale_price is not None else price_info.get("price")
            attributes = {
                "purchasable_offer": [
                    {
                        "audience": "ALL",
                        "currency": iso,
                        "marketplace_id": self.view.remote_id,
                        "our_price": [
                            {
                                "schedule": [
                                    {"value_with_tax": list_price}
                                ]
                            }
                        ],
                    }
                ]
            }

            if self.sales_channel.listing_owner:
                attributes["list_price"] = [{"currency": iso, "value": list_price}]


            resp = self.update_product(
                self.remote_product.remote_sku,
                self.view.remote_id,
                self.remote_product.get_remote_rule(),
                attributes,
            )
            responses.append(resp)

        return responses

    def serialize_response(self, response):
        return [r.payload if hasattr(r, "payload") else {} for r in response]
