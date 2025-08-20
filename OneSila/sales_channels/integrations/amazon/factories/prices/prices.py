from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from datetime import timedelta

from django.utils import timezone
from sales_channels.integrations.amazon.models import AmazonPrice, AmazonCurrency
from sales_channels.integrations.amazon.models.properties import (
    AmazonProductType,
    AmazonPublicDefinition,
)


class AmazonPriceUpdateFactory(GetAmazonAPIMixin, RemotePriceUpdateFactory):
    """Update product prices for a specific Amazon marketplace."""

    remote_model_class = AmazonPrice

    def __init__(
        self,
        sales_channel,
        local_instance,
        remote_product,
        view,
        api=None,
        currency=None,
        skip_checks=False,
        get_value_only=False,
    ):
        self.view = view
        self.get_value_only = get_value_only
        self.value = None
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

    def _get_list_price_config(self):
        rule = self.local_instance.get_product_rule()
        if not rule:
            return "value_with_tax"

        product_type = AmazonProductType.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=rule,
        ).first()
        if not product_type:
            return "value_with_tax"

        public_def = (
            AmazonPublicDefinition.objects.filter(
                api_region_code=self.view.api_region_code,
                product_type_code=product_type.product_type_code,
                code__in=["list_price"],
            )
            .first()
        )
        if not public_def:
            return "value_with_tax"

        schema = public_def.raw_schema or {}
        props = schema.get("items", {}).get("properties", {})
        value_key = "value_with_tax" if "value_with_tax" in props else "value"
        return value_key

    def update_remote(self):
        value_key = self._get_list_price_config()

        currencies = AmazonCurrency.objects.filter(
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            local_instance__iso_code__in=self.to_update_currencies,
        )

        purchasable_offer_values = []
        list_price_values = []

        for remote_currency in currencies:
            iso = remote_currency.local_instance.iso_code
            price_info = self.price_data.get(iso, {})
            if not price_info:
                continue

            full_price = price_info.get("price")
            discount_price = price_info.get("discount_price")

            offer_entry = {
                "audience": "ALL",
                "currency": iso,
                "marketplace_id": self.view.remote_id,
                "our_price": [
                    {"schedule": [{"value_with_tax": full_price}]}
                ],
            }

            if discount_price is not None:
                start = timezone.now().date().isoformat()
                end = (timezone.now() + timedelta(days=365)).date().isoformat()
                offer_entry["discounted_price"] = [
                    {
                        "schedule": [
                            {
                                "start_at": start,
                                "end_at": end,
                                "value_with_tax": discount_price,
                            }
                        ]
                    }
                ]
                # @TODO: connect with pricelists when needed

            purchasable_offer_values.append(offer_entry)

            if self.remote_product.product_owner and full_price is not None:
                list_price_values.append({"currency": iso, value_key: full_price})

        if self.get_value_only:
            self.value = {
                "purchasable_offer_values": purchasable_offer_values,
                "list_price_values": list_price_values if list_price_values else None,
            }

            return self.value

        attributes = {}
        if purchasable_offer_values:
            attributes["purchasable_offer"] = purchasable_offer_values

        if list_price_values:
            attributes["list_price"] = list_price_values

        if not attributes:
            return []

        resp = self.update_product(
            self.remote_product.remote_sku,
            self.view.remote_id,
            self.remote_product.get_remote_rule(),
            attributes,
        )
        return resp

    def serialize_response(self, response):
        return response.payload if hasattr(response, "payload") else {}
