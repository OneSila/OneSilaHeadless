from core.tests import TestCase
from products.models import SimpleProduct
from currencies.models import Currency
from sales_prices.models import SalesPriceList, SalesPriceListItem, SalesPrice
from sales_prices.factories import SalesPriceForSalesPriceListItemCreateFactory, \
    SalesPriceListForSalesPriceListItemsCreateUpdateFactory
from currencies.currencies import currencies


class SalesPriceListForSalesPriceListItemsCreateUpdateFactoryTestCase(TestCase):
    def test_create_salespricelist(self):
        """We want to ensure that when a new price list is created
        that we assign the relevant prices"""
        rrp = 100
        price = 90
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        currency_gbp, _ = Currency.objects.get_or_create(
            is_default_currency=True,
            multi_tenant_company=self.multi_tenant_company,
            **currencies['GB'])
        salesprice_gbp = product.salesprice_set.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency_gbp,
            rrp=rrp,
            price=price)
        price_list_gbp_auto = SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency_gbp,
            auto_add_products=True,
        )

        f = SalesPriceListForSalesPriceListItemsCreateUpdateFactory(salespricelist=price_list_gbp_auto)
        f.run()

        self.assertTrue(price_list_gbp_auto.salespricelistitem_set.filter(product=product).exists())

    def test_create_salespricelist_manual(self):
        """We want to ensure that when a new price list is created
        with the manual update flag that we don't assign the relevant prices"""
        rrp = 100
        price = 90
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        currency_gbp, _ = Currency.objects.get_or_create(
            is_default_currency=True,
            multi_tenant_company=self.multi_tenant_company,
            **currencies['GB'])
        salesprice_gbp = product.salesprice_set.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency_gbp,
            rrp=rrp,
            price=price)
        price_list_gbp_nonauto = SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency_gbp,
            auto_add_products=False,
        )

        f = SalesPriceListForSalesPriceListItemsCreateUpdateFactory(salespricelist=price_list_gbp_nonauto)
        f.run()

        self.assertFalse(price_list_gbp_nonauto.salespricelistitem_set.filter(product=product).exists())


class SalesPriceForSalesPriceListItemCreateFactoryTestCase(TestCase):
    def test_create_items(self):
        """ We want to ensure that the right items are created
        when adding salesprices and price lists exist.
        """

        # We need
        # 2 currencies
        # 1 product
        # 2 SalesPrices
        # 4 PriceLists (2 auto-add, 2 not)

        # after creating the products and price lists
        # we run the SalesPriceForSalesPriceListItemCreateFactory
        # for all sales prices
        # and verify that SalesPriceListItems have been created for only the
        # pricelists where the auto-add is added. And veriyf that they are not
        # created for the others.

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
            **currencies['FR'])

        salesprice_gbp = product.salesprice_set.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency_gbp,
            rrp=rrp,
            price=price)
        salesprice_eur = product.salesprice_set.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency_eur,
            rrp=rrp,
            price=price)

        price_list_gbp_auto = SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency_gbp,
            auto_add_products=True,
        )
        price_list_gbp_nonauto = SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency_gbp,
            auto_add_products=False,
        )
        price_list_eur_auto = SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency_eur,
            auto_add_products=True,
        )
        price_list_eur_nonauto = SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency_eur,
            auto_add_products=False,
        )

        f = SalesPriceForSalesPriceListItemCreateFactory(salesprice_gbp)
        f.run()

        f = SalesPriceForSalesPriceListItemCreateFactory(salesprice_eur)
        f.run()

        self.assertTrue(price_list_gbp_auto.salespricelistitem_set.filter(product=product).exists())
        self.assertFalse(price_list_gbp_nonauto.salespricelistitem_set.filter(product=product).exists())
        self.assertTrue(price_list_eur_auto.salespricelistitem_set.filter(product=product).exists())
        self.assertFalse(price_list_eur_nonauto.salespricelistitem_set.filter(product=product).exists())
