from django.core.exceptions import ValidationError
from django.test import TestCase

from core.models import MultiTenantCompany
from .models import WebhookIntegration


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
