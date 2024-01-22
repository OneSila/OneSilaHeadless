from django.db.models.signals import post_save
from django.dispatch import receiver
from properties.models import Property, PropertyTranslation, PropertySelectValue, ProductProperty

import logging
logger = logging.getLogger(__name__)
