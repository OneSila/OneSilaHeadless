from products.models import Product
from sales_channels.factories.mixins import RemoteInstanceUpdateFactory, ProductAssignmentMixin
from core.exceptions import SanityCheckError

import logging
logger = logging.getLogger(__name__)


class ToUpdateCurrenciesMixin:
    """Mixin to give populate all currencies that need updating.

    Remember:
    - self.currency is expected to exist as a RemoteCurrency instance.
    - self.currency_iso_code is expected to exist as a string.
    - self.get_product
    """

    def __init__(self, *args, **kwargs):
        self.to_update_currencies = []
        self.price_data = {}
        super().__init__(*args, **kwargs)

    def sanity_check(self):

        if hasattr(super(), "sanity_check"):
            super().sanity_check()

        # Thjs are not mandatory. Inspect why it awas added
        # if not self.currency:
        #     raise SanityCheckError("self.currency is not set")
        # if not self.currency_iso_code:
        #     raise SanityCheckError("self.currency_iso_code is not set")

    def set_to_update_currencies(self):
        from sales_channels.models import RemoteCurrency
        from currencies.models import Currency

        # we do that so if the currency inherit other currencies we make sure the updates goes for all
        # because the price_data here will override the inherited currency one and if this happen that one will be skipped
        if self.currency:
            reset_currency = Currency.objects.filter(inherits_from=self.currency, multi_tenant_company=self.sales_channel.multi_tenant_company).exists()

            if reset_currency:
                self.currency = None

        try:
            existing_price_data = self.remote_instance.price_data or {}
        except AttributeError:
            existing_price_data = {}

        all_remote_currencies = RemoteCurrency.objects.filter(sales_channel=self.sales_channel)

        logger.debug(f"{self.__class__.__name__} all remote currencies: {all_remote_currencies}")

        self.to_update_currencies = []
        self.price_data = {}

        for remote_currency in all_remote_currencies:
            local_currency = remote_currency.local_instance

            if not local_currency:
                continue

            limit_iso = getattr(self, "limit_to_currency_iso", None)
            if limit_iso and local_currency.iso_code != limit_iso:
                continue

            local_product = self.get_local_product()
            full_price, discount_price = local_product.get_price_for_sales_channel(
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

    def post_update_process(self):
        self.remote_instance.price_data = self.price_data
        self.remote_instance.save()
        super().post_update_process()

    def run(self):
        self.set_to_update_currencies()
        return super().run()


class RemotePriceUpdateFactory(ToUpdateCurrenciesMixin, ProductAssignmentMixin, RemoteInstanceUpdateFactory):
    local_model_class = Product
    local_product_map = 'local_instance'

    def __init__(self, sales_channel, local_instance, remote_product, api=None, currency=None, skip_checks=False):
        super().__init__(sales_channel, local_instance, api=api, remote_product=remote_product)
        self.currency = currency  # Currency model instance (optional)
        self.skip_checks = skip_checks
        self.remote_instance = None

    def preflight_check(self):
        if not self.skip_checks:
            if not self.sales_channel.sync_prices:
                logger.warning(f"{self.__class__.__name__} Preflight check: Sales channel {self.sales_channel.hostname} does not sync prices")
                return False
            if not self.remote_product:
                logger.warning(f"{self.__class__.__name__} Preflight check: Remote product not found for sales channel {self.sales_channel.hostname}")
                return False
            if not self.assigned_to_website():
                logger.warning(f"{self.__class__.__name__} Preflight check: Product {self.local_instance.name} is not assigned to website {self.sales_channel.hostname}")
                return False

        try:
            # If you have this failing, then it means that the ProductCreateFactory did not create
            # the remote Price object.
            self.remote_instance = self.remote_model_class.objects.get(remote_product=self.remote_product)
        except self.remote_model_class.DoesNotExist:
            if self.remote_model_class:
                self.remote_instance, _ = self.remote_model_class.objects.get_or_create(
                    remote_product=self.remote_product,
                    sales_channel=self.sales_channel,
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                )
            else:
                logger.error(f"{self.__class__.__name__} Preflight check: Remote instance {self.remote_model_class.__name__} not found for sales channel {self.sales_channel} and product {self.local_instance}")
                return False

        return bool(self.to_update_currencies)

    def needs_update(self):
        return bool(self.to_update_currencies)

    def get_remote_instance(self):
        # Already resolved in preflight_check
        pass
