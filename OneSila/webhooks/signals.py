from django.db.models.signals import post_delete as django_post_delete
from core.signals import post_create, post_update
from properties.signals import (
    property_created,
    property_select_value_created,
    product_properties_rule_created,
    product_properties_rule_updated,
)
from products.signals import product_created
from properties.models import (
    Property,
    PropertySelectValue,
    ProductPropertiesRule,
)
from products.models import Product
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


EXCLUDED_CREATE_MODELS = {Property, PropertySelectValue, ProductPropertiesRule, Product}
EXCLUDED_UPDATE_MODELS = {ProductPropertiesRule}

for model in TOPIC_MAP.keys():
    if model not in EXCLUDED_CREATE_MODELS:
        post_create.connect(_post_create, sender=model)
    if model not in EXCLUDED_UPDATE_MODELS:
        post_update.connect(_post_update, sender=model)
    django_post_delete.connect(_post_delete, sender=model)

property_created.connect(_post_create, sender=Property)
property_select_value_created.connect(_post_create, sender=PropertySelectValue)
product_properties_rule_created.connect(_post_create, sender=ProductPropertiesRule)
product_properties_rule_updated.connect(_post_update, sender=ProductPropertiesRule)
product_created.connect(_post_create, sender=Product)
