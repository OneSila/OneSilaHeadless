from core.tests import TestCase
from products.models import SimpleProduct
from sales_prices.models import SalesPriceList, SalesPriceListItem
from currencies.models import Currency
from currencies.currencies import currencies


class SalesPriceListItemQuerySetTestCase(TestCase):
    def test_annotate_prices(self):
        # We want to ensure that the prices are returned correctly
        # especially when price list settings are changes.
        rrp = 1000
        price = 900

        price_auto = 800
        price_override = 700

        discount_auto = 600
        discount_override = 500

        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        currency, _ = Currency.objects.get_or_create(
            is_default_currency=True,
            multi_tenant_company=self.multi_tenant_company,
            **currencies['GB'])
        salesprice = product.salesprice_set.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency,
            rrp=rrp,
            price=price)

        price_list = SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name='Test list test_discount_price',
            auto_update_prices=True,
            currency=currency,
        )

        price_list_price = SalesPriceListItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            salespricelist=price_list,
            product=product,
            price_auto=price_auto,
            price_override=price_override,
            discount_auto=discount_auto,
            discount_override=discount_override,
        )
        price_list_price = SalesPriceListItem.objects.get(id=price_list_price.id)

        self.assertTrue(price_list.auto_update_prices)
        self.assertTrue(price_list_price.price == price_auto)
        self.assertTrue(price_list_price.discount == discount_auto)

        price_list.auto_update_prices = False
        price_list.save()

        self.assertFalse(price_list.auto_update_prices)
        self.assertTrue(price_list_price.price == price_override)
        self.assertTrue(price_list_price.discount == discount_override)
