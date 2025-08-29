from django.db import transaction
from django.db.models import Q
from django.forms.models import model_to_dict

from integrations.tasks import add_task_to_queue
from webhooks.constants import ACTION_UPDATE, ACTION_DELETE, TOPIC_MAP
from webhooks.models import WebhookIntegration, WebhookOutbox, WebhookDelivery


class SendIntegrationsWebhooksFactory:
    def __init__(self, *, instance, action):
        self.instance = instance
        self.action = action
        self.multi_tenant_company = instance.multi_tenant_company

    def set_topic(self):
        self.topic = TOPIC_MAP.get(self.instance.__class__)

    def set_dirty_fields(self):
        if self.action == ACTION_UPDATE:
            self.dirty_fields = self.instance.get_dirty_fields()
        else:
            self.dirty_fields = {}

    def set_subject(self):
        self.subject_type = self.instance._meta.label_lower
        self.subject_id = str(self.instance.pk)

    def set_integrations(self):
        self.integrations = WebhookIntegration.objects.filter(
            active=True,
            multi_tenant_company=self.multi_tenant_company,
        ).filter(Q(topic=self.topic) | Q(topic="all"))

    def create_outboxes(self):
        for integration in self.integrations:
            payload = (
                model_to_dict(self.instance)
                if self.action == ACTION_DELETE
                else {}
            )
            outbox = WebhookOutbox.objects.create(
                webhook_integration=integration,
                topic=self.topic,
                action=self.action,
                subject_type=self.subject_type,
                subject_id=self.subject_id,
                payload=payload,
                multi_tenant_company=self.multi_tenant_company,
            )

            transaction.on_commit(
                lambda lb_integration=integration, lb_outbox=outbox, lb_dirty_fields=self.dirty_fields: self._create_delivery_and_enqueue(
                    lb_integration, lb_outbox, lb_dirty_fields
                )
            )

    def _create_delivery_and_enqueue(self, integration, outbox, dirty_fields):
        delivery = WebhookDelivery.objects.create(
            outbox=outbox,
            webhook_integration=integration,
            status=WebhookDelivery.PENDING,
            attempt=0,
            multi_tenant_company=self.multi_tenant_company,
        )
        add_task_to_queue(
            integration_id=integration.id,
            task_func_path="webhooks.tasks.send_webhook_delivery",
            task_kwargs={
                "delivery_id": delivery.pk,
                "outbox_id": outbox.pk,
                "dirty_fields": dirty_fields,
            },
        )

    def run(self):
        self.set_topic()
        if not self.topic:
            return
        self.set_dirty_fields()
        self.set_subject()
        self.set_integrations()
        self.create_outboxes()
