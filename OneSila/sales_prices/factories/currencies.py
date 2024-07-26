from currencies.signals import exchange_rate_change


class SalesPriceCurrencyChangeFactory:
    def __init__(self, currency):
        self.currency = currency
        self.multi_tenant_company = currency.multi_tenant_company

    def set_salesprice_qs(self):
        self.salesprices_qs = self.currency.salesprice_set.\
            filter_multi_tenant(self.multi_tenant_company)

    def trigger_exchange_change(self, sales_price):
        exchange_rate_change.send(sender=sales_price.__class__, instance=sales_price)

    def cycle(self):
        for sales_price in self.salesprices_qs.iterator():
            self.trigger_exchange_change(sales_price)

    def run(self):
        self.set_salesprice_qs()
        self.cycle()
