from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from unittest.mock import patch
from datetime import timedelta

from core.models import MultiTenantCompany
from .models import WebhookIntegration, WebhookOutbox, WebhookDelivery, WebhookDeliveryAttempt
from .constants import ACTION_CREATE, RETENTION_3M
from .factories import ReplayDelivery, WebhookPruneFactory
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


class ReplayWebhookDeliveryTests(TestCase):
    def setUp(self):
        self.company = MultiTenantCompany.objects.create(name="TestCo")
        self.integration = WebhookIntegration.objects.create(
            multi_tenant_company=self.company,
            hostname="https://example.com",
            topic="product",
            url="https://webhook.example.com",
        )
        self.outbox = WebhookOutbox.objects.create(
            multi_tenant_company=self.company,
            webhook_integration=self.integration,
            topic="product",
            action=ACTION_CREATE,
            subject_type="product",
            subject_id="1",
            payload={},
        )

    @patch("webhooks.factories.replay_delivery.add_task_to_queue")
    def test_replay_creates_additional_attempt(self, mock_queue):
        delivery = WebhookDelivery.objects.create(
            multi_tenant_company=self.company,
            outbox=self.outbox,
            webhook_integration=self.integration,
            status=WebhookDelivery.FAILED,
            attempt=1,
        )
        delivery.attempts.create(
            number=1,
            sent_at=timezone.now(),
            multi_tenant_company=self.company,
        )

        ReplayDelivery(delivery).run()

        delivery.refresh_from_db()
        self.assertEqual(delivery.status, WebhookDelivery.PENDING)
        self.assertEqual(delivery.attempt, 2)
        self.assertEqual(delivery.attempts.count(), 2)
        last_attempt = delivery.attempts.order_by("number").last()
        self.assertEqual(last_attempt.number, 2)
        self.assertEqual(last_attempt.delivery_id, delivery.id)
        mock_queue.assert_called_once()


class WebhookPruneFactoryTests(TestCase):
    def setUp(self):
        self.company = MultiTenantCompany.objects.create(name="TestCo")
        self.integration = WebhookIntegration.objects.create(
            multi_tenant_company=self.company,
            hostname="https://example.com",
            topic="product",
            url="https://webhook.example.com",
            retention_policy=RETENTION_3M,
        )

    def _create_delivery(self, *, status, sent_at, subject_id):
        outbox = WebhookOutbox.objects.create(
            multi_tenant_company=self.company,
            webhook_integration=self.integration,
            topic="product",
            action=ACTION_CREATE,
            subject_type="product",
            subject_id=subject_id,
            payload={},
        )
        delivery = WebhookDelivery.objects.create(
            multi_tenant_company=self.company,
            outbox=outbox,
            webhook_integration=self.integration,
            status=status,
            sent_at=sent_at,
        )
        WebhookDeliveryAttempt.objects.create(
            multi_tenant_company=self.company,
            delivery=delivery,
            number=1,
            sent_at=sent_at,
        )
        return outbox, delivery

    def test_prune_old_deliveries(self):
        now = timezone.now()
        old_outbox, old_delivery = self._create_delivery(
            status=WebhookDelivery.DELIVERED,
            sent_at=now - timedelta(days=91),
            subject_id="old",
        )
        _, fresh_delivery = self._create_delivery(
            status=WebhookDelivery.DELIVERED,
            sent_at=now - timedelta(days=10),
            subject_id="fresh",
        )
        self._create_delivery(
            status=WebhookDelivery.PENDING,
            sent_at=now - timedelta(days=91),
            subject_id="pending",
        )

        counts = WebhookPruneFactory(integration=self.integration).run()

        self.assertEqual(counts["deliveries"], 1)
        self.assertEqual(counts["attempts"], 1)
        self.assertEqual(counts["outboxes"], 1)
        self.assertFalse(
            WebhookDelivery.objects.filter(id=old_delivery.id).exists()
        )
        self.assertFalse(
            WebhookDeliveryAttempt.objects.filter(delivery_id=old_delivery.id).exists()
        )
        self.assertFalse(WebhookOutbox.objects.filter(id=old_outbox.id).exists())
        self.assertTrue(WebhookDelivery.objects.filter(id=fresh_delivery.id).exists())
