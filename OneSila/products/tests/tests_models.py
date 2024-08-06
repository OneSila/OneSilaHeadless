from django.db import IntegrityError
from core.tests import TestCase
from products.models import SimpleProduct, SupplierProduct, BundleProduct


# class ProductIntegrityTestCase(TestCase):
#     def test_supplier_on_bundle_product(self):
#         prod = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
#         sup = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

#         with self.assertRaises(IntegrityError):
#             prod.bundle_variations.add(sup)
