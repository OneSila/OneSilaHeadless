from core.tests import TestCaseDemoDataMixin, TransactionTestCase
from products.demo_data import SIMPLE_CHAIR_WOOD_SKU
from products.models import Product
from properties.models import Property
from properties.helpers import get_product_properties_dict


class PropertyHelpersTestCase(TestCaseDemoDataMixin, TransactionTestCase):
    def test_get_product_properties_dict(self):
        product = Product.objects.get(sku=SIMPLE_CHAIR_WOOD_SKU, multi_tenant_company=self.multi_tenant_company)
        properties_dict = get_product_properties_dict(product)
        self.assertTrue(isinstance(properties_dict, dict))
