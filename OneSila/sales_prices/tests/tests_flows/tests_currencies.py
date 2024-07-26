from core.tests import TestCase
from currencies.models import Currency
from currencies.currencies import currencies
from products.models import SimpleProduct
from sales_prices.models import SalesPriceList
from sales_prices.flows import salesprice_updatecreate_flow, \
    sales_price__salespricelistitem__create_update_flow, \
    sales_price__salespricelistitem__update_prices_flow, \
    salesprice_currency_change_flow


class CurrencyChangeTestCase(TestCase):
    def test_currency_rate_change(self):
        # When a currency rate has changed, we want
        # to ensure that all related prices have adjusted.
        rrp = 100
        price = 90

        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        currency_gbp, _ = Currency.objects.get_or_create(
            is_default_currency=True,
            multi_tenant_company=self.multi_tenant_company,
            **currencies['GB'])
        currency_eur, _ = Currency.objects.get_or_create(
            is_default_currency=False,
            multi_tenant_company=self.multi_tenant_company,
            inherits_from=currency_gbp,
            exchange_rate=1,
            follow_official_rate=False,
            **currencies['FR'])

        salesprice_gbp = product.salesprice_set.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency_gbp,
            rrp=rrp,
            price=price)
        salesprice_eur = product.salesprice_set.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency_eur)

        price_list_eur_auto = SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency_eur,
            auto_add_products=True,
            auto_update_prices=True,
            discount_pcnt=2,
        )

        salesprice_updatecreate_flow(salesprice_gbp)
        sales_price__salespricelistitem__create_update_flow(salesprice_eur)
        sales_price__salespricelistitem__update_prices_flow(salesprice_eur)

        salespricelistitem_eur = price_list_eur_auto.salespricelistitem_set.get(product=product)

        salesprice_eur.refresh_from_db()
        salespricelistitem_eur.refresh_from_db()

        salesprice_eur_before_rrp = salesprice_eur.rrp
        salesprice_eur_before_price = salesprice_eur.price

        salespricelistprice_eur_before_price = salespricelistitem_eur.price
        salespricelistprice_eur_before_discount = salespricelistitem_eur.discount

        # Now that the outline has been created.  It's time to change the
        # currency exchange rate.
        currency_eur.exchange_rate = 10
        currency_eur.save()

        salesprice_currency_change_flow(currency_eur)

        salesprice_updatecreate_flow(salesprice_gbp)
        sales_price__salespricelistitem__update_prices_flow(salesprice_eur)

        salesprice_eur.refresh_from_db()
        salespricelistitem_eur.refresh_from_db()

        salesprice_eur_after_rrp = salesprice_eur.rrp
        salesprice_eur_after_price = salesprice_eur.price

        # We're using the auto-field directly as annotation dont refresh.
        salespricelistprice_eur_after_price = salespricelistitem_eur.price_auto
        salespricelistprice_eur_after_discount = salespricelistitem_eur.discount_auto

        self.assertFalse(salesprice_eur_before_rrp == salesprice_eur_after_rrp)
        self.assertFalse(salesprice_eur_before_price == salesprice_eur_after_price)

        self.assertFalse(salespricelistprice_eur_before_price == salespricelistprice_eur_after_price)
        self.assertFalse(salespricelistprice_eur_before_discount == salespricelistprice_eur_after_discount)
