from contacts.models import Company, Supplier
from django.test import TestCase
from core.tests import TestCaseMixin


class CompanyTestCase(TestCaseMixin, TestCase):
    def test_supplier_create(self):
        supplier = Supplier.objects.create(name='test_supplier_create', multi_tenant_company=self.multi_tenant_company)
        self.assertTrue(supplier.is_supplier)
