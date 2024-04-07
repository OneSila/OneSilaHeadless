from django.db.models.signals import post_save
from django.dispatch import receiver
from properties.models import Property, PropertyTranslation, PropertySelectValue, ProductProperty

from core.schema.core.subscriptions import refresh_subscription_receiver

import logging
logger = logging.getLogger(__name__)
