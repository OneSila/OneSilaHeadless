from core.tests import TestCase
from currencies.models import Currency
from currencies.currencies import currencies
from products.models import SimpleProduct
from sales_prices.models import SalesPriceList
from sales_prices.flows import salesprice_create_for_currency_flow


class SalesPriceFlowsTestCase(TestCase):
    def test_no_default_currency_object_created(self):
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        currency, _ = Currency.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_default_currency=True,
            **currencies['GB'])

        salesprice_create_for_currency_flow(currency)

        self.assertFalse(product.salesprice_set.all().exists())
