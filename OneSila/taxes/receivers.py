from django.db.models.signals import post_save
from django.dispatch import receiver
from taxes.models import VatRate

from core.schema.core.subscriptions import refresh_subscription_receiver

import logging
logger = logging.getLogger(__name__)
