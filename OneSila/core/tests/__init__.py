from core.models import MultiTenantCompany
from django.contrib.auth import get_user_model
from model_bakery import baker


class TestCaseMixin:
    def setUp(self):
        self.multi_tenant_company = baker.make(MultiTenantCompany)
        self.user = baker.make(get_user_model(), multi_tenant_company=self.multi_tenant_company)
