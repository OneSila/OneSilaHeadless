from django.db.models import QuerySet, Manager, Q


class SalesPriceQuerySet(QuerySet):
    def get_default_price(self):
        return self.get(currency__is_default_currency=True)

    def get_currency_price(self, currency):
        return self.get(currency=currency)

    def filter_salesprices(self):
        return self.all()

    def filter_auto_update(self):
        return self.filter(auto_update=True)


class SalesPriceManager(Manager):
    def get_queryset(self):
        return SalesPriceQuerySet(self.model, using=self._db)  # Important!

    def get_default_price(self):
        return self.get_queryset().get_default_price()

    def get_currency_price(self, currency):
        return self.get_queryset().get_currency_price(currency)

    def filter_salesprices(self):
        return self.get_queryset().filter_salesprices()

    def filter_auto_update(self):
        return self.get_queryset().filter_auto_update()


class SalesPriceListItemQuerySet(QuerySet):
    def get_or_create__with_auto_price(self, product, salespricelist):
        from .factories import SalesPriceListItemGeneratorUpdater

        if not salespricelist.auto_update:
            raise TypeError('Salespricelist not marked for auto_update')

        fac = SalesPriceListItemGeneratorUpdater(salespricelist, product)
        fac.run()

        return fac.item, fac.item_created


class SalesPriceListItemManager(Manager):
    def get_queryset(self):
        return SalesPriceListItemQuerySet(self.model, using=self._db)  # Important!

    def get_or_create__with_auto_price(self, product, salespricelist=None):
        self.get_queryset().get_or_create__with_auto_price(product, salespricelist or self.instance)
