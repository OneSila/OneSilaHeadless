from django.db.models.signals import post_delete as django_post_delete

from core.signals import post_create, post_update
from webhooks.constants import (
    ACTION_CREATE,
    ACTION_UPDATE,
    ACTION_DELETE,
    TOPIC_MAP,
)
from webhooks.factories.send_integrations_webhooks import SendIntegrationsWebhooksFactory


def _post_create(sender, instance, **kwargs):
    SendIntegrationsWebhooksFactory(instance=instance, action=ACTION_CREATE).run()


def _post_update(sender, instance, **kwargs):
    SendIntegrationsWebhooksFactory(instance=instance, action=ACTION_UPDATE).run()


def _post_delete(sender, instance, **kwargs):
    SendIntegrationsWebhooksFactory(instance=instance, action=ACTION_DELETE).run()


for model in TOPIC_MAP.keys():
    post_create.connect(_post_create, sender=model)
    post_update.connect(_post_update, sender=model)
    django_post_delete.connect(_post_delete, sender=model)

