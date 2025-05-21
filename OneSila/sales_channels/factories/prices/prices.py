from products.models import Product
from sales_channels.factories.mixins import RemoteInstanceUpdateFactory, ProductAssignmentMixin

import logging
logger = logging.getLogger(__name__)


class RemotePriceUpdateFactory(ProductAssignmentMixin, RemoteInstanceUpdateFactory):
    local_model_class = Product
    local_product_map = 'local_instance'

    def __init__(self, sales_channel, local_instance, remote_product, api=None, currency=None, skip_checks=False):
        super().__init__(sales_channel, local_instance, api=api, remote_product=remote_product)
        self.currency = currency  # Currency model instance (optional)
        self.skip_checks = skip_checks
        self.to_update_currencies = []
        self.remote_instance = None
        self.price_data = {}

    def preflight_check(self):
        from sales_channels.models import RemoteCurrency
        from currencies.models import Currency

        if not self.skip_checks:
            if not self.sales_channel.sync_prices:
                logger.warning(f"Sales channel {self.sales_channel.name} does not sync prices")
                return False
            if not self.remote_product:
                logger.warning(f"Remote product not found for sales channel {self.sales_channel.name}")
                return False
            if not self.assigned_to_website():
                logger.warning(f"Product {self.local_instance.name} is not assigned to website {self.sales_channel.website.name}")
                return False

        try:
            self.remote_instance = self.remote_model_class.objects.get(remote_product=self.remote_product)
        except self.remote_model_class.DoesNotExist:
            return False

        # we do that so if the currency inherit other currencies we make sure the updates goes for all
        # because the price_data here will override the inherited currency one and if this happen that one will be skipped
        if self.currency:
            reset_currency = Currency.objects.filter(inherits_from=self.currency, multi_tenant_company=self.sales_channel.multi_tenant_company).exists()

            if reset_currency:
                self.currency = None

        existing_price_data = self.remote_instance.price_data or {}
        all_remote_currencies = RemoteCurrency.objects.filter(sales_channel=self.sales_channel)

        logger.debug(f"{self.__class__.__name__} all remote currencies: {all_remote_currencies}")

        for remote_currency in all_remote_currencies:
            local_currency = remote_currency.local_instance

            if not local_currency:
                continue

            full_price, discount_price = self.local_instance.get_price_for_sales_channel(
                self.sales_channel, currency=local_currency
            )

            price = float(full_price) if full_price is not None else None
            discount = float(discount_price) if discount_price is not None else None

            self.price_data[local_currency.iso_code] = {
                "price": price,
                "discount_price": discount,
            }

            # Only append to update list if currency matches or we're updating all
            if not self.currency or self.currency == local_currency:
                current = existing_price_data.get(local_currency.iso_code, {})
                if current.get("price", None) != price or current.get("discount_price", None) != discount:
                    self.to_update_currencies.append(local_currency.iso_code)

        return bool(self.to_update_currencies)

    def needs_update(self):
        return bool(self.to_update_currencies)

    def get_remote_instance(self):
        # Already resolved in preflight_check
        pass

    def post_update_process(self):
        self.remote_instance.price_data = self.price_data
        self.remote_instance.save()
