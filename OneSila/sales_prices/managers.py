from core.managers import MultiTenantQuerySet, MultiTenantManager
from django.db.models import Case, F, When, Value


class SalesPriceListQuerySet(MultiTenantQuerySet):
    pass


class SalesPriceListManager(MultiTenantManager):
    def get_queryset(self):
        return SalesPriceListQuerySet(self.model, using=self._db)


class SalesPriceQuerySet(MultiTenantQuerySet):
    def get_default_price(self):
        return self.get(currency__is_default_currency=True)

    def get_currency_price(self, currency):
        return self.get(currency=currency)

    def filter_salesprices(self):
        return self.all()

    def filter_auto_update_prices(self):
        return self.filter(auto_update_prices=True)


class SalesPriceManager(MultiTenantManager):
    def get_queryset(self):
        return SalesPriceQuerySet(self.model, using=self._db)  # Important!

    def get_default_price(self):
        return self.get_queryset().get_default_price()

    def get_currency_price(self, currency):
        return self.get_queryset().get_currency_price(currency)

    def filter_salesprices(self):
        return self.get_queryset().filter_salesprices()

    def filter_auto_update_prices(self):
        return self.get_queryset().filter_auto_update_prices()


class SalesPriceListItemQuerySet(MultiTenantQuerySet):
    def annotate_prices(self):
        # Let's think about this:
        # We can have automated pricelists which have auto-prices.
        # if the pricelist is automated, then field_override matters more
        # BUT if the price list is not automated, then only the override fields matter.

        # Both of this means that if the override contains value, you should give return that
        # or else you return the auto-price.

        # however, if you change the setting of the pricelist from auto to manual, what do you do?
        # only return the override?  For now, no - let's start off simplified and treat the entire thing
        # as override over auto.

        return self.annotate(
            price=Case(
                When(price_override__gt=0, then=F('price_override')),
                default=F('price_auto')
            ),
            discount=Case(
                When(discount_override__gt=0, then=F('discount_override')),
                default=F('discount_auto')
            )

        )


class SalesPriceListItemManager(MultiTenantManager):
    def get_queryset(self):
        return SalesPriceListItemQuerySet(self.model, using=self._db).\
            annotate_prices()

    def get_or_create__with_auto_price(self, product, salespricelist=None):
        self.get_queryset().get_or_create__with_auto_price(product, salespricelist or self.instance)
