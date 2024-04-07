from core.models import MultiTenantCompany
from django.contrib.auth import get_user_model
from model_bakery import baker
from django.test import TestCase as DjangoTestCase

from core.demo_data import DemoDataLibrary


class TestCaseMixin:
    # This variable will be shared across all TestCases subsclassed from here.
    # That will ensure we only try to generate the demo-data once.
    demo_data_generated = False

    def generate_demo_data(self):
        if not self.demo_data_generated:
            self.demo_data_registry = DemoDataLibrary()
            self.demo_data_registry.run(multi_tenant_company=self.multi_tenant_company)
            self.demo_data_generated = True

    def setUp(self):
        self.multi_tenant_company = baker.make(MultiTenantCompany)
        self.user = baker.make(get_user_model(), multi_tenant_company=self.multi_tenant_company)
        self.generate_demo_data()


class TestCase(TestCaseMixin, DjangoTestCase):
    pass
