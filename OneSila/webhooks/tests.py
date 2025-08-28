from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase

from core.models import MultiTenantCompany
from .models import WebhookIntegration
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class WebhookIntegrationModelTests(TestCase):
    def setUp(self):
        self.company = MultiTenantCompany.objects.create(name="TestCo")

    def test_requests_per_minute_cannot_exceed_120(self):
        integration = WebhookIntegration(
            multi_tenant_company=self.company,
            hostname="https://example.com",
            topic="product",
            url="https://webhook.example.com",
            requests_per_minute=121,
        )
        with self.assertRaises(ValidationError):
            integration.save(force_save=True)

    def test_requests_per_minute_allows_120(self):
        integration = WebhookIntegration(
            multi_tenant_company=self.company,
            hostname="https://example.com",
            topic="product",
            url="https://webhook.example.com",
            requests_per_minute=120,
        )
        integration.save(force_save=True)
        self.assertIsNotNone(integration.id)


class WebhookIntegrationMutationTests(TransactionTestCaseMixin, TransactionTestCase):
    def test_regenerate_secret(self):
        integration = WebhookIntegration.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://example.com",
            topic="product",
            url="https://webhook.example.com",
        )
        old_secret = integration.secret
        mutation = """
            mutation($id: GlobalID!){
              regenerateWebhookIntegrationSecret(instance: {id: $id}){
                secret
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={"id": self.to_global_id(integration)},
            asserts_errors=False,
        )
        self.assertTrue(resp.errors is None)
        new_secret = resp.data["regenerateWebhookIntegrationSecret"]["secret"]
        self.assertNotEqual(old_secret, new_secret)
