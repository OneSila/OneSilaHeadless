from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import MultiTenantCompany
from properties.models import Property, PropertyTranslation, PropertySelectValue, ProductProperty

import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=MultiTenantCompany)
def create_default_product_type_property(sender, instance, created, **kwargs):
    if created:
        Property.objects.create_product_type(instance)