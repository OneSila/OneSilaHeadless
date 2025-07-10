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


            list_price = price_info.get("price")
            # @TODO: Price is wrong we need to use
            # "purchasable_offer": [{
            #     "audience": "ALL",
            #     "currency": "USD",
            #     "marketplace_id": "xxx",
            #     "our_price": [{
            #         "schedule": [{
            #             "value_with_tax": 30.43
            #         }]
            #     }]
            # }]
            # the list_price only for LISTING and only if we are the owners

            body = {
                "productType": self.remote_product.remote_type,
                "requirements": "LISTING",
                "attributes": {
                    "list_price": [
                        {"currency": iso, "amount": list_price}
                    ],
                },
            }

            self.body = body

            current_attrs = self.get_listing_attributes(
                self.remote_product.remote_sku,
                self.view.remote_id,
            )
            resp = self.update_product(
                self.remote_product.remote_sku,
                self.view.remote_id,
                self.remote_product.remote_type,
                current_attrs,
                body.get("attributes", {}),
            )
            responses.append(resp)

        return responses

    def serialize_response(self, response):
        return [r.payload if hasattr(r, "payload") else {} for r in response]
