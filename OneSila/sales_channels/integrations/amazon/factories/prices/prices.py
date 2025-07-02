from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin, AmazonListingIssuesMixin
from sales_channels.integrations.amazon.models import AmazonPrice, AmazonCurrency
from spapi import ListingsApi


class AmazonPriceUpdateFactory(GetAmazonAPIMixin, AmazonListingIssuesMixin, RemotePriceUpdateFactory):
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
        listings = ListingsApi(self._get_client())
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

            list_price = price_info.get("discount_price") or price_info.get("price")
            rrp_price = price_info.get("price")

            body = {
                "productType": self.remote_product.remote_type,
                "requirements": "LISTING",
                "attributes": {
                    "list_price": [
                        {"currency": iso, "amount": list_price}
                    ],
                    "uvp_list_price": [
                        {"currency": iso, "amount": rrp_price}
                    ],
                },
            }

            self.body = body

            resp = listings.patch_listings_item(
                seller_id=self.sales_channel.remote_id,
                sku=self.remote_product.remote_sku,
                marketplace_ids=[self.view.remote_id],
                body=body,
            )
            self.update_assign_issues(getattr(resp, "issues", []))
            responses.append(resp)

        return responses

    def serialize_response(self, response):
        return [r.payload if hasattr(r, "payload") else {} for r in response]
